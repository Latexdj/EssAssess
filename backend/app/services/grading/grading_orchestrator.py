"""
Grading orchestrator.

Responsibilities:
  1. Load submission + full relationship chain from DB
  2. Retrieve RAG context (reference chunks + example answer)
  3. Build GradingRequest
  4. Call the grading adapter (LocalGradingAdapter by default)
  5. Persist AIGradingResult + AICriterionScore records
  6. Update Submission.status

The adapter (GradingPort) is DB-free; all DB work lives here.
"""
import uuid as _uuid
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.models.submission import Submission, SubmissionStatus
from app.models.assignment import Assignment
from app.models.class_subject import ClassSubject
from app.models.rubric_criterion import RubricCriterion
from app.models.ai_grading_result import AIGradingResult
from app.models.ai_criterion_score import AICriterionScore
from app.services.grading.contracts import (
    GradingRequest,
    GradingResponse,
    CriterionInput,
    RetrievedChunkDTO,
)
from app.services.grading.ports import GradingPort, LocalGradingAdapter
from app.services.grading import rag_retriever


async def _load_submission(db: AsyncSession, submission_id: UUID) -> Submission:
    """Load submission with all relationships needed for grading."""
    stmt = (
        select(Submission)
        .where(Submission.id == submission_id)
        .options(
            selectinload(Submission.assignment).options(
                selectinload(Assignment.class_subject).selectinload(ClassSubject.subject),
                selectinload(Assignment.rubric_criteria),
            )
        )
    )
    result = await db.execute(stmt)
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    return sub


async def _get_or_create_grading_result(
    db: AsyncSession,
    submission_id: UUID,
) -> tuple[AIGradingResult, bool]:
    """Return (result, created). If an existing result exists, increment retry_count."""
    stmt = select(AIGradingResult).where(AIGradingResult.submission_id == submission_id)
    existing = (await db.execute(stmt)).scalar_one_or_none()

    if existing:
        existing.retry_count += 1
        return existing, False

    new_result = AIGradingResult(
        submission_id=submission_id,
        total_ai_score=0,
        formative_feedback="",
        raw_response={},
        model_used="",
        retry_count=0,
    )
    db.add(new_result)
    await db.flush()
    return new_result, True


async def run_grading(
    db: AsyncSession,
    submission_id: UUID,
    adapter: GradingPort | None = None,
) -> GradingResponse:
    """
    Full grading pipeline for a single submission.
    Never raises — on error, marks submission as grading_failed and
    returns a GradingResponse with error set.
    """
    if adapter is None:
        adapter = LocalGradingAdapter()

    # 1. Load submission
    try:
        sub = await _load_submission(db, submission_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load submission: {exc}")

    assignment = sub.assignment
    subject_tag = assignment.class_subject.subject.code

    # 2. Mark as in-progress
    sub.status = SubmissionStatus.grading_in_progress
    await db.flush()

    # 3. RAG retrieval (best-effort — proceed without context if it fails)
    reference_chunks: tuple[RetrievedChunkDTO, ...] = ()
    example_chunks:   tuple[RetrievedChunkDTO, ...] = ()
    rag_error: str | None = None
    try:
        ctx = await rag_retriever.retrieve_context(
            db,
            query=assignment.question_text,
            subject_tag=subject_tag,
        )
        reference_chunks = tuple(
            RetrievedChunkDTO(
                id=c.id,
                source_title=c.source_title,
                content=c.content,
                similarity=c.similarity,
                is_example=False,
            )
            for c in ctx["reference_chunks"]
        )
        example_chunks = tuple(
            RetrievedChunkDTO(
                id=c.id,
                source_title=c.source_title,
                content=c.content,
                similarity=c.similarity,
                is_example=True,
            )
            for c in ctx["example_chunks"]
        )
    except Exception as exc:
        rag_error = f"RAG retrieval failed (grading without context): {exc}"

    # 3.5 Load image bytes for image submissions (vision grading)
    image_base64:     str | None = None
    image_media_type: str        = "image/jpeg"
    if sub.submission_type.value == "image" and sub.file_path:
        import base64
        _type_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                     "webp": "image/webp", "gif": "image/gif"}
        try:
            with open(sub.file_path, "rb") as _fh:
                image_base64 = base64.b64encode(_fh.read()).decode()
            _ext = (sub.file_name or "").lower().rsplit(".", 1)[-1]
            image_media_type = _type_map.get(_ext, "image/jpeg")
        except OSError as _exc:
            _msg = f"image read error: {_exc}"
            rag_error = f"{rag_error} | {_msg}" if rag_error else _msg

    # 4. Build GradingRequest
    student_text = sub.transcribed_text or sub.text_content or ""
    criteria = tuple(
        CriterionInput(
            criterion_id=c.id,
            name=c.name,
            description=c.description or "",
            max_marks=c.max_marks,
            display_order=c.display_order,
        )
        for c in assignment.rubric_criteria
    )

    request = GradingRequest(
        submission_id=submission_id,
        assignment_id=assignment.id,
        question_text=assignment.question_text,
        student_text=student_text,
        subject_tag=subject_tag,
        criteria=criteria,
        max_marks=assignment.max_marks,
        reference_chunks=reference_chunks,
        example_chunks=example_chunks,
        image_base64=image_base64,
        image_media_type=image_media_type,
    )

    # 5. Grade
    response = await adapter.grade(request)

    # Prepend any RAG error to the grading error message
    final_error = response.error
    if rag_error:
        final_error = f"{rag_error} | {final_error}" if final_error else rag_error

    # 6. Persist results
    grading_result, _ = await _get_or_create_grading_result(db, submission_id)
    grading_result.total_ai_score     = response.total_score
    grading_result.formative_feedback = response.formative_feedback
    grading_result.raw_response       = response.raw_response
    grading_result.model_used         = response.model_used
    grading_result.tokens_input       = response.tokens_input
    grading_result.tokens_output      = response.tokens_output
    grading_result.error_message      = final_error
    grading_result.retrieved_chunk_ids = [
        _uuid.UUID(cid) for cid in response.retrieved_chunk_ids
    ] if response.retrieved_chunk_ids else []

    await db.flush()

    # 7. Persist per-criterion scores (upsert)
    for cs in response.criterion_scores:
        stmt = select(AICriterionScore).where(
            AICriterionScore.grading_result_id   == grading_result.id,
            AICriterionScore.rubric_criterion_id == cs.criterion_id,
        )
        existing_cs = (await db.execute(stmt)).scalar_one_or_none()
        if existing_cs:
            existing_cs.ai_score         = cs.score
            existing_cs.ai_justification = cs.justification
        else:
            db.add(AICriterionScore(
                grading_result_id=grading_result.id,
                rubric_criterion_id=cs.criterion_id,
                ai_score=cs.score,
                ai_justification=cs.justification,
            ))

    # 8. Update submission status
    sub.status = (
        SubmissionStatus.grading_failed
        if (response.error and not response.criterion_scores)
        else SubmissionStatus.graded
    )
    await db.flush()

    # Return the response (with any accumulated error info)
    return GradingResponse(
        submission_id=response.submission_id,
        criterion_scores=response.criterion_scores,
        total_score=response.total_score,
        formative_feedback=response.formative_feedback,
        raw_response=response.raw_response,
        model_used=response.model_used,
        tokens_input=response.tokens_input,
        tokens_output=response.tokens_output,
        retrieved_chunk_ids=response.retrieved_chunk_ids,
        error=final_error,
    )

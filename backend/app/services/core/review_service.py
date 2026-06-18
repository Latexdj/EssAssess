"""
Teacher grading review service.

Handles:
  - Loading the full per-criterion review view of a submission
  - Setting / removing criterion score overrides
  - Finalising the grade (computes effective total, creates FinalisedGrade)
  - Publishing the finalised grade to the student
"""
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.submission import Submission, SubmissionStatus
from app.models.assignment import Assignment
from app.models.class_subject import ClassSubject
from app.models.ai_grading_result import AIGradingResult
from app.models.grade_override import GradeOverride
from app.models.finalised_grade import FinalisedGrade
from app.schemas.review import (
    CriterionReviewOut,
    FinalisedGradeOut,
    SubmissionReviewOut,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _load(db: AsyncSession, submission_id: UUID) -> Submission:
    """Load a submission with all review-related relationships."""
    stmt = (
        select(Submission)
        .where(Submission.id == submission_id)
        .options(
            selectinload(Submission.student),
            selectinload(Submission.assignment).options(
                selectinload(Assignment.class_subject).selectinload(ClassSubject.teacher),
                selectinload(Assignment.rubric_criteria),
            ),
            selectinload(Submission.ai_grading_result).selectinload(
                AIGradingResult.criterion_scores
            ),
            selectinload(Submission.grade_overrides),
            selectinload(Submission.finalised_grade),
        )
    )
    sub = (await db.execute(stmt)).scalar_one_or_none()
    if not sub:
        raise HTTPException(404, "Submission not found")
    return sub


def _authorise(sub: Submission, requester_id: UUID, is_admin: bool) -> None:
    if is_admin:
        return
    teacher_id = sub.assignment.class_subject.teacher_id
    if teacher_id != requester_id:
        raise HTTPException(403, "You are not the assigned teacher for this submission")


def _build(sub: Submission) -> SubmissionReviewOut:
    """Convert a fully-loaded Submission into SubmissionReviewOut."""
    ai_scores = {}
    ai_feedback: str | None = None
    total_ai: float | None = None
    if sub.ai_grading_result:
        ai_feedback = sub.ai_grading_result.formative_feedback
        total_ai    = float(sub.ai_grading_result.total_ai_score)
        ai_scores   = {cs.rubric_criterion_id: cs for cs in sub.ai_grading_result.criterion_scores}

    overrides = {go.rubric_criterion_id: go for go in sub.grade_overrides}

    criteria_out: list[CriterionReviewOut] = []
    for c in sorted(sub.assignment.rubric_criteria, key=lambda x: x.display_order):
        ai_cs    = ai_scores.get(c.id)
        override = overrides.get(c.id)
        ai_val   = float(ai_cs.ai_score)        if ai_cs    else None
        ov_val   = float(override.overridden_score) if override else None
        effective = ov_val if ov_val is not None else (ai_val or 0.0)
        criteria_out.append(CriterionReviewOut(
            criterion_id=c.id,
            name=c.name,
            description=c.description or "",
            max_marks=c.max_marks,
            display_order=c.display_order,
            ai_score=ai_val,
            ai_justification=ai_cs.ai_justification if ai_cs else None,
            override_score=ov_val,
            override_note=override.override_note if override else None,
            effective_score=effective,
        ))

    effective_total = sum(c.effective_score for c in criteria_out)

    fg = sub.finalised_grade
    fg_out: FinalisedGradeOut | None = None
    if fg:
        fg_out = FinalisedGradeOut(
            id=fg.id,
            submission_id=fg.submission_id,
            teacher_id=fg.teacher_id,
            total_score=float(fg.total_score),
            teacher_comment=fg.teacher_comment,
            is_published=fg.is_published,
            finalised_at=fg.finalised_at,
        )

    student = sub.student
    name = f"{student.first_name} {student.last_name}" if student else None

    return SubmissionReviewOut(
        id=sub.id,
        assignment_id=sub.assignment_id,
        student_id=sub.student_id,
        student_name=name,
        submission_type=sub.submission_type.value,
        status=sub.status.value,
        text_content=sub.text_content,
        file_name=sub.file_name,
        submitted_at=sub.submitted_at,
        assignment_title=sub.assignment.title,
        question_text=sub.assignment.question_text,
        max_marks=sub.assignment.max_marks,
        total_ai_score=total_ai,
        formative_feedback=ai_feedback,
        criteria=criteria_out,
        effective_total=effective_total,
        finalised_grade=fg_out,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def get_review(
    db:           AsyncSession,
    submission_id: UUID,
    requester_id:  UUID,
    is_admin:      bool,
) -> SubmissionReviewOut:
    sub = await _load(db, submission_id)
    _authorise(sub, requester_id, is_admin)
    return _build(sub)


async def set_override(
    db:            AsyncSession,
    submission_id: UUID,
    criterion_id:  UUID,
    teacher_id:    UUID,
    score:         float,
    note:          str | None,
) -> SubmissionReviewOut:
    sub = await _load(db, submission_id)
    _authorise(sub, teacher_id, False)

    if sub.status.value not in ("graded", "finalised"):
        raise HTTPException(422, "Submission must be graded before overrides can be set")

    criterion = next(
        (c for c in sub.assignment.rubric_criteria if c.id == criterion_id), None
    )
    if not criterion:
        raise HTTPException(404, "Criterion not found for this assignment")
    if score < 0 or score > criterion.max_marks:
        raise HTTPException(422, f"Score must be between 0 and {criterion.max_marks}")

    # Upsert
    existing_ov = next(
        (go for go in sub.grade_overrides if go.rubric_criterion_id == criterion_id), None
    )
    if existing_ov:
        existing_ov.overridden_score = score
        existing_ov.override_note    = note
        existing_ov.teacher_id       = teacher_id
    else:
        db.add(GradeOverride(
            submission_id=submission_id,
            rubric_criterion_id=criterion_id,
            teacher_id=teacher_id,
            overridden_score=score,
            override_note=note,
        ))

    await db.flush()
    sub = await _load(db, submission_id)
    return _build(sub)


async def remove_override(
    db:            AsyncSession,
    submission_id: UUID,
    criterion_id:  UUID,
    teacher_id:    UUID,
) -> SubmissionReviewOut:
    sub = await _load(db, submission_id)
    _authorise(sub, teacher_id, False)

    override = next(
        (go for go in sub.grade_overrides if go.rubric_criterion_id == criterion_id), None
    )
    if override:
        await db.delete(override)
        await db.flush()

    sub = await _load(db, submission_id)
    return _build(sub)


async def finalise(
    db:              AsyncSession,
    submission_id:   UUID,
    teacher_id:      UUID,
    teacher_comment: str | None,
) -> SubmissionReviewOut:
    sub = await _load(db, submission_id)
    _authorise(sub, teacher_id, False)

    if sub.status.value not in ("graded", "grading_failed", "finalised"):
        raise HTTPException(422, "Submission must be graded before it can be finalised")

    # Compute effective total from current overrides + AI scores
    ai_scores = {}
    if sub.ai_grading_result:
        ai_scores = {cs.rubric_criterion_id: float(cs.ai_score)
                     for cs in sub.ai_grading_result.criterion_scores}
    overrides = {go.rubric_criterion_id: float(go.overridden_score)
                 for go in sub.grade_overrides}

    effective_total = sum(
        overrides.get(c.id, ai_scores.get(c.id, 0.0))
        for c in sub.assignment.rubric_criteria
    )

    fg = sub.finalised_grade
    if fg:
        fg.total_score     = effective_total
        fg.teacher_comment = teacher_comment
        fg.teacher_id      = teacher_id
    else:
        db.add(FinalisedGrade(
            submission_id=submission_id,
            teacher_id=teacher_id,
            total_score=effective_total,
            teacher_comment=teacher_comment,
            is_published=False,
        ))

    sub.status = SubmissionStatus.finalised
    await db.flush()

    sub = await _load(db, submission_id)
    return _build(sub)


async def publish_grade(
    db:            AsyncSession,
    submission_id: UUID,
    teacher_id:    UUID,
) -> SubmissionReviewOut:
    sub = await _load(db, submission_id)
    _authorise(sub, teacher_id, False)

    if not sub.finalised_grade:
        raise HTTPException(422, "Grade must be finalised before it can be published")

    sub.finalised_grade.is_published = True
    await db.flush()

    sub = await _load(db, submission_id)
    return _build(sub)

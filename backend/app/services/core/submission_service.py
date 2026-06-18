"""
Submission service.

Handles create / get / list for student essay submissions.
Three submission types:
  text  — student types their answer; stored in text_content.
  pdf   — student uploads a PDF; text is extracted and stored in transcribed_text.
  image — student uploads an image of a handwritten essay; raw file saved for Claude vision.

Re-submission rules:
  - Already graded or grading_in_progress → 409
  - pending_grading or grading_failed → update the existing record
"""
import os
import re
import uuid
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.submission import Submission, SubmissionType, SubmissionStatus
from app.models.assignment import Assignment
from app.models.class_subject import ClassSubject
from app.models.enrolment import Enrolment
from app.models.user import User
from app.schemas.submission import SubmissionOut


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MEDIA_TYPES = {
    "jpg":  "image/jpeg",
    "jpeg": "image/jpeg",
    "png":  "image/png",
    "webp": "image/webp",
    "gif":  "image/gif",
}
_ALLOWED_IMAGE_EXTS = set(_MEDIA_TYPES)
_MAX_IMAGE_BYTES = 10 * 1024 * 1024


def _safe_filename(original: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]", "_", original)[:100]


def _enrich(sub: Submission) -> SubmissionOut:
    ai = sub.ai_grading_result
    student_name: str | None = None
    if sub.student:
        student_name = f"{sub.student.first_name} {sub.student.last_name}"
    return SubmissionOut(
        id=sub.id,
        assignment_id=sub.assignment_id,
        student_id=sub.student_id,
        submission_type=sub.submission_type.value,
        status=sub.status.value,
        text_content=sub.text_content,
        file_name=sub.file_name,
        file_size_bytes=sub.file_size_bytes,
        submitted_at=sub.submitted_at,
        updated_at=sub.updated_at,
        student_name=student_name,
        total_ai_score=float(ai.total_ai_score) if ai else None,
        formative_feedback=ai.formative_feedback if ai else None,
        error_message=ai.error_message if ai else None,
    )


async def _load_assignment(db: AsyncSession, assignment_id: UUID) -> Assignment:
    stmt = (
        select(Assignment)
        .where(Assignment.id == assignment_id, Assignment.is_published == True)
        .options(selectinload(Assignment.class_subject))
    )
    a = (await db.execute(stmt)).scalar_one_or_none()
    if not a:
        raise HTTPException(404, "Assignment not found or not published")
    return a


async def _check_enrolment(db: AsyncSession, class_id: UUID, student_id: UUID) -> None:
    stmt = select(func.count()).select_from(Enrolment).where(
        Enrolment.class_id == class_id,
        Enrolment.student_id == student_id,
        Enrolment.is_active == True,
    )
    count = (await db.execute(stmt)).scalar()
    if not count:
        raise HTTPException(403, "You are not enrolled in this class")


async def _get_existing(db: AsyncSession, assignment_id: UUID, student_id: UUID) -> Submission | None:
    stmt = select(Submission).where(
        Submission.assignment_id == assignment_id,
        Submission.student_id == student_id,
    )
    return (await db.execute(stmt)).scalar_one_or_none()


def _guard_resubmit(existing: Submission | None) -> None:
    if existing is None:
        return
    if existing.status == SubmissionStatus.grading_in_progress:
        raise HTTPException(409, "Your submission is currently being graded")
    if existing.status == SubmissionStatus.graded:
        raise HTTPException(409, "You have already submitted and this assignment has been graded")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def create_text_submission(
    db:            AsyncSession,
    assignment_id: UUID,
    student_id:    UUID,
    text_content:  str,
) -> SubmissionOut:
    a = await _load_assignment(db, assignment_id)
    await _check_enrolment(db, a.class_subject.class_id, student_id)

    if "text" not in a.allowed_submission_types:
        raise HTTPException(422, "Text submissions are not allowed for this assignment")

    existing = await _get_existing(db, assignment_id, student_id)
    _guard_resubmit(existing)

    if existing:
        existing.text_content     = text_content
        existing.submission_type  = SubmissionType.text
        existing.status           = SubmissionStatus.pending_grading
        existing.file_path        = None
        existing.file_name        = None
        existing.file_size_bytes  = None
        existing.transcribed_text = None
        await db.flush()
        sub = existing
    else:
        now = datetime.now(timezone.utc)
        sub = Submission(
            id=uuid.uuid4(),
            assignment_id=assignment_id,
            student_id=student_id,
            submission_type=SubmissionType.text,
            status=SubmissionStatus.pending_grading,
            text_content=text_content,
            submitted_at=now,
            updated_at=now,
        )
        db.add(sub)
        await db.flush()

    # Load student for denormalisation
    sub.student = await db.get(User, student_id)
    sub.ai_grading_result = None
    return _enrich(sub)


async def create_file_submission(
    db:            AsyncSession,
    assignment_id: UUID,
    student_id:    UUID,
    file_bytes:    bytes,
    original_name: str,
    upload_dir:    str,
) -> SubmissionOut:
    ext = original_name.lower().rsplit(".", 1)[-1] if "." in original_name else ""

    if ext == "pdf":
        sub_type = SubmissionType.pdf
    elif ext in _ALLOWED_IMAGE_EXTS:
        sub_type = SubmissionType.image
    else:
        raise HTTPException(422, "Only PDF and image files (JPEG/PNG/WebP) are accepted")

    a = await _load_assignment(db, assignment_id)
    await _check_enrolment(db, a.class_subject.class_id, student_id)

    if sub_type.value not in a.allowed_submission_types:
        raise HTTPException(422, f"{sub_type.value.upper()} submissions are not allowed for this assignment")

    if len(file_bytes) > _MAX_IMAGE_BYTES:
        raise HTTPException(413, "File too large. Maximum size is 10 MB")

    existing = await _get_existing(db, assignment_id, student_id)
    _guard_resubmit(existing)

    # For PDFs, extract text immediately
    transcribed: str | None = None
    if sub_type == SubmissionType.pdf:
        from app.services.grading.knowledge_service import extract_text_from_pdf
        try:
            transcribed = extract_text_from_pdf(file_bytes)
        except Exception:
            transcribed = None  # grade will fail gracefully

    # Persist file — we need an ID first
    tmp_id = existing.id if existing else uuid.uuid4()
    safe = _safe_filename(original_name)
    dest_dir = os.path.join(upload_dir, "submissions", str(tmp_id))
    os.makedirs(dest_dir, exist_ok=True)
    file_path = os.path.join(dest_dir, safe)
    with open(file_path, "wb") as fh:
        fh.write(file_bytes)

    if existing:
        # Remove old file if different path
        if existing.file_path and existing.file_path != file_path:
            try:
                os.remove(existing.file_path)
            except OSError:
                pass
        existing.submission_type  = sub_type
        existing.status           = SubmissionStatus.pending_grading
        existing.text_content     = None
        existing.file_path        = file_path
        existing.file_name        = original_name
        existing.file_size_bytes  = len(file_bytes)
        existing.transcribed_text = transcribed
        await db.flush()
        sub = existing
    else:
        now = datetime.now(timezone.utc)
        sub = Submission(
            id=tmp_id,
            assignment_id=assignment_id,
            student_id=student_id,
            submission_type=sub_type,
            status=SubmissionStatus.pending_grading,
            file_path=file_path,
            file_name=original_name,
            file_size_bytes=len(file_bytes),
            transcribed_text=transcribed,
            submitted_at=now,
            updated_at=now,
        )
        db.add(sub)
        await db.flush()

    sub.student = await db.get(User, student_id)
    sub.ai_grading_result = None
    return _enrich(sub)


async def get_submission(db: AsyncSession, submission_id: UUID) -> SubmissionOut:
    stmt = (
        select(Submission)
        .where(Submission.id == submission_id)
        .options(
            selectinload(Submission.ai_grading_result),
            selectinload(Submission.student),
        )
    )
    sub = (await db.execute(stmt)).scalar_one_or_none()
    if not sub:
        raise HTTPException(404, "Submission not found")
    return _enrich(sub)


async def list_submissions(
    db:            AsyncSession,
    *,
    assignment_id: UUID | None = None,
    student_id:    UUID | None = None,
) -> list[SubmissionOut]:
    stmt = (
        select(Submission)
        .options(
            selectinload(Submission.ai_grading_result),
            selectinload(Submission.student),
        )
        .order_by(Submission.submitted_at.desc())
    )
    if assignment_id:
        stmt = stmt.where(Submission.assignment_id == assignment_id)
    if student_id:
        stmt = stmt.where(Submission.student_id == student_id)

    rows = (await db.execute(stmt)).scalars().all()
    return [_enrich(s) for s in rows]

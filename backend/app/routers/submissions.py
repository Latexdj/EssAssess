import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, BackgroundTasks, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role, get_current_user
from app.models.user import User
from app.models.submission import Submission
from app.models.assignment import Assignment
from app.schemas.submission import TextSubmissionCreate, SubmissionOut
from app.schemas.review import OverrideIn, FinaliseRequest, SubmissionReviewOut
from app.services.core import submission_service, review_service
from app.tasks.grade_submission import grade_submission_task
from app.config import settings

router = APIRouter(prefix="/submissions", tags=["submissions"])


# ---------------------------------------------------------------------------
# POST /submissions  — text submission
# ---------------------------------------------------------------------------
@router.post("", response_model=SubmissionOut, status_code=201)
async def submit_text(
    body:             TextSubmissionCreate,
    background_tasks: BackgroundTasks,
    db:               AsyncSession = Depends(get_db),
    current_user:     User         = Depends(require_role("student")),
) -> SubmissionOut:
    out = await submission_service.create_text_submission(
        db, body.assignment_id, current_user.id, body.text_content
    )
    # Commit before scheduling the background task so the record is visible to the
    # new DB session the background task creates.
    await db.commit()
    background_tasks.add_task(grade_submission_task, out.id)
    return out


# ---------------------------------------------------------------------------
# POST /submissions/file  — PDF or image upload
# ---------------------------------------------------------------------------
@router.post("/file", response_model=SubmissionOut, status_code=201)
async def submit_file(
    assignment_id:    UUID          = Form(...),
    file:             UploadFile    = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db:               AsyncSession  = Depends(get_db),
    current_user:     User          = Depends(require_role("student")),
) -> SubmissionOut:
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    file_bytes = await file.read()
    if len(file_bytes) > max_bytes:
        raise HTTPException(413, f"File too large. Maximum {settings.max_file_size_mb} MB")

    out = await submission_service.create_file_submission(
        db,
        assignment_id,
        current_user.id,
        file_bytes,
        file.filename or "upload",
        settings.upload_dir,
    )
    await db.commit()
    background_tasks.add_task(grade_submission_task, out.id)
    return out


# ---------------------------------------------------------------------------
# GET /submissions  — list (filtered)
# ---------------------------------------------------------------------------
@router.get("", response_model=list[SubmissionOut])
async def list_submissions(
    assignment_id: UUID | None = None,
    db:            AsyncSession = Depends(get_db),
    current_user:  User        = Depends(get_current_user),
) -> list[SubmissionOut]:
    # Students only see their own submissions; teachers/admin see all for the assignment
    student_filter = current_user.id if current_user.role.value == "student" else None
    return await submission_service.list_submissions(
        db,
        assignment_id=assignment_id,
        student_id=student_filter,
    )


# ---------------------------------------------------------------------------
# GET /submissions/{id}  — single submission
# ---------------------------------------------------------------------------
@router.get("/{submission_id}", response_model=SubmissionOut)
async def get_submission(
    submission_id: UUID,
    db:            AsyncSession = Depends(get_db),
    current_user:  User        = Depends(get_current_user),
) -> SubmissionOut:
    out = await submission_service.get_submission(db, submission_id)

    # Students can only read their own submissions
    if current_user.role.value == "student" and out.student_id != current_user.id:
        raise HTTPException(403, "Access denied")

    return out


# ---------------------------------------------------------------------------
# Review endpoints (teacher/admin only)
# ---------------------------------------------------------------------------

@router.get("/{submission_id}/review", response_model=SubmissionReviewOut)
async def get_review(
    submission_id: UUID,
    db:            AsyncSession = Depends(get_db),
    current_user:  User        = Depends(get_current_user),
) -> SubmissionReviewOut:
    if current_user.role.value == "student":
        raise HTTPException(403, "Teacher access required")
    is_admin = current_user.role.value == "admin"
    return await review_service.get_review(db, submission_id, current_user.id, is_admin)


@router.post("/{submission_id}/overrides", response_model=SubmissionReviewOut)
async def set_override(
    submission_id: UUID,
    body:          OverrideIn,
    db:            AsyncSession = Depends(get_db),
    current_user:  User        = Depends(require_role("teacher")),
) -> SubmissionReviewOut:
    return await review_service.set_override(
        db, submission_id, body.rubric_criterion_id, current_user.id,
        body.overridden_score, body.override_note,
    )


@router.delete("/{submission_id}/overrides/{criterion_id}", response_model=SubmissionReviewOut)
async def remove_override(
    submission_id: UUID,
    criterion_id:  UUID,
    db:            AsyncSession = Depends(get_db),
    current_user:  User        = Depends(require_role("teacher")),
) -> SubmissionReviewOut:
    return await review_service.remove_override(
        db, submission_id, criterion_id, current_user.id,
    )


@router.post("/{submission_id}/finalise", response_model=SubmissionReviewOut)
async def finalise(
    submission_id: UUID,
    body:          FinaliseRequest,
    db:            AsyncSession = Depends(get_db),
    current_user:  User        = Depends(require_role("teacher")),
) -> SubmissionReviewOut:
    return await review_service.finalise(
        db, submission_id, current_user.id, body.teacher_comment,
    )


@router.post("/{submission_id}/publish-grade", response_model=SubmissionReviewOut)
async def publish_grade(
    submission_id: UUID,
    db:            AsyncSession = Depends(get_db),
    current_user:  User        = Depends(require_role("teacher")),
) -> SubmissionReviewOut:
    return await review_service.publish_grade(db, submission_id, current_user.id)

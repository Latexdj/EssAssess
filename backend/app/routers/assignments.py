import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.user import UserRole
from app.models.submission import Submission
from app.schemas.assignment import (
    AssignmentCreate, AssignmentUpdate, AssignmentOut,
    RubricCriterionCreate, RubricCriterionUpdate, RubricCriterionOut,
)
from app.services.core import assignment_service

router = APIRouter(prefix="/assignments", tags=["assignments"])


def _enrich(a, submission_count: int = 0) -> AssignmentOut:
    """Build AssignmentOut with denormalised display fields."""
    cs = a.class_subject
    return AssignmentOut(
        id=a.id,
        class_subject_id=a.class_subject_id,
        title=a.title,
        question_text=a.question_text,
        instructions=a.instructions,
        allowed_submission_types=a.allowed_submission_types,
        max_marks=a.max_marks,
        due_date=a.due_date,
        is_published=a.is_published,
        created_at=a.created_at,
        rubric_criteria=a.rubric_criteria,
        subject_name=cs.subject.name  if cs and cs.subject  else None,
        subject_code=cs.subject.code  if cs and cs.subject  else None,
        class_name=cs.class_.name     if cs and cs.class_   else None,
        teacher_name=(
            f"{cs.teacher.first_name} {cs.teacher.last_name}"
            if cs and cs.teacher else None
        ),
        submission_count=submission_count,
    )


async def _count_submissions(db: AsyncSession, assignment_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
    if not assignment_ids:
        return {}
    result = await db.execute(
        select(Submission.assignment_id, func.count(Submission.id))
        .where(Submission.assignment_id.in_(assignment_ids))
        .group_by(Submission.assignment_id)
    )
    return {row[0]: row[1] for row in result.all()}


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.post("", response_model=AssignmentOut, status_code=201)
async def create_assignment(
    body: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("teacher")),
):
    a = await assignment_service.create_assignment(
        db,
        class_subject_id=body.class_subject_id,
        teacher_id=current_user.id,
        title=body.title,
        question_text=body.question_text,
        instructions=body.instructions,
        allowed_submission_types=body.allowed_submission_types,
        max_marks=body.max_marks,
        due_date=body.due_date,
    )
    return _enrich(a)


@router.get("", response_model=list[AssignmentOut])
async def list_assignments(
    class_id:         uuid.UUID | None = Query(None),
    class_subject_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role == UserRole.student:
        assignments = await assignment_service.list_student_assignments(db, current_user.id)
    elif current_user.role == UserRole.teacher:
        assignments = await assignment_service.list_assignments(
            db,
            class_subject_id=class_subject_id,
            class_id=class_id,
            teacher_id=current_user.id,
        )
    else:  # admin
        assignments = await assignment_service.list_assignments(
            db,
            class_subject_id=class_subject_id,
            class_id=class_id,
        )

    counts = await _count_submissions(db, [a.id for a in assignments])
    return [_enrich(a, counts.get(a.id, 0)) for a in assignments]


@router.get("/{assignment_id}", response_model=AssignmentOut)
async def get_assignment(
    assignment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    a = await assignment_service.get_assignment(db, assignment_id)
    count_map = await _count_submissions(db, [assignment_id])
    return _enrich(a, count_map.get(assignment_id, 0))


@router.patch("/{assignment_id}", response_model=AssignmentOut)
async def update_assignment(
    assignment_id: uuid.UUID,
    body: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("teacher")),
):
    a = await assignment_service.update_assignment(
        db, assignment_id, current_user.id,
        **{k: v for k, v in body.model_dump().items() if v is not None},
    )
    return _enrich(a)


@router.post("/{assignment_id}/publish", response_model=AssignmentOut)
async def publish_assignment(
    assignment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("teacher")),
):
    a = await assignment_service.publish_assignment(db, assignment_id, current_user.id)
    return _enrich(a)


@router.delete("/{assignment_id}", status_code=204)
async def delete_assignment(
    assignment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("teacher")),
):
    await assignment_service.delete_assignment(db, assignment_id, current_user.id)


# ── Rubric criteria ───────────────────────────────────────────────────────────

@router.post("/{assignment_id}/criteria", response_model=RubricCriterionOut, status_code=201)
async def add_criterion(
    assignment_id: uuid.UUID,
    body: RubricCriterionCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("teacher")),
):
    c = await assignment_service.add_criterion(
        db, assignment_id, current_user.id,
        name=body.name, description=body.description, max_marks=body.max_marks,
    )
    return RubricCriterionOut.model_validate(c)


@router.patch("/{assignment_id}/criteria/{criterion_id}", response_model=RubricCriterionOut)
async def update_criterion(
    assignment_id: uuid.UUID,
    criterion_id: uuid.UUID,
    body: RubricCriterionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("teacher")),
):
    c = await assignment_service.update_criterion(
        db, criterion_id, current_user.id,
        name=body.name, description=body.description, max_marks=body.max_marks,
    )
    return RubricCriterionOut.model_validate(c)


@router.delete("/{assignment_id}/criteria/{criterion_id}", status_code=204)
async def delete_criterion(
    assignment_id: uuid.UUID,
    criterion_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("teacher")),
):
    await assignment_service.delete_criterion(db, criterion_id, current_user.id)


@router.post("/{assignment_id}/criteria/{criterion_id}/move", status_code=204)
async def move_criterion(
    assignment_id: uuid.UUID,
    criterion_id: uuid.UUID,
    direction: str = Query(..., pattern="^(up|down)$"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("teacher")),
):
    await assignment_service.move_criterion(db, criterion_id, current_user.id, direction)

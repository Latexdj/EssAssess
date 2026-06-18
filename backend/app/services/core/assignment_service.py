import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.assignment import Assignment
from app.models.rubric_criterion import RubricCriterion
from app.models.class_subject import ClassSubject
from app.models.submission import Submission
from app.models.enrolment import Enrolment


async def _load_assignment(db: AsyncSession, assignment_id: uuid.UUID) -> Assignment:
    result = await db.execute(
        select(Assignment)
        .where(Assignment.id == assignment_id)
        .options(
            selectinload(Assignment.rubric_criteria),
            selectinload(Assignment.class_subject).selectinload(ClassSubject.subject),
            selectinload(Assignment.class_subject).selectinload(ClassSubject.teacher),
            selectinload(Assignment.class_subject).selectinload(ClassSubject.class_),
        )
    )
    a = result.scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return a


async def _assert_teacher_owns(cs: ClassSubject, teacher_id: uuid.UUID) -> None:
    if cs.teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="You are not the teacher for this class subject")


# ── Assignment CRUD ───────────────────────────────────────────────────────────

async def create_assignment(
    db: AsyncSession,
    *,
    class_subject_id: uuid.UUID,
    teacher_id: uuid.UUID,
    title: str,
    question_text: str,
    instructions: str | None,
    allowed_submission_types: list[str],
    max_marks: int,
    due_date: datetime,
) -> Assignment:
    cs = await db.get(ClassSubject, class_subject_id)
    if not cs:
        raise HTTPException(status_code=404, detail="Class subject not found")
    await _assert_teacher_owns(cs, teacher_id)

    a = Assignment(
        class_subject_id=class_subject_id,
        title=title,
        question_text=question_text,
        instructions=instructions,
        allowed_submission_types=allowed_submission_types,
        max_marks=max_marks,
        due_date=due_date,
        is_published=False,
    )
    db.add(a)
    await db.flush()
    return await _load_assignment(db, a.id)


async def get_assignment(db: AsyncSession, assignment_id: uuid.UUID) -> Assignment:
    return await _load_assignment(db, assignment_id)


async def list_assignments(
    db: AsyncSession,
    *,
    class_subject_id: uuid.UUID | None = None,
    class_id: uuid.UUID | None = None,
    teacher_id: uuid.UUID | None = None,
    is_published: bool | None = None,
) -> list[Assignment]:
    """Return assignments with their class_subject (for display names)."""
    stmt = (
        select(Assignment)
        .options(
            selectinload(Assignment.rubric_criteria),
            selectinload(Assignment.class_subject).selectinload(ClassSubject.subject),
            selectinload(Assignment.class_subject).selectinload(ClassSubject.teacher),
            selectinload(Assignment.class_subject).selectinload(ClassSubject.class_),
        )
        .order_by(Assignment.due_date)
    )

    if class_subject_id is not None:
        stmt = stmt.where(Assignment.class_subject_id == class_subject_id)

    if class_id is not None:
        stmt = stmt.join(ClassSubject, Assignment.class_subject_id == ClassSubject.id).where(
            ClassSubject.class_id == class_id
        )
        if teacher_id is not None:
            stmt = stmt.where(ClassSubject.teacher_id == teacher_id)

    if is_published is not None:
        stmt = stmt.where(Assignment.is_published == is_published)

    result = await db.execute(stmt)
    return list(result.scalars().unique().all())


async def list_student_assignments(
    db: AsyncSession,
    student_id: uuid.UUID,
) -> list[Assignment]:
    """Published assignments for all classes the student is enrolled in."""
    enrolled_class_ids = select(Enrolment.class_id).where(
        Enrolment.student_id == student_id,
        Enrolment.is_active == True,
    )
    stmt = (
        select(Assignment)
        .join(ClassSubject, Assignment.class_subject_id == ClassSubject.id)
        .where(
            ClassSubject.class_id.in_(enrolled_class_ids),
            Assignment.is_published == True,
        )
        .options(
            selectinload(Assignment.rubric_criteria),
            selectinload(Assignment.class_subject).selectinload(ClassSubject.subject),
            selectinload(Assignment.class_subject).selectinload(ClassSubject.teacher),
            selectinload(Assignment.class_subject).selectinload(ClassSubject.class_),
        )
        .order_by(Assignment.due_date)
    )
    result = await db.execute(stmt)
    return list(result.scalars().unique().all())


async def update_assignment(
    db: AsyncSession,
    assignment_id: uuid.UUID,
    teacher_id: uuid.UUID,
    **kwargs,
) -> Assignment:
    a = await _load_assignment(db, assignment_id)
    await _assert_teacher_owns(a.class_subject, teacher_id)
    if a.is_published:
        # Allow updating instructions/due date only after publishing
        allowed_after_publish = {"instructions", "due_date"}
        disallowed = set(kwargs.keys()) - allowed_after_publish
        if disallowed:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot edit {disallowed} on a published assignment",
            )
    for k, v in kwargs.items():
        if v is not None:
            setattr(a, k, v)
    await db.flush()
    return await _load_assignment(db, assignment_id)


async def publish_assignment(
    db: AsyncSession,
    assignment_id: uuid.UUID,
    teacher_id: uuid.UUID,
) -> Assignment:
    a = await _load_assignment(db, assignment_id)
    await _assert_teacher_owns(a.class_subject, teacher_id)
    if not a.rubric_criteria:
        raise HTTPException(
            status_code=422,
            detail="Cannot publish an assignment with no rubric criteria",
        )
    a.is_published = True
    await db.flush()
    return await _load_assignment(db, assignment_id)


async def delete_assignment(
    db: AsyncSession,
    assignment_id: uuid.UUID,
    teacher_id: uuid.UUID,
) -> None:
    a = await _load_assignment(db, assignment_id)
    await _assert_teacher_owns(a.class_subject, teacher_id)
    if a.is_published:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a published assignment",
        )
    await db.delete(a)
    await db.flush()


# ── Rubric criteria ───────────────────────────────────────────────────────────

async def _next_order(db: AsyncSession, assignment_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.max(RubricCriterion.display_order)).where(
            RubricCriterion.assignment_id == assignment_id
        )
    )
    current_max = result.scalar_one_or_none()
    return (current_max or 0) + 1


async def add_criterion(
    db: AsyncSession,
    assignment_id: uuid.UUID,
    teacher_id: uuid.UUID,
    name: str,
    description: str,
    max_marks: int,
) -> RubricCriterion:
    a = await _load_assignment(db, assignment_id)
    await _assert_teacher_owns(a.class_subject, teacher_id)
    order = await _next_order(db, assignment_id)
    c = RubricCriterion(
        assignment_id=assignment_id,
        name=name,
        description=description,
        max_marks=max_marks,
        display_order=order,
    )
    db.add(c)
    await db.flush()
    await db.refresh(c)
    return c


async def update_criterion(
    db: AsyncSession,
    criterion_id: uuid.UUID,
    teacher_id: uuid.UUID,
    name: str | None = None,
    description: str | None = None,
    max_marks: int | None = None,
) -> RubricCriterion:
    c = await db.get(RubricCriterion, criterion_id)
    if not c:
        raise HTTPException(status_code=404, detail="Criterion not found")
    # Verify ownership via assignment
    a = await _load_assignment(db, c.assignment_id)
    await _assert_teacher_owns(a.class_subject, teacher_id)

    if name        is not None: c.name        = name
    if description is not None: c.description = description
    if max_marks   is not None: c.max_marks   = max_marks
    await db.flush()
    await db.refresh(c)
    return c


async def delete_criterion(
    db: AsyncSession,
    criterion_id: uuid.UUID,
    teacher_id: uuid.UUID,
) -> None:
    c = await db.get(RubricCriterion, criterion_id)
    if not c:
        raise HTTPException(status_code=404, detail="Criterion not found")
    a = await _load_assignment(db, c.assignment_id)
    await _assert_teacher_owns(a.class_subject, teacher_id)
    await db.delete(c)
    await db.flush()


async def move_criterion(
    db: AsyncSession,
    criterion_id: uuid.UUID,
    teacher_id: uuid.UUID,
    direction: str,  # "up" | "down"
) -> None:
    """Swap display_order with the adjacent criterion."""
    c = await db.get(RubricCriterion, criterion_id)
    if not c:
        raise HTTPException(status_code=404, detail="Criterion not found")
    a = await _load_assignment(db, c.assignment_id)
    await _assert_teacher_owns(a.class_subject, teacher_id)

    criteria = sorted(a.rubric_criteria, key=lambda x: x.display_order)
    idx = next((i for i, x in enumerate(criteria) if x.id == criterion_id), None)
    if idx is None:
        return
    swap_idx = idx - 1 if direction == "up" else idx + 1
    if swap_idx < 0 or swap_idx >= len(criteria):
        return

    criteria[idx].display_order, criteria[swap_idx].display_order = (
        criteria[swap_idx].display_order,
        criteria[idx].display_order,
    )
    await db.flush()

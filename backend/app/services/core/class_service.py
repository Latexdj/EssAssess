import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.class_ import Class
from app.models.class_subject import ClassSubject
from app.models.subject import Subject
from app.models.user import User, UserRole
from app.models.enrolment import Enrolment


async def create_class(
    db: AsyncSession,
    school_id: uuid.UUID,
    name: str,
    programme: str | None,
    year_group: int | None,
    academic_year: str | None,
) -> Class:
    cls = Class(
        school_id=school_id,
        name=name,
        programme=programme,
        year_group=year_group,
        academic_year=academic_year,
    )
    db.add(cls)
    await db.flush()
    await db.refresh(cls)
    return cls


async def get_class(db: AsyncSession, class_id: uuid.UUID) -> Class:
    cls = await db.get(Class, class_id)
    if not cls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return cls


async def list_classes(
    db: AsyncSession,
    school_id: uuid.UUID,
    teacher_id: uuid.UUID | None = None,
) -> list[tuple[Class, int]]:
    """Returns list of (Class, student_count) tuples."""
    student_count_sq = (
        select(func.count(Enrolment.id))
        .where(Enrolment.class_id == Class.id, Enrolment.is_active == True)
        .correlate(Class)
        .scalar_subquery()
    )

    query = select(Class, student_count_sq.label("student_count")).where(Class.school_id == school_id)

    if teacher_id is not None:
        query = (
            query.join(ClassSubject, ClassSubject.class_id == Class.id)
            .where(ClassSubject.teacher_id == teacher_id)
            .distinct()
        )

    result = await db.execute(query)
    return list(result.all())


async def update_class(
    db: AsyncSession,
    class_id: uuid.UUID,
    name: str | None = None,
    programme: str | None = None,
    year_group: int | None = None,
    academic_year: str | None = None,
) -> Class:
    cls = await get_class(db, class_id)
    if name          is not None: cls.name          = name
    if programme     is not None: cls.programme     = programme
    if year_group    is not None: cls.year_group    = year_group
    if academic_year is not None: cls.academic_year = academic_year
    await db.flush()
    await db.refresh(cls)
    return cls


async def assign_subject_teacher(
    db: AsyncSession,
    class_id: uuid.UUID,
    subject_id: uuid.UUID,
    teacher_id: uuid.UUID,
) -> ClassSubject:
    # Validate teacher role
    teacher = await db.get(User, teacher_id)
    if not teacher or teacher.role != UserRole.teacher:
        raise HTTPException(status_code=422, detail="User is not a teacher", headers={"code": "USER_NOT_TEACHER"})

    # Validate subject exists
    subject = await db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Check uniqueness
    existing = await db.execute(
        select(ClassSubject).where(ClassSubject.class_id == class_id, ClassSubject.subject_id == subject_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Subject already assigned in this class",
            headers={"code": "CLASS_SUBJECT_CONFLICT"},
        )

    cs = ClassSubject(class_id=class_id, subject_id=subject_id, teacher_id=teacher_id)
    db.add(cs)
    await db.flush()
    await db.refresh(cs)
    return cs


async def get_class_subjects(db: AsyncSession, class_id: uuid.UUID) -> list[ClassSubject]:
    result = await db.execute(
        select(ClassSubject)
        .where(ClassSubject.class_id == class_id)
        .options(selectinload(ClassSubject.subject), selectinload(ClassSubject.teacher))
    )
    return list(result.scalars().all())


async def remove_class_subject(db: AsyncSession, cs_id: uuid.UUID) -> None:
    cs = await db.get(ClassSubject, cs_id)
    if not cs:
        raise HTTPException(status_code=404, detail="Class subject not found")
    await db.delete(cs)
    await db.flush()

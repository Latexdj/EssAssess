import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.models.enrolment import Enrolment
from app.models.user import User, UserRole


async def bulk_enrol(
    db: AsyncSession,
    class_id: uuid.UUID,
    student_ids: list[uuid.UUID],
) -> dict:
    enrolled:         list[uuid.UUID] = []
    already_enrolled: list[uuid.UUID] = []
    not_found:        list[uuid.UUID] = []

    for sid in student_ids:
        user = await db.get(User, sid)
        if not user or user.role != UserRole.student:
            not_found.append(sid)
            continue

        existing = await db.execute(
            select(Enrolment).where(Enrolment.student_id == sid, Enrolment.class_id == class_id)
        )
        enrolment = existing.scalar_one_or_none()

        if enrolment:
            if not enrolment.is_active:
                enrolment.is_active = True
                await db.flush()
            already_enrolled.append(sid)
        else:
            db.add(Enrolment(student_id=sid, class_id=class_id))
            enrolled.append(sid)

    await db.flush()
    return {"enrolled": enrolled, "already_enrolled": already_enrolled, "not_found": not_found}


async def remove_enrolment(db: AsyncSession, class_id: uuid.UUID, student_id: uuid.UUID) -> None:
    result = await db.execute(
        select(Enrolment).where(Enrolment.student_id == student_id, Enrolment.class_id == class_id)
    )
    enrolment = result.scalar_one_or_none()
    if not enrolment:
        raise HTTPException(status_code=404, detail="Enrolment not found")
    enrolment.is_active = False
    await db.flush()


async def get_class_roster(db: AsyncSession, class_id: uuid.UUID) -> list[Enrolment]:
    result = await db.execute(
        select(Enrolment)
        .where(Enrolment.class_id == class_id, Enrolment.is_active == True)
        .options(selectinload(Enrolment.student))
        .order_by(Enrolment.enrolled_at)
    )
    return list(result.scalars().all())


async def get_student_classes(db: AsyncSession, student_id: uuid.UUID) -> list[Enrolment]:
    result = await db.execute(
        select(Enrolment)
        .where(Enrolment.student_id == student_id, Enrolment.is_active == True)
        .options(selectinload(Enrolment.class_))
    )
    return list(result.scalars().all())


async def is_enrolled(db: AsyncSession, student_id: uuid.UUID, class_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(Enrolment).where(
            Enrolment.student_id == student_id,
            Enrolment.class_id == class_id,
            Enrolment.is_active == True,
        )
    )
    return result.scalar_one_or_none() is not None

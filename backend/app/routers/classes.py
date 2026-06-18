import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.user import UserRole
from app.schemas.class_ import (
    ClassCreate, ClassOut, ClassListItem,
    ClassSubjectCreate, ClassSubjectOut,
)
from app.services.core import class_service

router = APIRouter(prefix="/classes", tags=["classes"])


def _cs_to_out(cs) -> ClassSubjectOut:
    return ClassSubjectOut(
        id=cs.id,
        class_id=cs.class_id,
        subject_id=cs.subject_id,
        teacher_id=cs.teacher_id,
        subject_name=cs.subject.name,
        subject_code=cs.subject.code,
        teacher_name=f"{cs.teacher.first_name} {cs.teacher.last_name}",
    )


@router.post("", response_model=ClassOut, status_code=201)
async def create_class(
    body: ClassCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin")),
):
    cls = await class_service.create_class(
        db, admin.school_id, body.name, body.programme, body.year_group, body.academic_year
    )
    return ClassOut.model_validate(cls)


@router.get("", response_model=list[ClassListItem])
async def list_classes(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    teacher_id = current_user.id if current_user.role == UserRole.teacher else None
    rows = await class_service.list_classes(db, current_user.school_id, teacher_id=teacher_id)
    return [
        ClassListItem(
            id=cls.id,
            school_id=cls.school_id,
            name=cls.name,
            programme=cls.programme,
            year_group=cls.year_group,
            academic_year=cls.academic_year,
            student_count=int(count or 0),
        )
        for cls, count in rows
    ]


@router.get("/{class_id}", response_model=ClassOut)
async def get_class(
    class_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    cls = await class_service.get_class(db, class_id)
    if cls.school_id != current_user.school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return ClassOut.model_validate(cls)


@router.patch("/{class_id}", response_model=ClassOut)
async def update_class(
    class_id: uuid.UUID,
    body: ClassCreate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    cls = await class_service.update_class(
        db, class_id, body.name, body.programme, body.year_group, body.academic_year
    )
    return ClassOut.model_validate(cls)


# ── Subject assignment ────────────────────────────────────────────────────────

@router.post("/{class_id}/subjects", response_model=ClassSubjectOut, status_code=201)
async def assign_subject(
    class_id: uuid.UUID,
    body: ClassSubjectCreate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    cs = await class_service.assign_subject_teacher(db, class_id, body.subject_id, body.teacher_id)
    cs_loaded = (await class_service.get_class_subjects(db, class_id))
    cs_loaded = next(x for x in cs_loaded if x.id == cs.id)
    return _cs_to_out(cs_loaded)


@router.get("/{class_id}/subjects", response_model=list[ClassSubjectOut])
async def list_class_subjects(
    class_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    subjects = await class_service.get_class_subjects(db, class_id)
    return [_cs_to_out(cs) for cs in subjects]


@router.delete("/{class_id}/subjects/{cs_id}", status_code=204)
async def remove_class_subject(
    class_id: uuid.UUID,
    cs_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    await class_service.remove_class_subject(db, cs_id)

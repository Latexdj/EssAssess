from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.subject import Subject
from app.schemas.subject import SubjectOut, SubjectCreate

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("", response_model=list[SubjectOut])
async def list_subjects(
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    result = await db.execute(select(Subject).order_by(Subject.name))
    return [SubjectOut.model_validate(s) for s in result.scalars().all()]


@router.post("", response_model=SubjectOut, status_code=201)
async def create_subject(
    body: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    existing = await db.execute(select(Subject).where(Subject.code == body.code))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Subject code already exists",
            headers={"code": "SUBJECT_CODE_CONFLICT"},
        )
    subject = Subject(name=body.name, code=body.code, ges_curriculum_area=body.ges_curriculum_area)
    db.add(subject)
    await db.flush()
    await db.refresh(subject)
    return SubjectOut.model_validate(subject)

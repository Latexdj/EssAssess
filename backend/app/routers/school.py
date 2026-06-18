from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.school import School
from app.schemas.school import SchoolOut, SchoolUpdate

router = APIRouter(prefix="/school", tags=["school"])


@router.get("", response_model=SchoolOut)
async def get_school(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    school = await db.get(School, current_user.school_id)
    return SchoolOut.model_validate(school)


@router.patch("", response_model=SchoolOut)
async def update_school(
    body: SchoolUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin")),
):
    school = await db.get(School, admin.school_id)
    if body.name   is not None: school.name   = body.name
    if body.region is not None: school.region = body.region
    if body.type   is not None: school.type   = body.type
    await db.flush()
    await db.refresh(school)
    return SchoolOut.model_validate(school)

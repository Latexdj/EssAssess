import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.dependencies import require_role
from app.models.user import UserRole
from app.schemas.user import UserCreate, UserUpdate, UserOut, UserListOut
from app.services.core import user_service

router = APIRouter(prefix="/users", tags=["users"])

AdminOnly = Depends(require_role("admin"))


@router.post("", response_model=UserOut, status_code=201)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    admin=AdminOnly,
):
    user = await user_service.create_user(
        db,
        school_id=admin.school_id,
        email=body.email,
        password=body.password,
        first_name=body.first_name,
        last_name=body.last_name,
        role=body.role,
    )
    return UserOut.model_validate(user)


@router.get("", response_model=UserListOut)
async def list_users(
    role:      Optional[UserRole] = Query(default=None),
    is_active: Optional[bool]     = Query(default=None),
    limit:     int                = Query(default=50, ge=1, le=200),
    offset:    int                = Query(default=0, ge=0),
    db:        AsyncSession       = Depends(get_db),
    admin=AdminOnly,
):
    users, total = await user_service.list_users(
        db, school_id=admin.school_id, role=role, is_active=is_active, limit=limit, offset=offset
    )
    return UserListOut(total=total, users=[UserOut.model_validate(u) for u in users])


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin=AdminOnly,
):
    user = await user_service.get_user(db, user_id)
    return UserOut.model_validate(user)


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    admin=AdminOnly,
):
    user = await user_service.update_user(
        db, user_id,
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        password=body.password,
        is_active=body.is_active,
    )
    return UserOut.model_validate(user)


@router.delete("/{user_id}", status_code=204)
async def deactivate_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin=AdminOnly,
):
    await user_service.deactivate_user(db, user_id)

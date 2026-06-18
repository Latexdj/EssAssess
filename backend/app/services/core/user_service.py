import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.user import User, UserRole
from app.services.core.auth_service import hash_password


async def create_user(
    db: AsyncSession,
    school_id: uuid.UUID,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: UserRole,
) -> User:
    existing = await get_user_by_email(db, email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
            headers={"code": "USER_EMAIL_CONFLICT"},
        )
    user = User(
        school_id=school_id,
        email=email,
        password_hash=hash_password(password),
        first_name=first_name,
        last_name=last_name,
        role=role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def get_user(db: AsyncSession, user_id: uuid.UUID) -> User:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    from app.services.core.auth_service import verify_password
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def list_users(
    db: AsyncSession,
    school_id: uuid.UUID,
    role: UserRole | None = None,
    is_active: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[User], int]:
    query = select(User).where(User.school_id == school_id)
    count_query = select(func.count()).select_from(User).where(User.school_id == school_id)

    if role is not None:
        query = query.where(User.role == role)
        count_query = count_query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
        count_query = count_query.where(User.is_active == is_active)

    total = (await db.execute(count_query)).scalar_one()
    users = (await db.execute(query.offset(offset).limit(limit))).scalars().all()
    return list(users), total


async def update_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    password: str | None = None,
    is_active: bool | None = None,
) -> User:
    user = await get_user(db, user_id)
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if email is not None:
        existing = await get_user_by_email(db, email)
        if existing and existing.id != user_id:
            raise HTTPException(status_code=409, detail="Email already registered")
        user.email = email
    if password is not None:
        user.password_hash = hash_password(password)
    if is_active is not None:
        user.is_active = is_active
    await db.flush()
    await db.refresh(user)
    return user


async def deactivate_user(db: AsyncSession, user_id: uuid.UUID) -> User:
    return await update_user(db, user_id, is_active=False)

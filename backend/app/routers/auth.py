from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.auth import LoginRequest, AuthResponse
from app.schemas.user import UserOut
from app.services.core import auth_service, user_service
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

ACCESS_COOKIE_MAX_AGE  = settings.jwt_access_expire_minutes * 60
REFRESH_COOKIE_MAX_AGE = settings.jwt_refresh_expire_days * 86400


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    cookie_kwargs = dict(httponly=True, samesite="lax", secure=False)
    response.set_cookie("access_token",  access_token,  max_age=ACCESS_COOKIE_MAX_AGE,  **cookie_kwargs)
    response.set_cookie("refresh_token", refresh_token, max_age=REFRESH_COOKIE_MAX_AGE, **cookie_kwargs)


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


@router.post("/login", response_model=AuthResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.authenticate_user(db, body.email, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"code": "AUTH_INVALID_CREDENTIALS"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
            headers={"code": "AUTH_ACCOUNT_INACTIVE"},
        )

    access_token  = auth_service.create_access_token(str(user.id), user.role.value, str(user.school_id))
    refresh_token = auth_service.create_refresh_token(str(user.id))
    _set_auth_cookies(response, access_token, refresh_token)

    return AuthResponse(user=UserOut.model_validate(user))


@router.post("/refresh", response_model=AuthResponse)
async def refresh(
    response: Response,
    refresh_token: Optional[str] = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    payload = auth_service.verify_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired or invalid",
            headers={"code": "AUTH_REFRESH_INVALID"},
        )

    import uuid as _uuid
    user = await user_service.get_user(db, _uuid.UUID(payload["sub"]))
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    new_access  = auth_service.create_access_token(str(user.id), user.role.value, str(user.school_id))
    new_refresh = auth_service.create_refresh_token(str(user.id))
    _set_auth_cookies(response, new_access, new_refresh)

    return AuthResponse(user=UserOut.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    _clear_auth_cookies(response)


@router.get("/me", response_model=AuthResponse)
async def me(current_user=Depends(get_current_user)):
    return AuthResponse(user=UserOut.model_validate(current_user))

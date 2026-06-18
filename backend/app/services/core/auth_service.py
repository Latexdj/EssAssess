from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str, role: str, school_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_expire_minutes)
    return jwt.encode(
        {"sub": user_id, "role": role, "school_id": school_id, "exp": expire, "type": "access"},
        settings.jwt_secret_key,
        algorithm=ALGORITHM,
    )


def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_expire_days)
    return jwt.encode(
        {"sub": user_id, "exp": expire, "type": "refresh"},
        settings.jwt_refresh_secret_key,
        algorithm=ALGORITHM,
    )


def verify_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def verify_refresh_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.jwt_refresh_secret_key, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None

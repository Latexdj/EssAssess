import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.user import UserRole


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:         uuid.UUID
    school_id:  uuid.UUID
    email:      str
    first_name: str
    last_name:  str
    role:       UserRole
    is_active:  bool
    created_at: datetime


class UserCreate(BaseModel):
    email:      EmailStr
    password:   str
    first_name: str
    last_name:  str
    role:       UserRole


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name:  str | None = None
    email:      EmailStr | None = None
    password:   str | None = None
    is_active:  bool | None = None


class UserListOut(BaseModel):
    total: int
    users: list[UserOut]

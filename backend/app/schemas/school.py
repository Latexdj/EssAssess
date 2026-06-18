import uuid
from pydantic import BaseModel, ConfigDict
from app.models.school import SchoolType


class SchoolOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:     uuid.UUID
    name:   str
    region: str
    type:   SchoolType


class SchoolUpdate(BaseModel):
    name:   str | None = None
    region: str | None = None
    type:   SchoolType | None = None

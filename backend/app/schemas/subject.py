import uuid
from pydantic import BaseModel, ConfigDict


class SubjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:                  uuid.UUID
    name:                str
    code:                str
    ges_curriculum_area: str | None


class SubjectCreate(BaseModel):
    name:                str
    code:                str
    ges_curriculum_area: str | None = None

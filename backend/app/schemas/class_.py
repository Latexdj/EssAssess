import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ClassCreate(BaseModel):
    name:          str
    programme:     str | None = None
    year_group:    int | None = None
    academic_year: str | None = None


class ClassOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:            uuid.UUID
    school_id:     uuid.UUID
    name:          str
    programme:     str | None
    year_group:    int | None
    academic_year: str | None


class ClassListItem(ClassOut):
    student_count: int = 0


class ClassSubjectCreate(BaseModel):
    subject_id: uuid.UUID
    teacher_id: uuid.UUID


class ClassSubjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:           uuid.UUID
    class_id:     uuid.UUID
    subject_id:   uuid.UUID
    teacher_id:   uuid.UUID
    subject_name: str
    subject_code: str
    teacher_name: str


class EnrolmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:           uuid.UUID
    student_id:   uuid.UUID
    class_id:     uuid.UUID
    enrolled_at:  datetime
    is_active:    bool
    student_name: str
    email:        str


class BulkEnrolRequest(BaseModel):
    student_ids: list[uuid.UUID]


class BulkEnrolResponse(BaseModel):
    enrolled:         list[uuid.UUID]
    already_enrolled: list[uuid.UUID]
    not_found:        list[uuid.UUID]

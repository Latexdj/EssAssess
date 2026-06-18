import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator


class RubricCriterionCreate(BaseModel):
    name:          str
    description:   str
    max_marks:     int

    @field_validator("max_marks")
    @classmethod
    def marks_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("max_marks must be at least 1")
        return v


class RubricCriterionUpdate(BaseModel):
    name:        str | None = None
    description: str | None = None
    max_marks:   int | None = None


class RubricCriterionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:            uuid.UUID
    assignment_id: uuid.UUID
    name:          str
    description:   str
    max_marks:     int
    display_order: int


class AssignmentCreate(BaseModel):
    class_subject_id:         uuid.UUID
    title:                    str
    question_text:            str
    instructions:             str | None = None
    allowed_submission_types: list[str]  = ["text", "pdf", "image"]
    max_marks:                int
    due_date:                 datetime

    @field_validator("max_marks")
    @classmethod
    def marks_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("max_marks must be at least 1")
        return v


class AssignmentUpdate(BaseModel):
    title:                    str | None      = None
    question_text:            str | None      = None
    instructions:             str | None      = None
    allowed_submission_types: list[str] | None = None
    max_marks:                int | None      = None
    due_date:                 datetime | None = None


class AssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:                       uuid.UUID
    class_subject_id:         uuid.UUID
    title:                    str
    question_text:            str
    instructions:             str | None
    allowed_submission_types: list[str]
    max_marks:                int
    due_date:                 datetime
    is_published:             bool
    created_at:               datetime
    rubric_criteria:          list[RubricCriterionOut] = []
    # Injected by router (not on ORM object directly)
    subject_name:             str | None = None
    subject_code:             str | None = None
    class_name:               str | None = None
    teacher_name:             str | None = None
    submission_count:         int = 0

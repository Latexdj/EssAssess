import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class TextSubmissionCreate(BaseModel):
    assignment_id: uuid.UUID
    text_content:  str = Field(..., min_length=50, max_length=10_000)


class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:              uuid.UUID
    assignment_id:   uuid.UUID
    student_id:      uuid.UUID
    submission_type: str
    status:          str
    text_content:    str | None
    file_name:       str | None
    file_size_bytes: int | None
    submitted_at:    datetime
    updated_at:      datetime
    # Denormalized
    student_name:    str | None = None
    # AI result (present when status == graded)
    total_ai_score:  float | None = None
    formative_feedback: str | None = None
    error_message:   str | None = None

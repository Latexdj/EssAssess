import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class OverrideIn(BaseModel):
    rubric_criterion_id: uuid.UUID
    overridden_score:    float = Field(..., ge=0)
    override_note:       str | None = None


class FinaliseRequest(BaseModel):
    teacher_comment: str | None = None


class CriterionReviewOut(BaseModel):
    criterion_id:     uuid.UUID
    name:             str
    description:      str
    max_marks:        int
    display_order:    int
    ai_score:         float | None
    ai_justification: str | None
    override_score:   float | None
    override_note:    str | None
    effective_score:  float


class FinalisedGradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:              uuid.UUID
    submission_id:   uuid.UUID
    teacher_id:      uuid.UUID
    total_score:     float
    teacher_comment: str | None
    is_published:    bool
    finalised_at:    datetime


class SubmissionReviewOut(BaseModel):
    id:              uuid.UUID
    assignment_id:   uuid.UUID
    student_id:      uuid.UUID
    student_name:    str | None
    submission_type: str
    status:          str
    text_content:    str | None
    file_name:       str | None
    submitted_at:    datetime
    # Assignment info
    assignment_title: str
    question_text:    str
    max_marks:        int
    # AI grading
    total_ai_score:     float | None
    formative_feedback: str | None
    # Per-criterion review
    criteria:        list[CriterionReviewOut]
    effective_total: float
    # Finalised grade (present once teacher finalises)
    finalised_grade: FinalisedGradeOut | None = None

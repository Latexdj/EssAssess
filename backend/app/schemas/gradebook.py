import uuid
from datetime import datetime
from pydantic import BaseModel


class StudentGradeOut(BaseModel):
    submission_id:      uuid.UUID
    assignment_id:      uuid.UUID
    assignment_title:   str
    class_name:         str
    subject_name:       str
    subject_code:       str
    max_marks:          int
    due_date:           datetime
    submitted_at:       datetime
    status:             str
    # AI grade (always shown once graded)
    ai_score:           float | None
    formative_feedback: str | None
    # Final grade (shown only after teacher publishes)
    final_score:        float | None
    teacher_comment:    str | None
    is_published:       bool


class AssignmentStatsOut(BaseModel):
    assignment_id:   uuid.UUID
    title:           str
    subject_name:    str
    subject_code:    str
    max_marks:       int
    due_date:        datetime
    is_published:    bool
    enrolled_count:  int
    submitted_count: int
    graded_count:    int
    finalised_count: int
    published_count: int
    avg_ai_score:    float | None
    avg_final_score: float | None


class ClassGradebookOut(BaseModel):
    class_id:        uuid.UUID
    class_name:      str
    enrolled_count:  int
    assignments:     list[AssignmentStatsOut]

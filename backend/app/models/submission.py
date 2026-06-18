import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, UniqueConstraint, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class SubmissionType(str, enum.Enum):
    text  = "text"
    pdf   = "pdf"
    image = "image"


class SubmissionStatus(str, enum.Enum):
    pending_grading      = "pending_grading"
    grading_in_progress  = "grading_in_progress"
    graded               = "graded"
    grading_failed       = "grading_failed"
    finalised            = "finalised"


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (UniqueConstraint("assignment_id", "student_id", name="uq_submission"),)

    id:               Mapped[uuid.UUID]       = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id:    Mapped[uuid.UUID]       = mapped_column(UUID(as_uuid=True), ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id:       Mapped[uuid.UUID]       = mapped_column(UUID(as_uuid=True), ForeignKey("users.id",       ondelete="CASCADE"), nullable=False, index=True)
    submission_type:  Mapped[SubmissionType]  = mapped_column(SAEnum(SubmissionType,  name="sub_type"),   nullable=False)
    status:           Mapped[SubmissionStatus] = mapped_column(SAEnum(SubmissionStatus, name="sub_status"), nullable=False, default=SubmissionStatus.pending_grading, index=True)
    text_content:     Mapped[str | None]      = mapped_column(Text, nullable=True)
    file_path:        Mapped[str | None]      = mapped_column(String, nullable=True)
    file_name:        Mapped[str | None]      = mapped_column(String, nullable=True)
    file_size_bytes:  Mapped[int | None]      = mapped_column(Integer, nullable=True)
    transcribed_text: Mapped[str | None]      = mapped_column(Text, nullable=True)
    submitted_at:     Mapped[datetime]        = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now())
    updated_at:       Mapped[datetime]        = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), onupdate=func.now())

    assignment:       Mapped["Assignment"]           = relationship("Assignment", back_populates="submissions")
    student:          Mapped["User"]                 = relationship("User",       back_populates="submissions")
    ai_grading_result: Mapped["AIGradingResult | None"] = relationship("AIGradingResult", back_populates="submission", uselist=False)
    grade_overrides:  Mapped[list["GradeOverride"]]  = relationship("GradeOverride", back_populates="submission")
    finalised_grade:  Mapped["FinalisedGrade | None"] = relationship("FinalisedGrade", back_populates="submission", uselist=False)

import uuid
from datetime import datetime
from sqlalchemy import String, SmallInteger, Boolean, DateTime, ForeignKey, ARRAY, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id:                       Mapped[uuid.UUID]     = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_subject_id:         Mapped[uuid.UUID]     = mapped_column(UUID(as_uuid=True), ForeignKey("class_subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    title:                    Mapped[str]            = mapped_column(String, nullable=False)
    question_text:            Mapped[str]            = mapped_column(String, nullable=False)
    instructions:             Mapped[str | None]     = mapped_column(String, nullable=True)
    allowed_submission_types: Mapped[list[str]]      = mapped_column(ARRAY(String), nullable=False, server_default="{text,pdf,image}")
    max_marks:                Mapped[int]            = mapped_column(SmallInteger, nullable=False)
    due_date:                 Mapped[datetime]       = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    is_published:             Mapped[bool]           = mapped_column(Boolean, nullable=False, default=False)
    created_at:               Mapped[datetime]       = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:               Mapped[datetime]       = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    class_subject:   Mapped["ClassSubject"]         = relationship("ClassSubject",  back_populates="assignments")
    rubric_criteria: Mapped[list["RubricCriterion"]] = relationship("RubricCriterion", back_populates="assignment", order_by="RubricCriterion.display_order")
    submissions:     Mapped[list["Submission"]]      = relationship("Submission", back_populates="assignment")

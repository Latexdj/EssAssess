import uuid
from datetime import datetime
from sqlalchemy import String, SmallInteger, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class RubricCriterion(Base):
    __tablename__ = "rubric_criteria"

    id:            Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
    name:          Mapped[str]       = mapped_column(String, nullable=False)
    description:   Mapped[str]       = mapped_column(String, nullable=False)
    max_marks:     Mapped[int]       = mapped_column(SmallInteger, nullable=False)
    display_order: Mapped[int]       = mapped_column(SmallInteger, nullable=False, default=0)
    created_at:    Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())

    assignment:         Mapped["Assignment"]              = relationship("Assignment", back_populates="rubric_criteria")
    ai_criterion_scores: Mapped[list["AICriterionScore"]] = relationship("AICriterionScore", back_populates="rubric_criterion")
    grade_overrides:    Mapped[list["GradeOverride"]]     = relationship("GradeOverride", back_populates="rubric_criterion")

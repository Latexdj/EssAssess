import uuid
from datetime import datetime
from sqlalchemy import Text, Numeric, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class GradeOverride(Base):
    __tablename__ = "grade_overrides"
    __table_args__ = (UniqueConstraint("submission_id", "rubric_criterion_id", name="uq_grade_override"),)

    id:                  Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id:       Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("submissions.id",      ondelete="CASCADE"),  nullable=False, index=True)
    rubric_criterion_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rubric_criteria.id",  ondelete="CASCADE"),  nullable=False)
    teacher_id:          Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id",            ondelete="RESTRICT"), nullable=False)
    overridden_score:    Mapped[float]     = mapped_column(Numeric(5, 2), nullable=False)
    override_note:       Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at:          Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:          Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    submission:       Mapped["Submission"]      = relationship("Submission",      back_populates="grade_overrides")
    rubric_criterion: Mapped["RubricCriterion"] = relationship("RubricCriterion", back_populates="grade_overrides")
    teacher:          Mapped["User"]            = relationship("User")

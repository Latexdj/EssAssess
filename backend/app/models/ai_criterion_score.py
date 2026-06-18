import uuid
from sqlalchemy import Text, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class AICriterionScore(Base):
    __tablename__ = "ai_criterion_scores"
    __table_args__ = (UniqueConstraint("grading_result_id", "rubric_criterion_id", name="uq_ai_criterion_score"),)

    id:                  Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    grading_result_id:   Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ai_grading_results.id", ondelete="CASCADE"), nullable=False, index=True)
    rubric_criterion_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rubric_criteria.id",    ondelete="CASCADE"), nullable=False)
    ai_score:            Mapped[float]     = mapped_column(Numeric(5, 2), nullable=False)
    ai_justification:    Mapped[str]       = mapped_column(Text, nullable=False)

    grading_result:  Mapped["AIGradingResult"]  = relationship("AIGradingResult",  back_populates="criterion_scores")
    rubric_criterion: Mapped["RubricCriterion"] = relationship("RubricCriterion",  back_populates="ai_criterion_scores")

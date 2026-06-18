import uuid
from datetime import datetime
from sqlalchemy import String, Integer, SmallInteger, Text, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.database import Base


class AIGradingResult(Base):
    __tablename__ = "ai_grading_results"

    id:                  Mapped[uuid.UUID]      = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id:       Mapped[uuid.UUID]      = mapped_column(UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    total_ai_score:      Mapped[float]          = mapped_column(Numeric(5, 2), nullable=False)
    formative_feedback:  Mapped[str]            = mapped_column(Text, nullable=False)
    raw_response:        Mapped[dict]           = mapped_column(JSONB, nullable=False)
    model_used:          Mapped[str]            = mapped_column(String, nullable=False)
    tokens_input:        Mapped[int | None]     = mapped_column(Integer, nullable=True)
    tokens_output:       Mapped[int | None]     = mapped_column(Integer, nullable=True)
    retrieved_chunk_ids: Mapped[list | None]    = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=True)
    graded_at:           Mapped[datetime]       = mapped_column(DateTime(timezone=True), server_default=func.now())
    retry_count:         Mapped[int]            = mapped_column(SmallInteger, nullable=False, default=0)
    error_message:       Mapped[str | None]     = mapped_column(Text, nullable=True)

    submission:       Mapped["Submission"]            = relationship("Submission", back_populates="ai_grading_result")
    criterion_scores: Mapped[list["AICriterionScore"]] = relationship("AICriterionScore", back_populates="grading_result")

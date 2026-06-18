import uuid
from datetime import datetime
from sqlalchemy import Text, Numeric, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class FinalisedGrade(Base):
    __tablename__ = "finalised_grades"

    id:              Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id:   Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="CASCADE"),  nullable=False, unique=True, index=True)
    teacher_id:      Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), ForeignKey("users.id",       ondelete="RESTRICT"), nullable=False)
    total_score:     Mapped[float]      = mapped_column(Numeric(5, 2), nullable=False)
    teacher_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_published:    Mapped[bool]       = mapped_column(Boolean, nullable=False, default=False, index=True)
    finalised_at:    Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:      Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    submission: Mapped["Submission"] = relationship("Submission", back_populates="finalised_grade")
    teacher:    Mapped["User"]       = relationship("User")

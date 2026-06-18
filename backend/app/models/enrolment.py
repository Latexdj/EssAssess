import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Enrolment(Base):
    __tablename__ = "enrolments"
    __table_args__ = (UniqueConstraint("student_id", "class_id", name="uq_enrolment"),)

    id:          Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id:  Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id",   ondelete="CASCADE"), nullable=False, index=True)
    class_id:    Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    enrolled_at: Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active:   Mapped[bool]      = mapped_column(Boolean, nullable=False, default=True)

    student: Mapped["User"]  = relationship("User",  back_populates="enrolments", foreign_keys=[student_id])
    class_:  Mapped["Class"] = relationship("Class", back_populates="enrolments")

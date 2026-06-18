import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class ClassSubject(Base):
    __tablename__ = "class_subjects"
    __table_args__ = (UniqueConstraint("class_id", "subject_id", name="uq_class_subject"),)

    id:         Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id:   Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("classes.id",  ondelete="CASCADE"),  nullable=False, index=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="RESTRICT"), nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id",    ondelete="RESTRICT"), nullable=False, index=True)
    created_at: Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())

    class_:      Mapped["Class"]             = relationship("Class",   back_populates="class_subjects")
    subject:     Mapped["Subject"]           = relationship("Subject", back_populates="class_subjects")
    teacher:     Mapped["User"]              = relationship("User")
    assignments: Mapped[list["Assignment"]]  = relationship("Assignment", back_populates="class_subject")

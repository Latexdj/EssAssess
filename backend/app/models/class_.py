import uuid
from datetime import datetime
from sqlalchemy import String, SmallInteger, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Class(Base):
    __tablename__ = "classes"

    id:            Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id:     Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name:          Mapped[str]        = mapped_column(String, nullable=False)
    programme:     Mapped[str | None] = mapped_column(String, nullable=True)
    year_group:    Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    academic_year: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at:    Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())

    school:         Mapped["School"]              = relationship("School", back_populates="classes")
    class_subjects: Mapped[list["ClassSubject"]]  = relationship("ClassSubject", back_populates="class_")
    enrolments:     Mapped[list["Enrolment"]]     = relationship("Enrolment", back_populates="class_")
    announcements:  Mapped[list["Announcement"]]  = relationship("Announcement", back_populates="class_")

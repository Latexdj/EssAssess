import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Subject(Base):
    __tablename__ = "subjects"

    id:                  Mapped[uuid.UUID]    = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name:                Mapped[str]          = mapped_column(String, nullable=False)
    code:                Mapped[str]          = mapped_column(String, nullable=False, unique=True)
    ges_curriculum_area: Mapped[str | None]   = mapped_column(String, nullable=True)
    created_at:          Mapped[datetime]     = mapped_column(DateTime(timezone=True), server_default=func.now())

    class_subjects: Mapped[list["ClassSubject"]] = relationship("ClassSubject", back_populates="subject")

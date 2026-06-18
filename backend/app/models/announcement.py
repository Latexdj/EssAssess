import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Announcement(Base):
    __tablename__ = "announcements"

    id:         Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id:   Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"),  nullable=False, index=True)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id",   ondelete="RESTRICT"), nullable=False)
    title:      Mapped[str]       = mapped_column(String, nullable=False)
    body:       Mapped[str]       = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())

    class_:  Mapped["Class"] = relationship("Class", back_populates="announcements")
    teacher: Mapped["User"]  = relationship("User")

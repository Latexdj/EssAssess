import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Boolean, Enum as SAEnum, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class UserRole(str, enum.Enum):
    admin   = "admin"
    teacher = "teacher"
    student = "student"


class User(Base):
    __tablename__ = "users"

    id:            Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id:     Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    email:         Mapped[str]       = mapped_column(String, nullable=False, unique=True, index=True)
    password_hash: Mapped[str]       = mapped_column(String, nullable=False)
    first_name:    Mapped[str]       = mapped_column(String, nullable=False)
    last_name:     Mapped[str]       = mapped_column(String, nullable=False)
    role:          Mapped[UserRole]  = mapped_column(SAEnum(UserRole, name="user_role"), nullable=False, index=True)
    is_active:     Mapped[bool]      = mapped_column(Boolean, nullable=False, default=True)
    created_at:    Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:    Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    school:      Mapped["School"]           = relationship("School", back_populates="users")
    enrolments:  Mapped[list["Enrolment"]]  = relationship("Enrolment", back_populates="student", foreign_keys="Enrolment.student_id")
    submissions: Mapped[list["Submission"]] = relationship("Submission", back_populates="student")

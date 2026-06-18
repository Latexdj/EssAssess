import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Enum as SAEnum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class SchoolType(str, enum.Enum):
    SHS  = "SHS"
    SHTS = "SHTS"
    TVET = "TVET"


class School(Base):
    __tablename__ = "schools"

    id:         Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name:       Mapped[str]       = mapped_column(String, nullable=False)
    region:     Mapped[str]       = mapped_column(String, nullable=False)
    type:       Mapped[SchoolType] = mapped_column(SAEnum(SchoolType, name="school_type"), nullable=False)
    created_at: Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())

    users:   Mapped[list["User"]]  = relationship("User",  back_populates="school")
    classes: Mapped[list["Class"]] = relationship("Class", back_populates="school")

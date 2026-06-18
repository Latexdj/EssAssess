import uuid
from datetime import datetime
from sqlalchemy import String, Text, Integer, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy import Float
from app.database import Base

EMBEDDING_DIM = 1536  # text-embedding-3-small


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id:           Mapped[uuid.UUID]       = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_title: Mapped[str]             = mapped_column(String, nullable=False)
    source_label: Mapped[str]             = mapped_column(String, nullable=False)
    content:      Mapped[str]             = mapped_column(Text, nullable=False)
    embedding:    Mapped[list | None]     = mapped_column(ARRAY(Float), nullable=True)
    subject_tag:  Mapped[str]             = mapped_column(String, nullable=False, index=True)
    chunk_index:  Mapped[int]             = mapped_column(Integer, nullable=False)
    is_example:   Mapped[bool]            = mapped_column(Boolean, nullable=False, default=False)
    created_at:   Mapped[datetime]        = mapped_column(DateTime(timezone=True), server_default=func.now())

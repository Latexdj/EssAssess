"""
Knowledge base management: extract → chunk → embed → store.

Chunk strategy: simple word-based sliding window (400 words, 80-word overlap).
This is deliberately minimal — appropriate for GES/WAEC marking-scheme PDFs
where each paragraph contains a distinct marking point.
"""
import io
import re
import uuid
from typing import AsyncIterator

import pdfplumber
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from app.config import settings
from app.models.knowledge_chunk import KnowledgeChunk, EMBEDDING_DIM

CHUNK_SIZE    = 400   # words per chunk
CHUNK_OVERLAP = 80    # words of overlap between adjacent chunks
MIN_CHUNK_LEN = 60    # discard chunks shorter than this many characters
EMBED_MODEL   = "text-embedding-3-small"
EMBED_BATCH   = 512   # max inputs per OpenAI embed call


# ── Text extraction ───────────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Return plain text from PDF bytes; raises ValueError if extraction yields nothing."""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    text = "\n\n".join(p.strip() for p in pages if p.strip())
    if not text:
        raise ValueError("PDF contains no extractable text (may be scanned image).")
    return text


def _normalise(text: str) -> str:
    """Collapse excessive whitespace while preserving paragraph breaks."""
    # Collapse runs of spaces/tabs into single space
    text = re.sub(r"[ \t]+", " ", text)
    # Normalise paragraph breaks to exactly two newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ── Chunking ─────────────────────────────────────────────────────────────────

def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping word-window chunks."""
    text = _normalise(text)
    words = text.split()
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        if len(chunk) >= MIN_CHUNK_LEN:
            chunks.append(chunk)
        if end >= len(words):
            break
        start = end - overlap
    return chunks


# ── Embedding ─────────────────────────────────────────────────────────────────

async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of strings using OpenAI text-embedding-3-small (1536-dim)."""
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    all_embeddings: list[list[float]] = []

    # Batch to stay within OpenAI limit
    for i in range(0, len(texts), EMBED_BATCH):
        batch = texts[i : i + EMBED_BATCH]
        response = await client.embeddings.create(
            model=EMBED_MODEL,
            input=batch,
            dimensions=EMBEDDING_DIM,
        )
        all_embeddings.extend(item.embedding for item in response.data)

    return all_embeddings


# ── Storage ───────────────────────────────────────────────────────────────────

async def store_chunks(
    db: AsyncSession,
    *,
    source_title: str,
    source_label: str,
    subject_tag: str,
    chunks: list[str],
    embeddings: list[list[float]],
    is_example: bool = False,
) -> int:
    """Persist chunks + embeddings. Returns number of rows inserted."""
    rows = [
        KnowledgeChunk(
            id=uuid.uuid4(),
            source_title=source_title,
            source_label=source_label,
            subject_tag=subject_tag,
            chunk_index=idx,
            content=chunk,
            embedding=emb,
            is_example=is_example,
        )
        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings))
    ]
    db.add_all(rows)
    await db.flush()
    return len(rows)


# ── Orchestration ─────────────────────────────────────────────────────────────

async def process_document(
    db: AsyncSession,
    *,
    file_bytes: bytes,
    source_title: str,
    source_label: str,
    subject_tag: str,
    is_example: bool = False,
) -> dict:
    """
    Full pipeline: extract → chunk → embed → store.
    Returns a summary dict for the API response.
    """
    text   = extract_text_from_pdf(file_bytes)
    chunks = chunk_text(text)
    if not chunks:
        raise ValueError("Document produced no usable chunks after text extraction.")

    embeddings = await embed_texts(chunks)
    count = await store_chunks(
        db,
        source_title=source_title,
        source_label=source_label,
        subject_tag=subject_tag,
        chunks=chunks,
        embeddings=embeddings,
        is_example=is_example,
    )
    return {
        "source_title": source_title,
        "source_label": source_label,
        "subject_tag": subject_tag,
        "is_example": is_example,
        "chunk_count": count,
    }


# ── Listing / deletion ────────────────────────────────────────────────────────

async def list_documents(db: AsyncSession) -> list[dict]:
    """Return one summary row per (source_label, subject_tag, is_example) group."""
    result = await db.execute(
        select(
            KnowledgeChunk.source_title,
            KnowledgeChunk.source_label,
            KnowledgeChunk.subject_tag,
            KnowledgeChunk.is_example,
            func.count(KnowledgeChunk.id).label("chunk_count"),
            func.max(KnowledgeChunk.created_at).label("uploaded_at"),
        ).group_by(
            KnowledgeChunk.source_title,
            KnowledgeChunk.source_label,
            KnowledgeChunk.subject_tag,
            KnowledgeChunk.is_example,
        ).order_by(func.max(KnowledgeChunk.created_at).desc())
    )
    return [row._asdict() for row in result.all()]


async def delete_document(db: AsyncSession, source_label: str) -> int:
    """Delete all chunks for a document. Returns rows deleted."""
    result = await db.execute(
        delete(KnowledgeChunk).where(KnowledgeChunk.source_label == source_label)
    )
    await db.flush()
    return result.rowcount

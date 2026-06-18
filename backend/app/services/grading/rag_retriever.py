"""
RAG retrieval: embed a query then run Python-side cosine similarity.

Uses standard PostgreSQL REAL[] for embedding storage — no pgvector extension required.
Suitable for thesis-scale knowledge bases (< 2000 chunks per subject).
"""
import math
from dataclasses import dataclass

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.knowledge_chunk import KnowledgeChunk, EMBEDDING_DIM

EMBED_MODEL = "text-embedding-3-small"
REF_K       = 6
EXAMPLE_K   = 1


@dataclass
class RetrievedChunk:
    id:           str
    source_title: str
    source_label: str
    subject_tag:  str
    chunk_index:  int
    content:      str
    is_example:   bool
    similarity:   float   # 0–1, higher is more similar


def _cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na  = math.sqrt(sum(x * x for x in a))
    nb  = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


async def embed_query(query: str) -> list[float]:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    resp = await client.embeddings.create(
        model=EMBED_MODEL,
        input=[query],
        dimensions=EMBEDDING_DIM,
    )
    return resp.data[0].embedding


async def _search(
    db:              AsyncSession,
    query_embedding: list[float],
    subject_tag:     str,
    is_example:      bool,
    k:               int,
) -> list[RetrievedChunk]:
    # Load candidate chunks (only those with embeddings)
    rows = (await db.execute(
        select(KnowledgeChunk).where(
            KnowledgeChunk.subject_tag == subject_tag,
            KnowledgeChunk.is_example  == is_example,
            KnowledgeChunk.embedding.is_not(None),
        )
    )).scalars().all()

    if not rows:
        return []

    # Rank by cosine similarity in Python
    scored = sorted(
        [(chunk, _cosine_sim(query_embedding, chunk.embedding)) for chunk in rows],
        key=lambda t: t[1],
        reverse=True,
    )

    return [
        RetrievedChunk(
            id=str(chunk.id),
            source_title=chunk.source_title,
            source_label=chunk.source_label,
            subject_tag=chunk.subject_tag,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            is_example=chunk.is_example,
            similarity=round(sim, 4),
        )
        for chunk, sim in scored[:k]
    ]


async def retrieve_chunks(
    db:          AsyncSession,
    query:       str,
    subject_tag: str,
    k:           int = REF_K,
) -> list[RetrievedChunk]:
    q_emb = await embed_query(query)
    return await _search(db, q_emb, subject_tag, is_example=False, k=k)


async def retrieve_examples(
    db:          AsyncSession,
    query:       str,
    subject_tag: str,
    k:           int = EXAMPLE_K,
) -> list[RetrievedChunk]:
    q_emb = await embed_query(query)
    return await _search(db, q_emb, subject_tag, is_example=True, k=k)


async def retrieve_context(
    db:          AsyncSession,
    query:       str,
    subject_tag: str,
    ref_k:       int = REF_K,
    example_k:   int = EXAMPLE_K,
) -> dict:
    q_emb    = await embed_query(query)
    refs     = await _search(db, q_emb, subject_tag, is_example=False, k=ref_k)
    examples = await _search(db, q_emb, subject_tag, is_example=True,  k=example_k)
    return {
        "reference_chunks": refs,
        "example_chunks":   examples,
        "chunk_ids":        [c.id for c in refs + examples],
    }

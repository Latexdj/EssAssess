import re
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.services.grading import knowledge_service, rag_retriever

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

MAX_PDF_BYTES = 20 * 1024 * 1024  # 20 MB


def _make_label(title: str) -> str:
    """Slugify a title into a stable source_label."""
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:80]


# ── Upload ────────────────────────────────────────────────────────────────────

@router.post("/upload", status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file:         UploadFile = File(...),
    subject_tag:  str        = Form(...),
    source_title: str        = Form(...),
    is_example:   bool       = Form(False),
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Only PDF files are accepted")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 20 MB limit")
    if not file_bytes:
        raise HTTPException(status_code=422, detail="Uploaded file is empty")

    source_label = _make_label(source_title)

    try:
        result = await knowledge_service.process_document(
            db,
            file_bytes=file_bytes,
            source_title=source_title,
            source_label=source_label,
            subject_tag=subject_tag.upper(),
            is_example=is_example,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return result


# ── Documents list / delete ───────────────────────────────────────────────────

@router.get("/documents")
async def list_documents(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    return await knowledge_service.list_documents(db)


@router.delete("/documents/{source_label}", status_code=204)
async def delete_document(
    source_label: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    deleted = await knowledge_service.delete_document(db, source_label)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Document not found")


# ── Test retrieval (admin only — used to validate RAG quality) ────────────────

class RetrieveRequest(BaseModel):
    query:       str
    subject_tag: str
    ref_k:       int = 6
    example_k:   int = 1


@router.post("/retrieve")
async def test_retrieve(
    body: RetrieveRequest,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    try:
        ctx = await rag_retriever.retrieve_context(
            db,
            query=body.query,
            subject_tag=body.subject_tag.upper(),
            ref_k=body.ref_k,
            example_k=body.example_k,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return {
        "reference_chunks": [
            {
                "id":           c.id,
                "source_title": c.source_title,
                "chunk_index":  c.chunk_index,
                "similarity":   c.similarity,
                "preview":      c.content[:300] + ("…" if len(c.content) > 300 else ""),
            }
            for c in ctx["reference_chunks"]
        ],
        "example_chunks": [
            {
                "id":           c.id,
                "source_title": c.source_title,
                "chunk_index":  c.chunk_index,
                "similarity":   c.similarity,
                "preview":      c.content[:300] + ("…" if len(c.content) > 300 else ""),
            }
            for c in ctx["example_chunks"]
        ],
    }

"""
Grading contract: frozen dataclasses that form the sole boundary between
the LMS core and the grading module.  Nothing on either side of this boundary
may import from the other side except through these types.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class CriterionInput:
    criterion_id:  UUID
    name:          str
    description:   str
    max_marks:     int
    display_order: int


@dataclass(frozen=True)
class RetrievedChunkDTO:
    """A RAG chunk pre-fetched by the orchestrator and embedded in the request."""
    id:           str
    source_title: str
    content:      str
    similarity:   float
    is_example:   bool


@dataclass(frozen=True)
class GradingRequest:
    submission_id:    UUID
    assignment_id:    UUID
    question_text:    str
    student_text:     str
    subject_tag:      str
    criteria:         tuple[CriterionInput, ...]
    max_marks:        int
    reference_chunks: tuple[RetrievedChunkDTO, ...] = ()
    example_chunks:   tuple[RetrievedChunkDTO, ...] = ()
    image_base64:     str | None = None
    image_media_type: str = "image/jpeg"


@dataclass(frozen=True)
class CriterionScore:
    criterion_id:  UUID
    score:         int
    justification: str


@dataclass(frozen=True)
class GradingResponse:
    submission_id:       UUID
    criterion_scores:    tuple[CriterionScore, ...]
    total_score:         int
    formative_feedback:  str
    raw_response:        dict
    model_used:          str
    tokens_input:        int
    tokens_output:       int
    retrieved_chunk_ids: tuple[str, ...]
    error:               str | None = None

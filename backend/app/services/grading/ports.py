"""
Adapter pattern for the grading module.

GradingPort — abstract interface (the "port")
LocalGradingAdapter — current implementation: RAG + Claude API in-process
HttpGradingAdapter  — future: delegate to a separate grading microservice
"""
from __future__ import annotations
from abc import ABC, abstractmethod

from app.services.grading.contracts import GradingRequest, GradingResponse, CriterionScore


class GradingPort(ABC):
    @abstractmethod
    async def grade(self, request: GradingRequest) -> GradingResponse: ...


class LocalGradingAdapter(GradingPort):
    """
    In-process implementation.  Calls OpenAI (embeddings) + Claude (grading).
    All AI calls happen synchronously within the request.
    """

    async def grade(self, request: GradingRequest) -> GradingResponse:
        from app.services.grading import prompt_builder, claude_client, response_parser

        # Build prompt (RAG context already embedded in request by orchestrator)
        system, user = prompt_builder.build_grading_prompt(request)

        # Call Claude
        try:
            result = await claude_client.call_claude(
                system=system,
                user=user,
                image_base64=request.image_base64,
                image_media_type=request.image_media_type,
            )
        except Exception as exc:
            return GradingResponse(
                submission_id=request.submission_id,
                criterion_scores=(),
                total_score=0,
                formative_feedback="",
                raw_response={"error": str(exc)},
                model_used="unknown",
                tokens_input=0,
                tokens_output=0,
                retrieved_chunk_ids=tuple(
                    c.id for c in (*request.reference_chunks, *request.example_chunks)
                ),
                error=f"Claude API error: {exc}",
            )

        # Parse response
        scores, feedback, parse_error = response_parser.parse_grading_response(
            result["text"],
            request.criteria,
        )

        total = sum(s.score for s in scores)
        chunk_ids = tuple(
            c.id for c in (*request.reference_chunks, *request.example_chunks)
        )

        return GradingResponse(
            submission_id=request.submission_id,
            criterion_scores=tuple(scores),
            total_score=total,
            formative_feedback=feedback,
            raw_response={"text": result["text"]},
            model_used=result["model"],
            tokens_input=result["input_tokens"],
            tokens_output=result["output_tokens"],
            retrieved_chunk_ids=chunk_ids,
            error=parse_error,
        )


class HttpGradingAdapter(GradingPort):
    """
    Future: forwards GradingRequest as JSON to an external grading microservice.
    Not implemented yet — placeholder to document the extension point.
    """

    def __init__(self, base_url: str, api_key: str) -> None:
        self._base_url = base_url
        self._api_key  = api_key

    async def grade(self, request: GradingRequest) -> GradingResponse:
        raise NotImplementedError("HttpGradingAdapter is not yet implemented")

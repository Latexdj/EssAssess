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
        from app.services.grading import (
            prompt_builder, claude_client, gemini_client, response_parser
        )
        from app.config import settings

        system, user = prompt_builder.build_grading_prompt(request)

        # Pick provider: Claude if key present, else Gemini, else error
        try:
            if settings.anthropic_api_key:
                result = await claude_client.call_claude(
                    system=system,
                    user=user,
                    image_base64=request.image_base64,
                    image_media_type=request.image_media_type,
                )
            elif settings.google_api_key:
                result = await gemini_client.call_gemini(
                    system=system,
                    user=user,
                    image_base64=request.image_base64,
                    image_media_type=request.image_media_type,
                )
            else:
                raise RuntimeError(
                    "No AI provider configured. Set ANTHROPIC_API_KEY (Claude) "
                    "or GOOGLE_API_KEY (Gemini free tier)."
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
                error=f"Grading API error: {exc}",
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

"""
Unit tests for the grading pipeline components.
All tests mock the Claude API — no real network calls.
"""
import json
import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.grading.contracts import (
    GradingRequest,
    CriterionInput,
    GradingResponse,
    RetrievedChunkDTO,
)
from app.services.grading.response_parser import parse_grading_response, _extract_json_text
from app.services.grading.prompt_builder import build_grading_prompt


# ── Shared fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def criterion_a():
    return CriterionInput(
        criterion_id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        name="Knowledge",
        description="Demonstrates factual knowledge of the topic",
        max_marks=4,
        display_order=1,
    )


@pytest.fixture
def criterion_b():
    return CriterionInput(
        criterion_id=uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        name="Analysis",
        description="Analyses the topic with supporting evidence",
        max_marks=4,
        display_order=2,
    )


@pytest.fixture
def grading_request(criterion_a, criterion_b):
    return GradingRequest(
        submission_id=uuid.uuid4(),
        assignment_id=uuid.uuid4(),
        question_text="Explain the causes of the 1948 Accra Riots.",
        student_text="The riots happened because ex-servicemen were not paid...",
        subject_tag="HIST",
        criteria=(criterion_a, criterion_b),
        max_marks=8,
    )


# ── Response parser tests ──────────────────────────────────────────────────────

class TestExtractJson:
    def test_pure_json(self):
        text = '{"key": "value"}'
        assert _extract_json_text(text) == '{"key": "value"}'

    def test_strips_markdown_fence(self):
        text = '```json\n{"key": "value"}\n```'
        result = _extract_json_text(text)
        assert result.strip() == '{"key": "value"}'

    def test_extracts_from_surrounding_text(self):
        text = 'Here is the response: {"key": "value"} as requested.'
        result = _extract_json_text(text)
        assert '"key"' in result


class TestParseGradingResponse:
    def _good_response(self, criterion_a, criterion_b):
        return json.dumps({
            "criterion_scores": [
                {
                    "criterion_id": str(criterion_a.criterion_id),
                    "score": 3,
                    "justification": "Good knowledge demonstrated.",
                },
                {
                    "criterion_id": str(criterion_b.criterion_id),
                    "score": 2,
                    "justification": "Some analysis, lacks depth.",
                },
            ],
            "formative_feedback": "Well done! Your essay shows good understanding.",
        })

    def test_parses_valid_response(self, criterion_a, criterion_b):
        raw = self._good_response(criterion_a, criterion_b)
        scores, feedback, error = parse_grading_response(raw, (criterion_a, criterion_b))
        assert error is None
        assert len(scores) == 2
        assert feedback.startswith("Well done")

    def test_clips_score_to_max(self, criterion_a, criterion_b):
        raw = json.dumps({
            "criterion_scores": [
                {"criterion_id": str(criterion_a.criterion_id), "score": 99, "justification": "x"},
                {"criterion_id": str(criterion_b.criterion_id), "score": 2,  "justification": "y"},
            ],
            "formative_feedback": "Good.",
        })
        scores, _, _ = parse_grading_response(raw, (criterion_a, criterion_b))
        a_score = next(s for s in scores if s.criterion_id == criterion_a.criterion_id)
        assert a_score.score == criterion_a.max_marks  # clipped

    def test_clips_score_to_zero(self, criterion_a, criterion_b):
        raw = json.dumps({
            "criterion_scores": [
                {"criterion_id": str(criterion_a.criterion_id), "score": -5, "justification": "x"},
                {"criterion_id": str(criterion_b.criterion_id), "score": 2,  "justification": "y"},
            ],
            "formative_feedback": "Good.",
        })
        scores, _, _ = parse_grading_response(raw, (criterion_a, criterion_b))
        a_score = next(s for s in scores if s.criterion_id == criterion_a.criterion_id)
        assert a_score.score == 0

    def test_fills_missing_criteria_with_zero(self, criterion_a, criterion_b):
        # Only one criterion in response
        raw = json.dumps({
            "criterion_scores": [
                {"criterion_id": str(criterion_a.criterion_id), "score": 3, "justification": "x"},
            ],
            "formative_feedback": "Partial feedback.",
        })
        scores, _, error = parse_grading_response(raw, (criterion_a, criterion_b))
        assert len(scores) == 2
        b_score = next(s for s in scores if s.criterion_id == criterion_b.criterion_id)
        assert b_score.score == 0
        assert error is not None  # should flag missing criterion

    def test_invalid_json_returns_error(self, criterion_a, criterion_b):
        scores, feedback, error = parse_grading_response("not json at all", (criterion_a, criterion_b))
        assert error is not None
        assert scores == []

    def test_unknown_criterion_id_flagged(self, criterion_a, criterion_b):
        raw = json.dumps({
            "criterion_scores": [
                {"criterion_id": "00000000-0000-0000-0000-000000000000", "score": 3, "justification": "x"},
                {"criterion_id": str(criterion_b.criterion_id), "score": 2, "justification": "y"},
            ],
            "formative_feedback": "OK.",
        })
        scores, _, error = parse_grading_response(raw, (criterion_a, criterion_b))
        assert error is not None  # unknown ID flagged


# ── Prompt builder tests ───────────────────────────────────────────────────────

class TestPromptBuilder:
    def test_system_prompt_contains_ghanaian_english_note(self, grading_request):
        system, _ = build_grading_prompt(grading_request)
        assert "Ghanaian English" in system
        assert "WAEC" in system

    def test_user_prompt_contains_question(self, grading_request):
        _, user = build_grading_prompt(grading_request)
        assert grading_request.question_text in user

    def test_user_prompt_contains_student_essay(self, grading_request):
        _, user = build_grading_prompt(grading_request)
        assert grading_request.student_text in user

    def test_user_prompt_contains_criterion_ids(self, grading_request, criterion_a, criterion_b):
        _, user = build_grading_prompt(grading_request)
        assert str(criterion_a.criterion_id) in user
        assert str(criterion_b.criterion_id) in user

    def test_user_prompt_contains_rag_chunks(self, grading_request):
        chunk = RetrievedChunkDTO(
            id=str(uuid.uuid4()),
            source_title="WAEC Marking Scheme 2022",
            content="Key point about the Accra riots...",
            similarity=0.85,
            is_example=False,
        )
        request_with_rag = GradingRequest(
            submission_id=grading_request.submission_id,
            assignment_id=grading_request.assignment_id,
            question_text=grading_request.question_text,
            student_text=grading_request.student_text,
            subject_tag=grading_request.subject_tag,
            criteria=grading_request.criteria,
            max_marks=grading_request.max_marks,
            reference_chunks=(chunk,),
        )
        _, user = build_grading_prompt(request_with_rag)
        assert "WAEC Marking Scheme 2022" in user
        assert "Key point about the Accra riots" in user


# ── LocalGradingAdapter tests ──────────────────────────────────────────────────

class TestLocalGradingAdapter:
    @pytest.mark.asyncio
    async def test_successful_grading(self, grading_request, criterion_a, criterion_b):
        mock_claude_result = {
            "text": json.dumps({
                "criterion_scores": [
                    {"criterion_id": str(criterion_a.criterion_id), "score": 3, "justification": "Good."},
                    {"criterion_id": str(criterion_b.criterion_id), "score": 2, "justification": "OK."},
                ],
                "formative_feedback": "Well done, keep it up!",
            }),
            "model": "claude-sonnet-4-5",
            "input_tokens": 500,
            "output_tokens": 200,
        }

        with patch("app.services.grading.claude_client.call_claude", new_callable=AsyncMock, return_value=mock_claude_result):
            from app.services.grading.ports import LocalGradingAdapter
            adapter = LocalGradingAdapter()
            response = await adapter.grade(grading_request)

        assert response.total_score == 5
        assert len(response.criterion_scores) == 2
        assert response.formative_feedback == "Well done, keep it up!"
        assert response.tokens_input == 500
        assert response.error is None

    @pytest.mark.asyncio
    async def test_claude_api_error_returns_error_response(self, grading_request):
        with patch("app.services.grading.claude_client.call_claude", new_callable=AsyncMock, side_effect=Exception("Rate limit exceeded")):
            from app.services.grading.ports import LocalGradingAdapter
            adapter = LocalGradingAdapter()
            response = await adapter.grade(grading_request)

        assert response.error is not None
        assert "Rate limit" in response.error
        assert response.total_score == 0
        assert response.criterion_scores == ()

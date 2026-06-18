"""
Parse Claude's JSON grading response into CriterionScore + formative_feedback.

Handles:
  - Pure JSON response
  - JSON wrapped in markdown code fences (```json ... ```)
  - JSON embedded in surrounding text (extracts first {...} block)

On parse failure, returns an empty score list with a None feedback and
an error string — the caller decides how to handle this.
"""
import json
import re
from uuid import UUID

from app.services.grading.contracts import CriterionInput, CriterionScore


def _extract_json_text(raw: str) -> str:
    """Strip markdown fences and find the first top-level JSON object."""
    # Remove ```json ... ``` or ``` ... ``` blocks
    raw = re.sub(r"```(?:json)?\s*", "", raw).strip()

    # Find the outermost { ... } using bracket counting
    start = raw.find("{")
    if start == -1:
        return raw

    depth, end = 0, -1
    for i, ch in enumerate(raw[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        if depth == 0:
            end = i
            break

    return raw[start : end + 1] if end != -1 else raw[start:]


def parse_grading_response(
    raw_text: str,
    criteria: tuple[CriterionInput, ...],
) -> tuple[list[CriterionScore], str, str | None]:
    """
    Parse Claude's response.

    Returns:
        (criterion_scores, formative_feedback, error_message)
        error_message is None on success.
    """
    try:
        json_str = _extract_json_text(raw_text)
        data = json.loads(json_str)
    except (json.JSONDecodeError, ValueError) as e:
        return [], "", f"JSON parse error: {e} | raw: {raw_text[:500]}"

    # Build criterion_id → CriterionInput lookup for validation
    criteria_map: dict[str, CriterionInput] = {str(c.criterion_id): c for c in criteria}

    scores: list[CriterionScore] = []
    parse_errors: list[str] = []

    raw_scores = data.get("criterion_scores", [])
    if not isinstance(raw_scores, list):
        return [], "", f"criterion_scores is not a list: {type(raw_scores)}"

    for item in raw_scores:
        cid_str = str(item.get("criterion_id", ""))
        if cid_str not in criteria_map:
            parse_errors.append(f"Unknown criterion_id: {cid_str!r}")
            continue

        criterion = criteria_map[cid_str]
        raw_score = item.get("score", 0)
        try:
            score = int(round(float(raw_score)))
        except (TypeError, ValueError):
            score = 0
            parse_errors.append(f"Non-numeric score for {cid_str}: {raw_score!r}")

        # Clip to [0, max_marks]
        score = max(0, min(score, criterion.max_marks))
        justification = str(item.get("justification", "")).strip() or "No justification provided."

        scores.append(CriterionScore(
            criterion_id=UUID(cid_str),
            score=score,
            justification=justification,
        ))

    # Fill in zero scores for any missing criteria
    scored_ids = {str(s.criterion_id) for s in scores}
    for c in criteria:
        if str(c.criterion_id) not in scored_ids:
            scores.append(CriterionScore(
                criterion_id=c.criterion_id,
                score=0,
                justification="Score not provided by grader.",
            ))
            parse_errors.append(f"Missing criterion in response: {c.criterion_id}")

    feedback = str(data.get("formative_feedback", "")).strip()
    if not feedback:
        feedback = "The student's work has been reviewed. Please consult your teacher for detailed feedback."

    error = ("; ".join(parse_errors)) if parse_errors else None
    return scores, feedback, error

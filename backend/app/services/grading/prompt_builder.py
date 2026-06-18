"""
Builds the system + user prompts for Claude grading.

Design constraints encoded here:
- Do not penalise Ghanaian English
- Follow GES/WAEC marking conventions
- Return strict JSON only
"""
from app.services.grading.contracts import GradingRequest

SYSTEM_PROMPT = """\
You are an expert essay grader for Ghanaian Senior High School (SHS), \
Senior High Technical School (SHTS), and TVET examinations. \
You apply marking conventions consistent with the West African Examinations \
Council (WAEC) and the Ghana Education Service (GES).

GRADING PRINCIPLES
1. Award marks strictly according to the rubric criteria provided. \
Award partial marks where work is partially correct.
2. GHANAIAN ENGLISH: Ghana has its own rich variety of English shaped by Akan, \
Dagbani, Ewe, and other local languages. Do NOT penalise students for Ghanaian \
English expressions, idioms, or phrasing (e.g. "I am coming" for "I'll be right \
back", "they are plenty" for "there are many") unless the meaning is genuinely \
unclear or comprehension is impaired. Judge content and reasoning, not dialect.
3. Be consistent and objective. Apply the same standard across all answers.
4. Formative feedback must be constructive, encouraging, and appropriate for a \
Ghanaian SHS student. Write as a supportive teacher who wants the student to improve.
5. Respond with ONLY a valid JSON object — no markdown fences, no preamble, \
no explanation outside the JSON structure.
"""


def build_grading_prompt(request: GradingRequest) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for Claude."""
    parts: list[str] = []

    # ── RAG reference material ────────────────────────────────────────────────
    if request.reference_chunks:
        parts.append("## REFERENCE MATERIAL (from GES syllabus / WAEC marking scheme)\n")
        for i, chunk in enumerate(request.reference_chunks, 1):
            parts.append(
                f"[{i}] {chunk.source_title} (similarity {chunk.similarity:.2f})\n{chunk.content}\n"
            )

    if request.example_chunks:
        parts.append(
            "## EXAMPLE MODEL ANSWER "
            "(for calibration — students are NOT expected to match this exactly)\n"
        )
        for chunk in request.example_chunks:
            parts.append(f"{chunk.source_title}\n{chunk.content}\n")

    # ── Question ──────────────────────────────────────────────────────────────
    parts.append(f"## ASSIGNMENT QUESTION\n{request.question_text}\n")

    # ── Rubric ────────────────────────────────────────────────────────────────
    parts.append(f"## MARKING RUBRIC (total: {request.max_marks} marks)\n")
    for c in sorted(request.criteria, key=lambda x: x.display_order):
        parts.append(
            f"Criterion {c.display_order}: {c.name} — {c.max_marks} mark(s)\n"
            f"criterion_id: {c.criterion_id}\n"
            f"Description: {c.description}\n"
        )

    # ── Student essay ─────────────────────────────────────────────────────────
    if request.image_base64:
        parts.append(
            "## STUDENT SUBMISSION\n"
            "(The student submitted a handwritten essay. "
            "The image is attached to this message.)\n"
        )
    else:
        parts.append(f"## STUDENT ESSAY\n{request.student_text}\n")

    # ── Output specification ──────────────────────────────────────────────────
    criterion_ids = "\n".join(f'  "{c.criterion_id}"' for c in request.criteria)
    parts.append(
        '## REQUIRED OUTPUT\n'
        'Return ONLY this JSON (no markdown, no text outside the braces):\n'
        '{\n'
        '  "criterion_scores": [\n'
        '    {\n'
        '      "criterion_id": "<exact UUID from rubric>",\n'
        '      "score": <integer 0 to max_marks for this criterion>,\n'
        '      "justification": "<1–2 sentences explaining the score>"\n'
        '    }\n'
        '  ],\n'
        '  "formative_feedback": "<3–5 sentences of constructive, '
        'encouraging feedback for the student>"\n'
        '}\n\n'
        f'Valid criterion_id values (use exactly as shown):\n{criterion_ids}'
    )

    return SYSTEM_PROMPT, "\n\n".join(parts)

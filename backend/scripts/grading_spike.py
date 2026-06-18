"""
Grading pipeline spike — validates the full AI grading pipeline without a database.

Usage:
    python -m scripts.grading_spike

Requires:
    ANTHROPIC_API_KEY and OPENAI_API_KEY in .env (or environment)
"""
import asyncio, sys, os, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv  # optional — works without it if env vars are set
try:
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
except ImportError:
    pass

from app.services.grading.contracts import GradingRequest, CriterionInput
from app.services.grading.ports import LocalGradingAdapter


SAMPLE_QUESTION = (
    "Explain the causes of the 1948 Accra Riots and their significance "
    "in the struggle for Ghanaian independence. (10 marks)"
)

# A sample student essay with intentional Ghanaian English phrasing
SAMPLE_ESSAY = """\
The 1948 Accra Riots, they were very important in the history of Ghana. The riots \
happened because of many things. One cause was that ex-servicemen were not paid \
their money after the Second World War. They were plenty of them who fought for \
Britain but when they came back, the government did not give them what was promised.

Another cause was that African traders and people were suffering because of the \
boycott of European goods. Nii Kwabena Bonne the Third, he started the boycott \
in February 1948 and Ghanaians stopped buying from European stores. When the \
boycott ended, the prices were not reduced and this made people very angry.

The final cause was when police shot at the ex-servicemen who were marching \
peacefully to the Governor's castle. Three men died and many were wounded. \
The news spread and people started rioting in Accra and other towns.

The significance was that the riots showed to the British that Ghanaians could \
not continue to be governed like that. The Watson Commission was set up to \
investigate, and this led to the Coussey Committee which gave Ghana a new \
constitution in 1951. It also helped Kwame Nkrumah to become popular because \
he was arrested after the riots and became a hero of the independence movement.

In conclusion, the 1948 Accra Riots were very significant because they were \
one of the first major signs that Ghana was ready for self-governance.
"""

CRITERIA = (
    CriterionInput(
        criterion_id=uuid.uuid4(),
        name="Identification of Causes",
        description=(
            "Student correctly identifies and explains at least 3 causes of the riots "
            "including: grievances of ex-servicemen, the Boycott of European goods, "
            "and the shooting of ex-servicemen by police."
        ),
        max_marks=4,
        display_order=1,
    ),
    CriterionInput(
        criterion_id=uuid.uuid4(),
        name="Significance of the Riots",
        description=(
            "Student explains the historical significance including: Watson Commission, "
            "Coussey Committee, new constitution, and role in the independence movement."
        ),
        max_marks=4,
        display_order=2,
    ),
    CriterionInput(
        criterion_id=uuid.uuid4(),
        name="Organisation and Expression",
        description=(
            "Essay is logically organised with an introduction, body paragraphs, "
            "and conclusion. Ideas are clearly expressed."
        ),
        max_marks=2,
        display_order=3,
    ),
)


async def run_spike() -> None:
    print("=" * 60)
    print("EssAssess Grading Pipeline Spike")
    print("=" * 60)
    print(f"\nQuestion:\n{SAMPLE_QUESTION}\n")
    print(f"Essay preview:\n{SAMPLE_ESSAY[:200]}...\n")
    print("Running LocalGradingAdapter (no RAG — spike mode)...\n")

    request = GradingRequest(
        submission_id=uuid.uuid4(),
        assignment_id=uuid.uuid4(),
        question_text=SAMPLE_QUESTION,
        student_text=SAMPLE_ESSAY,
        subject_tag="HIST",
        criteria=CRITERIA,
        max_marks=10,
        # No RAG chunks — spike tests the Claude pipeline only
    )

    adapter = LocalGradingAdapter()
    response = await adapter.grade(request)

    print(f"Model: {response.model_used}")
    print(f"Tokens: {response.tokens_input} in / {response.tokens_output} out")
    print(f"Total score: {response.total_score} / {request.max_marks}")
    if response.error:
        print(f"Parse warning: {response.error}")
    print()

    print("Per-criterion scores:")
    for cs in response.criterion_scores:
        # Find the criterion name
        c = next((x for x in CRITERIA if x.criterion_id == cs.criterion_id), None)
        name = c.name if c else str(cs.criterion_id)
        max_m = c.max_marks if c else "?"
        print(f"  [{cs.score}/{max_m}] {name}")
        print(f"    {cs.justification}")

    print(f"\nFormative feedback:\n{response.formative_feedback}")
    print("\n" + "=" * 60)
    print("Spike complete.")


if __name__ == "__main__":
    asyncio.run(run_spike())

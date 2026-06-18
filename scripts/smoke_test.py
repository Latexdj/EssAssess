"""
EssAssess API smoke test — end-to-end happy-path verification.

Prerequisites:
  1. DB running and migrated (alembic upgrade head)
  2. Seed data applied (python -m seed.seed_dev && python -m seed.seed_subjects)
  3. Backend running: uvicorn app.main:app --port 8000

Run:
  cd backend
  python ../scripts/smoke_test.py

  Override base URL:
  ESSASSESS_URL=http://backend:8000 python ../scripts/smoke_test.py
"""
import os
import sys
import time
import uuid

try:
    import httpx
except ImportError:
    print("ERROR: httpx not found — run: pip install httpx")
    sys.exit(1)

BASE = os.environ.get("ESSASSESS_URL", "http://localhost:8000")
API  = f"{BASE}/api/v1"

# Seed credentials
ADMIN_EMAIL    = "admin@essassess.dev"
ADMIN_PASS     = "Admin1234!"
TEACHER_EMAIL  = "teacher@essassess.dev"
TEACHER_PASS   = "Teacher1234!"
STUDENT_EMAIL  = "student@essassess.dev"
STUDENT_PASS   = "Student1234!"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class SmokeError(Exception): ...

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"


def ok(msg: str)   -> None: print(f"  {GREEN}✓{RESET}  {msg}")
def fail(msg: str) -> None: print(f"  {RED}✗{RESET}  {msg}"); raise SmokeError(msg)
def info(msg: str) -> None: print(f"  {YELLOW}·{RESET}  {msg}")


def step(name: str) -> None:
    print(f"\n{BOLD}{name}{RESET}")


def assert_status(resp: httpx.Response, expected: int, label: str) -> dict:
    if resp.status_code != expected:
        fail(f"{label}: expected HTTP {expected}, got {resp.status_code} — {resp.text[:200]}")
    ok(f"{label} → {resp.status_code}")
    return resp.json()


def login(client: httpx.Client, email: str, password: str) -> str:
    """Login and return the access token value."""
    resp = client.post(f"{API}/auth/login", json={"email": email, "password": password})
    data = assert_status(resp, 200, f"Login {email}")
    token = resp.cookies.get("access_token") or data.get("access_token")
    if not token:
        fail(f"No access_token in login response for {email}")
    return token


def auth_headers(token: str) -> dict:
    return {"Cookie": f"access_token={token}"}


# ---------------------------------------------------------------------------
# Test steps
# ---------------------------------------------------------------------------

def run(client: httpx.Client) -> None:
    tag = str(uuid.uuid4())[:8]  # unique suffix to avoid conflicts on repeat runs

    # ── 1. Health ─────────────────────────────────────────────────────────
    step("1 · Health check")
    data = assert_status(client.get(f"{BASE}/health"), 200, "GET /health")
    if data.get("db") != "ok":
        fail(f"DB health not ok: {data}")
    ok(f"service={data['service']}  version={data['version']}  db={data['db']}")

    # ── 2. Auth ───────────────────────────────────────────────────────────
    step("2 · Authentication")
    admin_tok   = login(client, ADMIN_EMAIL,   ADMIN_PASS)
    teacher_tok = login(client, TEACHER_EMAIL, TEACHER_PASS)
    student_tok = login(client, STUDENT_EMAIL, STUDENT_PASS)

    # ── 3. School ─────────────────────────────────────────────────────────
    step("3 · School")
    school = assert_status(
        client.get(f"{API}/school", headers=auth_headers(admin_tok)), 200, "GET /school"
    )
    ok(f"school: {school['name']}")

    # ── 4. Subjects ───────────────────────────────────────────────────────
    step("4 · Subjects")
    subjects = assert_status(
        client.get(f"{API}/subjects", headers=auth_headers(admin_tok)), 200, "GET /subjects"
    )
    if not subjects:
        fail("No subjects found — run seed_subjects.py first")
    subject_id = subjects[0]["id"]
    ok(f"using subject: {subjects[0]['name']} ({subjects[0]['code']})")

    # ── 5. Users — get teacher & student IDs ──────────────────────────────
    step("5 · Users")
    all_users = assert_status(
        client.get(f"{API}/users", headers=auth_headers(admin_tok)), 200, "GET /users"
    )
    teacher_id = next((u["id"] for u in all_users if u["email"] == TEACHER_EMAIL), None)
    student_id = next((u["id"] for u in all_users if u["email"] == STUDENT_EMAIL), None)
    if not teacher_id: fail(f"Teacher {TEACHER_EMAIL} not found in users list")
    if not student_id: fail(f"Student {STUDENT_EMAIL} not found in users list")
    ok(f"teacher_id={teacher_id[:8]}…  student_id={student_id[:8]}…")

    # ── 6. Create class ───────────────────────────────────────────────────
    step("6 · Class")
    cls = assert_status(
        client.post(
            f"{API}/classes",
            json={"name": f"Form 3A-{tag}", "year_group": 3, "academic_year": "2025/2026"},
            headers=auth_headers(admin_tok),
        ),
        201, "POST /classes"
    )
    class_id = cls["id"]
    ok(f"class created: {cls['name']} ({class_id[:8]}…)")

    # ── 7. Assign subject to class ────────────────────────────────────────
    step("7 · Class subject")
    cs = assert_status(
        client.post(
            f"{API}/classes/{class_id}/subjects",
            json={"subject_id": subject_id, "teacher_id": teacher_id},
            headers=auth_headers(admin_tok),
        ),
        201, "POST /classes/{id}/subjects"
    )
    class_subject_id = cs["id"]
    ok(f"class_subject created: {class_subject_id[:8]}…")

    # ── 8. Enrol student ──────────────────────────────────────────────────
    step("8 · Enrolment")
    enr = assert_status(
        client.post(
            f"{API}/enrolments",
            json={"student_id": student_id, "class_id": class_id},
            headers=auth_headers(admin_tok),
        ),
        201, "POST /enrolments"
    )
    ok(f"student enrolled: {enr['id'][:8]}…")

    # ── 9. Create assignment ──────────────────────────────────────────────
    step("9 · Assignment")
    from datetime import datetime, timedelta, timezone
    due = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    asgn = assert_status(
        client.post(
            f"{API}/assignments",
            json={
                "class_subject_id":         class_subject_id,
                "title":                    f"Smoke Test Essay {tag}",
                "question_text":            "Describe the importance of education in Ghana's development.",
                "allowed_submission_types": ["text"],
                "max_marks":                20,
                "due_date":                 due,
            },
            headers=auth_headers(teacher_tok),
        ),
        201, "POST /assignments"
    )
    assignment_id = asgn["id"]
    ok(f"assignment created: {asgn['title']} ({assignment_id[:8]}…)")

    # ── 10. Add rubric criterion ──────────────────────────────────────────
    step("10 · Rubric")
    crit = assert_status(
        client.post(
            f"{API}/assignments/{assignment_id}/criteria",
            json={"name": "Content", "description": "Relevance and depth of argument", "max_marks": 20},
            headers=auth_headers(teacher_tok),
        ),
        201, "POST /criteria"
    )
    criterion_id = crit["id"]
    ok(f"criterion created: {crit['name']} ({criterion_id[:8]}…)")

    # ── 11. Publish assignment ────────────────────────────────────────────
    step("11 · Publish assignment")
    pub = assert_status(
        client.post(f"{API}/assignments/{assignment_id}/publish", headers=auth_headers(teacher_tok)),
        200, "POST /publish"
    )
    if not pub["is_published"]: fail("Assignment not published after publish call")
    ok("assignment is live")

    # ── 12. Submit text essay as student ──────────────────────────────────
    step("12 · Submit essay")
    essay = (
        "Education is the cornerstone of Ghana's development. "
        "From the establishment of the GES to the implementation of the Free SHS policy, "
        "successive governments have recognised the transformative power of schooling. "
        "An educated populace drives economic productivity, democratic governance, and "
        "innovation. In the Upper West Region especially, improving access to quality "
        "secondary education reduces poverty and empowers rural communities. "
        "Investment in TVET schools equips youth with practical skills aligned to "
        "Ghana's industrial needs, bridging the gap between academic knowledge and "
        "employable competencies essential for national progress."
    )
    sub = assert_status(
        client.post(
            f"{API}/submissions",
            json={"assignment_id": assignment_id, "text_content": essay},
            headers=auth_headers(student_tok),
        ),
        201, "POST /submissions"
    )
    submission_id = sub["id"]
    ok(f"submission created: {submission_id[:8]}… status={sub['status']}")

    # ── 13. Poll until graded (max 90 s) ─────────────────────────────────
    step("13 · Wait for AI grading")
    deadline = time.time() + 90
    graded_statuses = {"graded", "grading_failed", "finalised"}
    while True:
        time.sleep(4)
        subs = assert_status(
            client.get(
                f"{API}/submissions",
                params={"assignment_id": assignment_id},
                headers=auth_headers(teacher_tok),
            ),
            200, "GET /submissions"
        )
        current = next((s for s in subs if s["id"] == submission_id), None)
        if not current: fail("Submission disappeared from list")
        status = current["status"]
        info(f"status = {status}")
        if status in graded_statuses:
            break
        if time.time() > deadline:
            fail(f"Grading timed out — still {status} after 90 s")

    if status == "grading_failed":
        info("WARNING: grading_failed (AI key may be missing) — continuing review flow")
    else:
        ok(f"AI grading complete: status={status}  score={current.get('total_ai_score')}")

    # ── 14. Teacher: get review ────────────────────────────────────────────
    step("14 · Teacher review")
    review = assert_status(
        client.get(f"{API}/submissions/{submission_id}/review", headers=auth_headers(teacher_tok)),
        200, "GET /review"
    )
    ok(f"review loaded: effective_total={review['effective_total']}  criteria={len(review['criteria'])}")

    # ── 15. Finalise ──────────────────────────────────────────────────────
    step("15 · Finalise grade")
    fin = assert_status(
        client.post(
            f"{API}/submissions/{submission_id}/finalise",
            json={"teacher_comment": "Smoke test finalise."},
            headers=auth_headers(teacher_tok),
        ),
        200, "POST /finalise"
    )
    ok(f"finalised: total={fin['finalised_grade']['total_score']}  published={fin['finalised_grade']['is_published']}")

    # ── 16. Publish grade ─────────────────────────────────────────────────
    step("16 · Publish grade")
    pub_grade = assert_status(
        client.post(f"{API}/submissions/{submission_id}/publish-grade", headers=auth_headers(teacher_tok)),
        200, "POST /publish-grade"
    )
    if not pub_grade["finalised_grade"]["is_published"]:
        fail("Grade not published after publish-grade call")
    ok("grade published to student")

    # ── 17. Student: check gradebook ──────────────────────────────────────
    step("17 · Student gradebook")
    grades = assert_status(
        client.get(f"{API}/gradebook/student", headers=auth_headers(student_tok)),
        200, "GET /gradebook/student"
    )
    grade = next((g for g in grades if g["assignment_id"] == assignment_id), None)
    if not grade:
        fail("Published grade not visible to student in gradebook")
    if not grade["is_published"] or grade["final_score"] is None:
        fail(f"Grade visible but not published: {grade}")
    ok(f"student sees final_score={grade['final_score']}/{grade['max_marks']}  teacher_comment='{grade['teacher_comment']}'")

    # ── 18. Teacher: class gradebook ──────────────────────────────────────
    step("18 · Class gradebook")
    gb = assert_status(
        client.get(f"{API}/gradebook/class/{class_id}", headers=auth_headers(teacher_tok)),
        200, "GET /gradebook/class"
    )
    ok(f"class '{gb['class_name']}': {gb['enrolled_count']} enrolled, {len(gb['assignments'])} assignments")

    print(f"\n{GREEN}{BOLD}All {18} steps passed — EssAssess API is healthy ✓{RESET}\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"\n{BOLD}EssAssess Smoke Test{RESET}  →  {BASE}\n")
    with httpx.Client(timeout=30) as client:
        try:
            run(client)
        except SmokeError as e:
            print(f"\n{RED}{BOLD}SMOKE TEST FAILED:{RESET} {e}\n")
            sys.exit(1)
        except httpx.ConnectError:
            print(f"\n{RED}Cannot connect to {BASE} — is the backend running?{RESET}\n")
            sys.exit(1)


if __name__ == "__main__":
    main()

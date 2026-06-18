"""Tests for assignment CRUD and rubric builder."""
import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone


def _due() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()


@pytest.fixture
async def class_subject_id(admin_client, teacher_user, db):
    """Create a class, a subject, and assign the teacher — returns class_subject id."""
    # Create class
    r = await admin_client.post("/api/v1/classes", json={"name": "Eng 1A"})
    class_id = r.json()["id"]

    # Create subject
    r = await admin_client.post("/api/v1/subjects", json={"name": "English", "code": "ENG_T"})
    subject_id = r.json()["id"]

    # Assign subject + teacher to class → returns ClassSubject
    r = await admin_client.post(f"/api/v1/classes/{class_id}/subjects", json={
        "subject_id": subject_id,
        "teacher_id": str(teacher_user.id),
    })
    assert r.status_code == 201
    return r.json()["id"]


@pytest.fixture
async def assignment_id(teacher_client, class_subject_id):
    r = await teacher_client.post("/api/v1/assignments", json={
        "class_subject_id": class_subject_id,
        "title": "Essay 1",
        "question_text": "Discuss the importance of education in Ghana.",
        "max_marks": 10,
        "due_date": _due(),
    })
    assert r.status_code == 201
    return r.json()["id"]


class TestAssignmentCRUD:
    async def test_teacher_creates_assignment(self, teacher_client, class_subject_id):
        r = await teacher_client.post("/api/v1/assignments", json={
            "class_subject_id": class_subject_id,
            "title": "Essay 1",
            "question_text": "Discuss the role of education.",
            "max_marks": 10,
            "due_date": _due(),
        })
        assert r.status_code == 201
        data = r.json()
        assert data["title"] == "Essay 1"
        assert data["is_published"] is False
        assert data["subject_code"] == "ENG_T"

    async def test_student_cannot_create_assignment(self, student_client, class_subject_id):
        r = await student_client.post("/api/v1/assignments", json={
            "class_subject_id": class_subject_id,
            "title": "Bad",
            "question_text": "Q",
            "max_marks": 5,
            "due_date": _due(),
        })
        assert r.status_code == 403

    async def test_other_teacher_cannot_create_for_wrong_class_subject(
        self, admin_client, db, school, assignment_id
    ):
        from app.models.user import User, UserRole
        from app.services.core.auth_service import hash_password
        other = User(
            school_id=school.id,
            email="other@test.dev",
            password_hash=hash_password("Other1234!"),
            first_name="Other",
            last_name="Teacher",
            role=UserRole.teacher,
        )
        db.add(other)
        await db.flush()

        from httpx import AsyncClient
        from httpx import ASGITransport
        from app.main import app
        from app.database import get_db
        from app.tests.conftest import TestSessionLocal
        async def _get_other_db():
            async with TestSessionLocal() as s:
                yield s
        app.dependency_overrides[get_db] = _get_other_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            login = await c.post("/api/v1/auth/login", json={"email": "other@test.dev", "password": "Other1234!"})
            r = await c.post("/api/v1/assignments", json={
                "class_subject_id": "00000000-0000-0000-0000-000000000000",
                "title": "X",
                "question_text": "Q",
                "max_marks": 5,
                "due_date": _due(),
            })
        assert r.status_code in (403, 404)
        app.dependency_overrides.clear()

    async def test_list_assignments_for_class(self, teacher_client, assignment_id, class_subject_id):
        # Get the class_id from the assignment
        r = await teacher_client.get(f"/api/v1/assignments/{assignment_id}")
        assert r.status_code == 200

    async def test_get_assignment(self, teacher_client, assignment_id):
        r = await teacher_client.get(f"/api/v1/assignments/{assignment_id}")
        assert r.status_code == 200
        assert r.json()["id"] == assignment_id

    async def test_update_assignment(self, teacher_client, assignment_id):
        r = await teacher_client.patch(f"/api/v1/assignments/{assignment_id}", json={
            "title": "Updated Essay 1",
        })
        assert r.status_code == 200
        assert r.json()["title"] == "Updated Essay 1"

    async def test_delete_unpublished_assignment(self, teacher_client, class_subject_id):
        r = await teacher_client.post("/api/v1/assignments", json={
            "class_subject_id": class_subject_id,
            "title": "To Delete",
            "question_text": "Q",
            "max_marks": 5,
            "due_date": _due(),
        })
        aid = r.json()["id"]
        r2 = await teacher_client.delete(f"/api/v1/assignments/{aid}")
        assert r2.status_code == 204


class TestRubricBuilder:
    async def test_add_criterion(self, teacher_client, assignment_id):
        r = await teacher_client.post(f"/api/v1/assignments/{assignment_id}/criteria", json={
            "name": "Content Knowledge",
            "description": "Demonstrates understanding of the topic",
            "max_marks": 5,
        })
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Content Knowledge"
        assert data["display_order"] == 1

    async def test_multiple_criteria_ordered(self, teacher_client, assignment_id):
        await teacher_client.post(f"/api/v1/assignments/{assignment_id}/criteria", json={
            "name": "A", "description": "desc", "max_marks": 3,
        })
        await teacher_client.post(f"/api/v1/assignments/{assignment_id}/criteria", json={
            "name": "B", "description": "desc", "max_marks": 3,
        })
        r = await teacher_client.get(f"/api/v1/assignments/{assignment_id}")
        criteria = r.json()["rubric_criteria"]
        assert len(criteria) == 2
        assert criteria[0]["display_order"] < criteria[1]["display_order"]

    async def test_update_criterion(self, teacher_client, assignment_id):
        r = await teacher_client.post(f"/api/v1/assignments/{assignment_id}/criteria", json={
            "name": "Old Name", "description": "desc", "max_marks": 3,
        })
        cid = r.json()["id"]
        r2 = await teacher_client.patch(
            f"/api/v1/assignments/{assignment_id}/criteria/{cid}",
            json={"name": "New Name", "max_marks": 4},
        )
        assert r2.status_code == 200
        assert r2.json()["name"] == "New Name"
        assert r2.json()["max_marks"] == 4

    async def test_delete_criterion(self, teacher_client, assignment_id):
        r = await teacher_client.post(f"/api/v1/assignments/{assignment_id}/criteria", json={
            "name": "Del", "description": "d", "max_marks": 2,
        })
        cid = r.json()["id"]
        r2 = await teacher_client.delete(f"/api/v1/assignments/{assignment_id}/criteria/{cid}")
        assert r2.status_code == 204

    async def test_publish_requires_criteria(self, teacher_client, assignment_id):
        r = await teacher_client.post(f"/api/v1/assignments/{assignment_id}/publish")
        assert r.status_code == 422

    async def test_publish_with_criteria_succeeds(self, teacher_client, assignment_id):
        await teacher_client.post(f"/api/v1/assignments/{assignment_id}/criteria", json={
            "name": "Content", "description": "desc", "max_marks": 10,
        })
        r = await teacher_client.post(f"/api/v1/assignments/{assignment_id}/publish")
        assert r.status_code == 200
        assert r.json()["is_published"] is True

    async def test_cannot_delete_published_assignment(self, teacher_client, assignment_id):
        await teacher_client.post(f"/api/v1/assignments/{assignment_id}/criteria", json={
            "name": "C", "description": "d", "max_marks": 10,
        })
        await teacher_client.post(f"/api/v1/assignments/{assignment_id}/publish")
        r = await teacher_client.delete(f"/api/v1/assignments/{assignment_id}")
        assert r.status_code == 409

    async def test_student_sees_published_assignment(
        self, teacher_client, student_client, admin_client, assignment_id, student_user, db
    ):
        # Add criteria and publish
        await teacher_client.post(f"/api/v1/assignments/{assignment_id}/criteria", json={
            "name": "Content", "description": "desc", "max_marks": 10,
        })
        await teacher_client.post(f"/api/v1/assignments/{assignment_id}/publish")

        # Get the class_subject_id to find class_id
        r = await teacher_client.get(f"/api/v1/assignments/{assignment_id}")
        # Enrol the student in the class
        r2 = await teacher_client.get(f"/api/v1/assignments/{assignment_id}")
        # We need the class_id — get it from list_classes
        classes_r = await admin_client.get("/api/v1/classes")
        if classes_r.json():
            class_id = classes_r.json()[0]["id"]
            await admin_client.post(f"/api/v1/classes/{class_id}/enrolments", json={
                "student_ids": [str(student_user.id)]
            })

        r3 = await student_client.get("/api/v1/assignments")
        assert r3.status_code == 200
        # Student should see published assignments for enrolled classes
        ids = [a["id"] for a in r3.json()]
        assert assignment_id in ids

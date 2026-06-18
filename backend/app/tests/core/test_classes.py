"""Tests for classes, subjects, and enrolments."""
import pytest
from httpx import AsyncClient


@pytest.fixture
async def cls_id(admin_client: AsyncClient, school) -> str:
    r = await admin_client.post("/api/v1/classes", json={
        "name": "Science 1A",
        "programme": "General Science",
        "year_group": 1,
        "academic_year": "2024/2025",
    })
    assert r.status_code == 201
    return r.json()["id"]


@pytest.fixture
async def subject_id(admin_client: AsyncClient) -> str:
    r = await admin_client.post("/api/v1/subjects", json={
        "name": "Biology",
        "code": "BIOL_TEST",
        "ges_curriculum_area": "Sciences",
    })
    assert r.status_code == 201
    return r.json()["id"]


class TestClassCRUD:
    async def test_admin_creates_class(self, admin_client):
        r = await admin_client.post("/api/v1/classes", json={"name": "Arts 2B"})
        assert r.status_code == 201
        assert r.json()["name"] == "Arts 2B"

    async def test_teacher_cannot_create_class(self, teacher_client):
        r = await teacher_client.post("/api/v1/classes", json={"name": "Arts 2B"})
        assert r.status_code == 403

    async def test_list_classes_admin_sees_all(self, admin_client, cls_id):
        r = await admin_client.get("/api/v1/classes")
        assert r.status_code == 200
        ids = [c["id"] for c in r.json()]
        assert cls_id in ids

    async def test_list_classes_teacher_sees_assigned_only(
        self, admin_client, teacher_client, teacher_user, cls_id, subject_id
    ):
        # Assign teacher to a subject in the class
        await admin_client.post(f"/api/v1/classes/{cls_id}/subjects", json={
            "subject_id": subject_id,
            "teacher_id": str(teacher_user.id),
        })
        # Teacher should now see that class
        r = await teacher_client.get("/api/v1/classes")
        assert r.status_code == 200
        ids = [c["id"] for c in r.json()]
        assert cls_id in ids

    async def test_list_classes_teacher_empty_when_not_assigned(self, teacher_client, cls_id):
        r = await teacher_client.get("/api/v1/classes")
        assert r.status_code == 200
        ids = [c["id"] for c in r.json()]
        assert cls_id not in ids

    async def test_update_class(self, admin_client, cls_id):
        r = await admin_client.patch(f"/api/v1/classes/{cls_id}", json={
            "name": "Science 1A Updated",
            "programme": "General Science",
            "year_group": 1,
            "academic_year": "2024/2025",
        })
        assert r.status_code == 200
        assert r.json()["name"] == "Science 1A Updated"


class TestSubjectAssignment:
    async def test_assign_subject_to_class(self, admin_client, cls_id, subject_id, teacher_user):
        r = await admin_client.post(f"/api/v1/classes/{cls_id}/subjects", json={
            "subject_id": subject_id,
            "teacher_id": str(teacher_user.id),
        })
        assert r.status_code == 201
        data = r.json()
        assert data["subject_id"] == subject_id
        assert data["teacher_id"] == str(teacher_user.id)
        assert "subject_name" in data
        assert "teacher_name" in data

    async def test_duplicate_subject_returns_409(self, admin_client, cls_id, subject_id, teacher_user):
        payload = {"subject_id": subject_id, "teacher_id": str(teacher_user.id)}
        await admin_client.post(f"/api/v1/classes/{cls_id}/subjects", json=payload)
        r = await admin_client.post(f"/api/v1/classes/{cls_id}/subjects", json=payload)
        assert r.status_code == 409

    async def test_list_class_subjects(self, admin_client, cls_id, subject_id, teacher_user):
        await admin_client.post(f"/api/v1/classes/{cls_id}/subjects", json={
            "subject_id": subject_id,
            "teacher_id": str(teacher_user.id),
        })
        r = await admin_client.get(f"/api/v1/classes/{cls_id}/subjects")
        assert r.status_code == 200
        assert len(r.json()) == 1

    async def test_remove_class_subject(self, admin_client, cls_id, subject_id, teacher_user):
        r = await admin_client.post(f"/api/v1/classes/{cls_id}/subjects", json={
            "subject_id": subject_id,
            "teacher_id": str(teacher_user.id),
        })
        cs_id = r.json()["id"]
        r2 = await admin_client.delete(f"/api/v1/classes/{cls_id}/subjects/{cs_id}")
        assert r2.status_code == 204

    async def test_assign_non_teacher_returns_422(self, admin_client, cls_id, subject_id, student_user):
        r = await admin_client.post(f"/api/v1/classes/{cls_id}/subjects", json={
            "subject_id": subject_id,
            "teacher_id": str(student_user.id),
        })
        assert r.status_code == 422


class TestEnrolments:
    async def test_bulk_enrol(self, admin_client, cls_id, student_user):
        r = await admin_client.post(f"/api/v1/classes/{cls_id}/enrolments", json={
            "student_ids": [str(student_user.id)]
        })
        assert r.status_code == 201
        data = r.json()
        assert str(student_user.id) in data["enrolled"]

    async def test_re_enrol_goes_to_already_enrolled(self, admin_client, cls_id, student_user):
        payload = {"student_ids": [str(student_user.id)]}
        await admin_client.post(f"/api/v1/classes/{cls_id}/enrolments", json=payload)
        r = await admin_client.post(f"/api/v1/classes/{cls_id}/enrolments", json=payload)
        data = r.json()
        assert str(student_user.id) in data["already_enrolled"]

    async def test_enrol_non_student_goes_to_not_found(self, admin_client, cls_id, teacher_user):
        r = await admin_client.post(f"/api/v1/classes/{cls_id}/enrolments", json={
            "student_ids": [str(teacher_user.id)]
        })
        data = r.json()
        assert str(teacher_user.id) in data["not_found"]

    async def test_list_enrolments(self, admin_client, cls_id, student_user):
        await admin_client.post(f"/api/v1/classes/{cls_id}/enrolments", json={
            "student_ids": [str(student_user.id)]
        })
        r = await admin_client.get(f"/api/v1/classes/{cls_id}/enrolments")
        assert r.status_code == 200
        assert len(r.json()) == 1

    async def test_list_student_count_in_class_list(self, admin_client, cls_id, student_user):
        await admin_client.post(f"/api/v1/classes/{cls_id}/enrolments", json={
            "student_ids": [str(student_user.id)]
        })
        r = await admin_client.get("/api/v1/classes")
        classes = r.json()
        target = next(c for c in classes if c["id"] == cls_id)
        assert target["student_count"] == 1

    async def test_remove_enrolment(self, admin_client, cls_id, student_user):
        await admin_client.post(f"/api/v1/classes/{cls_id}/enrolments", json={
            "student_ids": [str(student_user.id)]
        })
        r = await admin_client.delete(f"/api/v1/classes/{cls_id}/enrolments/{student_user.id}")
        assert r.status_code == 204
        r2 = await admin_client.get(f"/api/v1/classes/{cls_id}/enrolments")
        assert len(r2.json()) == 0

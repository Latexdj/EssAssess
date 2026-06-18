import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_creates_teacher(admin_client: AsyncClient):
    r = await admin_client.post("/api/v1/users", json={
        "email": "newteacher@test.dev",
        "password": "Pass1234!",
        "first_name": "New",
        "last_name": "Teacher",
        "role": "teacher",
    })
    assert r.status_code == 201
    assert r.json()["role"] == "teacher"
    assert r.json()["is_active"] is True


@pytest.mark.asyncio
async def test_duplicate_email_returns_409(admin_client: AsyncClient, admin_user):
    r = await admin_client.post("/api/v1/users", json={
        "email": "admin@test.dev",
        "password": "Pass1234!",
        "first_name": "Dup",
        "last_name": "User",
        "role": "teacher",
    })
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_list_users(admin_client: AsyncClient, teacher_user, student_user):
    r = await admin_client.get("/api/v1/users")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 3
    assert isinstance(data["users"], list)


@pytest.mark.asyncio
async def test_list_users_filter_by_role(admin_client: AsyncClient, teacher_user):
    r = await admin_client.get("/api/v1/users?role=teacher")
    assert r.status_code == 200
    assert all(u["role"] == "teacher" for u in r.json()["users"])


@pytest.mark.asyncio
async def test_deactivate_user(admin_client: AsyncClient, student_user):
    r = await admin_client.delete(f"/api/v1/users/{student_user.id}")
    assert r.status_code == 204

    r2 = await admin_client.get(f"/api/v1/users/{student_user.id}")
    assert r2.json()["is_active"] is False


@pytest.mark.asyncio
async def test_update_user_name(admin_client: AsyncClient, teacher_user):
    r = await admin_client.patch(f"/api/v1/users/{teacher_user.id}", json={"first_name": "Updated"})
    assert r.status_code == 200
    assert r.json()["first_name"] == "Updated"

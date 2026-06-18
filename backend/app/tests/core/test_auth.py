import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_valid(client: AsyncClient, admin_user):
    r = await client.post("/api/v1/auth/login", json={"email": "admin@test.dev", "password": "Admin1234!"})
    assert r.status_code == 200
    data = r.json()
    assert data["user"]["role"] == "admin"
    assert data["user"]["email"] == "admin@test.dev"
    assert "access_token" in r.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, admin_user):
    r = await client.post("/api/v1/auth/login", json={"email": "admin@test.dev", "password": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client: AsyncClient):
    r = await client.post("/api/v1/auth/login", json={"email": "nobody@test.dev", "password": "x"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_current_user(admin_client: AsyncClient):
    r = await admin_client.get("/api/v1/auth/me")
    assert r.status_code == 200
    assert r.json()["user"]["role"] == "admin"


@pytest.mark.asyncio
async def test_me_without_token(client: AsyncClient):
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_logout_clears_cookie(admin_client: AsyncClient):
    r = await admin_client.post("/api/v1/auth/logout")
    assert r.status_code == 204
    assert "access_token" not in r.cookies or r.cookies.get("access_token") == ""


@pytest.mark.asyncio
async def test_teacher_cannot_access_admin_users(teacher_client: AsyncClient):
    r = await teacher_client.get("/api/v1/users")
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_student_cannot_access_admin_users(student_client: AsyncClient):
    r = await student_client.get("/api/v1/users")
    assert r.status_code == 403

import pytest
import asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import Base, get_db
from app.models.school import School, SchoolType
from app.models.user import User, UserRole
from app.services.core.auth_service import hash_password

TEST_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/essassess_test"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """Create/drop all tables. Only triggered by tests that use `db` or `client`."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db(setup_database) -> AsyncSession:
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
def override_db(db):
    async def _get_db():
        yield db
    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def client(override_db) -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ── Seeded data ─────────────────────────────────────────────────────────────

@pytest.fixture
async def school(db) -> School:
    s = School(name="Test SHS", region="Greater Accra", type=SchoolType.SHS)
    db.add(s)
    await db.flush()
    await db.refresh(s)
    return s


@pytest.fixture
async def admin_user(db, school) -> User:
    u = User(school_id=school.id, email="admin@test.dev", password_hash=hash_password("Admin1234!"),
             first_name="Admin", last_name="User", role=UserRole.admin)
    db.add(u)
    await db.flush()
    await db.refresh(u)
    return u


@pytest.fixture
async def teacher_user(db, school) -> User:
    u = User(school_id=school.id, email="teacher@test.dev", password_hash=hash_password("Teacher1234!"),
             first_name="Teacher", last_name="User", role=UserRole.teacher)
    db.add(u)
    await db.flush()
    await db.refresh(u)
    return u


@pytest.fixture
async def student_user(db, school) -> User:
    u = User(school_id=school.id, email="student@test.dev", password_hash=hash_password("Student1234!"),
             first_name="Student", last_name="User", role=UserRole.student)
    db.add(u)
    await db.flush()
    await db.refresh(u)
    return u


# ── Auth helpers ─────────────────────────────────────────────────────────────

async def _login(client: AsyncClient, email: str, password: str):
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    return r


@pytest.fixture
async def admin_client(client, admin_user) -> AsyncClient:
    await _login(client, "admin@test.dev", "Admin1234!")
    return client


@pytest.fixture
async def teacher_client(client, teacher_user) -> AsyncClient:
    await _login(client, "teacher@test.dev", "Teacher1234!")
    return client


@pytest.fixture
async def student_client(client, student_user) -> AsyncClient:
    await _login(client, "student@test.dev", "Student1234!")
    return client

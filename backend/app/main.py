import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db

logger = logging.getLogger("essassess")


async def _auto_seed() -> None:
    """Seed demo data on first boot if the database is empty."""
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models.user import User
    from app.models.school import School, SchoolType
    from app.models.subject import Subject
    from app.models.user import UserRole
    from app.services.core.auth_service import hash_password

    async with AsyncSessionLocal() as db:
        existing = (await db.execute(select(User).limit(1))).scalar_one_or_none()
        if existing:
            return  # already seeded

        logger.info("Empty database detected — running auto-seed")

        # School
        school = School(
            name="Tamale Senior High Technical School",
            region="Northern Region",
            type=SchoolType.SHTS,
        )
        db.add(school)
        await db.flush()

        # Users
        for email, pw, first, last, role in [
            ("admin@essassess.dev",   "Admin1234!",   "Adwoa",   "Mensah",  UserRole.admin),
            ("teacher@essassess.dev", "Teacher1234!", "Kwabena", "Asante",  UserRole.teacher),
            ("student@essassess.dev", "Student1234!", "Akosua",  "Boateng", UserRole.student),
        ]:
            db.add(User(school_id=school.id, email=email,
                        password_hash=hash_password(pw),
                        first_name=first, last_name=last, role=role))

        # GES subjects
        subjects = [
            ("English Language",       "ENG",   "Languages"),
            ("Social Studies",         "SS",    "Social Sciences"),
            ("Integrated Science",     "ISCI",  "Sciences"),
            ("Mathematics (Core)",     "MATH",  "Mathematics"),
            ("Biology",                "BIOL",  "Sciences"),
            ("Chemistry",              "CHEM",  "Sciences"),
            ("Physics",                "PHYS",  "Sciences"),
            ("Elective Mathematics",   "EMATH", "Mathematics"),
            ("Economics",              "ECONS", "Social Sciences"),
            ("Government",             "GOVT",  "Social Sciences"),
            ("History",                "HIST",  "Social Sciences"),
            ("Geography",              "GEOG",  "Social Sciences"),
            ("Literature in English",  "LIT",   "Languages"),
            ("Business Management",    "BMGT",  "Business"),
            ("Financial Accounting",   "FACCT", "Business"),
            ("Cost Accounting",        "CACCT", "Business"),
            ("Technical Drawing",      "TDRAW", "Technical"),
            ("Building Construction",  "BCON",  "Technical"),
            ("Auto Mechanics",         "AMECH", "Technical"),
            ("Hospitality Management", "HOSP",  "TVET"),
            ("Information Technology", "IT",    "TVET"),
        ]
        for name, code, area in subjects:
            db.add(Subject(name=name, code=code, ges_curriculum_area=area))

        await db.commit()
        logger.info("Auto-seed complete — school, 3 users, 21 subjects created")


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(os.path.join(settings.upload_dir, "submissions"), exist_ok=True)
    await _auto_seed()
    logger.info("EssAssess API started — upload dir: %s", settings.upload_dir)
    yield
    logger.info("EssAssess API shutting down")


app = FastAPI(
    title="EssAssess API",
    description="LMS with AI-powered essay grading for Ghanaian SHS/SHTS/TVET institutions",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
async def health_check(db: AsyncSession = Depends(get_db)):
    db_ok = True
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    status = "ok" if db_ok else "degraded"
    return {
        "status":  status,
        "version": "1.0.0",
        "service": "EssAssess API",
        "db":      "ok" if db_ok else "error",
    }


from app.routers import auth, users, school, subjects, classes, enrolments, knowledge, assignments, submissions, gradebook

for r in [auth.router, users.router, school.router, subjects.router, classes.router, enrolments.router, knowledge.router, assignments.router, submissions.router, gradebook.router]:
    app.include_router(r, prefix="/api/v1")

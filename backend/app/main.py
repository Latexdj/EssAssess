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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    os.makedirs(os.path.join(settings.upload_dir, "submissions"), exist_ok=True)
    logger.info("EssAssess API started — upload dir: %s", settings.upload_dir)
    yield
    # Shutdown
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

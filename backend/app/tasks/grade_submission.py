"""
Background grading task.

Creates its own DB session — the request session is already closed by the time
FastAPI background tasks run.
"""
import logging
from uuid import UUID

from app.database import AsyncSessionLocal
from app.models.submission import Submission, SubmissionStatus

logger = logging.getLogger(__name__)


async def grade_submission_task(submission_id: UUID) -> None:
    """Run the full grading pipeline for one submission."""
    async with AsyncSessionLocal() as db:
        try:
            from app.services.grading.grading_orchestrator import run_grading
            await run_grading(db, submission_id)
            await db.commit()
        except Exception as exc:
            logger.error("Grading task failed for %s: %s", submission_id, exc)
            await db.rollback()
            # Best-effort: mark as failed
            try:
                async with AsyncSessionLocal() as err_db:
                    sub = await err_db.get(Submission, submission_id)
                    if sub and sub.status not in (
                        SubmissionStatus.graded,
                        SubmissionStatus.finalised,
                    ):
                        sub.status = SubmissionStatus.grading_failed
                        await err_db.commit()
            except Exception:
                logger.exception("Could not mark submission %s as grading_failed", submission_id)

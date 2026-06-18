"""
Phase 6 — Submission service unit tests.

All tests run without a real DB by mocking the DB session and model lookups.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

import pytest

from app.services.core import submission_service
from app.models.submission import SubmissionType, SubmissionStatus
from app.schemas.submission import TextSubmissionCreate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_assignment(class_id=None):
    a = MagicMock()
    a.id                       = uuid.uuid4()
    a.class_subject_id         = uuid.uuid4()
    a.class_subject            = MagicMock()
    a.class_subject.class_id   = class_id or uuid.uuid4()
    a.is_published             = True
    a.allowed_submission_types = ["text", "pdf", "image"]
    return a


def _fake_user(user_id=None):
    u = MagicMock()
    u.id         = user_id or uuid.uuid4()
    u.first_name = "Kwame"
    u.last_name  = "Mensah"
    return u


def _fake_submission(sub_type=SubmissionType.text, status=SubmissionStatus.pending_grading):
    s = MagicMock()
    s.id                = uuid.uuid4()
    s.assignment_id     = uuid.uuid4()
    s.student_id        = uuid.uuid4()
    s.submission_type   = sub_type
    s.status            = status
    s.text_content      = "Student essay text"
    s.file_name         = None
    s.file_size_bytes   = None
    s.submitted_at      = datetime.now(timezone.utc)
    s.updated_at        = datetime.now(timezone.utc)
    s.student           = _fake_user()
    s.ai_grading_result = None
    return s


# ---------------------------------------------------------------------------
# _enrich
# ---------------------------------------------------------------------------

class TestEnrich:
    def test_text_submission_no_ai_result(self):
        sub = _fake_submission()
        out = submission_service._enrich(sub)
        assert out.total_ai_score is None
        assert out.formative_feedback is None
        assert out.student_name == "Kwame Mensah"

    def test_graded_submission_includes_ai_score(self):
        sub = _fake_submission(status=SubmissionStatus.graded)
        sub.ai_grading_result               = MagicMock()
        sub.ai_grading_result.total_ai_score   = 15.0
        sub.ai_grading_result.formative_feedback = "Good work"
        sub.ai_grading_result.error_message    = None
        out = submission_service._enrich(sub)
        assert out.total_ai_score == 15.0
        assert out.formative_feedback == "Good work"

    def test_null_student_gives_none_name(self):
        sub = _fake_submission()
        sub.student = None
        out = submission_service._enrich(sub)
        assert out.student_name is None


# ---------------------------------------------------------------------------
# _guard_resubmit
# ---------------------------------------------------------------------------

class TestGuardResubmit:
    def test_none_existing_is_ok(self):
        submission_service._guard_resubmit(None)  # no exception

    def test_grading_in_progress_raises_409(self):
        sub = _fake_submission(status=SubmissionStatus.grading_in_progress)
        with pytest.raises(Exception) as exc:
            submission_service._guard_resubmit(sub)
        assert "409" in str(exc.value) or "graded" in str(exc.value).lower() or "grading" in str(exc.value).lower()

    def test_already_graded_raises_409(self):
        sub = _fake_submission(status=SubmissionStatus.graded)
        with pytest.raises(Exception):
            submission_service._guard_resubmit(sub)

    def test_pending_grading_allowed(self):
        sub = _fake_submission(status=SubmissionStatus.pending_grading)
        submission_service._guard_resubmit(sub)  # no exception

    def test_grading_failed_allowed(self):
        sub = _fake_submission(status=SubmissionStatus.grading_failed)
        submission_service._guard_resubmit(sub)  # no exception


# ---------------------------------------------------------------------------
# _safe_filename
# ---------------------------------------------------------------------------

class TestSafeFilename:
    def test_strips_special_chars(self):
        result = submission_service._safe_filename("my essay (final)!.pdf")
        assert " " not in result
        assert "(" not in result
        assert "!" not in result
        assert result.endswith(".pdf")

    def test_truncates_long_names(self):
        long = "a" * 200 + ".pdf"
        assert len(submission_service._safe_filename(long)) <= 100

    def test_keeps_allowed_chars(self):
        result = submission_service._safe_filename("my-essay_v2.pdf")
        assert result == "my-essay_v2.pdf"


# ---------------------------------------------------------------------------
# create_text_submission (mocked DB)
# ---------------------------------------------------------------------------

class TestCreateTextSubmission:
    @pytest.mark.asyncio
    async def test_creates_new_submission(self):
        db = AsyncMock()
        student_id = uuid.uuid4()
        assignment = _fake_assignment()
        user = _fake_user(student_id)

        with (
            patch.object(submission_service, "_load_assignment", AsyncMock(return_value=assignment)),
            patch.object(submission_service, "_check_enrolment", AsyncMock()),
            patch.object(submission_service, "_get_existing", AsyncMock(return_value=None)),
            patch.object(db, "get", AsyncMock(return_value=user)),
        ):
            db.flush = AsyncMock()
            db.add = MagicMock()

            out = await submission_service.create_text_submission(
                db, assignment.id, student_id, "A" * 60
            )

        assert out.student_name == "Kwame Mensah"
        db.add.assert_called_once()
        db.flush.assert_called()

    @pytest.mark.asyncio
    async def test_text_not_allowed_raises_422(self):
        db = AsyncMock()
        assignment = _fake_assignment()
        assignment.allowed_submission_types = ["pdf", "image"]

        with (
            patch.object(submission_service, "_load_assignment", AsyncMock(return_value=assignment)),
            patch.object(submission_service, "_check_enrolment", AsyncMock()),
            patch.object(submission_service, "_get_existing", AsyncMock(return_value=None)),
        ):
            with pytest.raises(Exception) as exc:
                await submission_service.create_text_submission(
                    db, assignment.id, uuid.uuid4(), "A" * 60
                )
        assert "422" in str(exc.value) or "not allowed" in str(exc.value).lower()

    @pytest.mark.asyncio
    async def test_updates_existing_failed_submission(self):
        db = AsyncMock()
        student_id = uuid.uuid4()
        assignment = _fake_assignment()
        existing = _fake_submission(status=SubmissionStatus.grading_failed)
        user = _fake_user(student_id)

        with (
            patch.object(submission_service, "_load_assignment", AsyncMock(return_value=assignment)),
            patch.object(submission_service, "_check_enrolment", AsyncMock()),
            patch.object(submission_service, "_get_existing", AsyncMock(return_value=existing)),
            patch.object(db, "get", AsyncMock(return_value=user)),
        ):
            db.flush = AsyncMock()
            out = await submission_service.create_text_submission(
                db, assignment.id, student_id, "B" * 60
            )

        assert existing.text_content == "B" * 60
        assert existing.status == SubmissionStatus.pending_grading


# ---------------------------------------------------------------------------
# create_file_submission (mocked DB + filesystem)
# ---------------------------------------------------------------------------

class TestCreateFileSubmission:
    @pytest.mark.asyncio
    async def test_rejects_unknown_extension(self):
        db = AsyncMock()
        with pytest.raises(Exception) as exc:
            await submission_service.create_file_submission(
                db, uuid.uuid4(), uuid.uuid4(), b"data", "essay.docx", "/tmp"
            )
        assert "422" in str(exc.value) or "accepted" in str(exc.value).lower()

    @pytest.mark.asyncio
    async def test_pdf_submission_extracts_text(self):
        db = AsyncMock()
        student_id = uuid.uuid4()
        assignment = _fake_assignment()
        user = _fake_user(student_id)

        with (
            patch.object(submission_service, "_load_assignment", AsyncMock(return_value=assignment)),
            patch.object(submission_service, "_check_enrolment", AsyncMock()),
            patch.object(submission_service, "_get_existing", AsyncMock(return_value=None)),
            patch.object(db, "get", AsyncMock(return_value=user)),
            patch("app.services.grading.knowledge_service.extract_text_from_pdf", return_value="Extracted PDF text"),
            patch("os.makedirs"),
            patch("builtins.open", MagicMock()),
        ):
            db.flush = AsyncMock()
            db.add = MagicMock()

            out = await submission_service.create_file_submission(
                db, assignment.id, student_id, b"%PDF fake", "essay.pdf", "/tmp/uploads"
            )

        db.add.assert_called_once()
        # transcribed_text is set on the model object that was added
        call_args = db.add.call_args[0][0]
        assert call_args.transcribed_text == "Extracted PDF text"
        assert call_args.submission_type == SubmissionType.pdf

    @pytest.mark.asyncio
    async def test_image_submission_no_extraction(self):
        db = AsyncMock()
        student_id = uuid.uuid4()
        assignment = _fake_assignment()
        user = _fake_user(student_id)

        with (
            patch.object(submission_service, "_load_assignment", AsyncMock(return_value=assignment)),
            patch.object(submission_service, "_check_enrolment", AsyncMock()),
            patch.object(submission_service, "_get_existing", AsyncMock(return_value=None)),
            patch.object(db, "get", AsyncMock(return_value=user)),
            patch("os.makedirs"),
            patch("builtins.open", MagicMock()),
        ):
            db.flush = AsyncMock()
            db.add = MagicMock()

            out = await submission_service.create_file_submission(
                db, assignment.id, student_id, b"\xff\xd8fake_jpeg", "photo.jpg", "/tmp/uploads"
            )

        call_args = db.add.call_args[0][0]
        assert call_args.submission_type == SubmissionType.image
        assert call_args.transcribed_text is None

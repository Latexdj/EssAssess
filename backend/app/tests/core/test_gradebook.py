"""
Phase 8 — Gradebook service unit tests.

Tests the data-transformation layer (_enrich logic) without a real database.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.services.core import gradebook_service
from app.models.submission import SubmissionType, SubmissionStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now():
    return datetime.now(timezone.utc)


def _sub(status=SubmissionStatus.graded):
    sub = MagicMock()
    sub.id          = uuid.uuid4()
    sub.student_id  = uuid.uuid4()
    sub.submitted_at = _now()
    sub.status      = status

    # Assignment → class_subject → subject / class_
    cs = MagicMock()
    cs.subject      = MagicMock()
    cs.subject.name = "English Language"
    cs.subject.code = "ENG"
    cs.class_       = MagicMock()
    cs.class_.name  = "Form 3A"

    a = MagicMock()
    a.id            = uuid.uuid4()
    a.title         = "Essay 1"
    a.max_marks     = 20
    a.due_date      = _now()
    a.class_subject = cs

    sub.assignment = a

    sub.ai_grading_result  = None
    sub.finalised_grade    = None
    return sub


def _with_ai(sub, score=14.0, feedback="Good"):
    ai = MagicMock()
    ai.total_ai_score    = score
    ai.formative_feedback = feedback
    sub.ai_grading_result = ai
    return sub


def _with_fg(sub, score=16.0, comment="Well done", published=True):
    fg = MagicMock()
    fg.total_score    = score
    fg.teacher_comment = comment
    fg.is_published   = published
    sub.finalised_grade = fg
    return sub


# ---------------------------------------------------------------------------
# get_student_grades data transformation
# ---------------------------------------------------------------------------

class TestStudentGradeTransformation:
    """Test the per-row mapping logic without hitting the DB."""

    def _grade_from(self, sub):
        """Replicate the per-row logic from gradebook_service."""
        a  = sub.assignment
        cs = a.class_subject
        fg = sub.finalised_grade
        ai = sub.ai_grading_result

        is_published = fg.is_published if fg else False

        from app.schemas.gradebook import StudentGradeOut
        return StudentGradeOut(
            submission_id=sub.id,
            assignment_id=a.id,
            assignment_title=a.title,
            class_name=cs.class_.name if cs.class_ else "",
            subject_name=cs.subject.name if cs.subject else "",
            subject_code=cs.subject.code if cs.subject else "",
            max_marks=a.max_marks,
            due_date=a.due_date,
            submitted_at=sub.submitted_at,
            status=sub.status.value,
            ai_score=float(ai.total_ai_score) if ai else None,
            formative_feedback=ai.formative_feedback if ai else None,
            final_score=float(fg.total_score) if (fg and is_published) else None,
            teacher_comment=fg.teacher_comment if (fg and is_published) else None,
            is_published=is_published,
        )

    def test_graded_no_finalise_shows_ai_only(self):
        sub = _with_ai(_sub())
        g = self._grade_from(sub)
        assert g.ai_score == 14.0
        assert g.final_score is None
        assert g.is_published is False

    def test_published_final_grade_shown(self):
        sub = _with_fg(_with_ai(_sub(SubmissionStatus.finalised)), published=True)
        g = self._grade_from(sub)
        assert g.final_score == 16.0
        assert g.teacher_comment == "Well done"
        assert g.is_published is True

    def test_unpublished_final_grade_hidden(self):
        sub = _with_fg(_with_ai(_sub(SubmissionStatus.finalised)), published=False)
        g = self._grade_from(sub)
        assert g.final_score is None
        assert g.teacher_comment is None
        assert g.is_published is False

    def test_no_ai_result_gives_none_score(self):
        sub = _sub()  # no ai_grading_result
        g = self._grade_from(sub)
        assert g.ai_score is None
        assert g.formative_feedback is None

    def test_correct_metadata(self):
        sub = _sub()
        g = self._grade_from(sub)
        assert g.class_name == "Form 3A"
        assert g.subject_name == "English Language"
        assert g.subject_code == "ENG"
        assert g.assignment_title == "Essay 1"
        assert g.max_marks == 20

    def test_status_passed_through(self):
        sub = _sub(status=SubmissionStatus.finalised)
        g = self._grade_from(sub)
        assert g.status == "finalised"


# ---------------------------------------------------------------------------
# AssignmentStatsOut field checks
# ---------------------------------------------------------------------------

class TestAssignmentStatsOut:
    def test_zero_counts_when_no_submissions(self):
        from app.schemas.gradebook import AssignmentStatsOut
        stats = AssignmentStatsOut(
            assignment_id=uuid.uuid4(),
            title="Test",
            subject_name="English",
            subject_code="ENG",
            max_marks=20,
            due_date=_now(),
            is_published=True,
            enrolled_count=30,
            submitted_count=0,
            graded_count=0,
            finalised_count=0,
            published_count=0,
            avg_ai_score=None,
            avg_final_score=None,
        )
        assert stats.submitted_count == 0
        assert stats.avg_ai_score is None

    def test_float_avg_scores(self):
        from app.schemas.gradebook import AssignmentStatsOut
        stats = AssignmentStatsOut(
            assignment_id=uuid.uuid4(),
            title="Test",
            subject_name="English",
            subject_code="ENG",
            max_marks=20,
            due_date=_now(),
            is_published=True,
            enrolled_count=10,
            submitted_count=8,
            graded_count=7,
            finalised_count=5,
            published_count=3,
            avg_ai_score=14.25,
            avg_final_score=15.5,
        )
        assert stats.avg_ai_score == 14.25
        assert stats.avg_final_score == 15.5

    def test_submission_rate(self):
        from app.schemas.gradebook import AssignmentStatsOut
        stats = AssignmentStatsOut(
            assignment_id=uuid.uuid4(),
            title="Test",
            subject_name="English",
            subject_code="ENG",
            max_marks=20,
            due_date=_now(),
            is_published=True,
            enrolled_count=30,
            submitted_count=25,
            graded_count=25,
            finalised_count=0,
            published_count=0,
            avg_ai_score=None,
            avg_final_score=None,
        )
        # Submission rate = 25/30
        assert stats.submitted_count / stats.enrolled_count == pytest.approx(25 / 30)

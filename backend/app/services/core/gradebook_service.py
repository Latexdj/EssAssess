"""
Gradebook service.

Two primary views:
  1. Student: own published grades across all assignments.
  2. Teacher: per-class assignment stats (submitted/graded/finalised/avg score).
"""
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.submission import Submission, SubmissionStatus
from app.models.assignment import Assignment
from app.models.class_subject import ClassSubject
from app.models.subject import Subject
from app.models.class_ import Class
from app.models.enrolment import Enrolment
from app.models.ai_grading_result import AIGradingResult
from app.models.finalised_grade import FinalisedGrade
from app.schemas.gradebook import (
    StudentGradeOut,
    AssignmentStatsOut,
    ClassGradebookOut,
)


# ---------------------------------------------------------------------------
# Student view
# ---------------------------------------------------------------------------

async def get_student_grades(
    db:         AsyncSession,
    student_id: UUID,
) -> list[StudentGradeOut]:
    stmt = (
        select(Submission)
        .where(
            Submission.student_id == student_id,
            Submission.status.in_([
                SubmissionStatus.graded,
                SubmissionStatus.finalised,
            ]),
        )
        .options(
            selectinload(Submission.assignment).options(
                selectinload(Assignment.class_subject).options(
                    selectinload(ClassSubject.subject),
                    selectinload(ClassSubject.class_),
                ),
            ),
            selectinload(Submission.ai_grading_result),
            selectinload(Submission.finalised_grade),
        )
        .order_by(Submission.submitted_at.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()

    out: list[StudentGradeOut] = []
    for sub in rows:
        a   = sub.assignment
        cs  = a.class_subject
        fg  = sub.finalised_grade
        ai  = sub.ai_grading_result

        is_published = fg.is_published if fg else False
        out.append(StudentGradeOut(
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
        ))
    return out


# ---------------------------------------------------------------------------
# Teacher class gradebook view
# ---------------------------------------------------------------------------

async def get_class_gradebook(
    db:         AsyncSession,
    class_id:   UUID,
    teacher_id: UUID,
    is_admin:   bool = False,
) -> ClassGradebookOut:
    # Load class
    cls = await db.get(Class, class_id)
    if not cls:
        raise HTTPException(404, "Class not found")

    # Enrolled student count
    enrolled_count = (await db.execute(
        select(func.count())
        .select_from(Enrolment)
        .where(Enrolment.class_id == class_id, Enrolment.is_active == True)
    )).scalar() or 0

    # Aggregate stats per assignment using a single SQL query
    # is(case) needs SQLAlchemy's case() function
    agg = (
        select(
            Assignment.id.label("assignment_id"),
            Assignment.title,
            Subject.name.label("subject_name"),
            Subject.code.label("subject_code"),
            Assignment.max_marks,
            Assignment.due_date,
            Assignment.is_published,
            func.count(Submission.id.distinct()).label("submitted_count"),
            func.count(AIGradingResult.id.distinct()).label("graded_count"),
            func.count(FinalisedGrade.id.distinct()).label("finalised_count"),
            func.sum(
                case((FinalisedGrade.is_published == True, 1), else_=0)
            ).label("published_count"),
            func.avg(AIGradingResult.total_ai_score).label("avg_ai_score"),
            func.avg(FinalisedGrade.total_score).label("avg_final_score"),
        )
        .select_from(Assignment)
        .join(ClassSubject, Assignment.class_subject_id == ClassSubject.id)
        .join(Subject, ClassSubject.subject_id == Subject.id)
        .outerjoin(Submission, Submission.assignment_id == Assignment.id)
        .outerjoin(AIGradingResult, AIGradingResult.submission_id == Submission.id)
        .outerjoin(FinalisedGrade, FinalisedGrade.submission_id == Submission.id)
        .where(ClassSubject.class_id == class_id)
        .group_by(
            Assignment.id,
            Assignment.title,
            Subject.name,
            Subject.code,
            Assignment.max_marks,
            Assignment.due_date,
            Assignment.is_published,
        )
        .order_by(Assignment.due_date)
    )
    if not is_admin:
        agg = agg.where(ClassSubject.teacher_id == teacher_id)

    result = (await db.execute(agg)).mappings().all()

    assignments = [
        AssignmentStatsOut(
            assignment_id=row["assignment_id"],
            title=row["title"],
            subject_name=row["subject_name"],
            subject_code=row["subject_code"],
            max_marks=row["max_marks"],
            due_date=row["due_date"],
            is_published=row["is_published"],
            enrolled_count=enrolled_count,
            submitted_count=row["submitted_count"] or 0,
            graded_count=row["graded_count"] or 0,
            finalised_count=row["finalised_count"] or 0,
            published_count=int(row["published_count"] or 0),
            avg_ai_score=float(row["avg_ai_score"]) if row["avg_ai_score"] is not None else None,
            avg_final_score=float(row["avg_final_score"]) if row["avg_final_score"] is not None else None,
        )
        for row in result
    ]

    return ClassGradebookOut(
        class_id=class_id,
        class_name=cls.name,
        enrolled_count=enrolled_count,
        assignments=assignments,
    )

"""Initial schema — all tables, enums, indexes

Revision ID: 001
Revises:
Create Date: 2025-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")

    # schools — SQLAlchemy auto-creates the school_type enum on first use
    op.create_table(
        "schools",
        sa.Column("id",         postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name",       sa.String,    nullable=False),
        sa.Column("region",     sa.String,    nullable=False),
        sa.Column("type",       sa.Enum("SHS", "SHTS", "TVET", name="school_type"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # users
    op.create_table(
        "users",
        sa.Column("id",            postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id",     postgresql.UUID(as_uuid=True), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email",         sa.String, nullable=False, unique=True),
        sa.Column("password_hash", sa.String, nullable=False),
        sa.Column("first_name",    sa.String, nullable=False),
        sa.Column("last_name",     sa.String, nullable=False),
        sa.Column("role",          sa.Enum("admin", "teacher", "student", name="user_role"), nullable=False),
        sa.Column("is_active",     sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at",    sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at",    sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_users_school", "users", ["school_id"])
    op.create_index("idx_users_role",   "users", ["role"])

    # subjects
    op.create_table(
        "subjects",
        sa.Column("id",                  postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name",                sa.String, nullable=False),
        sa.Column("code",                sa.String, nullable=False, unique=True),
        sa.Column("ges_curriculum_area", sa.String, nullable=True),
        sa.Column("created_at",          sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # classes
    op.create_table(
        "classes",
        sa.Column("id",            postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id",     postgresql.UUID(as_uuid=True), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name",          sa.String,      nullable=False),
        sa.Column("programme",     sa.String,      nullable=True),
        sa.Column("year_group",    sa.SmallInteger, nullable=True),
        sa.Column("academic_year", sa.String,      nullable=True),
        sa.Column("created_at",    sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_classes_school", "classes", ["school_id"])

    # class_subjects
    op.create_table(
        "class_subjects",
        sa.Column("id",         postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("class_id",   postgresql.UUID(as_uuid=True), sa.ForeignKey("classes.id",  ondelete="CASCADE"),  nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subjects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id",    ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("class_id", "subject_id", name="uq_class_subject"),
    )
    op.create_index("idx_class_subjects_class",   "class_subjects", ["class_id"])
    op.create_index("idx_class_subjects_teacher", "class_subjects", ["teacher_id"])

    # enrolments
    op.create_table(
        "enrolments",
        sa.Column("id",          postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("student_id",  postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id",   ondelete="CASCADE"), nullable=False),
        sa.Column("class_id",    postgresql.UUID(as_uuid=True), sa.ForeignKey("classes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("is_active",   sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("student_id", "class_id", name="uq_enrolment"),
    )
    op.create_index("idx_enrolments_student", "enrolments", ["student_id"])
    op.create_index("idx_enrolments_class",   "enrolments", ["class_id"])

    # announcements
    op.create_table(
        "announcements",
        sa.Column("id",         postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("class_id",   postgresql.UUID(as_uuid=True), sa.ForeignKey("classes.id", ondelete="CASCADE"),  nullable=False),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id",   ondelete="RESTRICT"), nullable=False),
        sa.Column("title",      sa.String, nullable=False),
        sa.Column("body",       sa.Text,   nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_announcements_class", "announcements", ["class_id"])

    # assignments
    op.create_table(
        "assignments",
        sa.Column("id",                       postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("class_subject_id",         postgresql.UUID(as_uuid=True), sa.ForeignKey("class_subjects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title",                    sa.String,       nullable=False),
        sa.Column("question_text",            sa.Text,         nullable=False),
        sa.Column("instructions",             sa.Text,         nullable=True),
        sa.Column("allowed_submission_types", postgresql.ARRAY(sa.String), nullable=False, server_default=sa.text("ARRAY['text','pdf','image']")),
        sa.Column("max_marks",                sa.SmallInteger, nullable=False),
        sa.Column("due_date",                 sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_published",             sa.Boolean,      nullable=False, server_default=sa.text("false")),
        sa.Column("created_at",               sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at",               sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_assignments_class_subject", "assignments", ["class_subject_id"])
    op.create_index("idx_assignments_due_date",      "assignments", ["due_date"])

    # rubric_criteria
    op.create_table(
        "rubric_criteria",
        sa.Column("id",            postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name",          sa.String,       nullable=False),
        sa.Column("description",   sa.Text,         nullable=False),
        sa.Column("max_marks",     sa.SmallInteger, nullable=False),
        sa.Column("display_order", sa.SmallInteger, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at",    sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_rubric_criteria_assignment", "rubric_criteria", ["assignment_id"])

    # submissions
    op.create_table(
        "submissions",
        sa.Column("id",               postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("assignment_id",    postgresql.UUID(as_uuid=True), sa.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id",       postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id",       ondelete="CASCADE"), nullable=False),
        sa.Column("submission_type",  sa.Enum("text", "pdf", "image", name="sub_type"), nullable=False),
        sa.Column("status",           sa.Enum("pending_grading", "grading_in_progress", "graded", "grading_failed", "finalised", name="sub_status"), nullable=False, server_default=sa.text("'pending_grading'")),
        sa.Column("text_content",     sa.Text,    nullable=True),
        sa.Column("file_path",        sa.String,  nullable=True),
        sa.Column("file_name",        sa.String,  nullable=True),
        sa.Column("file_size_bytes",  sa.Integer, nullable=True),
        sa.Column("transcribed_text", sa.Text,    nullable=True),
        sa.Column("submitted_at",     sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at",       sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("assignment_id", "student_id", name="uq_submission"),
    )
    op.create_index("idx_submissions_assignment", "submissions", ["assignment_id"])
    op.create_index("idx_submissions_student",    "submissions", ["student_id"])
    op.create_index("idx_submissions_status",     "submissions", ["status"])

    # ai_grading_results
    op.create_table(
        "ai_grading_results",
        sa.Column("id",                  postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("submission_id",       postgresql.UUID(as_uuid=True), sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("total_ai_score",      sa.Numeric(5, 2), nullable=False),
        sa.Column("formative_feedback",  sa.Text,          nullable=False),
        sa.Column("raw_response",        postgresql.JSONB,  nullable=False),
        sa.Column("model_used",          sa.String,         nullable=False),
        sa.Column("tokens_input",        sa.Integer,        nullable=True),
        sa.Column("tokens_output",       sa.Integer,        nullable=True),
        sa.Column("retrieved_chunk_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column("graded_at",           sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("retry_count",         sa.SmallInteger,   nullable=False, server_default=sa.text("0")),
        sa.Column("error_message",       sa.Text,           nullable=True),
    )
    op.create_index("idx_ai_grading_results_submission", "ai_grading_results", ["submission_id"])

    # ai_criterion_scores
    op.create_table(
        "ai_criterion_scores",
        sa.Column("id",                  postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("grading_result_id",   postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_grading_results.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rubric_criterion_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rubric_criteria.id",    ondelete="CASCADE"), nullable=False),
        sa.Column("ai_score",            sa.Numeric(5, 2), nullable=False),
        sa.Column("ai_justification",    sa.Text,          nullable=False),
        sa.UniqueConstraint("grading_result_id", "rubric_criterion_id", name="uq_ai_criterion_score"),
    )
    op.create_index("idx_ai_criterion_scores_result", "ai_criterion_scores", ["grading_result_id"])

    # grade_overrides
    op.create_table(
        "grade_overrides",
        sa.Column("id",                  postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("submission_id",       postgresql.UUID(as_uuid=True), sa.ForeignKey("submissions.id",     ondelete="CASCADE"),  nullable=False),
        sa.Column("rubric_criterion_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rubric_criteria.id", ondelete="CASCADE"),  nullable=False),
        sa.Column("teacher_id",          postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id",           ondelete="RESTRICT"), nullable=False),
        sa.Column("overridden_score",    sa.Numeric(5, 2), nullable=False),
        sa.Column("override_note",       sa.Text,          nullable=True),
        sa.Column("created_at",          sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at",          sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("submission_id", "rubric_criterion_id", name="uq_grade_override"),
    )
    op.create_index("idx_grade_overrides_submission", "grade_overrides", ["submission_id"])

    # finalised_grades
    op.create_table(
        "finalised_grades",
        sa.Column("id",              postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("submission_id",   postgresql.UUID(as_uuid=True), sa.ForeignKey("submissions.id", ondelete="CASCADE"),  nullable=False, unique=True),
        sa.Column("teacher_id",      postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id",       ondelete="RESTRICT"), nullable=False),
        sa.Column("total_score",     sa.Numeric(5, 2), nullable=False),
        sa.Column("teacher_comment", sa.Text,          nullable=True),
        sa.Column("is_published",    sa.Boolean,       nullable=False, server_default=sa.text("false")),
        sa.Column("finalised_at",    sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at",      sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_finalised_grades_submission", "finalised_grades", ["submission_id"])
    op.create_index("idx_finalised_grades_published",  "finalised_grades", ["is_published"])

    # knowledge_chunks
    op.create_table(
        "knowledge_chunks",
        sa.Column("id",           postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_title", sa.String,  nullable=False),
        sa.Column("source_label", sa.String,  nullable=False),
        sa.Column("content",      sa.Text,    nullable=False),
        sa.Column("embedding",    postgresql.ARRAY(sa.Float), nullable=True),
        sa.Column("subject_tag",  sa.String,  nullable=False),
        sa.Column("chunk_index",  sa.Integer, nullable=False),
        sa.Column("is_example",   sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at",   sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_knowledge_chunks_subject", "knowledge_chunks", ["subject_tag"])


def downgrade() -> None:
    op.drop_table("knowledge_chunks")
    op.drop_table("finalised_grades")
    op.drop_table("grade_overrides")
    op.drop_table("ai_criterion_scores")
    op.drop_table("ai_grading_results")
    op.drop_table("submissions")
    op.drop_table("rubric_criteria")
    op.drop_table("assignments")
    op.drop_table("announcements")
    op.drop_table("enrolments")
    op.drop_table("class_subjects")
    op.drop_table("classes")
    op.drop_table("subjects")
    op.drop_table("users")
    op.drop_table("schools")
    op.execute("DROP TYPE IF EXISTS sub_status")
    op.execute("DROP TYPE IF EXISTS sub_type")
    op.execute("DROP TYPE IF EXISTS user_role")
    op.execute("DROP TYPE IF EXISTS school_type")

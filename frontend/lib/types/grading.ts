export type SubmissionType = "text" | "pdf" | "image";
export type SubmissionStatus =
  | "pending_grading"
  | "grading_in_progress"
  | "graded"
  | "grading_failed"
  | "finalised";

export interface RubricCriterion {
  id: string;
  assignment_id: string;
  name: string;
  description: string;
  max_marks: number;
  display_order: number;
}

export interface Assignment {
  id: string;
  class_subject_id: string;
  title: string;
  question_text: string;
  instructions: string | null;
  allowed_submission_types: SubmissionType[];
  max_marks: number;
  due_date: string;
  is_published: boolean;
  created_at: string;
  rubric?: RubricCriterion[];
  subject_name?: string;
  class_name?: string;
}

export interface Submission {
  id: string;
  assignment_id: string;
  student_id: string;
  submission_type: SubmissionType;
  status: SubmissionStatus;
  file_name: string | null;
  submitted_at: string;
}

export interface CriterionScoreOut {
  rubric_criterion_id: string;
  criterion_name: string;
  max_marks: number;
  ai_score: number;
  ai_justification: string;
  override: { overridden_score: number; override_note: string | null } | null;
}

export interface GradingResult {
  submission_id: string;
  status: SubmissionStatus;
  model_used: string;
  graded_at: string;
  total_ai_score: number;
  formative_feedback: string;
  transcribed_text: string | null;
  criteria: CriterionScoreOut[];
  retrieved_sources: string[];
}

export interface FinalisedGrade {
  id: string;
  submission_id: string;
  total_score: number;
  teacher_comment: string | null;
  is_published: boolean;
  finalised_at: string;
}

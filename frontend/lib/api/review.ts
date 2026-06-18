import { api } from "./client";

export interface CriterionReview {
  criterion_id:     string;
  name:             string;
  description:      string;
  max_marks:        number;
  display_order:    number;
  ai_score:         number | null;
  ai_justification: string | null;
  override_score:   number | null;
  override_note:    string | null;
  effective_score:  number;
}

export interface FinalisedGradeOut {
  id:              string;
  submission_id:   string;
  teacher_id:      string;
  total_score:     number;
  teacher_comment: string | null;
  is_published:    boolean;
  finalised_at:    string;
}

export interface SubmissionReview {
  id:              string;
  assignment_id:   string;
  student_id:      string;
  student_name:    string | null;
  submission_type: string;
  status:          string;
  text_content:    string | null;
  file_name:       string | null;
  submitted_at:    string;
  assignment_title: string;
  question_text:    string;
  max_marks:        number;
  total_ai_score:     number | null;
  formative_feedback: string | null;
  criteria:           CriterionReview[];
  effective_total:    number;
  finalised_grade:    FinalisedGradeOut | null;
}

export const reviewApi = {
  get: (submissionId: string): Promise<SubmissionReview> =>
    api.get(`/submissions/${submissionId}/review`),

  setOverride: (
    submissionId:      string,
    rubricCriterionId: string,
    score:             number,
    note?:             string,
  ): Promise<SubmissionReview> =>
    api.post(`/submissions/${submissionId}/overrides`, {
      rubric_criterion_id: rubricCriterionId,
      overridden_score:    score,
      override_note:       note ?? null,
    }),

  removeOverride: (submissionId: string, criterionId: string): Promise<SubmissionReview> =>
    api.delete(`/submissions/${submissionId}/overrides/${criterionId}`),

  finalise: (submissionId: string, teacherComment?: string): Promise<SubmissionReview> =>
    api.post(`/submissions/${submissionId}/finalise`, { teacher_comment: teacherComment ?? null }),

  publishGrade: (submissionId: string): Promise<SubmissionReview> =>
    api.post(`/submissions/${submissionId}/publish-grade`),
};

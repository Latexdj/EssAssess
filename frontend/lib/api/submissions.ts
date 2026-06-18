import { api } from "./client";

export interface Submission {
  id:                 string;
  assignment_id:      string;
  student_id:         string;
  submission_type:    "text" | "pdf" | "image";
  status:             "pending_grading" | "grading_in_progress" | "graded" | "grading_failed" | "finalised";
  text_content:       string | null;
  file_name:          string | null;
  file_size_bytes:    number | null;
  submitted_at:       string;
  updated_at:         string;
  student_name:       string | null;
  total_ai_score:     number | null;
  formative_feedback: string | null;
  error_message:      string | null;
}

export const submissionsApi = {
  submitText: (assignmentId: string, textContent: string): Promise<Submission> =>
    api.post("/submissions", { assignment_id: assignmentId, text_content: textContent }),

  submitFile: (assignmentId: string, file: File): Promise<Submission> => {
    const form = new FormData();
    form.append("assignment_id", assignmentId);
    form.append("file", file);
    return api.upload("/submissions/file", form);
  },

  get: (id: string): Promise<Submission> =>
    api.get(`/submissions/${id}`),

  list: (params?: { assignment_id?: string }): Promise<Submission[]> => {
    const qs = params?.assignment_id ? `?assignment_id=${params.assignment_id}` : "";
    return api.get(`/submissions${qs}`);
  },
};

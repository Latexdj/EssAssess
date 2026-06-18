import { api } from "./client";

export interface RubricCriterion {
  id:            string;
  assignment_id: string;
  name:          string;
  description:   string;
  max_marks:     number;
  display_order: number;
}

export interface Assignment {
  id:                       string;
  class_subject_id:         string;
  title:                    string;
  question_text:            string;
  instructions:             string | null;
  allowed_submission_types: string[];
  max_marks:                number;
  due_date:                 string;
  is_published:             boolean;
  created_at:               string;
  rubric_criteria:          RubricCriterion[];
  subject_name:             string | null;
  subject_code:             string | null;
  class_name:               string | null;
  teacher_name:             string | null;
  submission_count:         number;
}

export const assignmentsApi = {
  list: (params?: { class_id?: string; class_subject_id?: string }): Promise<Assignment[]> => {
    const qs = new URLSearchParams();
    if (params?.class_id)         qs.set("class_id",         params.class_id);
    if (params?.class_subject_id) qs.set("class_subject_id", params.class_subject_id);
    const q = qs.toString();
    return api.get(`/assignments${q ? `?${q}` : ""}`);
  },

  get: (id: string): Promise<Assignment> => api.get(`/assignments/${id}`),

  create: (data: {
    class_subject_id:         string;
    title:                    string;
    question_text:            string;
    instructions?:            string;
    allowed_submission_types: string[];
    max_marks:                number;
    due_date:                 string;
  }): Promise<Assignment> => api.post("/assignments", data),

  update: (id: string, data: Partial<{
    title:                    string;
    question_text:            string;
    instructions:             string;
    allowed_submission_types: string[];
    max_marks:                number;
    due_date:                 string;
  }>): Promise<Assignment> => api.patch(`/assignments/${id}`, data),

  publish: (id: string): Promise<Assignment> =>
    api.post(`/assignments/${id}/publish`),

  delete: (id: string): Promise<void> =>
    api.delete(`/assignments/${id}`),

  addCriterion: (assignmentId: string, data: {
    name:        string;
    description: string;
    max_marks:   number;
  }): Promise<RubricCriterion> =>
    api.post(`/assignments/${assignmentId}/criteria`, data),

  updateCriterion: (assignmentId: string, criterionId: string, data: {
    name?:        string;
    description?: string;
    max_marks?:   number;
  }): Promise<RubricCriterion> =>
    api.patch(`/assignments/${assignmentId}/criteria/${criterionId}`, data),

  deleteCriterion: (assignmentId: string, criterionId: string): Promise<void> =>
    api.delete(`/assignments/${assignmentId}/criteria/${criterionId}`),

  moveCriterion: (assignmentId: string, criterionId: string, direction: "up" | "down"): Promise<void> =>
    api.post(`/assignments/${assignmentId}/criteria/${criterionId}/move?direction=${direction}`),
};

import { api } from "./client";

export interface StudentGrade {
  submission_id:      string;
  assignment_id:      string;
  assignment_title:   string;
  class_name:         string;
  subject_name:       string;
  subject_code:       string;
  max_marks:          number;
  due_date:           string;
  submitted_at:       string;
  status:             string;
  ai_score:           number | null;
  formative_feedback: string | null;
  final_score:        number | null;
  teacher_comment:    string | null;
  is_published:       boolean;
}

export interface AssignmentStats {
  assignment_id:   string;
  title:           string;
  subject_name:    string;
  subject_code:    string;
  max_marks:       number;
  due_date:        string;
  is_published:    boolean;
  enrolled_count:  number;
  submitted_count: number;
  graded_count:    number;
  finalised_count: number;
  published_count: number;
  avg_ai_score:    number | null;
  avg_final_score: number | null;
}

export interface ClassGradebook {
  class_id:       string;
  class_name:     string;
  enrolled_count: number;
  assignments:    AssignmentStats[];
}

export const gradebookApi = {
  getStudentGrades: (): Promise<StudentGrade[]> =>
    api.get("/gradebook/student"),

  getClassGradebook: (classId: string): Promise<ClassGradebook> =>
    api.get(`/gradebook/class/${classId}`),
};

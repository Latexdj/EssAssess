export interface Class {
  id: string;
  school_id: string;
  name: string;
  programme: string | null;
  year_group: number | null;
  academic_year: string | null;
}

export interface ClassSubject {
  id: string;
  class_id: string;
  subject_id: string;
  teacher_id: string;
  subject_name: string;
  subject_code: string;
  teacher_name: string;
}

export interface Enrolment {
  id: string;
  student_id: string;
  class_id: string;
  enrolled_at: string;
  is_active: boolean;
  student_name: string;
  email: string;
}

export interface Subject {
  id: string;
  name: string;
  code: string;
  ges_curriculum_area: string | null;
}

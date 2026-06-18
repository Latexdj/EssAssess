import { api } from "./client";
import type { Class, ClassSubject, Enrolment, Subject } from "@/lib/types/classes";

export interface ClassListItem extends Class {
  student_count: number;
}

export interface BulkEnrolResponse {
  enrolled: string[];
  already_enrolled: string[];
  not_found: string[];
}

export const subjectsApi = {
  list: (): Promise<Subject[]> => api.get("/subjects"),
  create: (data: { name: string; code: string; ges_curriculum_area?: string }) =>
    api.post("/subjects", data),
};

export const classesApi = {
  list: (): Promise<ClassListItem[]> => api.get("/classes"),

  get: (classId: string): Promise<Class> => api.get(`/classes/${classId}`),

  create: (data: {
    name: string;
    programme?: string;
    year_group?: number;
    academic_year?: string;
  }): Promise<Class> => api.post("/classes", data),

  update: (classId: string, data: Partial<{ name: string; programme: string; year_group: number; academic_year: string }>): Promise<Class> =>
    api.patch(`/classes/${classId}`, data),

  listSubjects: (classId: string): Promise<ClassSubject[]> =>
    api.get(`/classes/${classId}/subjects`),

  assignSubject: (classId: string, subjectId: string, teacherId: string): Promise<ClassSubject> =>
    api.post(`/classes/${classId}/subjects`, { subject_id: subjectId, teacher_id: teacherId }),

  removeSubject: (classId: string, csId: string): Promise<void> =>
    api.delete(`/classes/${classId}/subjects/${csId}`),

  listEnrolments: (classId: string): Promise<Enrolment[]> =>
    api.get(`/classes/${classId}/enrolments`),

  bulkEnrol: (classId: string, studentIds: string[]): Promise<BulkEnrolResponse> =>
    api.post(`/classes/${classId}/enrolments`, { student_ids: studentIds }),

  removeEnrolment: (classId: string, studentId: string): Promise<void> =>
    api.delete(`/classes/${classId}/enrolments/${studentId}`),
};

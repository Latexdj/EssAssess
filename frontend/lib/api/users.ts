import { api } from "./client";
import type { User, UserRole } from "@/lib/types/auth";

export interface UserListOut {
  users: User[];
  total: number;
}

export interface CreateUserPayload {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  role: UserRole;
}

export const usersApi = {
  list: (params?: { role?: UserRole; is_active?: boolean; limit?: number; offset?: number }) => {
    const qs = new URLSearchParams();
    if (params?.role)      qs.set("role", params.role);
    if (params?.is_active !== undefined) qs.set("is_active", String(params.is_active));
    if (params?.limit)     qs.set("limit", String(params.limit));
    if (params?.offset)    qs.set("offset", String(params.offset));
    const q = qs.toString();
    return api.get<UserListOut>(`/users${q ? `?${q}` : ""}`);
  },

  get: (userId: string): Promise<User> => api.get(`/users/${userId}`),

  create: (data: CreateUserPayload): Promise<User> => api.post("/users", data),

  update: (userId: string, data: Partial<{ first_name: string; last_name: string; is_active: boolean }>): Promise<User> =>
    api.patch(`/users/${userId}`, data),

  deactivate: (userId: string): Promise<User> =>
    api.delete(`/users/${userId}`),
};

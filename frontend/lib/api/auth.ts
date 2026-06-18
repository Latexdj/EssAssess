import { api } from "./client";
import type { User } from "@/lib/types/auth";

export const authApi = {
  login: (email: string, password: string) =>
    api.post<{ user: User }>("/auth/login", { email, password }),

  refresh: () => api.post<{ user: User }>("/auth/refresh"),

  logout: () => api.post<void>("/auth/logout"),

  me: () => api.get<{ user: User }>("/auth/me"),
};

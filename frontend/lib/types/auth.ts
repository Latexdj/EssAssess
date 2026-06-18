export type UserRole = "admin" | "teacher" | "student";

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  school_id: string;
  is_active: boolean;
}

export interface AuthState {
  user: User | null;
  isLoading: boolean;
}

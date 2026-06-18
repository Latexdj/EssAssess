"use client";
import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { authApi } from "@/lib/api/auth";
import type { UserRole } from "@/lib/types/auth";

const ROLE_HOME: Record<UserRole, string> = {
  admin:   "/admin",
  teacher: "/teacher",
  student: "/student",
};

export function LoginForm() {
  const router = useRouter();
  const [email,    setEmail]    = useState("");
  const [password, setPassword] = useState("");
  const [error,    setError]    = useState("");
  const [loading,  setLoading]  = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { user } = await authApi.login(email, password);
      router.push(ROLE_HOME[user.role] ?? "/");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Login failed. Please try again.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-sm rounded-2xl bg-white p-8 shadow-lg">
      <div className="mb-6 text-center">
        <h1 className="text-2xl font-bold text-gray-900">EssAssess</h1>
        <p className="mt-1 text-sm text-gray-500">AI-Powered Essay Grading</p>
      </div>

      {error && (
        <div className="mb-4">
          <Alert variant="error">{error}</Alert>
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Input
          label="Email address"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
          required
        />
        <Input
          label="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          required
        />
        <Button type="submit" loading={loading} className="mt-2 w-full">
          Sign in
        </Button>
      </form>
    </div>
  );
}

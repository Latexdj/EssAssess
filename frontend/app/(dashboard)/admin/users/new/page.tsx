"use client";
import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import Alert from "@/components/ui/Alert";
import { usersApi } from "@/lib/api/users";
import type { UserRole } from "@/lib/types/auth";

const ROLES: { value: UserRole; label: string }[] = [
  { value: "teacher", label: "Teacher" },
  { value: "student", label: "Student" },
  { value: "admin",   label: "Admin" },
];

export default function NewUserPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    first_name: "",
    last_name:  "",
    email:      "",
    password:   "",
    role:       "teacher" as UserRole,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((p) => ({ ...p, [k]: e.target.value }));

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await usersApi.create(form);
      router.push("/admin/users");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create user");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Add User</h1>

      {error && <Alert variant="error" message={error} className="mb-4" />}

      <form onSubmit={handleSubmit} className="space-y-4 bg-white rounded-lg border border-gray-200 p-6">
        <div className="grid grid-cols-2 gap-4">
          <Input label="First name" value={form.first_name} onChange={set("first_name")} required />
          <Input label="Last name"  value={form.last_name}  onChange={set("last_name")}  required />
        </div>
        <Input label="Email" type="email" value={form.email} onChange={set("email")} required />
        <Input label="Password" type="password" value={form.password} onChange={set("password")} required />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
          <select
            value={form.role}
            onChange={set("role")}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
          >
            {ROLES.map((r) => (
              <option key={r.value} value={r.value}>{r.label}</option>
            ))}
          </select>
        </div>

        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={loading}>Create User</Button>
          <Button type="button" variant="secondary" onClick={() => router.back()}>Cancel</Button>
        </div>
      </form>
    </div>
  );
}

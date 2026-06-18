"use client";
import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { usersApi } from "@/lib/api/users";
import type { User, UserRole } from "@/lib/types/auth";
import Button from "@/components/ui/Button";
import Alert from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";

const ROLES: { value: UserRole | ""; label: string }[] = [
  { value: "",          label: "All roles" },
  { value: "teacher",   label: "Teachers" },
  { value: "student",   label: "Students" },
  { value: "admin",     label: "Admins" },
];

export default function UsersPage() {
  const [users, setUsers]         = useState<User[]>([]);
  const [total, setTotal]         = useState(0);
  const [role, setRole]           = useState<UserRole | "">("");
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState<string | null>(null);
  const [deactivating, setDeact]  = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await usersApi.list({ role: role || undefined });
      setUsers(res.users);
      setTotal(res.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load users");
    } finally {
      setLoading(false);
    }
  }, [role]);

  useEffect(() => { load(); }, [load]);

  const handleDeactivate = async (userId: string) => {
    setDeact(userId);
    try {
      await usersApi.deactivate(userId);
      await load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to deactivate user");
    } finally {
      setDeact(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Users ({total})</h1>
        <Link href="/admin/users/new">
          <Button>Add User</Button>
        </Link>
      </div>

      <div className="flex gap-2">
        {ROLES.map((r) => (
          <button
            key={r.value}
            onClick={() => setRole(r.value)}
            className={`rounded-full px-3 py-1 text-sm border transition-colors ${
              role === r.value
                ? "border-blue-500 bg-blue-50 text-blue-700"
                : "border-gray-300 text-gray-600 hover:border-gray-400"
            }`}
          >
            {r.label}
          </button>
        ))}
      </div>

      {error && <Alert variant="error" message={error} />}

      {loading ? (
        <div className="flex justify-center py-8"><Spinner /></div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-gray-600">
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 font-medium">Email</th>
                <th className="px-4 py-3 font-medium">Role</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Action</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-900">{u.first_name} {u.last_name}</td>
                  <td className="px-4 py-3 text-gray-600">{u.email}</td>
                  <td className="px-4 py-3"><Badge variant={u.role}>{u.role}</Badge></td>
                  <td className="px-4 py-3">
                    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                      u.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"
                    }`}>
                      {u.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {u.is_active && (
                      <Button
                        variant="destructive"
                        onClick={() => handleDeactivate(u.id)}
                        loading={deactivating === u.id}
                        className="text-xs py-1 px-2 min-h-0"
                      >
                        Deactivate
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr><td colSpan={5} className="px-4 py-6 text-center text-gray-500">No users found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

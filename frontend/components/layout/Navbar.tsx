"use client";
import { useRouter } from "next/navigation";
import { authApi } from "@/lib/api/auth";
import type { User } from "@/lib/types/auth";

const ROLE_COLOURS: Record<string, string> = {
  admin:   "bg-purple-100 text-purple-800",
  teacher: "bg-blue-100 text-blue-800",
  student: "bg-green-100 text-green-800",
};

export function Navbar({ user }: { user: User }) {
  const router = useRouter();

  const handleLogout = async () => {
    await authApi.logout().catch(() => {});
    router.push("/login");
  };

  return (
    <header className="flex h-14 items-center justify-between border-b border-gray-200 bg-white px-4">
      <div />
      <div className="flex items-center gap-3">
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-semibold ${ROLE_COLOURS[user.role] ?? ""}`}
        >
          {user.role}
        </span>
        <span className="text-sm font-medium text-gray-700">
          {user.first_name} {user.last_name}
        </span>
        <button
          onClick={handleLogout}
          className="rounded-lg px-3 py-2 text-sm text-gray-500 hover:bg-gray-100 hover:text-gray-700 min-h-[44px]"
        >
          Log out
        </button>
      </div>
    </header>
  );
}

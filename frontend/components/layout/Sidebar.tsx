"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { UserRole } from "@/lib/types/auth";

interface NavItem {
  label: string;
  href: string;
}

const NAV: Record<UserRole, NavItem[]> = {
  admin: [
    { label: "Dashboard",      href: "/admin" },
    { label: "Users",          href: "/admin/users" },
    { label: "Classes",        href: "/admin/classes" },
    { label: "Knowledge Base", href: "/admin/knowledge" },
  ],
  teacher: [
    { label: "Dashboard",    href: "/teacher" },
    { label: "My Classes",   href: "/teacher/classes" },
    { label: "Assignments",  href: "/teacher/assignments" },
    { label: "Gradebook",    href: "/teacher/gradebook" },
  ],
  student: [
    { label: "Dashboard",      href: "/student" },
    { label: "My Assignments", href: "/student/assignments" },
    { label: "My Grades",      href: "/student/grades" },
  ],
};

export function Sidebar({ role }: { role: UserRole }) {
  const pathname = usePathname();
  const items = NAV[role] ?? [];

  return (
    <aside className="flex w-56 shrink-0 flex-col border-r border-gray-200 bg-white px-3 py-6 lg:w-64">
      <div className="mb-6 px-3">
        <span className="text-lg font-bold text-blue-700">EssAssess</span>
      </div>
      <nav className="flex flex-1 flex-col gap-1">
        {items.map((item) => {
          // Exact match for dashboard root links, prefix match for sub-pages
          const isDashboardRoot = ["/admin", "/teacher", "/student"].includes(item.href);
          const active = isDashboardRoot
            ? pathname === item.href
            : pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-lg px-3 py-3 text-sm font-medium transition-colors min-h-[44px] flex items-center ${
                active
                  ? "bg-blue-50 text-blue-700"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

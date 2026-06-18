import Link from "next/link";
import { cookies } from "next/headers";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function fetchData(path: string, cookieHeader: string) {
  try {
    const res = await fetch(`${API}${path}`, {
      headers: { Cookie: cookieHeader },
      cache: "no-store",
    });
    return res.ok ? res.json() : null;
  } catch {
    return null;
  }
}

export default async function AdminDashboard() {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();

  const [classes, teachers, students] = await Promise.all([
    fetchData("/classes", cookieHeader),
    fetchData("/users?role=teacher", cookieHeader),
    fetchData("/users?role=student", cookieHeader),
  ]);

  const classCount   = Array.isArray(classes) ? classes.length : 0;
  const teacherCount = teachers?.total ?? 0;
  const studentCount = students?.total ?? 0;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label="Classes"  value={classCount}   href="/admin/classes" />
        <StatCard label="Teachers" value={teacherCount} href="/admin/users?role=teacher" />
        <StatCard label="Students" value={studentCount} href="/admin/users?role=student" />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <QuickLink href="/admin/classes/new" label="Create Class" />
        <QuickLink href="/admin/users/new"   label="Add User" />
      </div>
    </div>
  );
}

function StatCard({ label, value, href }: { label: string; value: number; href: string }) {
  return (
    <Link
      href={href}
      className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm hover:border-blue-400 transition-colors"
    >
      <p className="text-3xl font-bold text-blue-600">{value}</p>
      <p className="text-sm text-gray-600 mt-1">{label}</p>
    </Link>
  );
}

function QuickLink({ href, label }: { href: string; label: string }) {
  return (
    <Link
      href={href}
      className="rounded-lg border border-dashed border-gray-300 bg-white p-4 text-center text-sm font-medium text-gray-600 hover:border-blue-400 hover:text-blue-600 transition-colors"
    >
      + {label}
    </Link>
  );
}

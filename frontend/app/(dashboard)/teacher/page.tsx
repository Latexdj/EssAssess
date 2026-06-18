import Link from "next/link";
import { cookies } from "next/headers";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export default async function TeacherDashboard() {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();

  let classCount = 0;
  try {
    const res = await fetch(`${API}/classes`, {
      headers: { Cookie: cookieHeader },
      cache: "no-store",
    });
    if (res.ok) {
      const data = await res.json();
      classCount = Array.isArray(data) ? data.length : 0;
    }
  } catch { /* offline — show 0 */ }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Teacher Dashboard</h1>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Link
          href="/teacher/classes"
          className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm hover:border-blue-400 transition-colors"
        >
          <p className="text-3xl font-bold text-blue-600">{classCount}</p>
          <p className="text-sm text-gray-600 mt-1">My Classes</p>
        </Link>

        <Link
          href="/teacher/assignments"
          className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm hover:border-blue-400 transition-colors"
        >
          <p className="text-3xl font-bold text-gray-400">—</p>
          <p className="text-sm text-gray-600 mt-1">Assignments</p>
        </Link>

        <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <p className="text-3xl font-bold text-gray-400">—</p>
          <p className="text-sm text-gray-600 mt-1">Pending Reviews</p>
        </div>
      </div>
    </div>
  );
}

"use client";
import { useState, useEffect } from "react";
import { assignmentsApi, type Assignment } from "@/lib/api/assignments";
import AssignmentCard from "@/components/lms/AssignmentCard";
import Alert from "@/components/ui/Alert";
import { SkeletonCard } from "@/components/ui/Skeleton";

export default function StudentAssignmentsPage() {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState<string | null>(null);

  useEffect(() => {
    assignmentsApi.list()
      .then(setAssignments)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const overdue  = assignments.filter((a) => new Date(a.due_date) < new Date());
  const upcoming = assignments.filter((a) => new Date(a.due_date) >= new Date());

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">My Assignments</h1>

      {error && <Alert variant="error" message={error} />}
      {loading && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      )}

      {!loading && assignments.length === 0 && (
        <p className="text-sm text-gray-500">
          No assignments yet. Your teacher will publish assignments when they are ready.
        </p>
      )}

      {upcoming.length > 0 && (
        <section>
          <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500 mb-3">Open</h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {upcoming.map((a) => (
              <AssignmentCard key={a.id} assignment={a} href={`/student/assignments/${a.id}`} showClass />
            ))}
          </div>
        </section>
      )}

      {overdue.length > 0 && (
        <section>
          <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500 mb-3">Past Due</h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {overdue.map((a) => (
              <AssignmentCard key={a.id} assignment={a} href={`/student/assignments/${a.id}`} showClass />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

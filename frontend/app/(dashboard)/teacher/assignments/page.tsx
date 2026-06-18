"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { assignmentsApi, type Assignment } from "@/lib/api/assignments";
import AssignmentCard from "@/components/lms/AssignmentCard";
import Button from "@/components/ui/Button";
import Alert from "@/components/ui/Alert";
import { SkeletonCard } from "@/components/ui/Skeleton";

export default function TeacherAssignmentsPage() {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState<string | null>(null);

  useEffect(() => {
    assignmentsApi.list()
      .then(setAssignments)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const drafts     = assignments.filter((a) => !a.is_published);
  const published  = assignments.filter((a) =>  a.is_published);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">My Assignments</h1>
        <Link href="/teacher/assignments/new"><Button>New Assignment</Button></Link>
      </div>

      {error && <Alert variant="error" message={error} />}
      {loading && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      )}

      {!loading && assignments.length === 0 && (
        <p className="text-sm text-gray-500">No assignments yet. Create one to get started.</p>
      )}

      {drafts.length > 0 && (
        <section>
          <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500 mb-3">Drafts</h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {drafts.map((a) => (
              <AssignmentCard key={a.id} assignment={a} href={`/teacher/assignments/${a.id}`} showClass />
            ))}
          </div>
        </section>
      )}

      {published.length > 0 && (
        <section>
          <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500 mb-3">Published</h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {published.map((a) => (
              <AssignmentCard key={a.id} assignment={a} href={`/teacher/assignments/${a.id}`} showClass />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

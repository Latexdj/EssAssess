"use client";
import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { assignmentsApi, type Assignment } from "@/lib/api/assignments";
import { submissionsApi, type Submission } from "@/lib/api/submissions";
import { formatDateTime } from "@/lib/utils/formatters";
import RubricBuilder from "@/components/lms/RubricBuilder";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import Spinner from "@/components/ui/Spinner";
import { useToast } from "@/lib/context/ToastContext";

const STATUS_LABELS: Record<Submission["status"], { label: string; cls: string }> = {
  pending_grading:     { label: "Queued",          cls: "bg-gray-100 text-gray-600" },
  grading_in_progress: { label: "Grading",         cls: "bg-blue-100 text-blue-700" },
  graded:              { label: "Graded",           cls: "bg-green-100 text-green-700" },
  grading_failed:      { label: "Failed",           cls: "bg-red-100 text-red-700" },
  finalised:           { label: "Finalised",       cls: "bg-indigo-100 text-indigo-700" },
};

export default function TeacherAssignmentDetailPage() {
  const { assignmentId } = useParams<{ assignmentId: string }>();
  const router = useRouter();
  const { toast } = useToast();

  const [assignment, setAssignment] = useState<Assignment | null>(null);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState<string | null>(null);
  const [publishing, setPublishing] = useState(false);
  const [deleting, setDeleting]     = useState(false);
  const [pubError, setPubError]     = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [a, subs] = await Promise.all([
        assignmentsApi.get(assignmentId),
        submissionsApi.list({ assignment_id: assignmentId }),
      ]);
      setAssignment(a);
      setSubmissions(subs);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load assignment");
    } finally {
      setLoading(false);
    }
  }, [assignmentId]);

  useEffect(() => { load(); }, [load]);

  const handlePublish = async () => {
    setPublishing(true);
    setPubError(null);
    try {
      setAssignment(await assignmentsApi.publish(assignmentId));
      toast("Assignment published — students can now submit", "success");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to publish";
      setPubError(msg);
      toast(msg, "error");
    } finally {
      setPublishing(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Delete this assignment? This cannot be undone.")) return;
    setDeleting(true);
    try {
      await assignmentsApi.delete(assignmentId);
      router.push("/teacher/assignments");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to delete");
      setDeleting(false);
    }
  };

  if (loading) return <div className="flex justify-center py-12"><Spinner /></div>;
  if (error)   return <Alert variant="error" message={error} />;
  if (!assignment) return null;

  const a = assignment;

  return (
    <div className="space-y-8 max-w-3xl">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">{a.title}</h1>
            {a.is_published ? (
              <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700">Published</span>
            ) : (
              <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">Draft</span>
            )}
          </div>
          <p className="text-sm text-gray-500 mt-1">
            {a.class_name} · {a.subject_name} · Due {formatDateTime(a.due_date)} · {a.max_marks} marks
          </p>
        </div>
        <div className="flex gap-2 shrink-0">
          {!a.is_published && (
            <>
              <Button onClick={handlePublish} loading={publishing}>
                Publish
              </Button>
              <Button variant="destructive" onClick={handleDelete} loading={deleting}>
                Delete
              </Button>
            </>
          )}
        </div>
      </div>

      {pubError && <Alert variant="error" message={pubError} />}

      {/* Question */}
      <section className="rounded-lg border border-gray-200 bg-white p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500 mb-2">Essay Question</h2>
        <p className="text-gray-900 leading-relaxed">{a.question_text}</p>
        {a.instructions && (
          <p className="mt-3 text-sm text-gray-600 border-t border-gray-100 pt-3">{a.instructions}</p>
        )}
      </section>

      {/* Rubric */}
      <section className="rounded-lg border border-gray-200 bg-white p-5">
        <RubricBuilder
          assignmentId={assignmentId}
          criteria={a.rubric_criteria}
          readOnly={a.is_published}
          onRefresh={load}
        />
      </section>

      {/* Submission types */}
      <section className="rounded-lg border border-gray-200 bg-white p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500 mb-2">Allowed Submission Types</h2>
        <div className="flex gap-2 flex-wrap">
          {a.allowed_submission_types.map((t) => (
            <span key={t} className="rounded-full bg-blue-50 border border-blue-200 px-3 py-1 text-sm text-blue-700">
              {t}
            </span>
          ))}
        </div>
      </section>

      {/* Submissions */}
      <section className="rounded-lg border border-gray-200 bg-white p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500 mb-3">
          Submissions ({submissions.length})
        </h2>
        {submissions.length === 0 ? (
          <p className="text-sm text-gray-500">No submissions yet.</p>
        ) : (
          <div className="divide-y divide-gray-100">
            {submissions.map((s) => {
              const { label, cls } = STATUS_LABELS[s.status];
              return (
                <div key={s.id} className="py-3 flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{s.student_name ?? "Student"}</p>
                    <p className="text-xs text-gray-500">{s.submission_type} · {formatDateTime(s.submitted_at)}</p>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    {s.total_ai_score != null && (
                      <span className="text-sm font-semibold text-gray-700">
                        {s.total_ai_score}/{a.max_marks}
                      </span>
                    )}
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>{label}</span>
                    {(s.status === "graded" || s.status === "finalised") && (
                      <Link
                        href={`/teacher/review/${s.id}`}
                        className="text-xs font-medium text-blue-600 hover:underline min-h-[44px] flex items-center"
                      >
                        Review
                      </Link>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}

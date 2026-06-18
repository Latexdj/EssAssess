"use client";
import { useState, useEffect, useCallback, FormEvent } from "react";
import { useParams, useRouter } from "next/navigation";
import { reviewApi, type SubmissionReview } from "@/lib/api/review";
import { formatDateTime } from "@/lib/utils/formatters";
import CriterionReviewRow from "@/components/review/CriterionReviewRow";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import Spinner from "@/components/ui/Spinner";
import { useToast } from "@/lib/context/ToastContext";

export default function TeacherReviewPage() {
  const { submissionId } = useParams<{ submissionId: string }>();
  const router = useRouter();

  const { toast } = useToast();
  const [review, setReview]         = useState<SubmissionReview | null>(null);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState<string | null>(null);
  const [comment, setComment]       = useState("");
  const [finalising, setFinalising] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const r = await reviewApi.get(submissionId);
      setReview(r);
      if (r.finalised_grade?.teacher_comment) {
        setComment(r.finalised_grade.teacher_comment);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load review");
    } finally {
      setLoading(false);
    }
  }, [submissionId]);

  useEffect(() => { load(); }, [load]);

  const handleFinalise = async (e: FormEvent) => {
    e.preventDefault();
    setFinalising(true);
    setActionError(null);
    try {
      setReview(await reviewApi.finalise(submissionId, comment || undefined));
      toast("Grade finalised", "success");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to finalise";
      setActionError(msg);
      toast(msg, "error");
    } finally {
      setFinalising(false);
    }
  };

  const handlePublish = async () => {
    setPublishing(true);
    setActionError(null);
    try {
      setReview(await reviewApi.publishGrade(submissionId));
      toast("Grade published to student", "success");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to publish";
      setActionError(msg);
      toast(msg, "error");
    } finally {
      setPublishing(false);
    }
  };

  if (loading) return <div className="flex justify-center py-12"><Spinner /></div>;
  if (error)   return <Alert variant="error" message={error} />;
  if (!review) return null;

  const r            = review;
  const isFinalised  = r.status === "finalised";
  const isPublished  = r.finalised_grade?.is_published ?? false;
  const totalMarks   = r.max_marks;

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Back */}
      <button
        onClick={() => router.push(`/teacher/assignments/${r.assignment_id}`)}
        className="text-sm text-blue-600 hover:underline min-h-[44px] flex items-center"
      >
        ← Back to assignment
      </button>

      {/* Header */}
      <div className="rounded-lg border border-gray-200 bg-white p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">{r.assignment_title}</p>
            <h1 className="text-xl font-bold text-gray-900 mt-1">
              {r.student_name ?? "Student"}'s submission
            </h1>
            <p className="text-sm text-gray-500 mt-0.5">
              {r.submission_type} · Submitted {formatDateTime(r.submitted_at)}
            </p>
          </div>
          <div className="shrink-0 text-right">
            {isFinalised ? (
              <div>
                <p className="text-3xl font-bold text-gray-900">
                  {r.finalised_grade?.total_score}
                </p>
                <p className="text-sm text-gray-500">/ {totalMarks}</p>
                {isPublished ? (
                  <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-700">Published</span>
                ) : (
                  <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-700">Not published</span>
                )}
              </div>
            ) : (
              <div>
                <p className="text-2xl font-bold text-gray-700">{r.effective_total}</p>
                <p className="text-sm text-gray-500">/ {totalMarks} (effective)</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Question + answer */}
      <section className="rounded-lg border border-gray-200 bg-white p-5 space-y-3">
        <div>
          <h2 className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1">Question</h2>
          <p className="text-gray-800 leading-relaxed">{r.question_text}</p>
        </div>
        {r.text_content && (
          <div className="border-t border-gray-100 pt-3">
            <h2 className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1">Student Answer</h2>
            <p className="text-gray-800 leading-relaxed whitespace-pre-wrap text-sm">{r.text_content}</p>
          </div>
        )}
        {r.file_name && !r.text_content && (
          <div className="border-t border-gray-100 pt-3">
            <h2 className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1">Submitted File</h2>
            <p className="text-sm text-gray-700">{r.file_name}</p>
          </div>
        )}
      </section>

      {/* AI feedback */}
      {r.formative_feedback && (
        <section className="rounded-lg border border-blue-200 bg-blue-50 p-5">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-blue-600 mb-2">AI Formative Feedback</h2>
          <p className="text-sm text-blue-900 leading-relaxed whitespace-pre-wrap">{r.formative_feedback}</p>
        </section>
      )}

      {/* Per-criterion review */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">Rubric Review</h2>
        {r.criteria.length === 0 ? (
          <p className="text-sm text-gray-500">No rubric criteria.</p>
        ) : (
          r.criteria.map((c) => (
            <CriterionReviewRow
              key={c.criterion_id}
              submissionId={submissionId}
              criterion={c}
              readOnly={isFinalised}
              onSaved={load}
            />
          ))
        )}
      </section>

      {/* Running total */}
      <div className="rounded-lg border border-gray-200 bg-gray-50 px-5 py-3 flex items-center justify-between">
        <span className="text-sm font-medium text-gray-600">Effective total</span>
        <span className="text-xl font-bold text-gray-900">{r.effective_total} / {totalMarks}</span>
      </div>

      {/* Finalise / publish */}
      {actionError && <Alert variant="error" message={actionError} />}

      {!isFinalised && (
        <section className="rounded-lg border border-gray-200 bg-white p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Finalise Grade</h2>
          <form onSubmit={handleFinalise} className="space-y-3">
            <div>
              <label className="block text-sm text-gray-600 mb-1">Teacher comment (optional)</label>
              <textarea
                rows={3}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Add a comment for the student…"
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <Button type="submit" loading={finalising}>
              Finalise Grade ({r.effective_total}/{totalMarks})
            </Button>
          </form>
        </section>
      )}

      {isFinalised && !isPublished && (
        <section className="rounded-lg border border-green-200 bg-green-50 p-5">
          <h2 className="text-sm font-semibold text-green-800 mb-2">Grade finalised</h2>
          {r.finalised_grade?.teacher_comment && (
            <p className="text-sm text-green-700 mb-3">{r.finalised_grade.teacher_comment}</p>
          )}
          <p className="text-sm text-green-700 mb-4">
            Publish to make this grade visible to {r.student_name ?? "the student"}.
          </p>
          <Button onClick={handlePublish} loading={publishing}>
            Publish Grade to Student
          </Button>
        </section>
      )}

      {isFinalised && isPublished && (
        <section className="rounded-lg border border-gray-200 bg-white p-4">
          <p className="text-sm text-gray-600">
            Grade published to {r.student_name ?? "student"} on{" "}
            {r.finalised_grade ? formatDateTime(r.finalised_grade.finalised_at) : "–"}.
          </p>
        </section>
      )}
    </div>
  );
}

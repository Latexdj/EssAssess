"use client";
import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import { assignmentsApi, type Assignment } from "@/lib/api/assignments";
import { submissionsApi, type Submission } from "@/lib/api/submissions";
import { formatDateTime } from "@/lib/utils/formatters";
import RubricBuilder from "@/components/lms/RubricBuilder";
import TextSubmissionForm from "@/components/submission/TextSubmissionForm";
import FileSubmissionForm from "@/components/submission/FileSubmissionForm";
import SubmissionStatusCard from "@/components/submission/SubmissionStatusCard";
import Alert from "@/components/ui/Alert";
import Spinner from "@/components/ui/Spinner";

type SubmitMode = "text" | "file";

export default function StudentAssignmentDetailPage() {
  const { assignmentId } = useParams<{ assignmentId: string }>();

  const [assignment, setAssignment]   = useState<Assignment | null>(null);
  const [submission, setSubmission]   = useState<Submission | null>(null);
  const [mode, setMode]               = useState<SubmitMode>("text");
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [a, subs] = await Promise.all([
        assignmentsApi.get(assignmentId),
        submissionsApi.list({ assignment_id: assignmentId }),
      ]);
      setAssignment(a);
      // student endpoint returns only their own submission
      setSubmission(subs[0] ?? null);
      // Pick default mode from allowed types
      if (!a.allowed_submission_types.includes("text") && a.allowed_submission_types.length > 0) {
        setMode("file");
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [assignmentId]);

  useEffect(() => { loadData(); }, [loadData]);

  if (loading) return <div className="flex justify-center py-12"><Spinner /></div>;
  if (error)   return <Alert variant="error" message={error} />;
  if (!assignment) return null;

  const a          = assignment;
  const isPastDue  = new Date(a.due_date) < new Date();
  const canSubmit  = !isPastDue || submission?.status === "grading_failed";
  const hasFile    = a.allowed_submission_types.some((t) => t === "pdf" || t === "image");
  const hasText    = a.allowed_submission_types.includes("text");
  const fileTypes  = a.allowed_submission_types.filter((t) => t !== "text");

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{a.title}</h1>
        <p className="text-sm text-gray-500 mt-1">
          {a.class_name} · {a.subject_name} · {a.max_marks} marks
        </p>
        <p className={`text-sm mt-1 font-medium ${isPastDue ? "text-red-600" : "text-gray-600"}`}>
          Due: {formatDateTime(a.due_date)}{isPastDue ? " — Past due" : ""}
        </p>
      </div>

      {/* Question */}
      <section className="rounded-lg border border-gray-200 bg-white p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500 mb-3">Question</h2>
        <p className="text-gray-900 leading-relaxed text-base">{a.question_text}</p>
        {a.instructions && (
          <div className="mt-4 border-t border-gray-100 pt-4">
            <p className="text-sm font-medium text-gray-600 mb-1">Instructions</p>
            <p className="text-sm text-gray-700">{a.instructions}</p>
          </div>
        )}
      </section>

      {/* Rubric */}
      <section className="rounded-lg border border-gray-200 bg-white p-5">
        <RubricBuilder
          assignmentId={assignmentId}
          criteria={a.rubric_criteria}
          readOnly
          onRefresh={() => {}}
        />
      </section>

      {/* Submission area */}
      <section className="rounded-lg border border-gray-200 bg-white p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500 mb-4">Your Submission</h2>

        {submission ? (
          <SubmissionStatusCard
            submission={submission}
            maxMarks={a.max_marks}
            onUpdate={setSubmission}
          />
        ) : canSubmit ? (
          <div className="space-y-4">
            {/* Mode tabs (only show when multiple types allowed) */}
            {hasText && hasFile && (
              <div className="flex gap-2 border-b border-gray-200 pb-3">
                <button
                  onClick={() => setMode("text")}
                  className={`px-4 py-2 rounded-t text-sm font-medium min-h-[44px] ${
                    mode === "text"
                      ? "border-b-2 border-blue-600 text-blue-700"
                      : "text-gray-500 hover:text-gray-700"
                  }`}
                >
                  Type Answer
                </button>
                <button
                  onClick={() => setMode("file")}
                  className={`px-4 py-2 rounded-t text-sm font-medium min-h-[44px] ${
                    mode === "file"
                      ? "border-b-2 border-blue-600 text-blue-700"
                      : "text-gray-500 hover:text-gray-700"
                  }`}
                >
                  Upload File
                </button>
              </div>
            )}

            {(mode === "text" && hasText) && (
              <TextSubmissionForm
                assignmentId={assignmentId}
                onSubmitted={setSubmission}
              />
            )}
            {(mode === "file" && hasFile) && (
              <FileSubmissionForm
                assignmentId={assignmentId}
                allowedTypes={fileTypes}
                onSubmitted={setSubmission}
              />
            )}
          </div>
        ) : (
          <p className="text-sm text-gray-500">
            This assignment is past due and submissions are closed.
          </p>
        )}
      </section>
    </div>
  );
}

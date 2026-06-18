"use client";
import { useEffect, useRef } from "react";
import type { Submission } from "@/lib/api/submissions";
import { submissionsApi } from "@/lib/api/submissions";
import { formatDateTime } from "@/lib/utils/formatters";
import Spinner from "@/components/ui/Spinner";

const TERMINAL = new Set(["graded", "grading_failed", "finalised"]);
const POLL_MS  = 4000;

interface Props {
  submission:     Submission;
  maxMarks:       number;
  onUpdate:       (sub: Submission) => void;
}

function StatusBadge({ status }: { status: Submission["status"] }) {
  const map: Record<Submission["status"], { label: string; cls: string }> = {
    pending_grading:     { label: "Queued",           cls: "bg-gray-100 text-gray-600" },
    grading_in_progress: { label: "Grading…",         cls: "bg-blue-100 text-blue-700" },
    graded:              { label: "Graded",            cls: "bg-green-100 text-green-700" },
    grading_failed:      { label: "Grading failed",   cls: "bg-red-100 text-red-700" },
    finalised:           { label: "Finalised",        cls: "bg-indigo-100 text-indigo-700" },
  };
  const { label, cls } = map[status];
  return (
    <span className={`rounded-full px-3 py-1 text-sm font-semibold ${cls}`}>{label}</span>
  );
}

export default function SubmissionStatusCard({ submission: sub, maxMarks, onUpdate }: Props) {
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (TERMINAL.has(sub.status)) return;
    pollRef.current = setInterval(async () => {
      try {
        const updated = await submissionsApi.get(sub.id);
        onUpdate(updated);
        if (TERMINAL.has(updated.status)) clearInterval(pollRef.current!);
      } catch {
        // Ignore transient errors; keep polling
      }
    }, POLL_MS);
    return () => clearInterval(pollRef.current!);
  }, [sub.id, sub.status, onUpdate]);

  const isPolling = !TERMINAL.has(sub.status);
  const scorePercent = sub.total_ai_score != null && maxMarks > 0
    ? Math.round((sub.total_ai_score / maxMarks) * 100)
    : null;

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        {isPolling && <Spinner className="w-4 h-4" />}
        <StatusBadge status={sub.status} />
        <span className="text-sm text-gray-500">
          Submitted {formatDateTime(sub.submitted_at)}
        </span>
      </div>

      {isPolling && (
        <p className="text-sm text-gray-600">
          {sub.status === "pending_grading"
            ? "Your submission is in the grading queue…"
            : "The AI is grading your essay. This usually takes 15–30 seconds."}
        </p>
      )}

      {sub.status === "grading_failed" && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-700">
          <p className="font-semibold mb-1">Grading could not be completed</p>
          <p>{sub.error_message ?? "An unexpected error occurred. Your teacher has been notified."}</p>
        </div>
      )}

      {(sub.status === "graded" || sub.status === "finalised") && sub.total_ai_score != null && (
        <div className="rounded-lg border border-gray-200 bg-white p-5 space-y-4">
          <div className="flex items-center gap-4">
            <div className="text-center">
              <p className="text-3xl font-bold text-gray-900">
                {sub.total_ai_score}
              </p>
              <p className="text-sm text-gray-500">out of {maxMarks}</p>
            </div>
            {scorePercent != null && (
              <div className="flex-1">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>Score</span>
                  <span>{scorePercent}%</span>
                </div>
                <div className="w-full rounded-full bg-gray-200 h-3">
                  <div
                    className={`h-3 rounded-full ${scorePercent >= 60 ? "bg-green-500" : "bg-amber-500"}`}
                    style={{ width: `${scorePercent}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          {sub.formative_feedback && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Feedback</h3>
              <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                {sub.formative_feedback}
              </p>
            </div>
          )}

          {sub.status === "graded" && (
            <p className="text-xs text-gray-400 italic">
              This grade is provisional and may be reviewed by your teacher.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

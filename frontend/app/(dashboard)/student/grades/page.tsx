"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { gradebookApi, type StudentGrade } from "@/lib/api/gradebook";
import { formatDate } from "@/lib/utils/formatters";
import Alert from "@/components/ui/Alert";
import { SkeletonCard } from "@/components/ui/Skeleton";

function ScoreBar({ score, max }: { score: number; max: number }) {
  const pct = Math.round((score / max) * 100);
  return (
    <div className="flex items-center gap-2">
      <span className="text-lg font-bold text-gray-900 tabular-nums w-16 text-right">
        {score}/{max}
      </span>
      <div className="flex-1 rounded-full bg-gray-200 h-2">
        <div
          className={`h-2 rounded-full ${pct >= 50 ? "bg-green-500" : "bg-amber-500"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-sm text-gray-500 w-10">{pct}%</span>
    </div>
  );
}

function GradeCard({ grade: g }: { grade: StudentGrade }) {
  const [expanded, setExpanded] = useState(false);
  const showFinal = g.is_published && g.final_score !== null;
  const displayScore = showFinal ? g.final_score! : g.ai_score;

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <Link
            href={`/student/assignments/${g.assignment_id}`}
            className="font-semibold text-gray-900 hover:text-blue-600"
          >
            {g.assignment_title}
          </Link>
          <p className="text-xs text-gray-500 mt-0.5">
            {g.class_name} · {g.subject_code} · Due {formatDate(g.due_date)}
          </p>
        </div>
        {showFinal && (
          <span className="shrink-0 rounded-full bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-700">
            Final
          </span>
        )}
        {!showFinal && g.ai_score !== null && (
          <span className="shrink-0 rounded-full bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-600">
            AI grade
          </span>
        )}
      </div>

      {displayScore !== null && (
        <ScoreBar score={displayScore} max={g.max_marks} />
      )}

      {showFinal && g.teacher_comment && (
        <div className="rounded bg-gray-50 px-3 py-2 text-sm text-gray-700 italic">
          "{g.teacher_comment}"
        </div>
      )}

      {g.formative_feedback && (
        <div>
          <button
            onClick={() => setExpanded((v) => !v)}
            className="text-sm text-blue-600 hover:underline min-h-[44px] flex items-center"
          >
            {expanded ? "Hide feedback ▲" : "Show AI feedback ▼"}
          </button>
          {expanded && (
            <p className="text-sm text-gray-700 leading-relaxed mt-2 whitespace-pre-wrap">
              {g.formative_feedback}
            </p>
          )}
        </div>
      )}

      {!showFinal && !g.ai_score && (
        <p className="text-sm text-gray-400 italic">
          Awaiting teacher review
        </p>
      )}
    </div>
  );
}

export default function StudentGradesPage() {
  const [grades, setGrades] = useState<StudentGrade[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);

  useEffect(() => {
    gradebookApi.getStudentGrades()
      .then(setGrades)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">My Grades</h1>

      {error && <Alert variant="error" message={error} />}
      {loading && (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      )}

      {!loading && grades.length === 0 && (
        <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
          <p className="text-gray-500">No grades yet.</p>
          <p className="text-sm text-gray-400 mt-1">
            Grades will appear here once your assignments have been graded.
          </p>
        </div>
      )}

      {grades.length > 0 && (
        <div className="space-y-3">
          {grades.map((g) => (
            <GradeCard key={g.submission_id} grade={g} />
          ))}
        </div>
      )}
    </div>
  );
}

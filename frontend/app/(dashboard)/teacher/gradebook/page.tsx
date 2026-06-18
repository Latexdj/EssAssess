"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { classesApi, type ClassListItem } from "@/lib/api/classes";
import { gradebookApi, type ClassGradebook, type AssignmentStats } from "@/lib/api/gradebook";
import { formatDate } from "@/lib/utils/formatters";
import Alert from "@/components/ui/Alert";
import { SkeletonTable } from "@/components/ui/Skeleton";

function pct(n: number, d: number) {
  if (!d) return 0;
  return Math.round((n / d) * 100);
}

function ProgressBar({ value, max, colorClass = "bg-blue-500" }: { value: number; max: number; colorClass?: string }) {
  const p = pct(value, max);
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 rounded-full bg-gray-100 h-1.5">
        <div className={`h-1.5 rounded-full ${colorClass}`} style={{ width: `${p}%` }} />
      </div>
      <span className="text-xs text-gray-500 tabular-nums w-8">{p}%</span>
    </div>
  );
}

function AssignmentRow({ a }: { a: AssignmentStats }) {
  const submitRate = pct(a.submitted_count, a.enrolled_count);
  const gradeRate  = pct(a.graded_count,    a.submitted_count);

  return (
    <tr className="border-b border-gray-100 hover:bg-gray-50">
      <td className="py-3 px-4">
        <Link
          href={`/teacher/assignments/${a.assignment_id}`}
          className="font-medium text-gray-900 hover:text-blue-600"
        >
          {a.title}
        </Link>
        <p className="text-xs text-gray-500 mt-0.5">{a.subject_code} · Due {formatDate(a.due_date)}</p>
      </td>
      <td className="py-3 px-4 text-center">
        {a.is_published ? (
          <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-700">Live</span>
        ) : (
          <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-semibold text-gray-600">Draft</span>
        )}
      </td>
      <td className="py-3 px-4">
        <div className="text-sm text-gray-700 mb-0.5">
          {a.submitted_count} / {a.enrolled_count}
        </div>
        <ProgressBar value={a.submitted_count} max={a.enrolled_count} />
      </td>
      <td className="py-3 px-4">
        <div className="text-sm text-gray-700 mb-0.5">
          {a.graded_count} / {a.submitted_count}
        </div>
        <ProgressBar value={a.graded_count} max={a.submitted_count} colorClass="bg-blue-500" />
      </td>
      <td className="py-3 px-4">
        <div className="text-sm text-gray-700 mb-0.5">
          {a.published_count} / {a.enrolled_count}
        </div>
        <ProgressBar value={a.published_count} max={a.enrolled_count} colorClass="bg-indigo-500" />
      </td>
      <td className="py-3 px-4 text-center">
        {a.avg_ai_score !== null ? (
          <span className="text-sm font-semibold text-gray-900">
            {a.avg_ai_score.toFixed(1)}/{a.max_marks}
          </span>
        ) : (
          <span className="text-sm text-gray-400">—</span>
        )}
      </td>
      <td className="py-3 px-4 text-center">
        {a.avg_final_score !== null ? (
          <span className="text-sm font-semibold text-gray-900">
            {a.avg_final_score.toFixed(1)}/{a.max_marks}
          </span>
        ) : (
          <span className="text-sm text-gray-400">—</span>
        )}
      </td>
    </tr>
  );
}

export default function TeacherGradebookPage() {
  const [classes, setClasses]       = useState<ClassListItem[]>([]);
  const [classId, setClassId]       = useState("");
  const [gradebook, setGradebook]   = useState<ClassGradebook | null>(null);
  const [loadingCls, setLoadingCls] = useState(true);
  const [loadingGB, setLoadingGB]   = useState(false);
  const [error, setError]           = useState<string | null>(null);

  useEffect(() => {
    classesApi.list()
      .then((cs) => { setClasses(cs); if (cs.length) setClassId(cs[0].id); })
      .finally(() => setLoadingCls(false));
  }, []);

  useEffect(() => {
    if (!classId) return;
    setLoadingGB(true);
    setError(null);
    gradebookApi.getClassGradebook(classId)
      .then(setGradebook)
      .catch((e) => setError(e.message))
      .finally(() => setLoadingGB(false));
  }, [classId]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Gradebook</h1>
        {!loadingCls && classes.length > 0 && (
          <select
            value={classId}
            onChange={(e) => setClassId(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
          >
            {classes.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        )}
      </div>

      {error && <Alert variant="error" message={error} />}

      {(loadingCls || loadingGB) && <SkeletonTable rows={5} />}

      {gradebook && !loadingGB && (
        <>
          <div className="flex gap-4 text-sm text-gray-600">
            <span className="font-medium text-gray-900">{gradebook.class_name}</span>
            <span>{gradebook.enrolled_count} students enrolled</span>
            <span>{gradebook.assignments.length} assignment{gradebook.assignments.length !== 1 ? "s" : ""}</span>
          </div>

          {gradebook.assignments.length === 0 ? (
            <p className="text-sm text-gray-500">No published assignments for this class.</p>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="py-3 px-4 text-left font-semibold text-gray-600">Assignment</th>
                    <th className="py-3 px-4 text-center font-semibold text-gray-600">Status</th>
                    <th className="py-3 px-4 text-left font-semibold text-gray-600">Submitted</th>
                    <th className="py-3 px-4 text-left font-semibold text-gray-600">Graded</th>
                    <th className="py-3 px-4 text-left font-semibold text-gray-600">Published</th>
                    <th className="py-3 px-4 text-center font-semibold text-gray-600">Avg AI</th>
                    <th className="py-3 px-4 text-center font-semibold text-gray-600">Avg Final</th>
                  </tr>
                </thead>
                <tbody>
                  {gradebook.assignments.map((a) => (
                    <AssignmentRow key={a.assignment_id} a={a} />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}

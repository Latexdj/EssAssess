"use client";
import Link from "next/link";
import type { Assignment } from "@/lib/api/assignments";
import { formatDate } from "@/lib/utils/formatters";

interface Props {
  assignment: Assignment;
  href:       string;
  showClass?: boolean;
}

function dueBadge(due: string): { label: string; cls: string } {
  const diff = new Date(due).getTime() - Date.now();
  const days  = diff / 86400000;
  if (diff < 0)      return { label: "Overdue",      cls: "bg-red-100 text-red-700" };
  if (days < 2)      return { label: "Due soon",     cls: "bg-orange-100 text-orange-700" };
  if (days < 7)      return { label: `${Math.ceil(days)}d left`, cls: "bg-yellow-100 text-yellow-700" };
  return              { label: formatDate(due),       cls: "bg-gray-100 text-gray-600" };
}

export default function AssignmentCard({ assignment: a, href, showClass }: Props) {
  const { label, cls } = dueBadge(a.due_date);

  return (
    <Link
      href={href}
      className="block rounded-lg border border-gray-200 bg-white p-4 shadow-sm hover:border-blue-400 hover:shadow-md transition-shadow"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="font-semibold text-gray-900 truncate">{a.title}</p>
          {showClass && a.class_name && (
            <p className="text-xs text-gray-500 mt-0.5">{a.class_name} · {a.subject_code}</p>
          )}
        </div>
        <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
          {label}
        </span>
      </div>

      <p className="text-sm text-gray-600 mt-2 line-clamp-2">{a.question_text}</p>

      <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
        <span>{a.max_marks} marks</span>
        <span>{a.rubric_criteria.length} criteria</span>
        {!a.is_published && (
          <span className="rounded-full bg-amber-100 px-2 py-0.5 text-amber-700 font-medium">Draft</span>
        )}
        {a.submission_count > 0 && (
          <span>{a.submission_count} submission{a.submission_count !== 1 ? "s" : ""}</span>
        )}
      </div>
    </Link>
  );
}

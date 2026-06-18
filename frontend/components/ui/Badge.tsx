import type { SubmissionStatus } from "@/lib/types/grading";

const STATUS_STYLES: Record<SubmissionStatus, string> = {
  pending_grading:     "bg-yellow-100 text-yellow-800",
  grading_in_progress: "bg-blue-100 text-blue-800",
  graded:              "bg-green-100 text-green-800",
  grading_failed:      "bg-red-100 text-red-800",
  finalised:           "bg-gray-100 text-gray-800",
};

const STATUS_LABELS: Record<SubmissionStatus, string> = {
  pending_grading:     "Pending",
  grading_in_progress: "Grading…",
  graded:              "Graded",
  grading_failed:      "Failed",
  finalised:           "Finalised",
};

export function StatusBadge({ status }: { status: SubmissionStatus }) {
  return (
    <span className={`inline-block rounded-full px-3 py-1 text-xs font-semibold ${STATUS_STYLES[status]}`}>
      {STATUS_LABELS[status]}
    </span>
  );
}

const ROLE_STYLES: Record<string, string> = {
  admin:   "bg-purple-100 text-purple-800",
  teacher: "bg-blue-100 text-blue-800",
  student: "bg-green-100 text-green-800",
};

export function Badge({
  label,
  variant,
  children,
  className = "",
}: {
  label?: string;
  variant?: string;
  children?: React.ReactNode;
  className?: string;
}) {
  const roleStyle = variant ? (ROLE_STYLES[variant] ?? "bg-gray-100 text-gray-700") : "";
  return (
    <span className={`inline-block rounded-full px-3 py-1 text-xs font-semibold ${roleStyle} ${className}`}>
      {label ?? children}
    </span>
  );
}

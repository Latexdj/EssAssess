"use client";
import type { Enrolment } from "@/lib/types/classes";
import Button from "@/components/ui/Button";

interface Props {
  enrolments: Enrolment[];
  onRemove?: (studentId: string) => void;
  removing?: string | null;
  readOnly?: boolean;
}

export default function StudentRosterTable({ enrolments, onRemove, removing, readOnly }: Props) {
  if (enrolments.length === 0) {
    return <p className="text-sm text-gray-500 py-4">No students enrolled yet.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm border-collapse">
        <thead>
          <tr className="border-b border-gray-200 text-left text-gray-600">
            <th className="pb-2 pr-4 font-medium">Name</th>
            <th className="pb-2 pr-4 font-medium">Email</th>
            {!readOnly && <th className="pb-2 font-medium">Action</th>}
          </tr>
        </thead>
        <tbody>
          {enrolments.map((e) => (
            <tr key={e.id} className="border-b border-gray-100 hover:bg-gray-50">
              <td className="py-2 pr-4 text-gray-900">{e.student_name}</td>
              <td className="py-2 pr-4 text-gray-600">{e.email}</td>
              {!readOnly && (
                <td className="py-2">
                  <Button
                    variant="destructive"
                    onClick={() => onRemove?.(e.student_id)}
                    loading={removing === e.student_id}
                    className="text-xs py-1 px-2 min-h-0"
                  >
                    Remove
                  </Button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

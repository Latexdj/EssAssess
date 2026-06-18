"use client";
import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { classesApi } from "@/lib/api/classes";
import type { Class, ClassSubject, Enrolment } from "@/lib/types/classes";
import Alert from "@/components/ui/Alert";
import Spinner from "@/components/ui/Spinner";
import StudentRosterTable from "@/components/lms/StudentRosterTable";

export default function TeacherClassDetailPage() {
  const { classId } = useParams<{ classId: string }>();

  const [cls, setCls]               = useState<Class | null>(null);
  const [subjects, setSubjects]     = useState<ClassSubject[]>([]);
  const [enrolments, setEnrolments] = useState<Enrolment[]>([]);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      classesApi.get(classId),
      classesApi.listSubjects(classId),
      classesApi.listEnrolments(classId),
    ])
      .then(([cls, subs, enrols]) => {
        setCls(cls);
        setSubjects(subs);
        setEnrolments(enrols);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [classId]);

  if (loading) return <div className="flex justify-center py-12"><Spinner /></div>;
  if (error)   return <Alert variant="error" message={error} />;
  if (!cls)    return null;

  return (
    <div className="space-y-8 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{cls.name}</h1>
        <p className="text-sm text-gray-500 mt-1">
          {[cls.programme, cls.year_group && `Year ${cls.year_group}`, cls.academic_year]
            .filter(Boolean).join(" · ")}
        </p>
      </div>

      <section>
        <h2 className="text-lg font-semibold text-gray-800 mb-3">Subjects</h2>
        {subjects.length === 0 ? (
          <p className="text-sm text-gray-500">No subjects assigned.</p>
        ) : (
          <ul className="divide-y divide-gray-100 rounded-lg border border-gray-200 bg-white">
            {subjects.map((cs) => (
              <li key={cs.id} className="flex items-center justify-between px-4 py-3">
                <span className="font-medium text-gray-900">{cs.subject_name}</span>
                <span className="text-xs text-gray-400">{cs.subject_code}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2 className="text-lg font-semibold text-gray-800 mb-3">
          Students ({enrolments.length})
        </h2>
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <StudentRosterTable enrolments={enrolments} readOnly />
        </div>
      </section>
    </div>
  );
}

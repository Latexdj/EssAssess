"use client";
import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import { classesApi } from "@/lib/api/classes";
import { subjectsApi } from "@/lib/api/classes";
import { usersApi } from "@/lib/api/users";
import type { Class, ClassSubject, Enrolment, Subject } from "@/lib/types/classes";
import type { User } from "@/lib/types/auth";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import Spinner from "@/components/ui/Spinner";
import EnrolmentManager from "@/components/lms/EnrolmentManager";

export default function ClassDetailPage() {
  const { classId } = useParams<{ classId: string }>();

  const [cls, setCls]               = useState<Class | null>(null);
  const [subjects, setSubjects]     = useState<ClassSubject[]>([]);
  const [enrolments, setEnrolments] = useState<Enrolment[]>([]);
  const [allSubjects, setAllSubjects] = useState<Subject[]>([]);
  const [teachers, setTeachers]     = useState<User[]>([]);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState<string | null>(null);

  const [selSubject,  setSelSubject]  = useState("");
  const [selTeacher,  setSelTeacher]  = useState("");
  const [assigning,   setAssigning]   = useState(false);
  const [assignError, setAssignError] = useState<string | null>(null);

  const loadEnrolments = useCallback(async () => {
    const e = await classesApi.listEnrolments(classId);
    setEnrolments(e);
  }, [classId]);

  useEffect(() => {
    Promise.all([
      classesApi.get(classId),
      classesApi.listSubjects(classId),
      classesApi.listEnrolments(classId),
      subjectsApi.list(),
      usersApi.list({ role: "teacher" }),
    ])
      .then(([cls, subs, enrols, allSubs, teacherRes]) => {
        setCls(cls);
        setSubjects(subs);
        setEnrolments(enrols);
        setAllSubjects(allSubs);
        setTeachers(teacherRes.users);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [classId]);

  const handleAssignSubject = async () => {
    if (!selSubject || !selTeacher) return;
    setAssigning(true);
    setAssignError(null);
    try {
      const cs = await classesApi.assignSubject(classId, selSubject, selTeacher);
      setSubjects((prev) => [...prev, cs]);
      setSelSubject("");
      setSelTeacher("");
    } catch (e: unknown) {
      setAssignError(e instanceof Error ? e.message : "Failed to assign subject");
    } finally {
      setAssigning(false);
    }
  };

  const handleRemoveSubject = async (csId: string) => {
    await classesApi.removeSubject(classId, csId);
    setSubjects((prev) => prev.filter((s) => s.id !== csId));
  };

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

      {/* Subject assignments */}
      <section>
        <h2 className="text-lg font-semibold text-gray-800 mb-3">Subjects & Teachers</h2>

        {subjects.length === 0 ? (
          <p className="text-sm text-gray-500 mb-3">No subjects assigned yet.</p>
        ) : (
          <ul className="divide-y divide-gray-100 rounded-lg border border-gray-200 bg-white mb-3">
            {subjects.map((cs) => (
              <li key={cs.id} className="flex items-center justify-between px-4 py-3">
                <div>
                  <span className="font-medium text-gray-900">{cs.subject_name}</span>
                  <span className="text-xs text-gray-400 ml-2">{cs.subject_code}</span>
                  <p className="text-sm text-gray-500">{cs.teacher_name}</p>
                </div>
                <Button
                  variant="destructive"
                  onClick={() => handleRemoveSubject(cs.id)}
                  className="text-xs py-1 px-2 min-h-0"
                >
                  Remove
                </Button>
              </li>
            ))}
          </ul>
        )}

        <div className="rounded-lg border border-gray-200 bg-white p-4 space-y-3">
          <p className="text-sm font-medium text-gray-700">Assign subject</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <select
              value={selSubject}
              onChange={(e) => setSelSubject(e.target.value)}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
            >
              <option value="">Select subject…</option>
              {allSubjects.map((s) => (
                <option key={s.id} value={s.id}>{s.name} ({s.code})</option>
              ))}
            </select>
            <select
              value={selTeacher}
              onChange={(e) => setSelTeacher(e.target.value)}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
            >
              <option value="">Select teacher…</option>
              {teachers.map((t) => (
                <option key={t.id} value={t.id}>{t.first_name} {t.last_name}</option>
              ))}
            </select>
          </div>
          {assignError && <Alert variant="error" message={assignError} />}
          <Button onClick={handleAssignSubject} loading={assigning} disabled={!selSubject || !selTeacher}>
            Assign
          </Button>
        </div>
      </section>

      {/* Enrolments */}
      <section>
        <h2 className="text-lg font-semibold text-gray-800 mb-3">
          Students ({enrolments.length})
        </h2>
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <EnrolmentManager
            classId={classId}
            enrolments={enrolments}
            onRefresh={loadEnrolments}
          />
        </div>
      </section>
    </div>
  );
}

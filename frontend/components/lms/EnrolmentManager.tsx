"use client";
import { useState } from "react";
import Button from "@/components/ui/Button";
import Alert from "@/components/ui/Alert";
import type { Enrolment } from "@/lib/types/classes";
import { classesApi } from "@/lib/api/classes";
import { usersApi } from "@/lib/api/users";
import StudentRosterTable from "./StudentRosterTable";

interface Props {
  classId: string;
  enrolments: Enrolment[];
  onRefresh: () => void;
}

export default function EnrolmentManager({ classId, enrolments, onRefresh }: Props) {
  const [emailInput, setEmailInput] = useState("");
  const [loading, setLoading]       = useState(false);
  const [removing, setRemoving]     = useState<string | null>(null);
  const [error, setError]           = useState<string | null>(null);
  const [info, setInfo]             = useState<string | null>(null);

  const handleEnrol = async () => {
    const emails = emailInput.split(/[\n,]+/).map((e) => e.trim()).filter(Boolean);
    if (emails.length === 0) return;

    setLoading(true);
    setError(null);
    setInfo(null);
    try {
      // Resolve emails → user IDs
      const ids: string[] = [];
      const missing: string[] = [];
      for (const email of emails) {
        const res = await usersApi.list({ role: "student" });
        const found = res.users.find((u) => u.email === email);
        if (found) ids.push(found.id);
        else missing.push(email);
      }

      if (ids.length > 0) {
        const res = await classesApi.bulkEnrol(classId, ids);
        const msgs: string[] = [];
        if (res.enrolled.length)         msgs.push(`${res.enrolled.length} enrolled`);
        if (res.already_enrolled.length) msgs.push(`${res.already_enrolled.length} already enrolled`);
        if (res.not_found.length)        msgs.push(`${res.not_found.length} not found`);
        if (missing.length)              msgs.push(`${missing.length} email(s) not found: ${missing.join(", ")}`);
        setInfo(msgs.join(" · "));
      } else {
        setError("No matching students found for those email addresses.");
      }

      setEmailInput("");
      onRefresh();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to enrol students");
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async (studentId: string) => {
    setRemoving(studentId);
    setError(null);
    try {
      await classesApi.removeEnrolment(classId, studentId);
      onRefresh();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to remove student");
    } finally {
      setRemoving(null);
    }
  };

  return (
    <div className="space-y-4">
      <StudentRosterTable enrolments={enrolments} onRemove={handleRemove} removing={removing} />

      <div className="border-t border-gray-200 pt-4">
        <p className="text-sm font-medium text-gray-700 mb-1">Enrol students by email</p>
        <p className="text-xs text-gray-500 mb-2">Enter one email per line or separate with commas</p>
        <textarea
          value={emailInput}
          onChange={(e) => setEmailInput(e.target.value)}
          rows={3}
          className="w-full rounded-md border border-gray-300 p-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="student@school.edu.gh"
        />
        {error && <Alert variant="error" message={error} className="mt-2" />}
        {info  && <Alert variant="info"  message={info}  className="mt-2" />}
        <Button onClick={handleEnrol} loading={loading} className="mt-2">
          Enrol Students
        </Button>
      </div>
    </div>
  );
}

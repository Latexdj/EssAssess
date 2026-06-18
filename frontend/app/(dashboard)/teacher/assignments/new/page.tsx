"use client";
import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { classesApi, type ClassListItem } from "@/lib/api/classes";
import { assignmentsApi } from "@/lib/api/assignments";
import type { ClassSubject } from "@/lib/types/classes";
import { Input } from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import Alert from "@/components/ui/Alert";
import Spinner from "@/components/ui/Spinner";

const TYPES = ["text", "pdf", "image"];

export default function NewAssignmentPage() {
  const router = useRouter();

  const [classes, setClasses]       = useState<ClassListItem[]>([]);
  const [subjects, setSubjects]     = useState<ClassSubject[]>([]);
  const [loadingClasses, setLCls]   = useState(true);

  const [form, setForm] = useState({
    class_id:     "",
    cs_id:        "",   // class_subject_id
    title:        "",
    question:     "",
    instructions: "",
    max_marks:    "10",
    due_date:     "",
    types:        ["text", "pdf", "image"] as string[],
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError]           = useState<string | null>(null);

  useEffect(() => {
    classesApi.list()
      .then(setClasses)
      .finally(() => setLCls(false));
  }, []);

  const handleClassChange = async (classId: string) => {
    setForm((p) => ({ ...p, class_id: classId, cs_id: "" }));
    if (!classId) { setSubjects([]); return; }
    const subs = await classesApi.listSubjects(classId);
    setSubjects(subs);
  };

  const toggleType = (t: string) => {
    setForm((p) => ({
      ...p,
      types: p.types.includes(t) ? p.types.filter((x) => x !== t) : [...p.types, t],
    }));
  };

  const set = (k: keyof typeof form) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
      setForm((p) => ({ ...p, [k]: e.target.value }));

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!form.cs_id || !form.title || !form.question || !form.due_date) return;
    if (form.types.length === 0) {
      setError("Select at least one submission type");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const a = await assignmentsApi.create({
        class_subject_id:         form.cs_id,
        title:                    form.title,
        question_text:            form.question,
        instructions:             form.instructions || undefined,
        allowed_submission_types: form.types,
        max_marks:                Number(form.max_marks),
        due_date:                 new Date(form.due_date).toISOString(),
      });
      router.push(`/teacher/assignments/${a.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create assignment");
    } finally {
      setSubmitting(false);
    }
  };

  if (loadingClasses) return <div className="flex justify-center py-12"><Spinner /></div>;

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">New Assignment</h1>
      {error && <Alert variant="error" message={error} className="mb-4" />}

      <form onSubmit={handleSubmit} className="space-y-5 bg-white rounded-lg border border-gray-200 p-6">
        {/* Class / Subject selection */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Class</label>
            <select
              value={form.class_id}
              onChange={(e) => handleClassChange(e.target.value)}
              required
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
            >
              <option value="">Select class…</option>
              {classes.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Subject</label>
            <select
              value={form.cs_id}
              onChange={set("cs_id")}
              required
              disabled={!form.class_id}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px] disabled:bg-gray-50"
            >
              <option value="">Select subject…</option>
              {subjects.map((s) => (
                <option key={s.id} value={s.id}>{s.subject_name}</option>
              ))}
            </select>
          </div>
        </div>

        <Input label="Assignment title" value={form.title} onChange={set("title")} required />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Essay question</label>
          <textarea
            value={form.question}
            onChange={set("question")}
            required
            rows={4}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Write the full essay question here…"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Instructions <span className="text-gray-400">(optional)</span>
          </label>
          <textarea
            value={form.instructions}
            onChange={set("instructions")}
            rows={2}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Additional instructions for students…"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Maximum marks"
            type="number"
            min={1}
            value={form.max_marks}
            onChange={set("max_marks")}
            required
          />
          <Input
            label="Due date"
            type="datetime-local"
            value={form.due_date}
            onChange={set("due_date")}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Allowed submission types</label>
          <div className="flex gap-4">
            {TYPES.map((t) => (
              <label key={t} className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.types.includes(t)}
                  onChange={() => toggleType(t)}
                  className="rounded border-gray-300 text-blue-600"
                />
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </label>
            ))}
          </div>
        </div>

        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={submitting}>Create Assignment</Button>
          <Button type="button" variant="secondary" onClick={() => router.back()}>Cancel</Button>
        </div>
      </form>
    </div>
  );
}

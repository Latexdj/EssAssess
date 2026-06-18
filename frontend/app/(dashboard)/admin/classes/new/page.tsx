"use client";
import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import Alert from "@/components/ui/Alert";
import { classesApi } from "@/lib/api/classes";

export default function NewClassPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    name: "", programme: "", year_group: "", academic_year: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((p) => ({ ...p, [k]: e.target.value }));

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const cls = await classesApi.create({
        name:          form.name,
        programme:     form.programme || undefined,
        year_group:    form.year_group ? Number(form.year_group) : undefined,
        academic_year: form.academic_year || undefined,
      });
      router.push(`/admin/classes/${cls.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create class");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Create Class</h1>

      {error && <Alert variant="error" message={error} className="mb-4" />}

      <form onSubmit={handleSubmit} className="space-y-4 bg-white rounded-lg border border-gray-200 p-6">
        <Input label="Class name" value={form.name} onChange={set("name")} required placeholder="e.g. Science 1A" />
        <Input label="Programme"  value={form.programme} onChange={set("programme")} placeholder="e.g. General Science" />
        <div className="grid grid-cols-2 gap-4">
          <Input label="Year group"    type="number" value={form.year_group}    onChange={set("year_group")}    placeholder="1" />
          <Input label="Academic year" value={form.academic_year} onChange={set("academic_year")} placeholder="2024/2025" />
        </div>
        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={loading}>Create</Button>
          <Button type="button" variant="secondary" onClick={() => router.back()}>Cancel</Button>
        </div>
      </form>
    </div>
  );
}

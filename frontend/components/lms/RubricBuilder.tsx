"use client";
import { useState } from "react";
import type { RubricCriterion } from "@/lib/api/assignments";
import { assignmentsApi } from "@/lib/api/assignments";
import Button from "@/components/ui/Button";
import Alert from "@/components/ui/Alert";

interface Props {
  assignmentId: string;
  criteria:     RubricCriterion[];
  readOnly?:    boolean;
  onRefresh:    () => void;
}

const EMPTY = { name: "", description: "", max_marks: "" };

export default function RubricBuilder({ assignmentId, criteria, readOnly, onRefresh }: Props) {
  const [form, setForm]     = useState(EMPTY);
  const [adding, setAdding] = useState(false);
  const [error, setError]   = useState<string | null>(null);
  const [busy, setBusy]     = useState<string | null>(null);  // criterionId being acted on

  const sorted = [...criteria].sort((a, b) => a.display_order - b.display_order);
  const totalMarks = sorted.reduce((s, c) => s + c.max_marks, 0);

  const handleAdd = async () => {
    if (!form.name || !form.description || !form.max_marks) return;
    setAdding(true);
    setError(null);
    try {
      await assignmentsApi.addCriterion(assignmentId, {
        name:        form.name,
        description: form.description,
        max_marks:   Number(form.max_marks),
      });
      setForm(EMPTY);
      onRefresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to add criterion");
    } finally {
      setAdding(false);
    }
  };

  const handleDelete = async (criterionId: string) => {
    setBusy(criterionId);
    try {
      await assignmentsApi.deleteCriterion(assignmentId, criterionId);
      onRefresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to delete criterion");
    } finally {
      setBusy(null);
    }
  };

  const handleMove = async (criterionId: string, dir: "up" | "down") => {
    setBusy(criterionId + dir);
    try {
      await assignmentsApi.moveCriterion(assignmentId, criterionId, dir);
      onRefresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to reorder");
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold text-gray-800">
          Rubric Criteria
        </h3>
        <span className="text-sm text-gray-500">
          Total: <span className="font-semibold text-gray-900">{totalMarks}</span> marks
        </span>
      </div>

      {error && <Alert variant="error" message={error} />}

      {sorted.length === 0 ? (
        <p className="text-sm text-gray-500">No criteria yet. Add one below.</p>
      ) : (
        <ol className="space-y-2">
          {sorted.map((c, i) => (
            <li key={c.id} className="rounded-lg border border-gray-200 bg-white p-3">
              <div className="flex items-start gap-3">
                {!readOnly && (
                  <div className="flex flex-col gap-1 pt-0.5">
                    <button
                      onClick={() => handleMove(c.id, "up")}
                      disabled={i === 0 || busy === c.id + "up"}
                      className="p-1 text-gray-400 hover:text-gray-700 disabled:opacity-30"
                      aria-label="Move up"
                    >▲</button>
                    <button
                      onClick={() => handleMove(c.id, "down")}
                      disabled={i === sorted.length - 1 || busy === c.id + "down"}
                      className="p-1 text-gray-400 hover:text-gray-700 disabled:opacity-30"
                      aria-label="Move down"
                    >▼</button>
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900">{c.name}</span>
                    <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-700">
                      {c.max_marks} mark{c.max_marks !== 1 ? "s" : ""}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-0.5">{c.description}</p>
                </div>
                {!readOnly && (
                  <Button
                    variant="destructive"
                    onClick={() => handleDelete(c.id)}
                    loading={busy === c.id}
                    className="text-xs py-1 px-2 min-h-0 shrink-0"
                  >
                    Remove
                  </Button>
                )}
              </div>
            </li>
          ))}
        </ol>
      )}

      {!readOnly && (
        <div className="rounded-lg border border-dashed border-gray-300 p-4 space-y-3">
          <p className="text-sm font-medium text-gray-700">Add criterion</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <input
              type="text"
              placeholder="Criterion name"
              value={form.name}
              onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
            />
            <input
              type="text"
              placeholder="Description / marking guidance"
              value={form.description}
              onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
            />
            <input
              type="number"
              placeholder="Max marks"
              min={1}
              value={form.max_marks}
              onChange={(e) => setForm((p) => ({ ...p, max_marks: e.target.value }))}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
            />
          </div>
          <Button
            onClick={handleAdd}
            loading={adding}
            disabled={!form.name || !form.description || !form.max_marks}
            variant="secondary"
          >
            Add Criterion
          </Button>
        </div>
      )}
    </div>
  );
}

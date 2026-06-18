"use client";
import { useState } from "react";
import type { CriterionReview } from "@/lib/api/review";
import { reviewApi } from "@/lib/api/review";
import Button from "@/components/ui/Button";

interface Props {
  submissionId: string;
  criterion:    CriterionReview;
  readOnly:     boolean;
  onSaved:      () => void;
}

export default function CriterionReviewRow({ submissionId, criterion: c, readOnly, onSaved }: Props) {
  const [editing, setEditing] = useState(false);
  const [score, setScore]     = useState(c.override_score?.toString() ?? "");
  const [note, setNote]       = useState(c.override_note ?? "");
  const [saving, setSaving]   = useState(false);
  const [error, setError]     = useState<string | null>(null);

  const hasOverride = c.override_score !== null;
  const effectiveLabel = hasOverride ? "Override" : "AI";

  const handleSave = async () => {
    const parsed = Number(score);
    if (isNaN(parsed) || parsed < 0 || parsed > c.max_marks) {
      setError(`Score must be 0–${c.max_marks}`);
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await reviewApi.setOverride(submissionId, c.criterion_id, parsed, note || undefined);
      setEditing(false);
      onSaved();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const handleRemove = async () => {
    setSaving(true);
    try {
      await reviewApi.removeOverride(submissionId, c.criterion_id);
      setScore("");
      setNote("");
      setEditing(false);
      onSaved();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Remove failed");
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setScore(c.override_score?.toString() ?? "");
    setNote(c.override_note ?? "");
    setEditing(false);
    setError(null);
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 space-y-3">
      {/* Header row */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <span className="font-medium text-gray-900">{c.name}</span>
          <span className="ml-2 text-sm text-gray-500">/ {c.max_marks} marks</span>
          {c.description && (
            <p className="text-xs text-gray-500 mt-0.5">{c.description}</p>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${hasOverride ? "bg-amber-100 text-amber-700" : "bg-blue-50 text-blue-700"}`}>
            {effectiveLabel}
          </span>
          <span className="text-xl font-bold text-gray-900">
            {c.effective_score}
          </span>
        </div>
      </div>

      {/* AI justification */}
      {c.ai_score !== null && (
        <div className="rounded-md bg-gray-50 px-3 py-2">
          <p className="text-xs font-medium text-gray-500 mb-0.5">
            AI score: {c.ai_score}/{c.max_marks}
          </p>
          {c.ai_justification && (
            <p className="text-sm text-gray-700 leading-relaxed">{c.ai_justification}</p>
          )}
        </div>
      )}

      {/* Override section */}
      {!readOnly && (
        <div>
          {editing ? (
            <div className="space-y-2">
              {error && <p className="text-xs text-red-600">{error}</p>}
              <div className="flex gap-2 items-center">
                <label className="text-sm text-gray-600 shrink-0">Override score:</label>
                <input
                  type="number"
                  min={0}
                  max={c.max_marks}
                  step={0.5}
                  value={score}
                  onChange={(e) => setScore(e.target.value)}
                  className="w-20 rounded border border-gray-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
                />
                <span className="text-sm text-gray-400">/ {c.max_marks}</span>
              </div>
              <textarea
                rows={2}
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Reason for override (optional)…"
                className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <div className="flex gap-2">
                <Button onClick={handleSave} loading={saving} className="text-sm py-1.5">Save</Button>
                <Button variant="secondary" onClick={handleCancel} className="text-sm py-1.5">Cancel</Button>
                {hasOverride && (
                  <Button variant="destructive" onClick={handleRemove} loading={saving} className="text-sm py-1.5">
                    Remove override
                  </Button>
                )}
              </div>
            </div>
          ) : (
            <button
              onClick={() => { setScore(c.override_score?.toString() ?? c.ai_score?.toString() ?? "0"); setEditing(true); }}
              className="text-sm text-blue-600 hover:underline min-h-[44px] flex items-center"
            >
              {hasOverride ? `Overridden: ${c.override_score}/${c.max_marks}` : "Override AI score"}
            </button>
          )}
        </div>
      )}

      {/* Show existing override note read-only */}
      {readOnly && hasOverride && (
        <div className="rounded-md bg-amber-50 px-3 py-2">
          <p className="text-xs font-medium text-amber-700">
            Override: {c.override_score}/{c.max_marks}
          </p>
          {c.override_note && (
            <p className="text-xs text-amber-700 mt-0.5">{c.override_note}</p>
          )}
        </div>
      )}
    </div>
  );
}

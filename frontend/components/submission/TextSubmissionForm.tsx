"use client";
import { useState, useEffect } from "react";
import { submissionsApi, type Submission } from "@/lib/api/submissions";
import Button from "@/components/ui/Button";
import Alert from "@/components/ui/Alert";
import { useToast } from "@/lib/context/ToastContext";

const DRAFT_KEY = (id: string) => `draft_essay_${id}`;
const MIN_CHARS = 50;
const MAX_CHARS = 10_000;

interface Props {
  assignmentId: string;
  onSubmitted:  (sub: Submission) => void;
}

export default function TextSubmissionForm({ assignmentId, onSubmitted }: Props) {
  const { toast } = useToast();
  const [text, setText]       = useState("");
  const [error, setError]     = useState<string | null>(null);
  const [saving, setSaving]   = useState(false);
  const [draftSaved, setDraftSaved] = useState(false);

  // Restore draft on mount
  useEffect(() => {
    const saved = typeof window !== "undefined"
      ? localStorage.getItem(DRAFT_KEY(assignmentId))
      : null;
    if (saved) setText(saved);
  }, [assignmentId]);

  // Auto-save draft every 10 seconds when text changes
  useEffect(() => {
    if (!text) return;
    const timer = setTimeout(() => {
      localStorage.setItem(DRAFT_KEY(assignmentId), text);
      setDraftSaved(true);
      setTimeout(() => setDraftSaved(false), 2000);
    }, 10_000);
    return () => clearTimeout(timer);
  }, [text, assignmentId]);

  const handleSubmit = async () => {
    if (text.length < MIN_CHARS) {
      setError(`Your answer must be at least ${MIN_CHARS} characters long`);
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const sub = await submissionsApi.submitText(assignmentId, text);
      localStorage.removeItem(DRAFT_KEY(assignmentId));
      toast("Essay submitted — AI grading is starting", "success");
      onSubmitted(sub);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to submit";
      setError(msg);
      toast(msg, "error");
    } finally {
      setSaving(false);
    }
  };

  const remaining = MAX_CHARS - text.length;
  const tooShort  = text.length > 0 && text.length < MIN_CHARS;

  return (
    <div className="space-y-3">
      {error && <Alert variant="error" message={error} />}

      <div className="relative">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          maxLength={MAX_CHARS}
          rows={12}
          placeholder="Type your essay answer here…"
          className="w-full rounded-lg border border-gray-300 px-4 py-3 text-base leading-relaxed focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
        />
        <div className="absolute bottom-2 right-3 text-xs text-gray-400">
          {draftSaved && <span className="text-green-600 mr-2">Draft saved</span>}
          {remaining < 500 && (
            <span className={remaining < 100 ? "text-red-500" : "text-gray-400"}>
              {remaining.toLocaleString()} characters left
            </span>
          )}
        </div>
      </div>

      {tooShort && (
        <p className="text-xs text-amber-600">
          {MIN_CHARS - text.length} more characters needed
        </p>
      )}

      <div className="flex items-center gap-3">
        <Button
          onClick={handleSubmit}
          loading={saving}
          disabled={text.length < MIN_CHARS}
        >
          Submit Answer
        </Button>
        <p className="text-xs text-gray-500">
          Once submitted, your essay will be graded automatically.
        </p>
      </div>
    </div>
  );
}

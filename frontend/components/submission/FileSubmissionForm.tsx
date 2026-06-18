"use client";
import { useState, useRef } from "react";
import { submissionsApi, type Submission } from "@/lib/api/submissions";
import Button from "@/components/ui/Button";
import Alert from "@/components/ui/Alert";
import { useToast } from "@/lib/context/ToastContext";

const MAX_MB   = 10;
const MAX_BYTES = MAX_MB * 1024 * 1024;
const ACCEPT   = ".pdf,.jpg,.jpeg,.png,.webp";

function formatBytes(n: number): string {
  if (n < 1024)       return `${n} B`;
  if (n < 1048576)    return `${(n / 1024).toFixed(0)} KB`;
  return `${(n / 1048576).toFixed(1)} MB`;
}

interface Props {
  assignmentId:      string;
  allowedTypes:      string[];   // ["pdf", "image"]
  onSubmitted:       (sub: Submission) => void;
}

export default function FileSubmissionForm({ assignmentId, allowedTypes, onSubmitted }: Props) {
  const { toast } = useToast();
  const inputRef              = useRef<HTMLInputElement>(null);
  const [file, setFile]       = useState<File | null>(null);
  const [error, setError]     = useState<string | null>(null);
  const [uploading, setUpload] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setError(null);
    if (f.size > MAX_BYTES) {
      setError(`File too large. Maximum size is ${MAX_MB} MB`);
      return;
    }
    const ext = f.name.toLowerCase().split(".").pop() ?? "";
    const isPdf   = ext === "pdf";
    const isImage = ["jpg", "jpeg", "png", "webp"].includes(ext);
    if (isPdf && !allowedTypes.includes("pdf")) {
      setError("PDF submissions are not allowed for this assignment");
      return;
    }
    if (isImage && !allowedTypes.includes("image")) {
      setError("Image submissions are not allowed for this assignment");
      return;
    }
    if (!isPdf && !isImage) {
      setError("Only PDF and image files (JPEG, PNG, WebP) are accepted");
      return;
    }
    setFile(f);
  };

  const handleSubmit = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const sub = await submissionsApi.submitFile(assignmentId, file);
      toast("File uploaded — AI grading is starting", "success");
      onSubmitted(sub);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Upload failed";
      setError(msg);
      toast(msg, "error");
    } finally {
      setUploading(false);
    }
  };

  const setUploading = (v: boolean) => setUpload(v);

  const allowed = [
    allowedTypes.includes("pdf")   && "PDF",
    allowedTypes.includes("image") && "Image (JPEG, PNG, WebP)",
  ].filter(Boolean).join(", ");

  return (
    <div className="space-y-4">
      {error && <Alert variant="error" message={error} />}

      <div
        className="rounded-lg border-2 border-dashed border-gray-300 p-6 text-center hover:border-blue-400 transition-colors cursor-pointer"
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          onChange={handleChange}
          className="hidden"
        />
        {file ? (
          <div className="space-y-1">
            <p className="font-medium text-gray-900">{file.name}</p>
            <p className="text-sm text-gray-500">{formatBytes(file.size)}</p>
            <p className="text-xs text-blue-600 mt-2">Tap to choose a different file</p>
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-gray-600">Tap to choose a file</p>
            <p className="text-sm text-gray-400">Accepted: {allowed}</p>
            <p className="text-sm text-gray-400">Maximum size: {MAX_MB} MB</p>
          </div>
        )}
      </div>

      {file && (
        <div className="flex items-center gap-3">
          <Button onClick={handleSubmit} loading={uploading}>
            Upload &amp; Submit
          </Button>
          <Button variant="secondary" onClick={() => { setFile(null); setError(null); }}>
            Remove
          </Button>
        </div>
      )}

      {!file && (
        <p className="text-xs text-gray-500">
          PDF files will have their text extracted automatically.
          Image files will be read by the AI grader.
        </p>
      )}
    </div>
  );
}

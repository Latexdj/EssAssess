"use client";
import { useState, useEffect, FormEvent } from "react";
import { knowledgeApi, type DocumentSummary, type RetrieveResult } from "@/lib/api/knowledge";
import { subjectsApi } from "@/lib/api/classes";
import type { Subject } from "@/lib/types/classes";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import Spinner from "@/components/ui/Spinner";

export default function KnowledgeBasePage() {
  const [subjects, setSubjects]   = useState<Subject[]>([]);
  const [docs, setDocs]           = useState<DocumentSummary[]>([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState<string | null>(null);

  // Upload state
  const [file, setFile]             = useState<File | null>(null);
  const [title, setTitle]           = useState("");
  const [upSubject, setUpSubject]   = useState("");
  const [isExample, setIsExample]   = useState(false);
  const [uploading, setUploading]   = useState(false);
  const [uploadMsg, setUploadMsg]   = useState<string | null>(null);
  const [uploadErr, setUploadErr]   = useState<string | null>(null);

  // Retrieval test state
  const [query, setQuery]           = useState("");
  const [rtSubject, setRtSubject]   = useState("");
  const [retrieving, setRetrieving] = useState(false);
  const [rtResult, setRtResult]     = useState<RetrieveResult | null>(null);
  const [rtError, setRtError]       = useState<string | null>(null);

  const [deleting, setDeleting]     = useState<string | null>(null);

  const loadDocs = async () => {
    try {
      setDocs(await knowledgeApi.listDocuments());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load documents");
    }
  };

  useEffect(() => {
    Promise.all([subjectsApi.list(), knowledgeApi.listDocuments()])
      .then(([subs, d]) => { setSubjects(subs); setDocs(d); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const handleUpload = async (e: FormEvent) => {
    e.preventDefault();
    if (!file || !upSubject || !title) return;
    setUploading(true);
    setUploadErr(null);
    setUploadMsg(null);
    try {
      const res = await knowledgeApi.upload(file, upSubject, title, isExample);
      setUploadMsg(`Uploaded "${res.source_title}": ${res.chunk_count} chunks stored.`);
      setFile(null);
      setTitle("");
      await loadDocs();
    } catch (e: unknown) {
      setUploadErr(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (sourceLabel: string) => {
    setDeleting(sourceLabel);
    try {
      await knowledgeApi.deleteDocument(sourceLabel);
      await loadDocs();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setDeleting(null);
    }
  };

  const handleRetrieve = async (e: FormEvent) => {
    e.preventDefault();
    if (!query || !rtSubject) return;
    setRetrieving(true);
    setRtError(null);
    setRtResult(null);
    try {
      setRtResult(await knowledgeApi.retrieve(query, rtSubject));
    } catch (e: unknown) {
      setRtError(e instanceof Error ? e.message : "Retrieval failed");
    } finally {
      setRetrieving(false);
    }
  };

  if (loading) return <div className="flex justify-center py-12"><Spinner /></div>;

  return (
    <div className="space-y-8 max-w-4xl">
      <h1 className="text-2xl font-bold text-gray-900">Knowledge Base</h1>
      {error && <Alert variant="error" message={error} />}

      {/* ── Upload ── */}
      <section className="rounded-lg border border-gray-200 bg-white p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-800">Upload Reference Document</h2>
        <p className="text-sm text-gray-500">
          Upload WAEC marking schemes, GES syllabuses, or model answers (PDF only).
          Each document is chunked, embedded, and stored for RAG retrieval during grading.
        </p>

        <form onSubmit={handleUpload} className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Document title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              placeholder="e.g. WAEC Biology 2023 Marking Scheme"
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Subject</label>
              <select
                value={upSubject}
                onChange={(e) => setUpSubject(e.target.value)}
                required
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
              >
                <option value="">Select subject…</option>
                {subjects.map((s) => (
                  <option key={s.id} value={s.code}>{s.name} ({s.code})</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">PDF file</label>
              <input
                type="file"
                accept=".pdf"
                required
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="block w-full text-sm text-gray-600 file:mr-3 file:rounded-md file:border-0 file:bg-blue-50 file:px-3 file:py-2 file:text-sm file:font-medium file:text-blue-700 hover:file:bg-blue-100"
              />
            </div>
          </div>

          <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
            <input
              type="checkbox"
              checked={isExample}
              onChange={(e) => setIsExample(e.target.checked)}
              className="rounded border-gray-300 text-blue-600"
            />
            This is a model / example answer (not a reference document)
          </label>

          {uploadErr && <Alert variant="error"  message={uploadErr} />}
          {uploadMsg && <Alert variant="success" message={uploadMsg} />}

          <Button type="submit" loading={uploading} disabled={!file || !title || !upSubject}>
            Upload & Process
          </Button>
        </form>
      </section>

      {/* ── Document list ── */}
      <section>
        <h2 className="text-lg font-semibold text-gray-800 mb-3">
          Stored Documents ({docs.length})
        </h2>

        {docs.length === 0 ? (
          <p className="text-sm text-gray-500">No documents uploaded yet.</p>
        ) : (
          <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 text-left text-gray-600">
                  <th className="px-4 py-3 font-medium">Title</th>
                  <th className="px-4 py-3 font-medium">Subject</th>
                  <th className="px-4 py-3 font-medium">Type</th>
                  <th className="px-4 py-3 font-medium">Chunks</th>
                  <th className="px-4 py-3 font-medium">Action</th>
                </tr>
              </thead>
              <tbody>
                {docs.map((d) => (
                  <tr key={d.source_label} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-900">{d.source_title}</td>
                    <td className="px-4 py-3">
                      <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
                        {d.subject_tag}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {d.is_example ? "Example" : "Reference"}
                    </td>
                    <td className="px-4 py-3 text-gray-600">{d.chunk_count}</td>
                    <td className="px-4 py-3">
                      <Button
                        variant="destructive"
                        onClick={() => handleDelete(d.source_label)}
                        loading={deleting === d.source_label}
                        className="text-xs py-1 px-2 min-h-0"
                      >
                        Delete
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* ── Test retrieval ── */}
      <section className="rounded-lg border border-gray-200 bg-white p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-800">Test Retrieval</h2>
        <p className="text-sm text-gray-500">
          Enter an essay question to validate what the AI will retrieve as context before grading.
        </p>

        <form onSubmit={handleRetrieve} className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Query / Essay question</label>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                required
                placeholder="e.g. Discuss the causes of the 1948 Accra riots"
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Subject</label>
              <select
                value={rtSubject}
                onChange={(e) => setRtSubject(e.target.value)}
                required
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
              >
                <option value="">Select…</option>
                {subjects.map((s) => (
                  <option key={s.id} value={s.code}>{s.code}</option>
                ))}
              </select>
            </div>
          </div>

          {rtError && <Alert variant="error" message={rtError} />}

          <Button type="submit" loading={retrieving} disabled={!query || !rtSubject}>
            Retrieve
          </Button>
        </form>

        {rtResult && (
          <div className="space-y-4 mt-4">
            <div>
              <p className="text-sm font-semibold text-gray-700 mb-2">
                Reference chunks ({rtResult.reference_chunks.length})
              </p>
              {rtResult.reference_chunks.length === 0 ? (
                <p className="text-sm text-gray-500">No reference chunks found for this subject.</p>
              ) : (
                <div className="space-y-2">
                  {rtResult.reference_chunks.map((c, i) => (
                    <div key={c.id} className="rounded border border-gray-200 p-3 text-sm">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-gray-700">{c.source_title} — chunk {c.chunk_index}</span>
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                          c.similarity >= 0.8 ? "bg-green-100 text-green-700" :
                          c.similarity >= 0.6 ? "bg-yellow-100 text-yellow-700" :
                          "bg-red-100 text-red-700"
                        }`}>
                          {(c.similarity * 100).toFixed(1)}% match
                        </span>
                      </div>
                      <p className="text-gray-600 text-xs leading-relaxed">{c.preview}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {rtResult.example_chunks.length > 0 && (
              <div>
                <p className="text-sm font-semibold text-gray-700 mb-2">Example answer chunks</p>
                {rtResult.example_chunks.map((c) => (
                  <div key={c.id} className="rounded border border-blue-200 bg-blue-50 p-3 text-sm">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-blue-700">{c.source_title} — chunk {c.chunk_index}</span>
                      <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
                        {(c.similarity * 100).toFixed(1)}% match
                      </span>
                    </div>
                    <p className="text-blue-800 text-xs leading-relaxed">{c.preview}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}

import { api } from "./client";

export interface DocumentSummary {
  source_title:  string;
  source_label:  string;
  subject_tag:   string;
  is_example:    boolean;
  chunk_count:   number;
  uploaded_at:   string;
}

export interface UploadResult {
  source_title: string;
  source_label: string;
  subject_tag:  string;
  is_example:   boolean;
  chunk_count:  number;
}

export interface ChunkPreview {
  id:           string;
  source_title: string;
  chunk_index:  number;
  similarity:   number;
  preview:      string;
}

export interface RetrieveResult {
  reference_chunks: ChunkPreview[];
  example_chunks:   ChunkPreview[];
}

export const knowledgeApi = {
  upload: (file: File, subjectTag: string, sourceTitle: string, isExample: boolean): Promise<UploadResult> => {
    const form = new FormData();
    form.append("file",         file);
    form.append("subject_tag",  subjectTag);
    form.append("source_title", sourceTitle);
    form.append("is_example",   String(isExample));
    return api.upload<UploadResult>("/knowledge/upload", form);
  },

  listDocuments: (): Promise<DocumentSummary[]> =>
    api.get("/knowledge/documents"),

  deleteDocument: (sourceLabel: string): Promise<void> =>
    api.delete(`/knowledge/documents/${encodeURIComponent(sourceLabel)}`),

  retrieve: (query: string, subjectTag: string, refK = 6, exampleK = 1): Promise<RetrieveResult> =>
    api.post("/knowledge/retrieve", { query, subject_tag: subjectTag, ref_k: refK, example_k: exampleK }),
};

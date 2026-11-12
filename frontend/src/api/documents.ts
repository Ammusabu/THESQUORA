import { api } from "./client";
import type { DocumentItem, DocumentListResponse } from "../types";

export async function listDocuments(params: {
  page?: number;
  limit?: number;
  category?: string;
  department?: string;
  q?: string;
}): Promise<DocumentListResponse> {
  const res = await api.get<DocumentListResponse>("/api/documents", { params });
  return res.data;
}

export async function getDocument(id: string): Promise<DocumentItem> {
  const res = await api.get<DocumentItem>(`/api/documents/${id}`);
  return res.data;
}

export async function deleteDocument(id: string): Promise<void> {
  await api.delete(`/api/documents/${id}`);
}

export async function uploadDocument(data: {
  file: File;
  title?: string;
  department?: string;
}): Promise<DocumentItem> {
  const form = new FormData();
  form.append("file", data.file);
  if (data.title) form.append("title", data.title);
  if (data.department) form.append("department", data.department);
  const res = await api.post<DocumentItem>("/api/documents/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export interface SimilarDoc {
  document_id: string;
  title: string;
  category: string | null;
  department: string | null;
  similarity: number;
  matched_page: number | null;
  snippet: string;
}

export interface ClusterMember { id: string; title: string; category: string | null; }
export interface Cluster {
  cluster_id: number;
  num_documents: number;
  dominant_terms: string[];
  documents: ClusterMember[];
}

export async function getSimilar(id: string, limit = 5) {
  const res = await api.get(`/api/documents/${id}/similar`, { params: { limit } });
  return res.data as { document: unknown; similar: SimilarDoc[] };
}

export async function getClusters() {
  const res = await api.get("/api/documents/cluster/all");
  return res.data as { clusters: Cluster[]; k?: number; docs_considered?: number; note?: string };
}


export interface PreviewChunk {
  chunk_index: number;
  page_number: number | null;
  text: string;
}

export interface PreviewResponse {
  document: DocumentItem;
  chunks: PreviewChunk[];
}

export async function previewDocument(id: string, chunks = 5): Promise<PreviewResponse> {
  const res = await api.get<PreviewResponse>(`/api/documents/${id}/preview`, {
    params: { chunks },
  });
  return res.data;
}

export async function reprocessDocument(id: string): Promise<{ document_id: string; chunks: number; status: string }> {
  const res = await api.post(`/api/documents/${id}/reprocess`);
  return res.data;
}

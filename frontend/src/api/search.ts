import { api } from "./client";

export interface SearchResult {
  chunk_id: string;
  document_id: string;
  document_title: string | null;
  chunk_index: number | null;
  page_number: number | null;
  text: string;
  category: string | null;
  department: string | null;
  score: number;
  rrf_score: number | null;
}

export interface SearchRequest {
  query: string;
  mode?: "vector" | "keyword" | "hybrid";
  limit?: number;
  offset?: number;
  category?: string;
  department?: string;
}

export interface SearchResponse {
  query: string;
  mode: string;
  count: number;
  offset: number;
  limit: number;
  latency_ms: number;
  results: SearchResult[];
}

export async function search(req: SearchRequest): Promise<SearchResponse> {
  const res = await api.post<SearchResponse>("/api/search", req);
  return res.data;
}

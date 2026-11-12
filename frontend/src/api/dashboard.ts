/**
 * Composite dashboard data fetch.
 * Runs all the small queries in parallel so the dashboard paints in one shot.
 */
import { api } from "./client";
import type { DocumentItem, DocumentListResponse } from "../types";
import type { UnansweredItem } from "./analytics";

export interface SearchHistoryRow {
  id: string;
  query: string;
  mode: string;
  result_count: number;
  latency_ms: number | null;
  created_at: string;
}

export interface ProcessingBreakdown {
  pending: number;
  processing: number;
  processed: number;
  failed: number;
  total: number;
}

export interface DashboardSnapshot {
  recent_docs: DocumentItem[];
  recent_searches: SearchHistoryRow[];
  processing: ProcessingBreakdown;
  failed_docs: DocumentItem[];
  unanswered: UnansweredItem[];
}

export async function fetchDashboard(): Promise<DashboardSnapshot> {
  const [docsRes, searchRes, unansweredRes] = await Promise.all([
    api.get<DocumentListResponse>("/api/documents", { params: { page: 1, limit: 100 } }),
    api
      .get<{ items: SearchHistoryRow[]; total: number }>("/api/search/history", {
        params: { page: 1, limit: 5 },
      })
      .catch(() => ({ data: { items: [], total: 0 } })),
    api
      .get<{ items: UnansweredItem[] }>("/api/analytics/unanswered-queries", {
        params: { limit: 5 },
      })
      .catch(() => ({ data: { items: [] } })),
  ]);

  const allDocs: DocumentItem[] = docsRes.data.items;
  const recent_docs = [...allDocs]
    .sort((a, b) => new Date(b.upload_date).getTime() - new Date(a.upload_date).getTime())
    .slice(0, 5);

  const processing: ProcessingBreakdown = {
    pending: 0,
    processing: 0,
    processed: 0,
    failed: 0,
    total: allDocs.length,
  };
  for (const d of allDocs) {
    if (d.processing_status in processing) {
      processing[d.processing_status] += 1;
    }
  }

  const failed_docs = allDocs.filter((d) => d.processing_status === "failed").slice(0, 5);

  return {
    recent_docs,
    recent_searches: searchRes.data.items,
    processing,
    failed_docs,
    unanswered: unansweredRes.data.items,
  };
}

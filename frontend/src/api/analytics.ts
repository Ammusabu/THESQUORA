import { api } from "./client";

export interface Overview {
  total_documents: number;
  total_chunks: number;
  total_searches: number;
  total_conversations: number;
  total_users: number;
}

export interface CategoryBucket { category: string; count: number; }

export interface SearchTrendPoint {
  date: string;
  count: number;
  avg_latency_ms: number | null;
}

export interface PopularDoc {
  document_id: string;
  title: string;
  category: string | null;
  search_count: number;
}

export interface UnansweredItem {
  query: string;
  times: number;
  last_seen: string;
}

export async function getOverview(): Promise<Overview> {
  const res = await api.get<Overview>("/api/analytics/overview");
  return res.data;
}

export async function getCategories(): Promise<CategoryBucket[]> {
  const res = await api.get<{ items: CategoryBucket[] }>("/api/analytics/categories");
  return res.data.items;
}

export async function getSearchTrends(days = 14): Promise<SearchTrendPoint[]> {
  const res = await api.get<{ items: SearchTrendPoint[] }>(
    "/api/analytics/search-trends", { params: { days } });
  return res.data.items;
}

export async function getPopularDocuments(limit = 10): Promise<PopularDoc[]> {
  const res = await api.get<{ items: PopularDoc[] }>(
    "/api/analytics/popular-documents", { params: { limit } });
  return res.data.items;
}

export async function getUnansweredQueries(limit = 10): Promise<UnansweredItem[]> {
  const res = await api.get<{ items: UnansweredItem[] }>(
    "/api/analytics/unanswered-queries", { params: { limit } });
  return res.data.items;
}

export async function getTopSearchedCategories(): Promise<CategoryBucket[]> {
  const res = await api.get<{ items: CategoryBucket[] }>(
    "/api/analytics/top-categories-searched");
  return res.data.items;
}

// ---------- Phase 12 extensions ----------
export interface CategoryPerformance {
  category: string;
  count: number;
  avg_confidence: number;
  min_confidence: number;
  max_confidence: number;
}

export interface ConfidenceBucket {
  bucket: string;
  count: number;
}

export interface TrainingMetrics {
  n_train: number | null;
  n_test: number | null;
  classes: string[];
  logreg_accuracy: number | null;
  logreg_macro_f1: number | null;
  nb_accuracy: number | null;
  nb_macro_f1: number | null;
}

export interface MLPerformance {
  categories: CategoryPerformance[];
  confidence_buckets: ConfidenceBucket[];
  training: TrainingMetrics | null;
}

export interface ModeStats {
  mode: string;
  count: number;
  avg_results: number;
  avg_latency_ms: number;
}

export interface SearchRelevance {
  total_searches: number;
  avg_results: number;
  avg_latency_ms: number;
  zero_result_rate: number;
  by_mode: ModeStats[];
}

export interface UnansweredTrendPoint {
  week: string;
  count: number;
  unique_queries: number;
}

export interface UsefulDoc {
  document_id: string;
  title: string;
  category: string | null;
  up: number;
  down: number;
  total: number;
  net_score: number;
}

export async function getMLPerformance(): Promise<MLPerformance> {
  const res = await api.get<MLPerformance>("/api/analytics/ml-performance");
  return res.data;
}

export async function getSearchRelevance(days = 30): Promise<SearchRelevance> {
  const res = await api.get<SearchRelevance>("/api/analytics/search-relevance", { params: { days } });
  return res.data;
}

export async function getUnansweredTrends(days = 60): Promise<UnansweredTrendPoint[]> {
  const res = await api.get<{ items: UnansweredTrendPoint[] }>("/api/analytics/unanswered-trends", { params: { days } });
  return res.data.items;
}

export async function getMostUsefulDocuments(limit = 10): Promise<UsefulDoc[]> {
  const res = await api.get<{ items: UsefulDoc[] }>("/api/analytics/most-useful-documents", { params: { limit } });
  return res.data.items;
}

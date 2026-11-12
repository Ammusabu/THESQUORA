import { useState } from "react";
import { Link } from "react-router-dom";
import { Search as SearchIcon, FileText, Sparkles } from "lucide-react";
import { search, type SearchResponse } from "../api/search";
import { getErrorMessage } from "../api/client";
import { useToast } from "../context/ToastContext";
import EmptyState from "../components/ui/EmptyState";
import Spinner from "../components/ui/Spinner";

const MODES: { key: "vector" | "keyword" | "hybrid"; label: string; hint: string }[] = [
  { key: "vector",  label: "Semantic", hint: "Meaning-based" },
  { key: "keyword", label: "Keyword",  hint: "Exact terms (BM25)" },
  { key: "hybrid",  label: "Hybrid",   hint: "RRF fusion" },
];

const CATEGORIES = ["", "HR", "Technical", "Finance", "Research", "Business", "Legal", "General"];

export default function Search() {
  const { push } = useToast();
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<"vector" | "keyword" | "hybrid">("hybrid");
  const [category, setCategory] = useState("");
  const [limit] = useState(10);
  const [offset, setOffset] = useState(0);
  const [res, setRes] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const runSearch = async (newOffset = 0) => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const data = await search({
        query: query.trim(),
        mode,
        limit,
        offset: newOffset,
        category: category || undefined,
      });
      setRes(data);
      setOffset(newOffset);
    } catch (err) {
      push("error", getErrorMessage(err, "Search failed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-1">Semantic Search</h1>
      <p className="text-slate-500 dark:text-slate-400 text-sm mb-6">
        Search across your documents by meaning, keyword, or a fusion of both.
      </p>

      <form
        onSubmit={(e) => { e.preventDefault(); runSearch(0); }}
        className="card p-4 space-y-3"
      >
        <div className="flex gap-2">
          <div className="relative flex-1">
            <SearchIcon className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              className="input pl-9"
              placeholder="Ask a question or search for terms..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <button type="submit" className="btn-primary" disabled={loading || !query.trim()}>
            {loading ? "Searching..." : "Search"}
          </button>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {MODES.map((m) => (
            <button
              key={m.key}
              type="button"
              onClick={() => setMode(m.key)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition ${
                mode === m.key
                  ? "bg-brand-50 border-brand-200 text-brand-700 dark:bg-brand-600/20 dark:border-brand-500/40 dark:text-brand-200"
                  : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-700"
              }`}
              title={m.hint}
            >
              {m.label}
            </button>
          ))}
          <select
            className="input max-w-[180px] ml-auto"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c || "All categories"}</option>
            ))}
          </select>
        </div>
      </form>

      {loading && <Spinner label="Searching..." />}

      {!loading && res && (
        <>
          <div className="mt-4 mb-3 flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400">
            <Sparkles className="w-4 h-4" />
            <span>
              {res.count} result{res.count === 1 ? "" : "s"} · {res.latency_ms}ms · mode: <strong>{res.mode}</strong>
            </span>
          </div>

          {res.results.length === 0 ? (
            <EmptyState
              icon={SearchIcon}
              title="No matches"
              description="Try a different query, mode, or remove filters."
            />
          ) : (
            <div className="space-y-3">
              {res.results.map((r) => (
                <div key={r.chunk_id} className="card p-4">
                  <div className="flex items-center justify-between mb-2">
                    <Link
                      to={`/documents/${r.document_id}`}
                      className="font-medium text-slate-900 dark:text-slate-100 hover:text-brand-600 dark:hover:text-brand-400 flex items-center gap-2"
                    >
                      <FileText className="w-4 h-4 text-slate-400" />
                      {r.document_title || "(unknown)"}
                      {r.page_number != null && (
                        <span className="text-xs text-slate-500 dark:text-slate-400">· page {r.page_number}</span>
                      )}
                    </Link>
                    <div className="flex items-center gap-2 text-xs">
                      {r.category && (
                        <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300">{r.category}</span>
                      )}
                      <span className="font-mono text-slate-500 dark:text-slate-400">
                        {r.rrf_score != null ? `rrf ${r.rrf_score.toFixed(4)}` : `score ${r.score.toFixed(4)}`}
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-slate-700 dark:text-slate-200 whitespace-pre-line">
                    {r.text.length > 400 ? r.text.slice(0, 400) + "..." : r.text}
                  </p>
                </div>
              ))}
            </div>
          )}

          {res.results.length > 0 && (
            <div className="flex items-center justify-center gap-2 mt-6">
              <button
                className="btn-secondary"
                disabled={offset === 0 || loading}
                onClick={() => runSearch(Math.max(0, offset - limit))}
              >
                Previous
              </button>
              <span className="text-sm text-slate-600 dark:text-slate-300">
                {offset + 1}–{offset + res.results.length}
              </span>
              <button
                className="btn-secondary"
                disabled={res.results.length < limit || loading}
                onClick={() => runSearch(offset + limit)}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}

      {!loading && !res && (
        <EmptyState
          icon={SearchIcon}
          title="Search your knowledge base"
          description="Type a question above. Hybrid mode combines semantic and keyword retrieval."
        />
      )}
    </div>
  );
}

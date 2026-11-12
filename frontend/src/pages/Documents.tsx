import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  FileText, Trash2, Upload, Filter, ArrowDownUp, Eye, RefreshCw,
  GitCompareArrows, X, Loader2,
} from "lucide-react";
import {
  listDocuments, deleteDocument, reprocessDocument,
} from "../api/documents";
import { getErrorMessage } from "../api/client";
import type { DocumentItem } from "../types";
import { useToast } from "../context/ToastContext";
import StatusBadge from "../components/ui/StatusBadge";
import EmptyState from "../components/ui/EmptyState";
import Spinner from "../components/ui/Spinner";
import ConfidenceBar from "../components/documents/ConfidenceBar";
import PreviewDrawer from "../components/documents/PreviewDrawer";
import CompareDialog from "../components/documents/CompareDialog";

const CATEGORIES = ["", "HR", "Technical", "Finance", "Research", "Business", "Legal", "General"];

type SortKey = "date" | "size" | "confidence";
type SortDir = "asc" | "desc";

export default function Documents() {
  const { push } = useToast();
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState("");
  const [page, setPage] = useState(1);
  const [sortKey, setSortKey] = useState<SortKey>("date");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const limit = 10;

  // Feature state
  const [previewId, setPreviewId] = useState<string | null>(null);
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [showCompare, setShowCompare] = useState(false);
  const [reprocessing, setReprocessing] = useState<string | null>(null);

  const fetchDocs = async () => {
    setLoading(true);
    try {
      // Fetch up to 100 for client-side sort to work correctly across the whole set
      const res = await listDocuments({ page: 1, limit: 100, category: category || undefined });
      setDocs(res.items);
      setTotal(res.total);
    } catch (err) {
      push("error", getErrorMessage(err, "Failed to load documents"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void fetchDocs(); /* eslint-disable-next-line */ }, [category]);

  const sorted = useMemo(() => {
    const arr = [...docs];
    const mul = sortDir === "asc" ? 1 : -1;
    arr.sort((a, b) => {
      if (sortKey === "date") {
        return (new Date(a.upload_date).getTime() - new Date(b.upload_date).getTime()) * mul;
      }
      if (sortKey === "size") {
        return (a.file_size - b.file_size) * mul;
      }
      // confidence — nulls last
      const av = a.classification_confidence ?? -1;
      const bv = b.classification_confidence ?? -1;
      return (av - bv) * mul;
    });
    return arr;
  }, [docs, sortKey, sortDir]);

  // Client-side pagination on the sorted list
  const totalPages = Math.max(1, Math.ceil(sorted.length / limit));
  const paginated = sorted.slice((page - 1) * limit, page * limit);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "desc" ? "asc" : "desc"));
    } else {
      setSortKey(key);
      setSortDir(key === "confidence" ? "desc" : "desc");
    }
    setPage(1);
  };

  const onDelete = async (id: string, title: string) => {
    if (!confirm(`Delete "${title}"? This cannot be undone.`)) return;
    try {
      await deleteDocument(id);
      push("success", "Document deleted");
      void fetchDocs();
    } catch (err) {
      push("error", getErrorMessage(err, "Delete failed"));
    }
  };

  const onReprocess = async (id: string, title: string) => {
    if (!confirm(`Re-run processing on "${title}"? This will re-extract, re-chunk and re-embed.`)) return;
    setReprocessing(id);
    try {
      const res = await reprocessDocument(id);
      push("success", `Reprocessed "${title}" — ${res.chunks} chunks`);
      void fetchDocs();
    } catch (err) {
      push("error", getErrorMessage(err, "Reprocess failed"));
    } finally {
      setReprocessing(null);
    }
  };

  const toggleCompare = (id: string) => {
    setCompareIds((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 2) return [prev[1], id]; // shift out oldest
      return [...prev, id];
    });
  };

  const sortLabel = (key: SortKey, label: string) => {
    const active = sortKey === key;
    return (
      <button
        onClick={() => toggleSort(key)}
        className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-md
          transition
          ${active
            ? "bg-brand-50 text-brand-700 dark:bg-brand-500/20 dark:text-brand-200"
            : "text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"}`}
      >
        {label}
        <ArrowDownUp className={`w-3 h-3 transition-transform ${active && sortDir === "asc" ? "rotate-180" : ""}`} />
      </button>
    );
  };

  return (
    <div className="max-w-6xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Document Library</h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            {total} document{total === 1 ? "" : "s"}
            {compareIds.length > 0 && ` · ${compareIds.length} selected for compare`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {compareIds.length === 2 && (
            <button onClick={() => setShowCompare(true)} className="btn-secondary">
              <GitCompareArrows className="w-4 h-4" /> Compare
            </button>
          )}
          {compareIds.length > 0 && (
            <button onClick={() => setCompareIds([])} className="btn-secondary">
              <X className="w-4 h-4" /> Clear selection
            </button>
          )}
          <Link to="/upload" className="btn-primary">
            <Upload className="w-4 h-4" /> Upload
          </Link>
        </div>
      </div>

      {/* Filter + sort bar */}
      <div className="card p-3 mb-4 flex items-center gap-3 flex-wrap">
        <Filter className="w-4 h-4 text-slate-500 dark:text-slate-400" />
        <select
          className="input max-w-xs"
          value={category}
          onChange={(e) => { setPage(1); setCategory(e.target.value); }}
        >
          {CATEGORIES.map((c) => <option key={c} value={c}>{c || "All categories"}</option>)}
        </select>

        <div className="ml-auto flex items-center gap-1">
          <span className="text-xs text-slate-500 dark:text-slate-400 mr-1">Sort by</span>
          {sortLabel("date", "Date")}
          {sortLabel("size", "Size")}
          {sortLabel("confidence", "Confidence")}
        </div>
      </div>

      {loading ? (
        <Spinner label="Loading documents..." />
      ) : sorted.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No documents yet"
          description="Upload your first PDF, DOCX, or TXT to get started."
          action={<Link to="/upload" className="btn-primary mt-2"><Upload className="w-4 h-4" /> Upload document</Link>}
        />
      ) : (
        <div className="card-table overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th className="text-left font-medium px-3 py-3 w-8"></th>
                <th className="text-left font-medium px-3 py-3">Title</th>
                <th className="text-left font-medium px-3 py-3">Category</th>
                <th className="text-left font-medium px-3 py-3 w-32">Confidence</th>
                <th className="text-left font-medium px-3 py-3">Status</th>
                <th className="text-right font-medium px-3 py-3">Chunks</th>
                <th className="text-right font-medium px-3 py-3">Size</th>
                <th className="text-right font-medium px-3 py-3">Uploaded</th>
                <th className="px-3 py-3 w-32"></th>
              </tr>
            </thead>
            <tbody>
              {paginated.map((d) => {
                const selected = compareIds.includes(d.id);
                return (
                  <tr key={d.id} className={selected ? "bg-brand-50/40 dark:bg-brand-500/10" : ""}>
                    <td className="px-3 py-3">
                      <input
                        type="checkbox"
                        checked={selected}
                        onChange={() => toggleCompare(d.id)}
                        className="w-4 h-4 rounded border-slate-300 accent-brand-600 dark:border-slate-600"
                        title="Select for compare"
                      />
                    </td>
                    <td className="px-3 py-3">
                      <Link
                        to={`/documents/${d.id}`}
                        className="font-medium text-slate-900 dark:text-slate-100 hover:text-brand-600 dark:hover:text-brand-400"
                      >
                        {d.title}
                      </Link>
                      <p className="text-xs text-slate-500 dark:text-slate-400">{d.filename}</p>
                    </td>
                    <td className="px-3 py-3">
                      {d.category ?? <span className="text-slate-400">—</span>}
                    </td>
                    <td className="px-3 py-3">
                      <ConfidenceBar value={d.classification_confidence} />
                    </td>
                    <td className="px-3 py-3"><StatusBadge status={d.processing_status} /></td>
                    <td className="px-3 py-3 text-right">{d.total_chunks}</td>
                    <td className="px-3 py-3 text-right">{(d.file_size / 1024).toFixed(1)} KB</td>
                    <td className="px-3 py-3 text-right text-slate-500 dark:text-slate-400 text-xs">
                      {new Date(d.upload_date).toLocaleDateString()}
                    </td>
                    <td className="px-3 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => setPreviewId(d.id)}
                          className="p-1.5 rounded-md text-slate-400 hover:text-brand-600 hover:bg-brand-50
                                     dark:text-slate-500 dark:hover:text-brand-300 dark:hover:bg-brand-500/10"
                          title="Preview"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => onReprocess(d.id, d.title)}
                          disabled={reprocessing === d.id}
                          className="p-1.5 rounded-md text-slate-400 hover:text-accent-600 hover:bg-accent-50
                                     dark:text-slate-500 dark:hover:text-accent-300 dark:hover:bg-accent-500/10
                                     disabled:opacity-40"
                          title="Reprocess"
                        >
                          {reprocessing === d.id
                            ? <Loader2 className="w-4 h-4 animate-spin" />
                            : <RefreshCw className="w-4 h-4" />}
                        </button>
                        <button
                          onClick={() => onDelete(d.id, d.title)}
                          className="p-1.5 rounded-md text-slate-400 hover:text-red-600 hover:bg-red-50
                                     dark:text-slate-500 dark:hover:text-red-400 dark:hover:bg-red-500/10"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-6">
          <button className="btn-secondary" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>Previous</button>
          <span className="text-sm text-slate-600 dark:text-slate-300">Page {page} of {totalPages}</span>
          <button className="btn-secondary" disabled={page === totalPages} onClick={() => setPage((p) => p + 1)}>Next</button>
        </div>
      )}

      {/* Overlays */}
      {previewId && <PreviewDrawer docId={previewId} onClose={() => setPreviewId(null)} />}
      {showCompare && compareIds.length === 2 && (
        <CompareDialog
          leftId={compareIds[0]}
          rightId={compareIds[1]}
          onClose={() => setShowCompare(false)}
        />
      )}
    </div>
  );
}

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  FileText, Layers, Search as SearchIcon, MessageSquare,
  Upload, ArrowRight, Clock, AlertCircle, CheckCircle2, XCircle,
  Loader2, TrendingUp, AlertTriangle,
} from "lucide-react";
import { getOverview, type Overview } from "../api/analytics";
import { fetchDashboard, type DashboardSnapshot } from "../api/dashboard";
import { useAuth } from "../context/AuthContext";
import Spinner from "../components/ui/Spinner";
import StatusBadge from "../components/ui/StatusBadge";

const CATEGORY_COLORS: Record<string, string> = {
  HR:        "bg-orange-50 text-orange-700 border border-orange-100 dark:bg-orange-500/15 dark:text-orange-200 dark:border-orange-500/20",
  Technical: "bg-orange-50 text-orange-700 border border-orange-100 dark:bg-orange-500/15 dark:text-orange-200 dark:border-orange-500/20",
  Finance:   "bg-orange-50 text-orange-700 border border-orange-100 dark:bg-orange-500/15 dark:text-orange-200 dark:border-orange-500/20",
  Research:  "bg-orange-50 text-orange-700 border border-orange-100 dark:bg-orange-500/15 dark:text-orange-200 dark:border-orange-500/20",
  Business:  "bg-orange-50 text-orange-700 border border-orange-100 dark:bg-orange-500/15 dark:text-orange-200 dark:border-orange-500/20",
  Legal:     "bg-slate-100 text-slate-700 border border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700",
  General:   "bg-slate-100 text-slate-700 border border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700",
};

function ProcessingBar({ breakdown }: { breakdown: DashboardSnapshot["processing"] }) {
  const total = Math.max(breakdown.total, 1);
  const segs = [
    { key: "processed",  n: breakdown.processed,  color: "bg-orange-500",  label: "Processed" },
    { key: "processing", n: breakdown.processing, color: "bg-orange-400",  label: "Processing" },
    { key: "pending",    n: breakdown.pending,    color: "bg-orange-300",  label: "Pending" },
    { key: "failed",     n: breakdown.failed,     color: "bg-rose-500",    label: "Failed" },
  ];
  return (
    <div className="space-y-3">
      {/* Slimmer 4px bar */}
      <div className="flex w-full h-1.5 rounded-full overflow-hidden bg-slate-100 dark:bg-slate-800">
        {segs.map((s) =>
          s.n > 0 ? (
            <div
              key={s.key}
              className={`${s.color} transition-all duration-500`}
              style={{ width: `${(s.n / total) * 100}%` }}
            />
          ) : null
        )}
      </div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
        {segs.map((s) => (
          <div key={s.key} className="flex items-center gap-2">
            <span className={`w-1.5 h-1.5 rounded-full ${s.color}`} />
            <span className="text-slate-500 dark:text-slate-400">{s.label}</span>
            <span className="ml-auto font-semibold text-slate-700 dark:text-slate-200 tabular-nums">
              {s.n}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const [overview, setOverview] = useState<Overview | null>(null);
  const [snapshot, setSnapshot] = useState<DashboardSnapshot | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [o, snap] = await Promise.all([getOverview(), fetchDashboard()]);
        setOverview(o);
        setSnapshot(snap);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <Spinner label="Loading dashboard..." />;
  if (!overview || !snapshot) return null;

  const kpis = [
    { label: "Documents",     value: overview.total_documents,     icon: FileText,      tile: "bg-orange-50 text-orange-600 dark:bg-orange-500/15 dark:text-orange-300" },
    { label: "Chunks",        value: overview.total_chunks,        icon: Layers,        tile: "bg-orange-50 text-orange-600 dark:bg-orange-500/15 dark:text-orange-300" },
    { label: "Searches",      value: overview.total_searches,      icon: SearchIcon,    tile: "bg-orange-50 text-orange-600 dark:bg-orange-500/15 dark:text-orange-300" },
    { label: "Conversations", value: overview.total_conversations, icon: MessageSquare, tile: "bg-orange-50 text-orange-600 dark:bg-orange-500/15 dark:text-orange-300" },
  ];

  const actionItems =
    snapshot.failed_docs.length + snapshot.unanswered.length +
    snapshot.processing.pending + snapshot.processing.processing;

  return (
    <div className="max-w-7xl mx-auto space-y-6
                    [&_.card]:rounded-2xl [&_.card]:border-slate-200/80 [&_.card]:shadow-[0_1px_2px_rgba(15,23,42,0.04)]
                    [&_.card]:transition-shadow [&_.card]:duration-200
                    [&_a:hover]:no-underline">

      {/* ---------- Page header ---------- */}
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider
                        text-orange-600 dark:text-orange-400 mb-1.5">
            Overview
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white leading-tight">
            Dashboard
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1.5">
            Welcome back{user?.name ? `, ${user.name.split(" ")[0]}` : ""} — here's your knowledge base at a glance.
          </p>
        </div>
        <Link
          to="/upload"
          className="btn-primary !rounded-xl !px-5 !py-2.5 !shadow-sm
                     hover:!bg-orange-600 hover:!shadow-md
                     transition-all duration-150
                     dark:hover:!bg-orange-500"
        >
          <Upload className="w-4 h-4" />
          Upload
        </Link>
      </div>

      {/* ---------- KPI cards ---------- */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map(({ label, value, icon: Icon, tile }) => (
          <div
            key={label}
            className="card p-5 group hover:shadow-[0_4px_12px_rgba(15,23,42,0.06)]
                       hover:-translate-y-0.5 transition-all duration-200"
          >
            <div
              className={`w-10 h-10 rounded-xl flex items-center justify-center mb-4
                          transition-transform duration-200 group-hover:scale-105 ${tile}`}
            >
              <Icon className="w-5 h-5" strokeWidth={2.25} />
            </div>
            <p className="text-[13px] font-medium text-slate-500 dark:text-slate-400">
              {label}
            </p>
            <p className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white mt-1 tabular-nums">
              {value}
            </p>
          </div>
        ))}
      </div>

      {/* ---------- Row: Recently uploaded + Processing status ---------- */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Recently uploaded */}
        <div className="card p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-orange-600 dark:text-orange-400" />
              <h2 className="text-base font-semibold text-slate-900 dark:text-white">
                Recently uploaded
              </h2>
            </div>
            <Link
              to="/documents"
              className="text-sm font-medium text-orange-600 dark:text-orange-400
                         hover:text-orange-700 dark:hover:text-orange-300
                         inline-flex items-center gap-1 transition-colors"
            >
              View all <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {snapshot.recent_docs.length === 0 ? (
            <div className="text-center py-10">
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-3">
                No documents yet.
              </p>
              <Link to="/upload" className="btn-secondary inline-flex">
                <Upload className="w-4 h-4" /> Upload your first document
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {snapshot.recent_docs.map((d) => (
                <Link
                  key={d.id}
                  to={`/documents/${d.id}`}
                  className="flex items-center gap-3 py-3 first:pt-0 last:pb-0 -mx-2 px-2
                             rounded-xl hover:bg-orange-50/60 dark:hover:bg-slate-800/40
                             transition-colors group"
                >
                  <div className="w-9 h-9 rounded-xl bg-orange-50 dark:bg-orange-500/15
                                  flex items-center justify-center shrink-0
                                  group-hover:bg-orange-100 dark:group-hover:bg-orange-500/20 transition-colors">
                    <FileText className="w-4 h-4 text-orange-600 dark:text-orange-300" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-slate-900 dark:text-slate-100 truncate">
                      {d.title}
                    </p>
                    <p className="text-[12px] text-slate-500 dark:text-slate-400 mt-0.5">
                      {d.total_chunks} chunk{d.total_chunks === 1 ? "" : "s"} ·{" "}
                      {(d.file_size / 1024).toFixed(0)} KB ·{" "}
                      {new Date(d.upload_date).toLocaleDateString(undefined, {
                        day: "numeric", month: "short", year: "numeric",
                      })}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {d.category && (
                      <span className={`text-[11px] px-2.5 py-0.5 rounded-full font-medium ${
                        CATEGORY_COLORS[d.category] ?? "bg-slate-100 text-slate-700 border border-slate-200"
                      }`}>
                        {d.category}
                      </span>
                    )}
                    <StatusBadge status={d.processing_status} />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Processing status */}
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-5">
            <Loader2 className="w-4 h-4 text-orange-600 dark:text-orange-400" />
            <h2 className="text-base font-semibold text-slate-900 dark:text-white">
              Processing status
            </h2>
          </div>

          {snapshot.processing.total === 0 ? (
            <p className="text-sm text-slate-500 dark:text-slate-400 py-6">
              No documents to report on yet.
            </p>
          ) : (
            <>
              <div className="mb-5">
                <p className="text-4xl font-bold tracking-tight text-slate-900 dark:text-white tabular-nums">
                  {snapshot.processing.processed}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  of {snapshot.processing.total} documents fully processed
                </p>
              </div>
              <ProcessingBar breakdown={snapshot.processing} />
            </>
          )}
        </div>
      </div>

      {/* ---------- Row: Recent searches + Knowledge gaps ---------- */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Recent searches */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <SearchIcon className="w-4 h-4 text-orange-600 dark:text-orange-400" />
              <h2 className="text-base font-semibold text-slate-900 dark:text-white">
                Recent searches
              </h2>
            </div>
            <Link
              to="/search"
              className="text-sm font-medium text-orange-600 dark:text-orange-400
                         hover:text-orange-700 dark:hover:text-orange-300
                         inline-flex items-center gap-1 transition-colors"
            >
              New search <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {snapshot.recent_searches.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-3">
                You haven't searched yet.
              </p>
              <Link to="/search" className="btn-secondary inline-flex">
                <SearchIcon className="w-4 h-4" /> Start searching
              </Link>
            </div>
          ) : (
            <ul className="divide-y divide-slate-100 dark:divide-slate-800">
              {snapshot.recent_searches.map((s) => (
                <li
                  key={s.id}
                  className="flex items-start gap-3 py-3 first:pt-0 last:pb-0"
                >
                  <div className="w-7 h-7 rounded-lg bg-orange-50 dark:bg-orange-500/15
                                  flex items-center justify-center shrink-0 mt-0.5">
                    <TrendingUp className="w-3.5 h-3.5 text-orange-600 dark:text-orange-300" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-slate-800 dark:text-slate-100 truncate">
                      {s.query}
                    </p>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                      <span className="capitalize font-medium">{s.mode}</span>
                      {" · "}{s.result_count} result{s.result_count === 1 ? "" : "s"}
                      {s.latency_ms != null && ` · ${s.latency_ms}ms`}
                    </p>
                  </div>
                  <span className="text-[11px] text-slate-400 dark:text-slate-500 shrink-0 tabular-nums">
                    {new Date(s.created_at).toLocaleTimeString([], {
                      hour: "2-digit", minute: "2-digit",
                    })}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Knowledge gaps */}
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-5">
            <AlertTriangle className="w-4 h-4 text-orange-600 dark:text-orange-400" />
            <h2 className="text-base font-semibold text-slate-900 dark:text-white">
              Needs attention
            </h2>
            {actionItems > 0 && (
              <span className="text-[11px] bg-orange-50 text-orange-700 border border-orange-100
                               dark:bg-orange-500/15 dark:text-orange-200 dark:border-orange-500/20
                               px-2 py-0.5 rounded-full font-semibold">
                {actionItems}
              </span>
            )}
          </div>

          {actionItems === 0 ? (
            <div className="text-center py-8">
              <div className="w-12 h-12 rounded-full bg-orange-50 dark:bg-orange-500/15
                              flex items-center justify-center mx-auto mb-3">
                <CheckCircle2 className="w-6 h-6 text-orange-600 dark:text-orange-300" />
              </div>
              <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">
                All clear
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-xs mx-auto">
                No failed documents, unanswered queries, or pending processing.
              </p>
            </div>
          ) : (
            <div className="space-y-5">
              {snapshot.failed_docs.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <XCircle className="w-3.5 h-3.5 text-rose-500" />
                    <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      Failed documents
                    </p>
                  </div>
                  <ul className="space-y-1.5 pl-5">
                    {snapshot.failed_docs.map((d) => (
                      <li key={d.id}>
                        <Link
                          to={`/documents/${d.id}`}
                          className="text-sm text-slate-700 dark:text-slate-200
                                     hover:text-orange-600 dark:hover:text-orange-300
                                     truncate block transition-colors"
                        >
                          {d.title}
                        </Link>
                        {d.error && (
                          <p className="text-[11px] text-rose-600 dark:text-rose-400 truncate">
                            {d.error}
                          </p>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {snapshot.processing.pending + snapshot.processing.processing > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Loader2 className="w-3.5 h-3.5 text-orange-500 animate-spin" />
                    <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      In progress
                    </p>
                  </div>
                  <p className="text-sm text-slate-600 dark:text-slate-300 pl-5">
                    {snapshot.processing.processing} processing ·{" "}
                    {snapshot.processing.pending} pending
                  </p>
                </div>
              )}

              {snapshot.unanswered.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <AlertCircle className="w-3.5 h-3.5 text-orange-500" />
                    <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      Unanswered searches
                    </p>
                  </div>
                  <ul className="space-y-1.5 pl-5">
                    {snapshot.unanswered.map((u, i) => (
                      <li
                        key={i}
                        className="text-sm text-slate-700 dark:text-slate-200 truncate"
                        title={u.query}
                      >
                        "{u.query}"
                        <span className="text-[11px] text-slate-400 dark:text-slate-500 ml-1.5">
                          ×{u.times}
                        </span>
                      </li>
                    ))}
                  </ul>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 pl-5 mt-2">
                    Consider uploading documents that cover these topics.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ---------- Quick action cards ---------- */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { to: "/upload",  icon: Upload,        title: "Upload documents", text: "PDF, DOCX, TXT — auto-classified and embedded." },
          { to: "/search",  icon: SearchIcon,    title: "Semantic search",  text: "Vector, keyword, or hybrid retrieval." },
          { to: "/chat",    icon: MessageSquare, title: "Ask questions",    text: "RAG answers with page-level citations." },
        ].map(({ to, icon: Icon, title, text }) => (
          <Link
            key={to}
            to={to}
            className="card p-5 hover:border-orange-200 hover:shadow-[0_4px_12px_rgba(15,23,42,0.06)]
                       hover:-translate-y-0.5 transition-all duration-200 group
                       dark:hover:border-orange-500/30"
          >
            <div className="w-10 h-10 rounded-xl bg-orange-50 dark:bg-orange-500/15
                            flex items-center justify-center mb-4
                            group-hover:bg-orange-100 dark:group-hover:bg-orange-500/20 transition-colors">
              <Icon className="w-5 h-5 text-orange-600 dark:text-orange-300" />
            </div>
            <p className="font-semibold text-slate-900 dark:text-white flex items-center gap-1">
              {title}
              <ArrowRight className="w-4 h-4 text-orange-500 transition-transform group-hover:translate-x-1" />
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1.5 leading-relaxed">
              {text}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}

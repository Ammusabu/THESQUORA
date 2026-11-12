import { useEffect, useState } from "react";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis,
  Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from "recharts";
import {
  FileText, Layers, Search as SearchIcon, MessageSquare, Users,
  TrendingUp, AlertCircle, Brain, Gauge, Target, ThumbsUp,
} from "lucide-react";
import {
  getCategories, getOverview, getPopularDocuments, getSearchTrends,
  getTopSearchedCategories, getUnansweredQueries,
  getMLPerformance, getSearchRelevance, getUnansweredTrends, getMostUsefulDocuments,
  type CategoryBucket, type Overview, type PopularDoc,
  type SearchTrendPoint, type UnansweredItem,
  type MLPerformance, type SearchRelevance, type UnansweredTrendPoint, type UsefulDoc,
} from "../api/analytics";
import { getClusters, type Cluster } from "../api/documents";
import { getErrorMessage } from "../api/client";
import { useToast } from "../context/ToastContext";
import Spinner from "../components/ui/Spinner";

const COLORS = ["#164E52", "#287C78", "#4D9C8F", "#D98D1C", "#2F7268", "#7BB5A9", "#94a3b8"];

export default function Analytics() {
  const { push } = useToast();

  const [overview, setOverview] = useState<Overview | null>(null);
  const [categories, setCategories] = useState<CategoryBucket[]>([]);
  const [trends, setTrends] = useState<SearchTrendPoint[]>([]);
  const [popular, setPopular] = useState<PopularDoc[]>([]);
  const [unanswered, setUnanswered] = useState<UnansweredItem[]>([]);
  const [topSearched, setTopSearched] = useState<CategoryBucket[]>([]);
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [clusterNote, setClusterNote] = useState("");

  const [ml, setMl] = useState<MLPerformance | null>(null);
  const [rel, setRel] = useState<SearchRelevance | null>(null);
  const [trendsUnans, setTrendsUnans] = useState<UnansweredTrendPoint[]>([]);
  const [useful, setUseful] = useState<UsefulDoc[]>([]);

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [o, c, t, p, u, ts, cl, m, r, tu, uf] = await Promise.all([
          getOverview(),
          getCategories(),
          getSearchTrends(14).catch(() => []),
          getPopularDocuments(5).catch(() => []),
          getUnansweredQueries(5).catch(() => []),
          getTopSearchedCategories().catch(() => []),
          getClusters().catch(() => ({ clusters: [], note: "" })),
          getMLPerformance().catch(() => null),
          getSearchRelevance(30).catch(() => null),
          getUnansweredTrends(60).catch(() => []),
          getMostUsefulDocuments(10).catch(() => []),
        ]);
        setOverview(o);
        setCategories(c);
        setTrends(t);
        setPopular(p);
        setUnanswered(u);
        setTopSearched(ts);
        setClusters((cl as { clusters?: Cluster[] }).clusters || []);
        setClusterNote((cl as { note?: string }).note || "");
        setMl(m);
        setRel(r);
        setTrendsUnans(tu);
        setUseful(uf);
      } catch (err) {
        push("error", getErrorMessage(err, "Failed to load analytics"));
      } finally {
        setLoading(false);
      }
    })();
  }, [push]);

  if (loading) return <Spinner label="Loading analytics..." />;
  if (!overview) return null;

  const cards = [
    { label: "Documents",     value: overview.total_documents,     icon: FileText,      tint: "bg-orange-50 text-orange-600 dark:bg-orange-500/15 dark:text-orange-300" },
    { label: "Chunks",        value: overview.total_chunks,        icon: Layers,        tint: "bg-orange-100 text-orange-600 dark:bg-orange-500/20 dark:text-orange-300" },
    { label: "Searches",      value: overview.total_searches,      icon: SearchIcon,    tint: "bg-orange-50 text-orange-700 dark:bg-orange-500/15 dark:text-orange-200" },
    { label: "Conversations", value: overview.total_conversations, icon: MessageSquare, tint: "bg-orange-100 text-orange-700 dark:bg-orange-500/20 dark:text-orange-200" },
    { label: "Users",         value: overview.total_users,         icon: Users,         tint: "bg-orange-50 text-orange-600 dark:bg-orange-500/15 dark:text-orange-300" },
  ];

  return (
    <div className="max-w-7xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-1">Analytics</h1>
        <p className="text-slate-500 dark:text-slate-400 text-sm">
          ML quality, search health, and content usefulness.
        </p>
      </div>

      {/* ---------- KPI cards ---------- */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {cards.map(({ label, value, icon: Icon, tint }) => (
          <div key={label} className="card p-4">
            <div className={`w-9 h-9 rounded-lg flex items-center justify-center mb-2 ${tint}`}>
              <Icon className="w-4 h-4" />
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">{label}</p>
            <p className="text-xl font-bold text-slate-900 dark:text-white">{value}</p>
          </div>
        ))}
      </div>

      {/* ---------- ML classification performance ---------- */}
      {ml && (
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Brain className="w-4 h-4 text-accent-500" />
            <h2 className="font-semibold text-slate-900 dark:text-white">ML classification performance</h2>
          </div>

          {ml.training && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
              <div className="rounded-lg p-3 bg-orange-50 dark:bg-orange-500/15">
                <p className="text-[11px] text-orange-700 dark:text-orange-300 uppercase tracking-wide font-semibold">
                  LogReg accuracy
                </p>
                <p className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                  {ml.training.logreg_accuracy != null ? `${(ml.training.logreg_accuracy * 100).toFixed(1)}%` : "—"}
                </p>
                <p className="text-[10px] text-slate-500 dark:text-slate-400">
                  macro F1: {ml.training.logreg_macro_f1 != null ? ml.training.logreg_macro_f1.toFixed(3) : "—"}
                </p>
              </div>
              <div className="rounded-lg p-3 bg-orange-100 dark:bg-orange-500/20">
                <p className="text-[11px] text-orange-700 dark:text-orange-200 uppercase tracking-wide font-semibold">
                  NB baseline
                </p>
                <p className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                  {ml.training.nb_accuracy != null ? `${(ml.training.nb_accuracy * 100).toFixed(1)}%` : "—"}
                </p>
                <p className="text-[10px] text-slate-500 dark:text-slate-400">
                  macro F1: {ml.training.nb_macro_f1 != null ? ml.training.nb_macro_f1.toFixed(3) : "—"}
                </p>
              </div>
              <div className="rounded-lg p-3 bg-slate-50 dark:bg-slate-800">
                <p className="text-[11px] text-slate-600 dark:text-slate-400 uppercase tracking-wide font-semibold">
                  Train / Test
                </p>
                <p className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                  {ml.training.n_train} / {ml.training.n_test}
                </p>
                <p className="text-[10px] text-slate-500 dark:text-slate-400">
                  {ml.training.classes.length} classes
                </p>
              </div>
              <div className="rounded-lg p-3 bg-orange-50 dark:bg-orange-500/15">
                <p className="text-[11px] text-orange-600 dark:text-orange-300 uppercase tracking-wide font-semibold">
                  Confidence buckets
                </p>
                <div className="mt-1 space-y-0.5">
                  {ml.confidence_buckets.map((b) => (
                    <p key={b.bucket} className="text-[11px] text-slate-700 dark:text-slate-300 flex justify-between">
                      <span>{b.bucket}</span>
                      <span className="font-semibold">{b.count}</span>
                    </p>
                  ))}
                </div>
              </div>
            </div>
          )}

          {ml.categories.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer>
                <BarChart data={ml.categories}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="category" tick={{ fontSize: 12 }} />
                  <YAxis yAxisId="left" tick={{ fontSize: 11 }} allowDecimals={false} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} domain={[0, 1]} />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="count" name="Documents" fill="#164E52" radius={[4, 4, 0, 0]} />
                  <Bar yAxisId="right" dataKey="avg_confidence" name="Avg confidence" fill="#287C78" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-sm text-slate-500 dark:text-slate-400">No classified documents yet.</p>
          )}
        </div>
      )}

      {/* ---------- Search relevance ---------- */}
      {rel && (
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Gauge className="w-4 h-4 text-brand-500" />
            <h2 className="font-semibold text-slate-900 dark:text-white">Search relevance (last 30 days)</h2>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <div className="rounded-lg p-3 bg-orange-50 dark:bg-orange-500/15">
              <p className="text-[11px] text-orange-700 dark:text-orange-300 uppercase tracking-wide font-semibold">Total searches</p>
              <p className="text-xl font-bold text-slate-900 dark:text-white mt-1">{rel.total_searches}</p>
            </div>
            <div className="rounded-lg p-3 bg-orange-50 dark:bg-orange-500/15">
              <p className="text-[11px] text-orange-600 dark:text-orange-300 uppercase tracking-wide font-semibold">Avg results/query</p>
              <p className="text-xl font-bold text-slate-900 dark:text-white mt-1">{rel.avg_results}</p>
            </div>
            <div className="rounded-lg p-3 bg-orange-100 dark:bg-orange-500/20">
              <p className="text-[11px] text-orange-700 dark:text-orange-200 uppercase tracking-wide font-semibold">Avg latency</p>
              <p className="text-xl font-bold text-slate-900 dark:text-white mt-1">{rel.avg_latency_ms}ms</p>
            </div>
            <div className="rounded-lg p-3 bg-orange-100 dark:bg-orange-500/20">
              <p className="text-[11px] text-orange-700 dark:text-orange-200 uppercase tracking-wide font-semibold">Zero-result rate</p>
              <p className="text-xl font-bold text-slate-900 dark:text-white mt-1">{rel.zero_result_rate}%</p>
            </div>
          </div>

          {rel.by_mode.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 dark:border-slate-800 text-slate-600 dark:text-slate-400">
                    <th className="text-left py-2 px-2 text-xs font-medium uppercase tracking-wide">Mode</th>
                    <th className="text-right py-2 px-2 text-xs font-medium uppercase tracking-wide">Searches</th>
                    <th className="text-right py-2 px-2 text-xs font-medium uppercase tracking-wide">Avg results</th>
                    <th className="text-right py-2 px-2 text-xs font-medium uppercase tracking-wide">Avg latency</th>
                  </tr>
                </thead>
                <tbody>
                  {rel.by_mode.map((m) => (
                    <tr key={m.mode} className="border-b border-slate-100 dark:border-slate-800 last:border-0">
                      <td className="py-2 px-2 capitalize text-slate-800 dark:text-slate-100">{m.mode}</td>
                      <td className="py-2 px-2 text-right text-slate-700 dark:text-slate-200">{m.count}</td>
                      <td className="py-2 px-2 text-right text-slate-700 dark:text-slate-200">{m.avg_results}</td>
                      <td className="py-2 px-2 text-right text-slate-700 dark:text-slate-200">{m.avg_latency_ms}ms</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ---------- Row: Category charts ---------- */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-5">
          <h2 className="font-semibold text-slate-900 dark:text-white mb-4">Chunks by category</h2>
          <div className="h-64">
            <ResponsiveContainer>
              <BarChart data={categories}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="category" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#164E52" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card p-5">
          <h2 className="font-semibold text-slate-900 dark:text-white mb-4">Category distribution</h2>
          <div className="h-64">
            <ResponsiveContainer>
              <PieChart>
                <Pie data={categories} dataKey="count" nameKey="category"
                     cx="50%" cy="50%" outerRadius={85} innerRadius={45} paddingAngle={2}>
                  {categories.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Legend /><Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* ---------- Search activity ---------- */}
      <div className="card p-5">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="w-4 h-4 text-brand-500" />
          <h2 className="font-semibold text-slate-900 dark:text-white">Search activity (last 14 days)</h2>
        </div>
        {trends.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">No searches yet.</p>
        ) : (
          <div className="h-64">
            <ResponsiveContainer>
              <LineChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#287C78" strokeWidth={2} dot={{ r: 3, fill: "#287C78" }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* ---------- Unanswered query trends ---------- */}
      <div className="card p-5">
        <div className="flex items-center gap-2 mb-4">
          <AlertCircle className="w-4 h-4 text-warn-500" />
          <h2 className="font-semibold text-slate-900 dark:text-white">Unanswered query trends (last 60 days, weekly)</h2>
        </div>
        {trendsUnans.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">No unanswered queries in the window.</p>
        ) : (
          <div className="h-64">
            <ResponsiveContainer>
              <BarChart data={trendsUnans}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="week" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" name="Zero-result searches" fill="#287C78" radius={[4, 4, 0, 0]} />
                <Bar dataKey="unique_queries" name="Unique queries" fill="#D98D1C" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* ---------- Most useful documents ---------- */}
      <div className="card p-5">
        <div className="flex items-center gap-2 mb-4">
          <ThumbsUp className="w-4 h-4 text-emerald-500" />
          <h2 className="font-semibold text-slate-900 dark:text-white">Most useful documents</h2>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400 mb-3">
          Ranked by thumbs-up minus thumbs-down on answers that cited them.
        </p>
        {useful.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">
            No feedback yet — thumbs-up/down on chat answers to populate this.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 dark:border-slate-800 text-slate-600 dark:text-slate-400">
                  <th className="text-left py-2 px-2 text-xs font-medium uppercase tracking-wide">Document</th>
                  <th className="text-right py-2 px-2 text-xs font-medium uppercase tracking-wide">👍</th>
                  <th className="text-right py-2 px-2 text-xs font-medium uppercase tracking-wide">👎</th>
                  <th className="text-right py-2 px-2 text-xs font-medium uppercase tracking-wide">Net score</th>
                </tr>
              </thead>
              <tbody>
                {useful.map((d) => (
                  <tr key={d.document_id} className="border-b border-slate-100 dark:border-slate-800 last:border-0">
                    <td className="py-2 px-2 text-slate-800 dark:text-slate-100 truncate max-w-[300px]">
                      {d.title}
                      {d.category && (
                        <span className="ml-2 text-xs text-slate-400 dark:text-slate-500">({d.category})</span>
                      )}
                    </td>
                    <td className="py-2 px-2 text-right text-emerald-600 dark:text-emerald-400">{d.up}</td>
                    <td className="py-2 px-2 text-right text-rose-600 dark:text-rose-400">{d.down}</td>
                    <td className="py-2 px-2 text-right font-semibold text-slate-900 dark:text-white">
                      {d.net_score > 0 ? `+${d.net_score}` : d.net_score}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ---------- Popular + Unanswered (live) ---------- */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-5">
          <h2 className="font-semibold text-slate-900 dark:text-white mb-3">Popular documents (by search hits)</h2>
          {popular.length === 0 ? (
            <p className="text-sm text-slate-500 dark:text-slate-400">Run some searches to populate this.</p>
          ) : (
            <ul className="space-y-2">
              {popular.map((d) => (
                <li key={d.document_id} className="flex items-center justify-between text-sm py-1.5 border-b border-slate-100 dark:border-slate-800 last:border-0">
                  <span className="truncate text-slate-800 dark:text-slate-100">{d.title}</span>
                  <span className="text-xs text-slate-500 dark:text-slate-400 ml-3">{d.search_count} hits</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-2 mb-3">
            <AlertCircle className="w-4 h-4 text-warn-500" />
            <h2 className="font-semibold text-slate-900 dark:text-white">Live unanswered queries</h2>
          </div>
          {unanswered.length === 0 ? (
            <p className="text-sm text-slate-500 dark:text-slate-400">None — nice!</p>
          ) : (
            <ul className="space-y-2">
              {unanswered.map((u, i) => (
                <li key={i} className="text-sm py-1.5 border-b border-slate-100 dark:border-slate-800 last:border-0">
                  <p className="text-slate-800 dark:text-slate-100 truncate">{u.query}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">×{u.times} · last {u.last_seen}</p>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* ---------- Top searched categories ---------- */}
      {topSearched.length > 0 && (
        <div className="card p-5">
          <h2 className="font-semibold text-slate-900 dark:text-white mb-3">Top searched categories</h2>
          <div className="h-56">
            <ResponsiveContainer>
              <BarChart data={topSearched} layout="vertical" margin={{ left: 30 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" tick={{ fontSize: 12 }} allowDecimals={false} />
                <YAxis dataKey="category" type="category" tick={{ fontSize: 12 }} width={110} />
                <Tooltip />
                <Bar dataKey="count" fill="#D98D1C" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* ---------- Cluster analysis ---------- */}
      <div className="card p-5">
        <div className="flex items-center gap-2 mb-1">
          <Target className="w-4 h-4 text-accent-500" />
          <h2 className="font-semibold text-slate-900 dark:text-white">Document similarity clusters</h2>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
          Documents grouped by topic similarity (KMeans on mean embeddings).
        </p>
        {clusters.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {clusterNote || "Not enough documents to cluster yet."}
          </p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {clusters.map((c) => (
              <div key={c.cluster_id} className="border border-slate-200 dark:border-slate-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-slate-900 dark:text-slate-100">Cluster {c.cluster_id}</span>
                  <span className="text-xs text-slate-500 dark:text-slate-400">{c.num_documents} doc(s)</span>
                </div>
                {c.dominant_terms.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-3">
                    {c.dominant_terms.slice(0, 5).map((t) => (
                      <span key={t} className="px-2 py-0.5 rounded-full bg-accent-50 text-accent-700 dark:bg-accent-500/20 dark:text-accent-200 text-xs">
                        {t}
                      </span>
                    ))}
                  </div>
                )}
                <ul className="text-sm text-slate-700 dark:text-slate-200 space-y-1">
                  {c.documents.map((d) => (
                    <li key={d.id} className="truncate">• {d.title}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

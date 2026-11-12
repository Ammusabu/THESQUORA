import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { X, FileText, Loader2 } from "lucide-react";
import { previewDocument, type PreviewResponse } from "../../api/documents";
import { getErrorMessage } from "../../api/client";
import StatusBadge from "../ui/StatusBadge";
import ConfidenceBar from "./ConfidenceBar";

interface Props {
  docId: string;
  onClose: () => void;
}

export default function PreviewDrawer({ docId, onClose }: Props) {
  const [data, setData] = useState<PreviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setData(await previewDocument(docId, 6));
      } catch (e) {
        setErr(getErrorMessage(e, "Failed to load preview"));
      } finally {
        setLoading(false);
      }
    })();
  }, [docId]);

  // Escape to close
  useEffect(() => {
    const h = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-40 flex justify-end" onClick={onClose}>
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />
      <aside
        className="relative w-full max-w-2xl h-full bg-white dark:bg-slate-900
                   border-l border-slate-200 dark:border-slate-800 shadow-2xl
                   flex flex-col animate-[slideIn_0.2s_ease-out]"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="h-16 shrink-0 px-5 flex items-center justify-between border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-2 min-w-0">
            <FileText className="w-5 h-5 text-brand-500 shrink-0" />
            <p className="font-semibold text-slate-900 dark:text-white truncate">
              {data?.document.title ?? "Loading…"}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-500 hover:bg-slate-100
                       dark:text-slate-400 dark:hover:bg-slate-800"
            aria-label="Close preview"
          >
            <X className="w-5 h-5" />
          </button>
        </header>

        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {loading && (
            <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 text-sm">
              <Loader2 className="w-4 h-4 animate-spin" /> Loading preview…
            </div>
          )}
          {err && (
            <div className="card p-4 border-l-4 border-l-red-500 text-red-700 dark:text-red-400 text-sm">
              {err}
            </div>
          )}

          {data && (
            <>
              {/* Metadata grid */}
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-slate-500 dark:text-slate-400">Category</p>
                  <p className="font-medium text-slate-900 dark:text-slate-100">
                    {data.document.category ?? "—"}
                  </p>
                </div>
                <div>
                  <p className="text-slate-500 dark:text-slate-400">Confidence</p>
                  <ConfidenceBar value={data.document.classification_confidence} />
                </div>
                <div>
                  <p className="text-slate-500 dark:text-slate-400">Chunks</p>
                  <p className="font-medium text-slate-900 dark:text-slate-100">{data.document.total_chunks}</p>
                </div>
                <div>
                  <p className="text-slate-500 dark:text-slate-400">Size</p>
                  <p className="font-medium text-slate-900 dark:text-slate-100">
                    {(data.document.file_size / 1024).toFixed(1)} KB
                  </p>
                </div>
                <div>
                  <p className="text-slate-500 dark:text-slate-400">Status</p>
                  <StatusBadge status={data.document.processing_status} />
                </div>
                <div>
                  <p className="text-slate-500 dark:text-slate-400">Uploaded</p>
                  <p className="font-medium text-slate-900 dark:text-slate-100">
                    {new Date(data.document.upload_date).toLocaleDateString()}
                  </p>
                </div>
              </div>

              {/* Chunk preview */}
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400 mb-2">
                  First {data.chunks.length} chunk{data.chunks.length === 1 ? "" : "s"}
                </p>
                <div className="space-y-2">
                  {data.chunks.length === 0 && (
                    <p className="text-sm text-slate-500 dark:text-slate-400">No chunks available.</p>
                  )}
                  {data.chunks.map((c) => (
                    <div
                      key={c.chunk_index}
                      className="border border-slate-100 dark:border-slate-800 rounded-lg p-3
                                 bg-slate-50 dark:bg-slate-800/50"
                    >
                      <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">
                        chunk #{c.chunk_index}
                        {c.page_number != null && ` · page ${c.page_number}`}
                      </p>
                      <p className="text-sm text-slate-700 dark:text-slate-200 whitespace-pre-line line-clamp-4">
                        {c.text}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>

        <footer className="p-4 border-t border-slate-200 dark:border-slate-800 flex justify-end">
          <Link
            to={`/documents/${docId}`}
            className="btn-secondary"
            onClick={onClose}
          >
            Open full detail
          </Link>
        </footer>
      </aside>

      <style>{`
        @keyframes slideIn {
          from { transform: translateX(40px); opacity: 0; }
          to   { transform: translateX(0); opacity: 1; }
        }
      `}</style>
    </div>
  );
}

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { X, Loader2, ArrowLeftRight } from "lucide-react";
import { previewDocument, type PreviewResponse } from "../../api/documents";
import { getErrorMessage } from "../../api/client";
import StatusBadge from "../ui/StatusBadge";
import ConfidenceBar from "./ConfidenceBar";

interface Props {
  leftId: string;
  rightId: string;
  onClose: () => void;
}

function Column({ data, side }: { data: PreviewResponse | null; side: "left" | "right" }) {
  if (!data) {
    return (
      <div className="flex-1 flex items-center justify-center text-slate-400 dark:text-slate-500">
        <Loader2 className="w-5 h-5 animate-spin" />
      </div>
    );
  }
  const d = data.document;
  return (
    <div className="flex-1 min-w-0 space-y-3">
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-1">
          {side === "left" ? "Left" : "Right"}
        </p>
        <Link
          to={`/documents/${d.id}`}
          className="font-semibold text-slate-900 dark:text-white hover:text-brand-600 truncate block"
        >
          {d.title}
        </Link>
        <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
          {d.filename} · {(d.file_size / 1024).toFixed(0)} KB
        </p>
      </div>
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div>
          <p className="text-slate-500 dark:text-slate-400 text-xs">Category</p>
          <p className="font-medium text-slate-900 dark:text-slate-100">{d.category ?? "—"}</p>
        </div>
        <div>
          <p className="text-slate-500 dark:text-slate-400 text-xs">Chunks</p>
          <p className="font-medium text-slate-900 dark:text-slate-100">{d.total_chunks}</p>
        </div>
        <div className="col-span-2">
          <p className="text-slate-500 dark:text-slate-400 text-xs">Confidence</p>
          <ConfidenceBar value={d.classification_confidence} />
        </div>
        <div className="col-span-2">
          <p className="text-slate-500 dark:text-slate-400 text-xs">Status</p>
          <StatusBadge status={d.processing_status} />
        </div>
      </div>
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400 mb-2">
          First {data.chunks.length} chunk{data.chunks.length === 1 ? "" : "s"}
        </p>
        <div className="space-y-2">
          {data.chunks.slice(0, 3).map((c) => (
            <div
              key={c.chunk_index}
              className="border border-slate-100 dark:border-slate-800 rounded-lg p-2
                         bg-slate-50 dark:bg-slate-800/50 text-xs
                         text-slate-700 dark:text-slate-200 whitespace-pre-line line-clamp-4"
            >
              <p className="text-[10px] text-slate-500 dark:text-slate-400 mb-1">
                #{c.chunk_index}{c.page_number != null && ` · p.${c.page_number}`}
              </p>
              {c.text}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function CompareDialog({ leftId, rightId, onClose }: Props) {
  const [left, setLeft] = useState<PreviewResponse | null>(null);
  const [right, setRight] = useState<PreviewResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [l, r] = await Promise.all([
          previewDocument(leftId, 3),
          previewDocument(rightId, 3),
        ]);
        setLeft(l);
        setRight(r);
      } catch (e) {
        setErr(getErrorMessage(e, "Failed to load"));
      }
    })();
  }, [leftId, rightId]);

  useEffect(() => {
    const h = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center p-4" onClick={onClose}>
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />
      <div
        className="relative w-full max-w-5xl max-h-[90vh] rounded-xl bg-white dark:bg-slate-900
                   border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="h-14 shrink-0 px-5 flex items-center justify-between border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <ArrowLeftRight className="w-5 h-5 text-brand-500" />
            <p className="font-semibold text-slate-900 dark:text-white">Compare documents</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-500 hover:bg-slate-100
                       dark:text-slate-400 dark:hover:bg-slate-800"
            aria-label="Close compare"
          >
            <X className="w-5 h-5" />
          </button>
        </header>

        <div className="flex-1 overflow-y-auto p-5">
          {err && (
            <div className="card p-4 border-l-4 border-l-red-500 text-red-700 dark:text-red-400 text-sm">
              {err}
            </div>
          )}
          <div className="flex gap-6">
            <Column data={left} side="left" />
            <div className="w-px bg-slate-200 dark:bg-slate-800" />
            <Column data={right} side="right" />
          </div>
        </div>
      </div>
    </div>
  );
}

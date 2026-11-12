import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { X, FileText, Loader2, ExternalLink } from "lucide-react";
import { previewDocument } from "../../api/documents";
import { getErrorMessage } from "../../api/client";
import type { SourceRef } from "../../api/chat";

interface Props {
  source: SourceRef;
  onClose: () => void;
}

export default function SourcePassageDialog({ source, onClose }: Props) {
  const [chunks, setChunks] = useState<{ chunk_index: number; page_number: number | null; text: string }[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await previewDocument(source.document_id, 20);
        // Show only the chunks around the cited one if possible, else all
        const cited = data.chunks.find((c) => c.chunk_index === source.chunk_index);
        if (cited) setChunks([cited]);
        else setChunks(data.chunks.slice(0, 3));
      } catch (e) {
        setErr(getErrorMessage(e, "Failed to load source"));
      }
    })();
  }, [source.document_id, source.chunk_index]);

  useEffect(() => {
    const h = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
      <div
        className="relative w-full max-w-2xl max-h-[85vh] rounded-xl bg-white dark:bg-slate-900
                   border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="h-14 shrink-0 px-5 flex items-center justify-between border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-2 min-w-0">
            <FileText className="w-5 h-5 text-brand-500 shrink-0" />
            <div className="min-w-0">
              <p className="font-semibold text-slate-900 dark:text-white truncate">{source.title}</p>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                {source.page_number != null ? `Page ${source.page_number}` : "Source passage"}
                {source.chunk_index != null ? ` · chunk #${source.chunk_index}` : ""}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-500 hover:bg-slate-100
                       dark:text-slate-400 dark:hover:bg-slate-800"
            aria-label="Close source"
          >
            <X className="w-5 h-5" />
          </button>
        </header>

        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {!chunks && !err && (
            <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 text-sm">
              <Loader2 className="w-4 h-4 animate-spin" /> Loading passage…
            </div>
          )}
          {err && (
            <div className="card p-4 border-l-4 border-l-red-500 text-red-700 dark:text-red-400 text-sm">
              {err}
            </div>
          )}
          {chunks?.map((c) => (
            <div
              key={c.chunk_index}
              className="rounded-lg p-4 bg-slate-50 dark:bg-slate-800/60
                         border border-slate-100 dark:border-slate-700"
            >
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">
                chunk #{c.chunk_index}
                {c.page_number != null && ` · page ${c.page_number}`}
              </p>
              <p className="text-sm text-slate-800 dark:text-slate-100 whitespace-pre-line leading-relaxed">
                {c.text}
              </p>
            </div>
          ))}
        </div>

        <footer className="p-3 border-t border-slate-200 dark:border-slate-800 flex justify-end">
          <Link
            to={`/documents/${source.document_id}`}
            onClick={onClose}
            className="btn-secondary"
          >
            <ExternalLink className="w-4 h-4" /> Open full document
          </Link>
        </footer>
      </div>
    </div>
  );
}

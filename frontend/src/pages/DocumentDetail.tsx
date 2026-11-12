import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { getDocument, getSimilar, type SimilarDoc } from "../api/documents";
import { getErrorMessage } from "../api/client";
import type { DocumentItem } from "../types";
import { useToast } from "../context/ToastContext";
import Spinner from "../components/ui/Spinner";
import StatusBadge from "../components/ui/StatusBadge";

export default function DocumentDetail() {
  const { id } = useParams<{ id: string }>();
  const { push } = useToast();
  const [doc, setDoc] = useState<DocumentItem | null>(null);
  const [similar, setSimilar] = useState<SimilarDoc[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    (async () => {
      try {
        const [d, s] = await Promise.all([
          getDocument(id),
          getSimilar(id).catch(() => ({ similar: [] })),
        ]);
        setDoc(d);
        setSimilar(s.similar);
      } catch (err) {
        push("error", getErrorMessage(err, "Failed to load document"));
      } finally {
        setLoading(false);
      }
    })();
  }, [id, push]);

  if (loading) return <Spinner label="Loading..." />;
  if (!doc) return <p className="text-slate-500 dark:text-slate-400">Not found.</p>;

  return (
    <div className="max-w-3xl">
      <Link to="/documents" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-brand-600 dark:text-slate-400 dark:hover:text-brand-400 mb-4">
        <ArrowLeft className="w-4 h-4" /> Back to library
      </Link>
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">{doc.title}</h1>
      <div className="flex items-center gap-3 mb-6">
        <StatusBadge status={doc.processing_status} />
        {doc.category && <span className="text-sm text-slate-600 dark:text-slate-300">Category: <strong>{doc.category}</strong></span>}
        {doc.classification_confidence != null && (
          <span className="text-sm text-slate-500 dark:text-slate-400">
            ({(doc.classification_confidence * 100).toFixed(0)}% confidence)
          </span>
        )}
      </div>

      <div className="card p-6 grid grid-cols-2 gap-4 text-sm text-slate-700 dark:text-slate-200">
        <div><p className="text-slate-500 dark:text-slate-400">Filename</p><p className="font-medium">{doc.filename}</p></div>
        <div><p className="text-slate-500 dark:text-slate-400">File type</p><p className="font-medium uppercase">{doc.file_type}</p></div>
        <div><p className="text-slate-500 dark:text-slate-400">Size</p><p className="font-medium">{(doc.file_size / 1024).toFixed(1)} KB</p></div>
        <div><p className="text-slate-500 dark:text-slate-400">Chunks</p><p className="font-medium">{doc.total_chunks}</p></div>
        <div><p className="text-slate-500 dark:text-slate-400">Department</p><p className="font-medium">{doc.department ?? "—"}</p></div>
        <div><p className="text-slate-500 dark:text-slate-400">Uploaded</p><p className="font-medium">{new Date(doc.upload_date).toLocaleString()}</p></div>
      </div>

      {doc.summary && (
        <div className="card p-6 mt-4">
          <h2 className="font-semibold text-slate-900 dark:text-white mb-2">Summary</h2>
          <p className="text-sm text-slate-700 dark:text-slate-200 whitespace-pre-line">{doc.summary}</p>
        </div>
      )}

      {doc.error && (
        <div className="card p-4 mt-4 border-l-4 border-l-red-500 text-sm text-red-700">
          Processing error: {doc.error}
        </div>
      )}
    
      <div className="card p-6 mt-4">
        <h2 className="font-semibold text-slate-900 dark:text-white mb-3">Similar documents</h2>
        {similar.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">No similar documents found.</p>
        ) : (
          <ul className="space-y-3">
            {similar.map((s) => (
              <li key={s.document_id} className="border border-slate-100 dark:border-slate-800 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <Link to={`/documents/${s.document_id}`} className="font-medium text-slate-900 dark:text-slate-100 hover:text-brand-600 dark:hover:text-brand-400">
                    {s.title}
                  </Link>
                  <span className="text-xs text-slate-500 dark:text-slate-400">similarity {s.similarity.toFixed(3)}</span>
                </div>
                {s.category && <p className="text-xs text-slate-500 mt-1">Category: {s.category}</p>}
                <p className="text-sm text-slate-600 dark:text-slate-300 mt-2 whitespace-pre-line line-clamp-3">
                  {s.snippet}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>
</div>
  );
}

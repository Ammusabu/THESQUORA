import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Upload as UploadIcon, FileText } from "lucide-react";
import { uploadDocument } from "../api/documents";
import { getErrorMessage } from "../api/client";
import { useToast } from "../context/ToastContext";

export default function Upload() {
  const { push } = useToast();
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [department, setDepartment] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) { push("error", "Choose a file first"); return; }
    setSubmitting(true);
    try {
      const doc = await uploadDocument({ file, title: title || undefined, department: department || undefined });
      push("success", `Uploaded "${doc.title}" — ${doc.total_chunks} chunk(s), category: ${doc.category ?? "General"}`);
      navigate("/documents");
    } catch (err) {
      push("error", getErrorMessage(err, "Upload failed"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-slate-900 mb-1">Upload Document</h1>
      <p className="text-slate-500 text-sm mb-6">PDF, DOCX, or TXT. Max 25 MB. Duplicate content is blocked.</p>

      <form onSubmit={onSubmit} className="card p-6 space-y-4">
        <div>
          <label className="label">File</label>
          <label className="flex flex-col items-center justify-center gap-2 border-2 border-dashed border-slate-300 rounded-lg p-8 cursor-pointer hover:border-brand-400 hover:bg-brand-50/40">
            <UploadIcon className="w-8 h-8 text-slate-400" />
            <span className="text-sm text-slate-600">
              {file ? file.name : "Click to choose a file"}
            </span>
            {file && <span className="text-xs text-slate-400">{(file.size / 1024).toFixed(1)} KB</span>}
            <input
              type="file" className="hidden" accept=".pdf,.docx,.txt"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </label>
        </div>
        <div>
          <label className="label">Title (optional)</label>
          <input className="input" value={title} onChange={(e) => setTitle(e.target.value)}
                 placeholder="Defaults to filename" />
        </div>
        <div>
          <label className="label">Department (optional)</label>
          <input className="input" value={department} onChange={(e) => setDepartment(e.target.value)}
                 placeholder="Engineering, HR, Finance..." />
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" className="btn-secondary" onClick={() => navigate("/documents")}>Cancel</button>
          <button type="submit" className="btn-primary" disabled={submitting || !file}>
            <FileText className="w-4 h-4" />
            {submitting ? "Uploading & processing..." : "Upload"}
          </button>
        </div>
      </form>
    </div>
  );
}

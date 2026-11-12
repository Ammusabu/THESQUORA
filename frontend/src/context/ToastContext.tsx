import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { CheckCircle2, AlertCircle, Info, X } from "lucide-react";

type ToastKind = "success" | "error" | "info";
interface Toast { id: number; kind: ToastKind; message: string; }

interface ToastState {
  push: (kind: ToastKind, message: string) => void;
}

const ToastContext = createContext<ToastState | undefined>(undefined);

let nextId = 1;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const push = useCallback((kind: ToastKind, message: string) => {
    const id = nextId++;
    setToasts((prev) => [...prev, { id, kind, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  }, []);

  const dismiss = (id: number) =>
    setToasts((prev) => prev.filter((t) => t.id !== id));

  const value = useMemo(() => ({ push }), [push]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 w-80">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`card p-3 flex items-start gap-2 shadow-lg border-l-4 ${
              t.kind === "success" ? "border-l-emerald-500" :
              t.kind === "error"   ? "border-l-red-500" :
                                     "border-l-brand-500"
            }`}
          >
            {t.kind === "success" && <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />}
            {t.kind === "error" && <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />}
            {t.kind === "info" && <Info className="w-5 h-5 text-brand-600 shrink-0" />}
            <p className="text-sm text-slate-800 flex-1">{t.message}</p>
            <button onClick={() => dismiss(t.id)} className="text-slate-400 hover:text-slate-600">
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used inside <ToastProvider>");
  return ctx;
}

import { Loader2 } from "lucide-react";

export default function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-16 text-slate-500">
      <Loader2 className="w-6 h-6 animate-spin" />
      {label && <p className="text-sm">{label}</p>}
    </div>
  );
}

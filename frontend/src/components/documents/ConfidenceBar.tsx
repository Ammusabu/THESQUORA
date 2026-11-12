export default function ConfidenceBar({ value }: { value: number | null }) {
  if (value == null) {
    return <span className="text-xs text-slate-400 dark:text-slate-500">—</span>;
  }
  const pct = Math.round(value * 100);
  const tone =
    pct >= 75 ? "bg-emerald-500"
    : pct >= 45 ? "bg-amber-500"
    : "bg-rose-500";
  return (
    <div className="flex items-center gap-2 min-w-[80px]">
      <div className="flex-1 h-1.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
        <div className={`h-full ${tone}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-medium text-slate-700 dark:text-slate-200 tabular-nums w-9 text-right">
        {pct}%
      </span>
    </div>
  );
}

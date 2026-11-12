import { useLocation } from "react-router-dom";
import { Sun, Sunrise, Moon } from "lucide-react";
import { useAuth } from "../../context/AuthContext";

const TITLES: Record<string, string> = {
  "/dashboard":  "Dashboard",
  "/documents":  "Documents",
  "/upload":     "Upload",
  "/search":     "Search",
  "/chat":       "AI Chat",
  "/analytics":  "Analytics",
  "/settings":   "Settings",
};

function titleFor(p: string): string {
  if (TITLES[p]) return TITLES[p];
  if (p.startsWith("/documents/")) return "Document Detail";
  return "THINKNOVA";
}

function greetingFor(hour: number): { text: string; Icon: typeof Sun } {
  if (hour < 5)  return { text: "Working late",      Icon: Moon };
  if (hour < 12) return { text: "Good morning",      Icon: Sunrise };
  if (hour < 17) return { text: "Good afternoon",    Icon: Sun };
  if (hour < 21) return { text: "Good evening",      Icon: Sun };
  return           { text: "Working late",      Icon: Moon };
}

function formatDate(d: Date): string {
  return d.toLocaleDateString(undefined, {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
}

export default function Topbar() {
  const { user } = useAuth();
  const location = useLocation();
  const title = titleFor(location.pathname);

  const now = new Date();
  const { text: greeting, Icon: GreetIcon } = greetingFor(now.getHours());
  const firstName = user?.name?.split(" ")[0] ?? "there";
  const dateLine = formatDate(now);

  return (
    <header className="h-16 shrink-0 border-b border-brand-100 bg-white
                       dark:bg-slate-900 dark:border-slate-800
                       flex items-center justify-between px-6 gap-4">
      {/* Left — page context */}
      <div className="min-w-0">
        <p className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-brand-500" />
          Workspace
        </p>
        <h1 className="text-sm font-semibold text-slate-900 dark:text-white truncate">
          {title}
        </h1>
      </div>

      {/* Right — greeting + date */}
      <div className="hidden sm:flex items-center gap-4 shrink-0">
        <div className="text-right">
          <p className="text-[11px] uppercase tracking-wider font-semibold
                        text-slate-400 dark:text-slate-500 flex items-center justify-end gap-1">
            <GreetIcon className="w-3 h-3" />
            {greeting}
          </p>
          <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 leading-tight">
            {firstName}
          </p>
        </div>
        <div className="w-px h-8 bg-brand-100 dark:bg-slate-700" />
        <div className="text-right">
          <p className="text-[11px] uppercase tracking-wider font-semibold
                        text-slate-400 dark:text-slate-500">
            Today
          </p>
          <p className="text-sm font-medium text-slate-700 dark:text-slate-300 leading-tight">
            {dateLine}
          </p>
        </div>
        <div className="relative shrink-0">
          <div className="w-9 h-9 rounded-full bg-brand-tile
                          flex items-center justify-center text-white text-xs font-bold shadow ring-2 ring-white dark:ring-slate-900">
            {(firstName[0] ?? "?").toUpperCase()}
          </div>
          <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-500
                           border-2 border-white dark:border-slate-900" title="Online" />
        </div>
      </div>
    </header>
  );
}

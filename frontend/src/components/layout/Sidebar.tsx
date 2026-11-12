import { useEffect, useRef, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, FileText, Upload, Search, MessageSquare,
  BarChart3, Settings as SettingsIcon, Orbit, LogOut,
  Sun, Moon, ChevronDown, User as UserIcon,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { useTheme } from "../../context/ThemeContext";

type NavItem = { to: string; label: string; icon: typeof LayoutDashboard };

const GROUPS: { label: string; items: NavItem[] }[] = [
  { label: "Workspace", items: [
    { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { to: "/documents", label: "Documents", icon: FileText },
    { to: "/upload",    label: "Upload",    icon: Upload },
  ]},
  { label: "Insights", items: [
    { to: "/search",    label: "Search",    icon: Search },
    { to: "/chat",      label: "AI Chat",   icon: MessageSquare },
    { to: "/analytics", label: "Analytics", icon: BarChart3 },
  ]},
  { label: "Account", items: [
    { to: "/settings", label: "Settings", icon: SettingsIcon },
  ]},
];

function initialsOf(name: string | undefined): string {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export default function Sidebar() {
  const { user, logout } = useAuth();
  const { theme, toggle } = useTheme();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (!menuRef.current?.contains(e.target as Node)) setMenuOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleLogout = () => { logout(); navigate("/login", { replace: true }); };

  return (
    <aside className="w-64 shrink-0 flex flex-col
                      bg-surface-warm border-r border-orange-100/70
                      dark:bg-slate-900 dark:border-slate-800">
      {/* ---------- Brand header — orange gradient tile ---------- */}
      <div className="h-16 flex items-center gap-3 px-4 border-b border-orange-100/70 dark:border-slate-800">
        <div className="relative shrink-0">
          <div className="absolute inset-0 rounded-xl blur-lg opacity-40 dark:opacity-20
                          bg-gradient-to-br from-orange-400 to-orange-600" />
          <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-orange-700
                          flex items-center justify-center shadow-lg ring-1 ring-white/30">
            <Orbit className="w-5 h-5 text-white" strokeWidth={2.5} />
          </div>
        </div>
        <div className="min-w-0">
          <p className="font-extrabold tracking-tight leading-none text-[15px]">
            <span className="bg-gradient-to-r from-orange-500 to-orange-700 bg-clip-text text-transparent">
              THINKNOVA
            </span>
          </p>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 truncate">
            Knowledge Orbit
          </p>
        </div>
      </div>

      {/* ---------- Navigation ---------- */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-5">
        {GROUPS.map((group) => (
          <div key={group.label}>
            <p className="px-3 mb-1.5 text-[10px] font-semibold uppercase tracking-wider
                          text-slate-400 dark:text-slate-500">
              {group.label}
            </p>
            <div className="space-y-1">
              {group.items.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) =>
                    `group relative flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all
                     ${isActive
                       ? "bg-orange-50 text-orange-700 dark:bg-orange-500/15 dark:text-orange-200"
                       : "text-slate-600 hover:bg-orange-50/60 hover:text-orange-700 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"}`
                  }
                >
                  {({ isActive }) => (
                    <>
                      <span className={`absolute left-0 top-1.5 bottom-1.5 w-0.5 rounded-full transition-all
                        ${isActive ? "bg-orange-500 opacity-100 dark:bg-orange-400" : "opacity-0 group-hover:opacity-40"}`}
                      />
                      <Icon className="w-4 h-4 shrink-0 transition-transform group-hover:scale-110" />
                      <span className="truncate">{label}</span>
                    </>
                  )}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* ---------- Footer ---------- */}
      <div className="border-t border-orange-100/70 dark:border-slate-800 p-3 space-y-2">
        <button
          onClick={toggle}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium
                     text-slate-600 hover:bg-orange-50 hover:text-orange-700
                     dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white transition"
          title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
        >
          <span className="relative w-4 h-4 shrink-0">
            <Sun className={`absolute inset-0 w-4 h-4 transition-all duration-300
              ${theme === "dark" ? "opacity-0 rotate-90 scale-50" : "opacity-100 rotate-0 scale-100"}`} />
            <Moon className={`absolute inset-0 w-4 h-4 transition-all duration-300
              ${theme === "dark" ? "opacity-100 rotate-0 scale-100" : "opacity-0 -rotate-90 scale-50"}`} />
          </span>
          <span>{theme === "dark" ? "Light mode" : "Dark mode"}</span>
        </button>

        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setMenuOpen((v) => !v)}
            className="w-full flex items-center gap-3 p-2 rounded-lg text-left
                       hover:bg-orange-50 dark:hover:bg-slate-800 transition"
          >
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-orange-500 to-orange-700
                            flex items-center justify-center text-white text-xs font-bold shrink-0 shadow">
              {initialsOf(user?.name)}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                {user?.name ?? "—"}
              </p>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 capitalize truncate">
                {user?.role ?? ""}{user?.department ? ` · ${user.department}` : ""}
              </p>
            </div>
            <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${menuOpen ? "rotate-180" : ""}`} />
          </button>

          {menuOpen && (
            <div className="absolute bottom-full left-0 right-0 mb-2 rounded-lg overflow-hidden
                            bg-white border border-orange-100 shadow-xl
                            dark:bg-slate-800 dark:border-slate-700">
              <button
                onClick={() => { setMenuOpen(false); navigate("/settings"); }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-700
                           hover:bg-orange-50 dark:text-slate-200 dark:hover:bg-slate-700"
              >
                <UserIcon className="w-4 h-4" /> Profile & Settings
              </button>
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600
                           hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/40"
              >
                <LogOut className="w-4 h-4" /> Log out
              </button>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}

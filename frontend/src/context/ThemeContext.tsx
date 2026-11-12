import {
  createContext, useCallback, useContext, useMemo, useState,
} from "react";
import type { ReactNode } from "react";

type Theme = "light" | "dark";
const KEY = "thesqora_theme";

function applyTheme(t: Theme) {
  const root = document.documentElement;
  if (t === "dark") root.classList.add("dark");
  else root.classList.remove("dark");
  root.style.colorScheme = t;
}

function readStoredTheme(): Theme {
  const v = localStorage.getItem(KEY);
  return v === "dark" ? "dark" : "light"; // default light
}

interface ThemeState {
  theme: Theme;
  toggle: () => void;
  setTheme: (t: Theme) => void;
}

const ThemeContext = createContext<ThemeState | undefined>(undefined);

// Apply once at module load — before React even renders.
// This is safe because it only touches document.documentElement.
applyTheme(readStoredTheme());

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(readStoredTheme);

  const setTheme = useCallback((t: Theme) => {
    applyTheme(t);                                  // 1. flip DOM synchronously
    try { localStorage.setItem(KEY, t); } catch {}  // 2. persist
    setThemeState(t);                               // 3. update React
  }, []);

  const toggle = useCallback(() => {
    // Read from DOM — the DOM is authoritative
    const next: Theme = document.documentElement.classList.contains("dark")
      ? "light"
      : "dark";
    setTheme(next);
  }, [setTheme]);

  const value = useMemo(() => ({ theme, toggle, setTheme }), [theme, toggle, setTheme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used inside <ThemeProvider>");
  return ctx;
}

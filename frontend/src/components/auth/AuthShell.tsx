import { Link } from "react-router-dom";
import type { ReactNode } from "react";
import { Orbit, FileText, Search, MessageSquare, Sparkles } from "lucide-react";

const HIGHLIGHTS = [
  { icon: FileText,     title: "Ingest PDFs, DOCX, TXT",     text: "Auto-classified and chunked with embeddings." },
  { icon: Search,       title: "Vector + keyword + hybrid",  text: "Three retrieval modes, one API." },
  { icon: MessageSquare, title: "Grounded AI chat",          text: "Every answer cites its source page." },
];

interface Props {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer?: ReactNode;
}

export default function AuthShell({ title, subtitle, children, footer }: Props) {
  return (
    <div className="min-h-screen grid lg:grid-cols-5 bg-surface-warm dark:bg-slate-950">
      {/* ---------- LEFT: orange branded hero ---------- */}
      <div className="hidden lg:flex lg:col-span-3 relative overflow-hidden
                      bg-gradient-to-br from-orange-400 via-orange-500 to-orange-700
                      dark:from-slate-900 dark:via-slate-900 dark:to-slate-900">
        <div className="absolute -top-40 -left-40 w-96 h-96 rounded-full bg-white/15 blur-3xl" />
        <div className="absolute -bottom-40 -right-40 w-[28rem] h-[28rem] rounded-full bg-white/10 blur-3xl" />
        <div
          className="absolute inset-0 opacity-[0.08] pointer-events-none"
          style={{
            backgroundImage: "radial-gradient(circle at 1px 1px, white 1px, transparent 0)",
            backgroundSize: "22px 22px",
          }}
        />

        <div className="relative z-10 flex flex-col justify-between p-12 w-full">
          <Link to="/login" className="flex items-center gap-3 w-fit">
            <div className="w-11 h-11 rounded-xl bg-white/15 backdrop-blur ring-1 ring-white/30
                            flex items-center justify-center shadow-xl">
              <Orbit className="w-6 h-6 text-white" strokeWidth={2.5} />
            </div>
            <div>
              <p className="font-extrabold tracking-tight text-white leading-none text-lg">
                THESQUORA
              </p>
              <p className="text-[11px] text-white/80 mt-1">Knowledge Orbit</p>
            </div>
          </Link>

          <div className="max-w-lg">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full
                             bg-white/15 backdrop-blur text-white/90 text-xs font-medium
                             ring-1 ring-white/20 mb-5">
              <Sparkles className="w-3 h-3" />
              Enterprise knowledge intelligence
            </span>
            <h1 className="text-4xl font-extrabold text-white leading-tight tracking-tight">
              Ask your documents.
              <br />
              <span className="text-white/85">Get cited answers.</span>
            </h1>
            <p className="mt-4 text-white/80 text-sm leading-relaxed">
              THESQUORA turns your internal PDFs, handbooks and research into a
              permission-aware search & chat layer — powered by MongoDB Atlas
              Vector Search and grounded LLM responses.
            </p>
          </div>

          <div className="space-y-3 max-w-lg">
            {HIGHLIGHTS.map(({ icon: Icon, title: t, text }) => (
              <div key={t} className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-white/15 backdrop-blur
                                flex items-center justify-center ring-1 ring-white/20 shrink-0">
                  <Icon className="w-4 h-4 text-white" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">{t}</p>
                  <p className="text-xs text-white/70">{text}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ---------- RIGHT: auth form ---------- */}
      <div className="lg:col-span-2 flex items-center justify-center p-6 sm:p-10">
        <div className="w-full max-w-md">
          {/* Mobile brand strip — orange */}
          <div className="lg:hidden mb-8 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-orange-700
                            flex items-center justify-center shadow-lg ring-1 ring-white/30">
              <Orbit className="w-5 h-5 text-white" strokeWidth={2.5} />
            </div>
            <div>
              <p className="font-extrabold tracking-tight text-[15px]">
                <span className="bg-gradient-to-r from-orange-500 to-orange-700 bg-clip-text text-transparent">
                  THESQUORA
                </span>
              </p>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                Knowledge Orbit
              </p>
            </div>
          </div>

          <div className="card p-8 shadow-md">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-1">
              {title}
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">{subtitle}</p>
            {children}
            {footer && <div className="mt-6 text-center">{footer}</div>}
          </div>

          <p className="text-center text-xs text-slate-400 dark:text-slate-500 mt-6">
            © {new Date().getFullYear()} THESQUORA · All rights reserved
          </p>
        </div>
      </div>
    </div>
  );
}

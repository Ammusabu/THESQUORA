import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Mail, Lock, Eye, EyeOff, LogIn, User as UserIcon, Sparkles } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { getErrorMessage } from "../api/client";
import AuthShell from "../components/auth/AuthShell";

export default function Login() {
  const { login } = useAuth();
  const { push } = useToast();
  const navigate = useNavigate();
  const location = useLocation() as { state?: { from?: { pathname: string } } };
  const from = location.state?.from?.pathname || "/dashboard";

  const [email, setEmail] = useState(localStorage.getItem("thesqora_last_email") ?? "");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await login(email, password);
      localStorage.setItem("thesqora_last_email", email);
      push("success", "Welcome back");
      navigate(from, { replace: true });
    } catch (err) {
      push("error", getErrorMessage(err, "Login failed"));
    } finally {
      setSubmitting(false);
    }
  };

  const fillDemo = () => {
    setEmail("amrita@thesqora.local");
    setPassword("SecurePass123");
  };

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Sign in to your organisation's knowledge workspace."
      footer={
        <p className="text-sm text-slate-500 dark:text-slate-400">
          New here?{" "}
          <Link to="/register" className="text-brand-600 dark:text-brand-400 hover:underline font-semibold">
            Create an account
          </Link>
        </p>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4" autoComplete="on">
        <div>
          <label className="label">Email address</label>
          <div className="relative">
            <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
            <input
              className="input pl-9"
              type="email"
              required
              autoComplete="email"
              placeholder="you@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="label mb-0">Password</label>
            <button
              type="button"
              className="text-xs text-brand-600 dark:text-brand-400 hover:underline"
              onClick={() => push("info", "Password reset is not enabled in this demo.")}
            >
              Forgot password?
            </button>
          </div>
          <div className="relative">
            <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
            <input
              className="input pl-9 pr-10"
              type={showPw ? "text" : "password"}
              required
              autoComplete="current-password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <button
              type="button"
              onClick={() => setShowPw((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              aria-label={showPw ? "Hide password" : "Show password"}
            >
              {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        <button type="submit" className="btn-primary w-full !py-2.5" disabled={submitting}>
          <LogIn className="w-4 h-4" />
          {submitting ? "Signing in..." : "Sign in"}
        </button>

        <div className="relative py-2">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-slate-200 dark:border-slate-700" />
          </div>
          <div className="relative flex justify-center">
            <span className="px-3 bg-white dark:bg-slate-900 text-xs text-slate-400 dark:text-slate-500">
              or
            </span>
          </div>
        </div>

        <button
          type="button"
          onClick={fillDemo}
          className="btn-secondary w-full !py-2.5"
        >
          <Sparkles className="w-4 h-4 text-brand-600 dark:text-brand-400" />
          Use demo account
        </button>
      </form>
    </AuthShell>
  );
}

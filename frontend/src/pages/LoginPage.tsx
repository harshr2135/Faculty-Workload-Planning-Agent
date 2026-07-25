import { type FormEvent, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { demoCredentials, useAuth } from "@/auth/AuthContext";
import { IconSpark } from "@/components/ui/icons";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from =
    (location.state as { from?: string } | null)?.from &&
    (location.state as { from?: string }).from !== "/login"
      ? (location.state as { from: string }).from
      : "/";

  const [email, setEmail] = useState(demoCredentials.email);
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="relative flex min-h-screen overflow-hidden bg-[#071018] text-slate-100">
      <div
        className="pointer-events-none absolute inset-0 opacity-90"
        aria-hidden
        style={{
          backgroundImage: `
            radial-gradient(ellipse 70% 55% at 15% 20%, rgba(16, 185, 129, 0.28), transparent 55%),
            radial-gradient(ellipse 50% 45% at 85% 80%, rgba(14, 165, 233, 0.12), transparent 50%),
            linear-gradient(160deg, #071018 0%, #0b1220 45%, #0f1c24 100%)
          `,
        }}
      />
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.035]"
        aria-hidden
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")",
        }}
      />

      <div className="relative z-10 mx-auto flex w-full max-w-6xl flex-col justify-center gap-12 px-6 py-12 lg:flex-row lg:items-center lg:gap-20 lg:px-10">
        <section className="login-reveal max-w-xl flex-1">
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald-400">
            NVIDIA Capstone · AI&amp;ML
          </p>
          <h1 className="mt-5 text-4xl font-semibold tracking-tight text-white sm:text-5xl sm:leading-[1.08]">
            Workload Planner
          </h1>
          <p className="mt-4 max-w-md text-base leading-relaxed text-slate-300">
            Sign in to allocate teaching load, build clash-free timetables, and generate
            explainable department reports.
          </p>
          <ul className="mt-8 space-y-3 text-sm text-slate-400">
            <li className="flex items-start gap-2.5">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400" />
              Deterministic CP-SAT optimization — not a chatbot inventing allocations
            </li>
            <li className="flex items-start gap-2.5">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400" />
              AICTE-aware policies with grounded, HOD-ready explanations
            </li>
          </ul>
        </section>

        <section className="login-reveal-delay w-full max-w-md flex-1">
          <form
            onSubmit={handleSubmit}
            className="rounded-3xl border border-white/10 bg-white/[0.04] p-7 shadow-2xl shadow-black/30 backdrop-blur-md sm:p-8"
          >
            <div className="mb-6 flex items-center gap-3">
              <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-500/15 ring-1 ring-emerald-400/30">
                <IconSpark className="h-5 w-5 text-emerald-300" />
              </span>
              <div>
                <h2 className="text-lg font-semibold tracking-tight text-white">Sign in</h2>
                <p className="text-xs text-slate-400">Department administrator access</p>
              </div>
            </div>

            <label className="block text-sm text-slate-300">
              Email
              <input
                type="email"
                autoComplete="username"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1.5 w-full rounded-xl border border-white/10 bg-slate-950/50 px-3.5 py-2.5 text-sm text-white outline-none ring-emerald-500/0 transition placeholder:text-slate-500 focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/25"
                placeholder="hod@aiml.edu"
              />
            </label>

            <label className="mt-4 block text-sm text-slate-300">
              Password
              <div className="relative mt-1.5">
                <input
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-xl border border-white/10 bg-slate-950/50 px-3.5 py-2.5 pr-20 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/25"
                  placeholder="Enter password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute inset-y-0 right-2 my-auto rounded-lg px-2 text-xs font-medium text-slate-400 transition hover:text-white"
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </label>

            {error && (
              <p className="mt-4 rounded-xl border border-red-400/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="mt-6 flex w-full items-center justify-center rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {submitting ? "Signing in…" : "Continue to planner"}
            </button>

            <p className="mt-5 rounded-xl border border-white/5 bg-black/20 px-3 py-2.5 text-[11px] leading-relaxed text-slate-400">
              Demo credentials:{" "}
              <span className="font-medium text-slate-200">{demoCredentials.email}</span> /{" "}
              <span className="font-medium text-slate-200">{demoCredentials.password}</span>
            </p>
          </form>
        </section>
      </div>
    </div>
  );
}

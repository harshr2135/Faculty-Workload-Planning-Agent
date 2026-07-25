import { useLocation } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";

const PAGE_META: Record<string, { title: string; subtitle: string }> = {
  "/": {
    title: "Dashboard",
    subtitle: "Department planning overview",
  },
  "/faculty": {
    title: "Faculty",
    subtitle: "Roster, designations & specializations",
  },
  "/courses": {
    title: "Courses",
    subtitle: "Subjects by batch and semester",
  },
  "/classrooms": {
    title: "Rooms",
    subtitle: "Classrooms and lecture halls",
  },
  "/laboratories": {
    title: "Laboratories",
    subtitle: "Lab rooms for practical sessions",
  },
  "/timetable": {
    title: "Time slots",
    subtitle: "Daily teaching periods and breaks",
  },
  "/allocations": {
    title: "Allocation",
    subtitle: "Run, review, and save workload plans",
  },
  "/policies": {
    title: "Policies",
    subtitle: "AICTE limits and planning rules",
  },
};

export function Header() {
  const { pathname } = useLocation();
  const { user, logout } = useAuth();
  const meta = PAGE_META[pathname] ?? {
    title: "Workload Planner",
    subtitle: "Faculty workload planning & allocation",
  };

  return (
    <header className="shrink-0 border-b border-slate-200/80 bg-white/80 px-4 py-3.5 backdrop-blur-md sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold tracking-tight text-slate-900">{meta.title}</p>
          <p className="mt-0.5 truncate text-xs text-slate-500">{meta.subtitle}</p>
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <div className="hidden text-right sm:block">
            <p className="text-xs font-medium text-slate-700">
              {user?.displayName ?? "Department Administrator"}
            </p>
            <p className="text-[11px] text-slate-400">{user?.email ?? "Signed in locally"}</p>
          </div>
          <div className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold tracking-wide text-emerald-700 ring-1 ring-emerald-200/80">
            {user?.department ?? "AIML"}
          </div>
          <button
            type="button"
            onClick={logout}
            className="rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900"
          >
            Sign out
          </button>
        </div>
      </div>
    </header>
  );
}

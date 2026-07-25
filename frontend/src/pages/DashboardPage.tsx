import { Link } from "react-router-dom";
import { fetchAllocationRuns } from "@/api/allocations";
import { fetchCourses } from "@/api/courses";
import { fetchFaculty } from "@/api/faculty";
import { fetchClassrooms, fetchLaboratories } from "@/api/rooms";
import { PageHeader } from "@/components/ui/PageHeader";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Badge } from "@/components/ui/Badge";
import {
  IconArrowRight,
  IconBook,
  IconBuilding,
  IconCheck,
  IconClock,
  IconFlask,
  IconShield,
  IconSpark,
  IconUsers,
} from "@/components/ui/icons";
import { useFetch } from "@/hooks/useFetch";

function StatCard({
  label,
  value,
  to,
  hint,
  icon: Icon,
}: {
  label: string;
  value: number | string;
  to: string;
  hint: string;
  icon: typeof IconUsers;
}) {
  return (
    <Link
      to={to}
      className="group ui-card relative overflow-hidden p-5 transition duration-200 hover:-translate-y-0.5 hover:border-emerald-300 hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <p className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">{value}</p>
        </div>
        <span className="rounded-xl bg-emerald-50 p-2.5 text-emerald-700 ring-1 ring-emerald-100 transition group-hover:bg-emerald-100">
          <Icon className="h-4 w-4" />
        </span>
      </div>
      <p className="mt-4 flex items-center gap-1 text-xs font-medium text-emerald-700">
        {hint}
        <IconArrowRight className="h-3.5 w-3.5 transition group-hover:translate-x-0.5" />
      </p>
    </Link>
  );
}

const workflow = [
  {
    step: "01",
    title: "Master data",
    body: "Faculty, courses, rooms, and labs are loaded for the department.",
    to: "/faculty",
  },
  {
    step: "02",
    title: "Policies",
    body: "AICTE hour caps and lab rules guide the solver as soft targets.",
    to: "/policies",
  },
  {
    step: "03",
    title: "Allocate",
    body: "CP-SAT assigns teaching load and builds clash-free timetables.",
    to: "/allocations",
  },
  {
    step: "04",
    title: "Explain",
    body: "Generate grounded reports for HOD review and approval.",
    to: "/allocations",
  },
];

function formatWhen(value: string | null): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return value;
  }
}

function statusVariant(status: string): "success" | "warning" | "default" {
  if (status === "optimal" || status === "feasible") return "success";
  if (status === "infeasible" || status === "error") return "warning";
  return "default";
}

export default function DashboardPage() {
  const faculty = useFetch(fetchFaculty);
  const courses = useFetch(fetchCourses);
  const classrooms = useFetch(fetchClassrooms);
  const laboratories = useFetch(fetchLaboratories);
  const runs = useFetch(fetchAllocationRuns);

  const loading =
    faculty.loading ||
    courses.loading ||
    classrooms.loading ||
    laboratories.loading ||
    runs.loading;
  const error =
    faculty.error || courses.error || classrooms.error || laboratories.error || runs.error;

  if (loading) return <LoadingState message="Loading dashboard..." />;
  if (error) {
    return (
      <>
        <PageHeader title="Dashboard" description="AIML department planning overview" />
        <ErrorState
          message={error}
          onRetry={() => {
            faculty.reload();
            courses.reload();
            classrooms.reload();
            laboratories.reload();
            runs.reload();
          }}
        />
      </>
    );
  }

  const recentRuns = (runs.data ?? []).slice(0, 5);
  const savedCount = (runs.data ?? []).filter((run) => run.is_saved).length;

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="AIML master data, recent plans, and the path from roster to report"
        action={
          <Link to="/allocations" className="ui-btn-accent">
            <IconSpark className="h-4 w-4" />
            Run allocation
          </Link>
        }
      />

      <section className="ui-section relative mb-6 overflow-hidden">
        <div
          className="pointer-events-none absolute inset-y-0 right-0 w-1/2 bg-[radial-gradient(ellipse_at_top_right,rgba(16,185,129,0.14),transparent_60%)]"
          aria-hidden
        />
        <div className="relative flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-2xl">
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-emerald-700">
              Faculty Workload Planning Agent
            </p>
            <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-900 sm:text-2xl">
              Plan teaching load with constraints you can trust
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-500">
              Optimization decides who teaches what and when. The AI layer only explains results —
              never invents allocations.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
              <IconCheck className="h-3.5 w-3.5 text-emerald-600" />
              {(runs.data ?? []).length} runs
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-800 ring-1 ring-emerald-100">
              <IconShield className="h-3.5 w-3.5" />
              {savedCount} saved plans
            </span>
          </div>
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Faculty members"
          value={faculty.data?.length ?? 0}
          to="/faculty"
          hint="View roster"
          icon={IconUsers}
        />
        <StatCard
          label="Courses"
          value={courses.data?.length ?? 0}
          to="/courses"
          hint="Browse catalog"
          icon={IconBook}
        />
        <StatCard
          label="Classrooms"
          value={classrooms.data?.length ?? 0}
          to="/classrooms"
          hint="View rooms"
          icon={IconBuilding}
        />
        <StatCard
          label="Laboratories"
          value={laboratories.data?.length ?? 0}
          to="/laboratories"
          hint="View labs"
          icon={IconFlask}
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-5">
        <section className="ui-section lg:col-span-3">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <h2 className="ui-section-title">Recent allocation runs</h2>
              <p className="mt-1 text-xs text-slate-500">Open a plan without re-running the solver</p>
            </div>
            <Link to="/allocations" className="ui-link-quiet inline-flex items-center gap-1">
              View all
              <IconArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          {recentRuns.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50/80 px-4 py-10 text-center">
              <IconClock className="mx-auto h-6 w-6 text-slate-400" />
              <p className="mt-3 text-sm font-medium text-slate-700">No allocation runs yet</p>
              <p className="mt-1 text-xs text-slate-500">
                Select batches and semesters, then run the optimizer.
              </p>
              <Link to="/allocations" className="ui-btn-primary mt-4">
                Start planning
              </Link>
            </div>
          ) : (
            <ul className="divide-y divide-slate-100">
              {recentRuns.map((run) => (
                <li key={run.id}>
                  <Link
                    to="/allocations"
                    className="flex flex-wrap items-center justify-between gap-3 rounded-xl px-2 py-3 transition hover:bg-slate-50"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-slate-900">
                        {run.is_saved ? "★ " : ""}
                        {run.plan_name}
                      </p>
                      <p className="mt-0.5 truncate text-xs text-slate-500">
                        {run.batch_label} · {run.assignment_count} slots ·{" "}
                        {formatWhen(run.updated_at ?? run.created_at)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={statusVariant(run.status)}>{run.status}</Badge>
                      {run.timetable_status && (
                        <Badge variant={statusVariant(run.timetable_status)}>
                          tt: {run.timetable_status}
                        </Badge>
                      )}
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="ui-section lg:col-span-2">
          <h2 className="ui-section-title">Planning workflow</h2>
          <ol className="mt-4 space-y-3">
            {workflow.map((item) => (
              <li key={item.step}>
                <Link
                  to={item.to}
                  className="group flex gap-3 rounded-xl border border-transparent p-2 transition hover:border-emerald-100 hover:bg-emerald-50/60"
                >
                  <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-slate-900 text-[11px] font-semibold text-white">
                    {item.step}
                  </span>
                  <span className="min-w-0">
                    <span className="flex items-center gap-1 text-sm font-medium text-slate-900">
                      {item.title}
                      <IconArrowRight className="h-3.5 w-3.5 opacity-0 transition group-hover:opacity-100" />
                    </span>
                    <span className="mt-0.5 block text-xs leading-relaxed text-slate-500">
                      {item.body}
                    </span>
                  </span>
                </Link>
              </li>
            ))}
          </ol>
        </section>
      </div>
    </>
  );
}

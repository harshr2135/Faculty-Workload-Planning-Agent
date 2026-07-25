import { NavLink } from "react-router-dom";
import { cn } from "@/utils/formatters";
import {
  IconBook,
  IconBuilding,
  IconCalendar,
  IconDashboard,
  IconFlask,
  IconShield,
  IconSpark,
  IconUsers,
} from "@/components/ui/icons";

const masterData = [
  { to: "/faculty", label: "Faculty", icon: IconUsers },
  { to: "/courses", label: "Courses", icon: IconBook },
  { to: "/classrooms", label: "Rooms", icon: IconBuilding },
  { to: "/laboratories", label: "Laboratories", icon: IconFlask },
  { to: "/timetable", label: "Time slots", icon: IconCalendar },
];

const planning = [
  { to: "/allocations", label: "Allocation", icon: IconSpark },
  { to: "/policies", label: "Policies", icon: IconShield },
];

function NavGroup({
  title,
  items,
}: {
  title: string;
  items: { to: string; label: string; icon: typeof IconDashboard; end?: boolean }[];
}) {
  return (
    <div className="space-y-1">
      <p className="px-3 pb-1 pt-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
        {title}
      </p>
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              cn(
                "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium tracking-tight transition-all duration-200",
                isActive
                  ? "bg-emerald-600 text-white shadow-lg shadow-emerald-950/40"
                  : "text-slate-300 hover:bg-white/5 hover:text-white",
              )
            }
          >
            {({ isActive }) => (
              <>
                <Icon
                  className={cn(
                    "h-4 w-4 shrink-0 transition",
                    isActive ? "text-white" : "text-slate-400 group-hover:text-emerald-300",
                  )}
                />
                {item.label}
              </>
            )}
          </NavLink>
        );
      })}
    </div>
  );
}

export function Sidebar() {
  return (
    <aside className="relative flex h-screen w-64 shrink-0 flex-col overflow-y-auto border-r border-slate-800/80 bg-[var(--sidebar)] text-slate-100">
      <div className="pointer-events-none absolute inset-0 bg-sidebar-glow opacity-90" aria-hidden />
      <div className="relative border-b border-slate-800/80 px-5 py-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/15 ring-1 ring-emerald-400/30">
            <IconSpark className="h-5 w-5 text-emerald-300" />
          </div>
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-emerald-400">
              NVIDIA Capstone
            </p>
            <h1 className="mt-0.5 text-base font-semibold leading-tight tracking-tight text-white">
              Workload Planner
            </h1>
          </div>
        </div>
        <p className="mt-3 text-xs text-slate-400">AI&amp;ML Department</p>
      </div>

      <nav className="relative flex-1 space-y-2 p-3">
        <NavLink
          to="/"
          end
          className={({ isActive }) =>
            cn(
              "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium tracking-tight transition-all duration-200",
              isActive
                ? "bg-emerald-600 text-white shadow-lg shadow-emerald-950/40"
                : "text-slate-300 hover:bg-white/5 hover:text-white",
            )
          }
        >
          {({ isActive }) => (
            <>
              <IconDashboard
                className={cn(
                  "h-4 w-4 shrink-0",
                  isActive ? "text-white" : "text-slate-400 group-hover:text-emerald-300",
                )}
              />
              Dashboard
            </>
          )}
        </NavLink>
        <NavGroup title="Master data" items={masterData} />
        <NavGroup title="Planning" items={planning} />
      </nav>

      <div className="relative border-t border-slate-800/80 px-4 py-4">
        <p className="text-[11px] leading-relaxed text-slate-500">
          CP-SAT allocates · LLM explains
        </p>
      </div>
    </aside>
  );
}

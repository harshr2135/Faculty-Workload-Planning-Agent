import { NavLink } from "react-router-dom";
import { cn } from "@/utils/formatters";

const navItems = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/faculty", label: "Faculty" },
  { to: "/courses", label: "Courses" },
  { to: "/classrooms", label: "Rooms" },
  { to: "/laboratories", label: "Laboratories" },
  { to: "/timetable", label: "Timetable" },
  { to: "/allocations", label: "Allocation" },
  { to: "/policies", label: "Policies" },
];

export function Sidebar() {
  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-slate-200 bg-slate-900 text-slate-100">
      <div className="border-b border-slate-800 px-5 py-5">
        <p className="text-xs font-semibold uppercase tracking-wider text-emerald-400">
          NVIDIA Capstone
        </p>
        <h1 className="mt-1 text-lg font-semibold leading-tight">Workload Planner</h1>
        <p className="mt-1 text-xs text-slate-400">AI&amp;ML Department</p>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              cn(
                "block rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-emerald-600 text-white"
                  : "text-slate-300 hover:bg-slate-800 hover:text-white",
              )
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

import type { ReactNode } from "react";
import type { TimetableGrid, TimetableGridItem } from "@/types/api";

interface TimetableGridProps {
  grid: TimetableGrid;
  compact?: boolean;
  hideBatch?: boolean;
  hideRoom?: boolean;
  showLegend?: boolean;
  footer?: ReactNode;
}

interface SessionStyle {
  card: string;
  meta: string;
  legendLabel: string;
  swatch: string;
}

const SESSION_LEGEND: SessionStyle[] = [
  {
    legendLabel: "Theory (classroom)",
    swatch: "bg-sky-400",
    card: "border-sky-400 bg-sky-50",
    meta: "text-sky-800",
  },
  {
    legendLabel: "PEC (lecture hall)",
    swatch: "bg-indigo-400",
    card: "border-indigo-400 bg-indigo-50",
    meta: "text-indigo-800",
  },
  {
    legendLabel: "SEC (lecture hall)",
    swatch: "bg-emerald-400",
    card: "border-emerald-400 bg-emerald-50",
    meta: "text-emerald-800",
  },
  {
    legendLabel: "Lab",
    swatch: "bg-violet-400",
    card: "border-violet-400 bg-violet-50",
    meta: "text-violet-800",
  },
];

function normalizeCourseType(courseType: string): string {
  return courseType.trim().toUpperCase();
}

function sessionStyle(item: TimetableGridItem): SessionStyle {
  if (item.kind === "lab") {
    return SESSION_LEGEND[3];
  }
  const courseType = normalizeCourseType(item.course_type);
  if (courseType === "PEC") {
    return SESSION_LEGEND[1];
  }
  if (courseType === "SEC") {
    return SESSION_LEGEND[2];
  }
  return SESSION_LEGEND[0];
}

function itemCardClass(item: TimetableGridItem): string {
  const style = sessionStyle(item);
  return `mb-1 rounded border p-1 last:mb-0 flex h-full min-h-[3rem] flex-col justify-center ${style.card}`;
}

function cellClass(slotType: string): string {
  if (slotType === "break") {
    return "bg-amber-50 text-amber-800";
  }
  if (slotType === "lunch") {
    return "bg-orange-50 text-orange-900";
  }
  return "bg-white";
}

function headerClass(slotType: string): string {
  if (slotType === "break") {
    return "bg-amber-100 text-amber-900";
  }
  if (slotType === "lunch") {
    return "bg-orange-100 text-orange-900";
  }
  return "bg-slate-100 text-slate-800";
}

function cellColSpan(cell: TimetableGrid["rows"][number]["cells"][number]): number {
  if (cell.items.length === 0) {
    return 1;
  }
  return Math.max(...cell.items.map((item) => item.col_span ?? 1));
}

export function TimetableGridView({
  grid,
  compact = false,
  hideBatch = false,
  hideRoom = false,
  showLegend = true,
  footer,
}: TimetableGridProps) {
  if (grid.rows.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      {showLegend && (
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-slate-600">
          {SESSION_LEGEND.map((entry) => (
            <span key={entry.legendLabel} className="inline-flex items-center gap-1.5">
              <span className={`h-3 w-3 rounded-sm border border-slate-300 ${entry.swatch}`} />
              {entry.legendLabel}
            </span>
          ))}
        </div>
      )}
      <div className="overflow-x-auto rounded-lg border border-slate-300">
      <table className="min-w-full border-collapse text-xs">
        <thead>
          <tr>
            <th
              rowSpan={2}
              className="sticky left-0 z-10 border border-slate-300 bg-slate-200 px-3 py-2 text-left font-semibold"
            >
              Day
            </th>
            {grid.periods.map((period) => (
              <th
                key={period.sort_order}
                className={`min-w-[5.5rem] border border-slate-300 px-1 py-1 text-center font-semibold ${headerClass(period.slot_type)}`}
              >
                {period.column_header}
              </th>
            ))}
          </tr>
          <tr>
            {grid.periods.map((period) => (
              <th
                key={`label-${period.sort_order}`}
                className={`border border-slate-300 px-1 py-1 text-center text-[10px] font-bold tracking-wide ${headerClass(period.slot_type)}`}
              >
                {period.fixed_label ?? period.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {grid.rows.map((row) => (
            <tr key={row.day}>
              <td className="sticky left-0 z-10 border border-slate-300 bg-slate-50 px-3 py-2 font-semibold capitalize">
                {row.day}
              </td>
              {row.cells.map((cell) => {
                if (cell.span_continuation) {
                  return null;
                }
                const colSpan = cellColSpan(cell);
                return (
                  <td
                    key={`${row.day}-${cell.sort_order}`}
                    colSpan={colSpan > 1 ? colSpan : undefined}
                    className={`border border-slate-300 align-top p-1 ${cellClass(cell.slot_type)}`}
                  >
                    {cell.slot_type !== "teaching" ? (
                      <div className="flex h-full min-h-[3rem] items-center justify-center text-lg font-bold tracking-widest">
                        {cell.fixed_label}
                      </div>
                    ) : cell.items.length === 0 ? (
                      <span className="text-slate-300"> </span>
                    ) : (
                      cell.items.map((item, index) => {
                        const style = sessionStyle(item);
                        return (
                        <div
                          key={`${item.batch_code}-${item.course_code}-${index}`}
                          className={`${itemCardClass(item)} ${compact ? "text-[10px]" : ""}`}
                        >
                          <div className="font-mono font-semibold text-slate-900">
                            {hideBatch
                              ? item.course_code
                              : `${item.batch_code} · ${item.course_code}`}
                          </div>
                          <div
                            className={`font-medium leading-tight text-slate-800 ${compact ? "text-[10px]" : "text-xs"}`}
                            title={item.course_name}
                          >
                            {item.course_name}
                          </div>
                          <div className={`${style.meta}`}>
                            <span className="font-semibold">{item.course_type}</span>
                            {" · "}
                            Sec {item.section_indices.join(", ")}
                            {!compact && ` · ${item.kind}`}
                            {(item.col_span ?? 1) > 1 && ` · ${item.period_label}`}
                          </div>
                          {!hideRoom && (
                            <div className="text-slate-600">{item.room_name}</div>
                          )}
                          {!compact && (
                            <div className="text-slate-700">{item.faculty_names.join(" · ")}</div>
                          )}
                        </div>
                        );
                      })
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      {footer && <div className="border-t border-slate-300">{footer}</div>}
      </div>
    </div>
  );
}

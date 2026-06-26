import type { TimetableGrid } from "@/types/api";

interface TimetableGridProps {
  grid: TimetableGrid;
  compact?: boolean;
  hideBatch?: boolean;
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

export function TimetableGridView({ grid, compact = false, hideBatch = false }: TimetableGridProps) {
  if (grid.rows.length === 0) {
    return null;
  }

  return (
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
              {row.cells.map((cell) => (
                <td
                  key={`${row.day}-${cell.sort_order}`}
                  className={`border border-slate-300 align-top p-1 ${cellClass(cell.slot_type)}`}
                >
                  {cell.slot_type !== "teaching" ? (
                    <div className="flex h-full min-h-[3rem] items-center justify-center text-lg font-bold tracking-widest">
                      {cell.fixed_label}
                    </div>
                  ) : cell.items.length === 0 ? (
                    <span className="text-slate-300"> </span>
                  ) : (
                    cell.items.map((item, index) => (
                      <div
                        key={`${item.batch_code}-${item.course_code}-${index}`}
                        className={`mb-1 rounded border border-slate-200 bg-white/80 p-1 last:mb-0 ${compact ? "text-[10px]" : ""}`}
                      >
                        <div className="font-mono font-semibold text-slate-900">
                          {hideBatch
                            ? item.course_code
                            : `${item.batch_code} · ${item.course_code}`}
                        </div>
                        <div className="text-slate-600">
                          Sec {item.section_indices.join(", ")}
                          {!compact && ` · ${item.kind}`}
                        </div>
                        <div className="text-slate-500">{item.room_name}</div>
                        {!compact && (
                          <div className="text-slate-700">{item.faculty_names.join(" · ")}</div>
                        )}
                      </div>
                    ))
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

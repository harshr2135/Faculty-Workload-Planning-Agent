import { fetchTimetableOverview } from "@/api/timetable";
import { PageHeader } from "@/components/ui/PageHeader";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import {
  DataTable,
  DataTableBody,
  DataTableCell,
  DataTableHead,
  DataTableHeaderCell,
} from "@/components/ui/DataTable";
import { Badge } from "@/components/ui/Badge";
import { useFetch } from "@/hooks/useFetch";
import { formatTime } from "@/utils/formatters";

export default function TimetablePage() {
  const { data, loading, error, reload } = useFetch(fetchTimetableOverview);

  return (
    <>
      <PageHeader
        title="Timetable"
        description={
          data
            ? `${data.teaching_periods_per_day} teaching periods per working day`
            : "Daily period template"
        }
      />
      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {!loading && !error && data && (
        <DataTable>
          <DataTableHead>
            <DataTableHeaderCell>Order</DataTableHeaderCell>
            <DataTableHeaderCell>Period</DataTableHeaderCell>
            <DataTableHeaderCell>Time</DataTableHeaderCell>
            <DataTableHeaderCell>Duration</DataTableHeaderCell>
            <DataTableHeaderCell>Type</DataTableHeaderCell>
          </DataTableHead>
          <DataTableBody>
            {data.slots.map((slot) => (
              <tr key={slot.id} className="hover:bg-slate-50">
                <DataTableCell>{slot.sort_order}</DataTableCell>
                <DataTableCell className="font-medium text-slate-900">{slot.label}</DataTableCell>
                <DataTableCell>
                  {formatTime(slot.start_time)} – {formatTime(slot.end_time)}
                </DataTableCell>
                <DataTableCell>{slot.duration_minutes} min</DataTableCell>
                <DataTableCell>
                  <Badge
                    variant={
                      slot.slot_type === "teaching"
                        ? "success"
                        : slot.slot_type === "break"
                          ? "warning"
                          : "default"
                    }
                  >
                    {slot.slot_type}
                  </Badge>
                </DataTableCell>
              </tr>
            ))}
          </DataTableBody>
        </DataTable>
      )}
    </>
  );
}

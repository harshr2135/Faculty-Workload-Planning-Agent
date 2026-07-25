import { fetchClassrooms, fetchLectureHalls } from "@/api/rooms";
import type { LectureHall } from "@/types/api";
import { PageHeader } from "@/components/ui/PageHeader";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import {
  DataTable,
  DataTableBody,
  DataTableCell,
  DataTableHead,
  DataTableHeaderCell,
  EmptyRow,
} from "@/components/ui/DataTable";
import { useFetch } from "@/hooks/useFetch";

export default function ClassroomsPage() {
  const classrooms = useFetch(fetchClassrooms);
  const lectureHalls = useFetch(fetchLectureHalls);
  const loading = classrooms.loading || lectureHalls.loading;
  const error = classrooms.error || lectureHalls.error;

  return (
    <>
      <PageHeader
        eyebrow="Master data"
        title="Rooms"
        description="Department classrooms and college lecture halls (PEC/SEC combined sections)"
      />
      {loading && <LoadingState />}
      {error && (
        <ErrorState
          message={error}
          onRetry={() => {
            classrooms.reload();
            lectureHalls.reload();
          }}
        />
      )}
      {!loading && !error && classrooms.data && lectureHalls.data && (
        <div className="space-y-8">
          <RoomTable
            title="Department classrooms"
            subtitle="IPCC, PCC, BSC, HSMC — one section per room"
            columns={["Room number", "Capacity"]}
            rows={classrooms.data.map((room) => [room.room_number, room.capacity ?? "—"])}
            emptyMessage="No classrooms configured."
          />
          <RoomTable
            title="College lecture halls"
            subtitle="PEC and SEC — 2–3 sections combined per session"
            columns={["Hall", "Combined sections", "Capacity"]}
            rows={lectureHalls.data.map((hall: LectureHall) => [
              hall.name,
              `${hall.min_combined_sections}–${hall.max_combined_sections}`,
              hall.capacity ?? "—",
            ])}
            emptyMessage="No lecture halls configured."
          />
        </div>
      )}
    </>
  );
}

function RoomTable({
  title,
  subtitle,
  columns,
  rows,
  emptyMessage,
}: {
  title: string;
  subtitle: string;
  columns: string[];
  rows: (string | number)[][];
  emptyMessage: string;
}) {
  return (
    <section>
      <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
      <p className="mb-3 text-sm text-slate-600">{subtitle}</p>
      <DataTable>
        <DataTableHead>
          {columns.map((column) => (
            <DataTableHeaderCell key={column}>{column}</DataTableHeaderCell>
          ))}
        </DataTableHead>
        <DataTableBody>
          {rows.length === 0 ? (
            <EmptyRow colSpan={columns.length} message={emptyMessage} />
          ) : (
            rows.map((row, index) => (
              <tr key={`${title}-${index}`} className="hover:bg-slate-50">
                {row.map((cell, cellIndex) => (
                  <DataTableCell
                    key={cellIndex}
                    className={cellIndex === 0 ? "font-medium text-slate-900" : undefined}
                  >
                    {cell}
                  </DataTableCell>
                ))}
              </tr>
            ))
          )}
        </DataTableBody>
      </DataTable>
    </section>
  );
}

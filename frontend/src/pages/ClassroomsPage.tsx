import { fetchClassrooms } from "@/api/rooms";
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
  const { data, loading, error, reload } = useFetch(fetchClassrooms);

  return (
    <>
      <PageHeader
        title="Classrooms"
        description="Teaching rooms allocated to the AI&ML department"
      />
      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {!loading && !error && data && (
        <DataTable>
          <DataTableHead>
            <DataTableHeaderCell>Room number</DataTableHeaderCell>
            <DataTableHeaderCell>Capacity</DataTableHeaderCell>
          </DataTableHead>
          <DataTableBody>
            {data.length === 0 ? (
              <EmptyRow colSpan={2} message="No classrooms configured." />
            ) : (
              data.map((room) => (
                <tr key={room.id} className="hover:bg-slate-50">
                  <DataTableCell className="font-medium text-slate-900">{room.room_number}</DataTableCell>
                  <DataTableCell>{room.capacity ?? "—"}</DataTableCell>
                </tr>
              ))
            )}
          </DataTableBody>
        </DataTable>
      )}
    </>
  );
}

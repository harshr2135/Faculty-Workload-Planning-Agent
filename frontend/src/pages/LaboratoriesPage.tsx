import { fetchLaboratories } from "@/api/rooms";
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

export default function LaboratoriesPage() {
  const { data, loading, error, reload } = useFetch(fetchLaboratories);

  return (
    <>
      <PageHeader
        eyebrow="Master data"
        title="Laboratories"
        description="Lab rooms for continuous practical sessions"
      />
      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {!loading && !error && data && (
        <DataTable>
          <DataTableHead>
            <DataTableHeaderCell>Lab room</DataTableHeaderCell>
            <DataTableHeaderCell>Capacity</DataTableHeaderCell>
          </DataTableHead>
          <DataTableBody>
            {data.length === 0 ? (
              <EmptyRow colSpan={2} message="No laboratories configured." />
            ) : (
              data.map((lab) => (
                <tr key={lab.id} className="hover:bg-slate-50">
                  <DataTableCell className="font-medium text-slate-900">{lab.room_number}</DataTableCell>
                  <DataTableCell>{lab.capacity ?? "—"}</DataTableCell>
                </tr>
              ))
            )}
          </DataTableBody>
        </DataTable>
      )}
    </>
  );
}

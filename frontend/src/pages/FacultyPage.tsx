import { fetchFaculty } from "@/api/faculty";
import { PageHeader } from "@/components/ui/PageHeader";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import {
  DataTable,
  DataTableBody,
  DataTableCell,
  DataTableHead,
  DataTableHeaderCell,
} from "@/components/ui/DataTable";
import { Badge } from "@/components/ui/Badge";
import { useFetch } from "@/hooks/useFetch";

export default function FacultyPage() {
  const { data, loading, error, reload } = useFetch(fetchFaculty);

  return (
    <>
      <PageHeader
        eyebrow="Master data"
        title="Faculty"
        description={`${data?.length ?? 0} AIML faculty members with specializations`}
      />
      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {!loading && !error && data && data.length === 0 && (
        <EmptyState
          title="No faculty imported yet"
          description="Import the department faculty Excel into the backend, then refresh this page."
        />
      )}
      {!loading && !error && data && data.length > 0 && (
        <DataTable>
          <DataTableHead>
            <DataTableHeaderCell>Name</DataTableHeaderCell>
            <DataTableHeaderCell>Designation</DataTableHeaderCell>
            <DataTableHeaderCell>Email</DataTableHeaderCell>
            <DataTableHeaderCell>Phone</DataTableHeaderCell>
            <DataTableHeaderCell>Cabin</DataTableHeaderCell>
            <DataTableHeaderCell>Specializations</DataTableHeaderCell>
          </DataTableHead>
          <DataTableBody>
            {data.map((member) => (
              <tr key={member.id} className="hover:bg-slate-50">
                <DataTableCell>
                  <div className="font-medium text-slate-900">{member.full_name}</div>
                </DataTableCell>
                <DataTableCell>{member.designation}</DataTableCell>
                <DataTableCell>{member.email}</DataTableCell>
                <DataTableCell>{member.phone ?? "—"}</DataTableCell>
                <DataTableCell>{member.cabin_number ?? "—"}</DataTableCell>
                <DataTableCell>
                  <div className="flex max-w-md flex-wrap gap-1">
                    {member.specializations.map((spec) => (
                      <Badge key={spec.id}>{spec.name}</Badge>
                    ))}
                  </div>
                </DataTableCell>
              </tr>
            ))}
          </DataTableBody>
        </DataTable>
      )}
    </>
  );
}

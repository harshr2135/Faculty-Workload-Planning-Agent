import { fetchPolicies } from "@/api/policies";
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
import { useFetch } from "@/hooks/useFetch";

export default function PoliciesPage() {
  const { data, loading, error, reload } = useFetch(fetchPolicies);

  return (
    <>
      <PageHeader
        title="Policies"
        description="AICTE workload rules and department planning policies"
      />
      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {!loading && !error && data && (
        <div className="space-y-8">
          <section>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
              Designation workload (AICTE)
            </h2>
            <DataTable>
              <DataTableHead>
                <DataTableHeaderCell>Designation</DataTableHeaderCell>
                <DataTableHeaderCell>Max weekly hours</DataTableHeaderCell>
                <DataTableHeaderCell>Max lab sessions</DataTableHeaderCell>
              </DataTableHead>
              <DataTableBody>
                {data.designation_policies.map((policy) => (
                  <tr key={policy.id} className="hover:bg-slate-50">
                    <DataTableCell className="font-medium text-slate-900">
                      {policy.designation_label}
                    </DataTableCell>
                    <DataTableCell>{policy.max_weekly_hours}</DataTableCell>
                    <DataTableCell>
                      {policy.max_lab_sessions != null ? policy.max_lab_sessions : "—"}
                    </DataTableCell>
                  </tr>
                ))}
              </DataTableBody>
            </DataTable>
          </section>

          <section>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
              Planning rules
            </h2>
            <div className="space-y-3">
              {data.planning_policies.map((policy) => (
                <div
                  key={policy.id}
                  className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
                >
                  <p className="font-mono text-xs text-emerald-700">{policy.policy_key}</p>
                  <p className="mt-1 text-sm font-medium text-slate-900">{policy.policy_value}</p>
                  {policy.description && (
                    <p className="mt-2 text-sm text-slate-600">{policy.description}</p>
                  )}
                </div>
              ))}
            </div>
          </section>
        </div>
      )}
    </>
  );
}

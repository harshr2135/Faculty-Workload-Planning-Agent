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

const UNLIMITED_WEEKLY_HOURS = 999;

function formatWeeklyHourCap(value: number): string {
  if (value >= UNLIMITED_WEEKLY_HOURS) {
    return "No limit";
  }
  return `${value} hrs`;
}

function formatLabSessionCap(value: number | null): string {
  if (value === null) {
    return "No limit";
  }
  return `${value} sessions`;
}

function formatMinimum(value: number | null): string {
  if (!value) {
    return "—";
  }
  return String(value);
}

export default function PoliciesPage() {
  const { data, loading, error, reload } = useFetch(fetchPolicies);

  return (
    <>
      <PageHeader
        eyebrow="Planning"
        title="Policies"
        description="AICTE workload rules and department planning policies"
      />
      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {!loading && !error && data && (
        <div className="space-y-8">
          <section>
            <h2 className="mb-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
              Designation workload (AICTE)
            </h2>
            <DataTable>
              <DataTableHead>
                <DataTableHeaderCell>Designation</DataTableHeaderCell>
                <DataTableHeaderCell>Min theory courses</DataTableHeaderCell>
                <DataTableHeaderCell>Min lab sessions</DataTableHeaderCell>
                <DataTableHeaderCell>Weekly hour cap</DataTableHeaderCell>
                <DataTableHeaderCell>Lab session cap</DataTableHeaderCell>
              </DataTableHead>
              <DataTableBody>
                {data.designation_policies.map((policy) => (
                  <tr key={policy.id} className="hover:bg-slate-50">
                    <DataTableCell className="font-medium text-slate-900">
                      {policy.designation_label}
                    </DataTableCell>
                    <DataTableCell>{formatMinimum(policy.min_theory_courses)}</DataTableCell>
                    <DataTableCell>{formatMinimum(policy.min_lab_sessions)}</DataTableCell>
                    <DataTableCell>{formatWeeklyHourCap(policy.max_weekly_hours)}</DataTableCell>
                    <DataTableCell>{formatLabSessionCap(policy.max_lab_sessions)}</DataTableCell>
                  </tr>
                ))}
              </DataTableBody>
            </DataTable>
            <p className="mt-2 text-xs text-slate-500">
              Minimums and maximums are AICTE targets applied as soft policies: allocation
              prefers to keep faculty within these limits but is never blocked by them. Faculty
              outside their limits are flagged as policy warnings in the allocation report.
            </p>
          </section>

          <section>
            <h2 className="mb-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
              Planning rules
            </h2>
            <div className="space-y-3">
              {data.planning_policies.map((policy) => (
                <div key={policy.id} className="ui-card p-4">
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

import { useEffect, useMemo, useState } from "react";
import { fetchStudentBatches } from "@/api/courses";
import { runAllocation } from "@/api/allocations";
import type { AllocationRun } from "@/types/api";
import { PageHeader } from "@/components/ui/PageHeader";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Badge } from "@/components/ui/Badge";
import { TimetableGridView } from "@/components/TimetableGridView";
import {
  DataTable,
  DataTableBody,
  DataTableCell,
  DataTableHead,
  DataTableHeaderCell,
  EmptyRow,
} from "@/components/ui/DataTable";
import { useFetch } from "@/hooks/useFetch";

const SEMESTER_OPTIONS = [3, 4, 5, 6, 7];

export default function AllocationsPage() {
  const batches = useFetch(fetchStudentBatches);
  const [selectedBatches, setSelectedBatches] = useState<string[]>([]);
  const [semesterByBatch, setSemesterByBatch] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AllocationRun | null>(null);

  const allBatchCodes = useMemo(
    () => (batches.data ?? []).map((batch) => batch.batch_code),
    [batches.data],
  );

  useEffect(() => {
    if (!batches.data?.length) {
      return;
    }
    setSelectedBatches((current) => (current.length > 0 ? current : allBatchCodes));
    setSemesterByBatch((current) => {
      const next = { ...current };
      for (const batch of batches.data ?? []) {
        if (next[batch.batch_code] === undefined) {
          next[batch.batch_code] = batch.default_planning_semester;
        }
      }
      return next;
    });
  }, [batches.data, allBatchCodes]);

  function toggleBatch(batchCode: string) {
    setSelectedBatches((current) =>
      current.includes(batchCode)
        ? current.filter((code) => code !== batchCode)
        : [...current, batchCode].sort(),
    );
  }

  function selectAllBatches() {
    setSelectedBatches(allBatchCodes);
  }

  function setBatchSemester(batchCode: string, semester: number) {
    setSemesterByBatch((current) => ({ ...current, [batchCode]: semester }));
  }

  async function handleRun() {
    if (selectedBatches.length === 0) {
      setError("Select at least one student batch.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const batch_plans = selectedBatches.map((batch_code) => ({
        batch_code,
        semester_number: semesterByBatch[batch_code] ?? 5,
      }));
      const run = await runAllocation({
        batch_plans,
        max_time_seconds: selectedBatches.length > 1 ? 180 : 120,
      });
      setResult(run);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Allocation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Workload allocation"
        description="Each batch can be on a different semester — same as a real department planning cycle"
        action={
          <button
            type="button"
            onClick={handleRun}
            disabled={loading || selectedBatches.length === 0}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
          >
            {loading ? "Running…" : "Run allocation"}
          </button>
        }
      />
      {batches.loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={handleRun} />}
      {loading && (
        <LoadingState message="Solving workload and timetable with OR-Tools CP-SAT — this can take 2–5 minutes for all batches…" />
      )}
      {!batches.loading && allBatchCodes.length > 0 && (
        <section className="mb-6 rounded-lg border border-slate-200 bg-white p-4">
          <div className="mb-3 flex items-center justify-between gap-2">
            <h2 className="text-sm font-semibold text-slate-900">Batches & semesters</h2>
            <button
              type="button"
              onClick={selectAllBatches}
              className="text-xs text-slate-600 underline hover:text-slate-900"
            >
              Select all
            </button>
          </div>
          <div className="space-y-2">
            {(batches.data ?? []).map((batch) => (
              <div
                key={batch.batch_code}
                className="flex flex-wrap items-center gap-3 rounded-md border border-slate-100 px-3 py-2 text-sm"
              >
                <label className="inline-flex min-w-[6rem] items-center gap-2 font-medium">
                  <input
                    type="checkbox"
                    checked={selectedBatches.includes(batch.batch_code)}
                    onChange={() => toggleBatch(batch.batch_code)}
                  />
                  {batch.batch_code}
                </label>
                <label className="inline-flex items-center gap-2 text-slate-600">
                  Semester
                  <select
                    value={semesterByBatch[batch.batch_code] ?? batch.default_planning_semester}
                    onChange={(e) => setBatchSemester(batch.batch_code, Number(e.target.value))}
                    disabled={!selectedBatches.includes(batch.batch_code)}
                    className="rounded border border-slate-300 bg-white px-2 py-1 disabled:opacity-50"
                  >
                    {SEMESTER_OPTIONS.map((n) => (
                      <option key={n} value={n}>
                        {n}
                      </option>
                    ))}
                  </select>
                </label>
                <span className="text-xs text-slate-500">
                  default sem {batch.default_planning_semester}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}
      {result && !loading && <AllocationResults result={result} />}
    </>
  );
}

function AllocationResults({ result }: { result: AllocationRun }) {
  const planLabel = result.batch_plans
    .map((plan) => `${plan.batch_code} (sem ${plan.semester_number}, ${plan.section_count} sec)`)
    .join(" · ");

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap gap-3 text-sm text-slate-600">
        <span>Run #{result.id}</span>
        <span>{planLabel}</span>
        <Badge variant={result.status === "optimal" ? "success" : "warning"}>
          workload: {result.status}
        </Badge>
        {result.timetable_status && (
          <Badge variant={result.timetable_status === "optimal" ? "success" : "warning"}>
            timetable: {result.timetable_status}
          </Badge>
        )}
        <span>{result.assignment_count} workload slots</span>
        <span>{result.timetable_entry_count} timetable entries</span>
        {result.objective_value !== null && <span>objective {result.objective_value}</span>}
      </div>
      {result.messages.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          {result.messages.map((msg) => (
            <p key={msg}>{msg}</p>
          ))}
        </div>
      )}
      {result.violations.length > 0 && (
        <section>
          <h2 className="mb-2 text-lg font-semibold text-slate-900">
            Policy warnings ({result.violations.length})
          </h2>
          <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
            {result.violations.slice(0, 15).map((v, i) => (
              <li key={`${v.code}-${i}`}>{v.message}</li>
            ))}
          </ul>
        </section>
      )}
      {result.timetable_messages.length > 0 && (
        <div className="rounded-lg border border-sky-200 bg-sky-50 p-4 text-sm text-sky-900">
          {result.timetable_messages.map((msg) => (
            <p key={msg}>{msg}</p>
          ))}
        </div>
      )}
      {(result.timetable_grid ||
        (result.section_timetable_grids?.length ?? 0) > 0 ||
        (result.faculty_timetable_grids?.length ?? 0) > 0) && (
        <TimetableResults result={result} />
      )}
      <section>
        <h2 className="mb-3 text-lg font-semibold text-slate-900">Workload assignments</h2>
        <DataTable>
          <DataTableHead>
            <DataTableHeaderCell>Batch</DataTableHeaderCell>
            <DataTableHeaderCell>Course</DataTableHeaderCell>
            <DataTableHeaderCell>Type</DataTableHeaderCell>
            <DataTableHeaderCell>Kind</DataTableHeaderCell>
            <DataTableHeaderCell>Sections</DataTableHeaderCell>
            <DataTableHeaderCell>Hrs/wk</DataTableHeaderCell>
            <DataTableHeaderCell>Faculty</DataTableHeaderCell>
          </DataTableHead>
          <DataTableBody>
            {result.assignments.length === 0 ? (
              <EmptyRow colSpan={7} message="No assignments." />
            ) : (
              result.assignments.map((row) => (
                <tr key={row.slot_id} className="hover:bg-slate-50">
                  <DataTableCell className="font-mono text-xs">{row.batch_code}</DataTableCell>
                  <DataTableCell>
                    <div className="font-mono text-xs">{row.course_code}</div>
                    <div className="text-slate-600">{row.course_name}</div>
                  </DataTableCell>
                  <DataTableCell>{row.course_type}</DataTableCell>
                  <DataTableCell>{row.kind}</DataTableCell>
                  <DataTableCell>{row.section_indices.join(", ")}</DataTableCell>
                  <DataTableCell>{row.weekly_hours}</DataTableCell>
                  <DataTableCell>{row.faculty_names.join(" · ")}</DataTableCell>
                </tr>
              ))
            )}
          </DataTableBody>
        </DataTable>
      </section>
      <section>
        <h2 className="mb-3 text-lg font-semibold text-slate-900">Faculty workload</h2>
        <DataTable>
          <DataTableHead>
            <DataTableHeaderCell>Faculty</DataTableHeaderCell>
            <DataTableHeaderCell>Theory hrs</DataTableHeaderCell>
            <DataTableHeaderCell>Lab hrs</DataTableHeaderCell>
            <DataTableHeaderCell>Total</DataTableHeaderCell>
            <DataTableHeaderCell>Theory courses</DataTableHeaderCell>
            <DataTableHeaderCell>Lab sessions</DataTableHeaderCell>
          </DataTableHead>
          <DataTableBody>
            {result.faculty_summaries
              .filter((f) => f.total_weekly_hours > 0)
              .map((f) => (
                <tr key={f.faculty_id} className="hover:bg-slate-50">
                  <DataTableCell className="font-medium">{f.full_name}</DataTableCell>
                  <DataTableCell>{f.theory_weekly_hours}</DataTableCell>
                  <DataTableCell>{f.lab_weekly_hours}</DataTableCell>
                  <DataTableCell>{f.total_weekly_hours}</DataTableCell>
                  <DataTableCell>{f.theory_course_count}</DataTableCell>
                  <DataTableCell>{f.lab_session_count}</DataTableCell>
                </tr>
              ))}
          </DataTableBody>
        </DataTable>
      </section>
    </div>
  );
}

type TimetableTab = "department" | "sections" | "faculty";

function sectionGridKey(batchCode: string, sectionIndex: number): string {
  return `${batchCode}::${sectionIndex}`;
}

function TimetableResults({ result }: { result: AllocationRun }) {
  const [tab, setTab] = useState<TimetableTab>("sections");
  const [facultyId, setFacultyId] = useState<number | null>(null);
  const [sectionKey, setSectionKey] = useState<string | null>(null);

  const facultyGrids = result.faculty_timetable_grids ?? [];
  const sectionGrids = result.section_timetable_grids ?? [];

  const selectedFacultyGrid = useMemo(() => {
    if (facultyGrids.length === 0) {
      return null;
    }
    const targetId = facultyId ?? facultyGrids[0].faculty_id;
    return facultyGrids.find((item) => item.faculty_id === targetId) ?? facultyGrids[0];
  }, [facultyGrids, facultyId]);

  const selectedSectionGrid = useMemo(() => {
    if (sectionGrids.length === 0) {
      return null;
    }
    const defaultKey = sectionGridKey(sectionGrids[0].batch_code, sectionGrids[0].section_index);
    const targetKey = sectionKey ?? defaultKey;
    return (
      sectionGrids.find(
        (item) => sectionGridKey(item.batch_code, item.section_index) === targetKey,
      ) ?? sectionGrids[0]
    );
  }, [sectionGrids, sectionKey]);

  const tabClass = (active: boolean) =>
    `rounded-lg px-3 py-1.5 text-sm font-medium ${
      active
        ? "bg-slate-900 text-white"
        : "border border-slate-300 bg-white text-slate-700"
    }`;

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">Weekly timetable</h2>
        <p className="text-sm text-slate-600">
          Official AIML grid: Mon–Fri rows, 7 teaching periods with BREAK and LUNCH columns
        </p>
        {result.timetable_status && result.timetable_status !== "optimal" && (
          <p className="mt-1 text-sm text-amber-700">
            Timetable status: {result.timetable_status}. Section grids may be empty until scheduling
            succeeds.
          </p>
        )}
      </div>
      <div className="flex flex-wrap gap-2">
        <button type="button" onClick={() => setTab("sections")} className={tabClass(tab === "sections")}>
          By batch & section ({sectionGrids.length})
        </button>
        <button
          type="button"
          onClick={() => setTab("department")}
          className={tabClass(tab === "department")}
          disabled={!result.timetable_grid}
        >
          All batches (combined)
        </button>
        <button type="button" onClick={() => setTab("faculty")} className={tabClass(tab === "faculty")}>
          By faculty ({facultyGrids.length})
        </button>
      </div>
      {tab === "sections" && selectedSectionGrid && (
        <div className="space-y-3">
          <label className="flex flex-wrap items-center gap-2 text-sm text-slate-700">
            Batch & section
            <select
              value={sectionGridKey(
                selectedSectionGrid.batch_code,
                selectedSectionGrid.section_index,
              )}
              onChange={(e) => setSectionKey(e.target.value)}
              className="rounded-lg border border-slate-300 bg-white px-3 py-2"
            >
              {sectionGrids.map((item) => (
                <option
                  key={sectionGridKey(item.batch_code, item.section_index)}
                  value={sectionGridKey(item.batch_code, item.section_index)}
                >
                  {item.batch_code} · Section {item.section_index} (sem {item.semester_number})
                </option>
              ))}
            </select>
          </label>
          <TimetableGridView grid={selectedSectionGrid.grid} compact hideBatch />
        </div>
      )}
      {tab === "department" && result.timetable_grid && (
        <TimetableGridView grid={result.timetable_grid} />
      )}
      {tab === "faculty" && selectedFacultyGrid && (
        <div className="space-y-3">
          <label className="flex flex-wrap items-center gap-2 text-sm text-slate-700">
            Faculty
            <select
              value={selectedFacultyGrid.faculty_id}
              onChange={(e) => setFacultyId(Number(e.target.value))}
              className="rounded-lg border border-slate-300 bg-white px-3 py-2"
            >
              {facultyGrids.map((item) => (
                <option key={item.faculty_id} value={item.faculty_id}>
                  {item.faculty_name}
                </option>
              ))}
            </select>
          </label>
          <TimetableGridView grid={selectedFacultyGrid.grid} compact />
        </div>
      )}
    </section>
  );
}

import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchCourses, fetchStudentBatches } from "@/api/courses";
import { fetchFaculty } from "@/api/faculty";
import {
  fetchAllocationRun,
  fetchAllocationRuns,
  runAllocation,
  updateAllocationRun,
} from "@/api/allocations";
import type { AllocationAssignment, AllocationRun, BatchSemesterPlanInput, Course } from "@/types/api";
import { EditableAssignmentsTable } from "@/components/EditableAssignmentsTable";
import { AllocationReportPanel } from "@/components/AllocationReportPanel";
import {
  buildPecEnrollmentsPayload,
  isPecCourseType,
  PecCourseEnrollments,
  type PecEnrollmentMap,
} from "@/components/PecCourseEnrollments";
import { PageHeader } from "@/components/ui/PageHeader";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Badge } from "@/components/ui/Badge";
import { TimetableGridView } from "@/components/TimetableGridView";
import {
  ClassFacultyContactsFooter,
  buildSectionContactGroups,
} from "@/components/ClassFacultyContactsTable";
import {
  DataTable,
  DataTableBody,
  DataTableCell,
  DataTableHead,
  DataTableHeaderCell,
} from "@/components/ui/DataTable";
import { useFetch } from "@/hooks/useFetch";

const SEMESTER_OPTIONS = [3, 4, 5, 6, 7];

function isSolverOk(status: string) {
  return status === "optimal" || status === "feasible";
}

export default function AllocationsPage() {
  const batches = useFetch(fetchStudentBatches);
  const savedPlans = useFetch(fetchAllocationRuns);
  const [selectedBatches, setSelectedBatches] = useState<string[]>([]);
  const [semesterByBatch, setSemesterByBatch] = useState<Record<string, number>>({});
  const [pecEnrollments, setPecEnrollments] = useState<PecEnrollmentMap>({});
  const [pecCoursesByBatch, setPecCoursesByBatch] = useState<Record<string, Course[]>>({});
  const [loading, setLoading] = useState(false);
  const [loadPlanLoading, setLoadPlanLoading] = useState(false);
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

  function setPecEnrollment(batchCode: string, courseCode: string, studentCount: number) {
    setPecEnrollments((current) => ({
      ...current,
      [batchCode]: {
        ...(current[batchCode] ?? {}),
        [courseCode]: studentCount,
      },
    }));
  }

  const handlePecCoursesLoaded = useCallback((batchCode: string, courses: Course[]) => {
    setPecCoursesByBatch((current) => {
      const existing = current[batchCode];
      if (
        existing &&
        existing.length === courses.length &&
        existing.every((course, index) => course.course_code === courses[index]?.course_code)
      ) {
        return current;
      }
      return { ...current, [batchCode]: courses };
    });
  }, []);

  function restorePecEnrollmentsFromRun(run: AllocationRun) {
    const next: PecEnrollmentMap = {};
    for (const plan of run.batch_plans ?? []) {
      const batchMap: Record<string, number> = {};
      for (const entry of plan.pec_enrollments ?? []) {
        batchMap[entry.course_code] = entry.student_count;
      }
      if (Object.keys(batchMap).length > 0) {
        next[plan.batch_code] = batchMap;
      }
    }
    setPecEnrollments(next);
  }

  async function handleRun() {
    if (selectedBatches.length === 0) {
      setError("Select at least one student batch.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const batch_plans: BatchSemesterPlanInput[] = await Promise.all(
        selectedBatches.map(async (batch_code) => {
          const semester_number = semesterByBatch[batch_code] ?? 5;
          let pecCourses = pecCoursesByBatch[batch_code];
          if (!pecCourses) {
            const rows = await fetchCourses(semester_number, batch_code);
            pecCourses = rows.filter((course) => isPecCourseType(course.course_type));
          }
          return {
            batch_code,
            semester_number,
            pec_enrollments: buildPecEnrollmentsPayload(
              batch_code,
              pecCourses,
              pecEnrollments,
            ),
          };
        }),
      );
      const run = await runAllocation({
        batch_plans,
        schedule_timetable: true,
      });
      if (run.status === "failed") {
        setError(run.error_message ?? run.messages?.[0] ?? "Allocation failed");
        return;
      }
      setResult(run);
      restorePecEnrollmentsFromRun(run);
      savedPlans.reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Allocation failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleLoadPlan(runId: number) {
    setLoadPlanLoading(true);
    setError(null);
    try {
      const loaded = await fetchAllocationRun(runId);
      setResult(loaded);
      restorePecEnrollmentsFromRun(loaded);
      setSemesterByBatch((current) => {
        const next = { ...current };
        for (const plan of loaded.batch_plans ?? []) {
          next[plan.batch_code] = plan.semester_number;
        }
        return next;
      });
      setSelectedBatches(loaded.batch_codes ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load saved plan.");
    } finally {
      setLoadPlanLoading(false);
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
        <LoadingState message="Assigning workload and building timetable (greedy, all batches)…" />
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
          <div className="space-y-3">
            {(batches.data ?? []).map((batch) => {
              const isSelected = selectedBatches.includes(batch.batch_code);
              const semester =
                semesterByBatch[batch.batch_code] ?? batch.default_planning_semester;

              return (
                <div
                  key={batch.batch_code}
                  className={`rounded-lg border ${
                    isSelected ? "border-slate-300 bg-white" : "border-slate-100 bg-slate-50/50"
                  }`}
                >
                  <div className="flex flex-wrap items-center gap-3 px-3 py-2.5">
                    <label className="inline-flex min-w-[6rem] items-center gap-2 font-medium text-slate-900">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleBatch(batch.batch_code)}
                      />
                      {batch.batch_code}
                    </label>
                    <label className="inline-flex items-center gap-2 text-slate-600">
                      Semester
                      <select
                        value={semester}
                        onChange={(e) => setBatchSemester(batch.batch_code, Number(e.target.value))}
                        disabled={!isSelected}
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
                  {isSelected && (
                    <div className="border-t border-slate-200 px-3 py-3">
                      <PecCourseEnrollments
                        batchCode={batch.batch_code}
                        semesterNumber={semester}
                        enabled={isSelected}
                        enrollments={pecEnrollments[batch.batch_code] ?? {}}
                        onChange={(courseCode, studentCount) =>
                          setPecEnrollment(batch.batch_code, courseCode, studentCount)
                        }
                        onCoursesLoaded={(courses) =>
                          handlePecCoursesLoaded(batch.batch_code, courses)
                        }
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}
      {!batches.loading && (
        <section className="mb-6 rounded-lg border border-slate-200 bg-white p-4">
          <h2 className="text-sm font-semibold text-slate-900">Previous runs</h2>
          <p className="mb-3 text-xs text-slate-600">
            Open a past allocation version without running again.
          </p>
          {savedPlans.loading && (
            <p className="text-sm text-slate-500">Loading previous runs…</p>
          )}
          {savedPlans.error && (
            <ErrorState message={savedPlans.error} onRetry={savedPlans.reload} />
          )}
          {!savedPlans.loading && !savedPlans.error && (
            <label className="flex max-w-3xl flex-col gap-1 text-sm text-slate-700">
              Select run
              <select
                value={result?.id ?? ""}
                disabled={loadPlanLoading || (savedPlans.data?.length ?? 0) === 0}
                onChange={(event) => {
                  const runId = Number(event.target.value);
                  if (runId > 0) {
                    void handleLoadPlan(runId);
                  }
                }}
                className="rounded-lg border border-slate-300 bg-white px-3 py-2"
              >
                <option value="">
                  {(savedPlans.data?.length ?? 0) === 0
                    ? "No previous runs yet"
                    : "Choose a previous run…"}
                </option>
                {(savedPlans.data ?? []).map((plan) => (
                  <option key={plan.id} value={plan.id}>
                    {plan.is_saved ? "★ " : ""}
                    {plan.plan_name} — {plan.batch_label}
                    {plan.updated_at
                      ? ` · ${new Date(plan.updated_at).toLocaleString()}`
                      : ""}
                  </option>
                ))}
              </select>
            </label>
          )}
          {loadPlanLoading && (
            <p className="mt-2 text-xs text-slate-500">Loading selected run…</p>
          )}
        </section>
      )}
      {result && !loading && (
        <AllocationResults
          result={result}
          onResultChange={setResult}
          onPlansChanged={savedPlans.reload}
        />
      )}
    </>
  );
}

function AllocationResults({
  result,
  onResultChange,
  onPlansChanged,
}: {
  result: AllocationRun;
  onResultChange: (run: AllocationRun) => void;
  onPlansChanged: () => void;
}) {
  const facultyRoster = useFetch(fetchFaculty);
  const [isEditing, setIsEditing] = useState(false);
  const [draftAssignments, setDraftAssignments] = useState<AllocationAssignment[]>([]);
  const [planName, setPlanName] = useState(result.plan_name ?? "");
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    setPlanName(result.plan_name ?? "");
    setIsEditing(false);
    setDraftAssignments(result.assignments.map((row) => ({ ...row })));
  }, [result.id]);

  const planLabel = result.batch_plans
    .map((plan) => `${plan.batch_code} (sem ${plan.semester_number}, ${plan.section_count} sec)`)
    .join(" · ");

  function startEditing() {
    setDraftAssignments(result.assignments.map((row) => ({ ...row })));
    setIsEditing(true);
  }

  function cancelEditing() {
    setDraftAssignments(result.assignments.map((row) => ({ ...row })));
    setIsEditing(false);
  }

  async function handleSavePlan() {
    const trimmedName = planName.trim();
    if (!trimmedName) {
      setSaveError("Enter a plan name before saving.");
      return;
    }
    setSaveLoading(true);
    setSaveError(null);
    try {
      const updated = await updateAllocationRun(result.id, {
        plan_name: trimmedName,
        is_saved: true,
        assignments: isEditing ? draftAssignments : result.assignments,
      });
      onResultChange(updated);
      setIsEditing(false);
      onPlansChanged();
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Could not save plan.");
    } finally {
      setSaveLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <section className="rounded-lg border border-slate-200 bg-white p-4">
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex min-w-[14rem] flex-1 flex-col gap-1 text-sm text-slate-700">
            Plan name
            <input
              type="text"
              value={planName}
              onChange={(event) => setPlanName(event.target.value)}
              placeholder="e.g. AIML Sem 5 draft"
              className="rounded-lg border border-slate-300 px-3 py-2"
            />
          </label>
          {!isEditing ? (
            <button
              type="button"
              onClick={startEditing}
              className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Edit assignments
            </button>
          ) : (
            <button
              type="button"
              onClick={cancelEditing}
              className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Cancel edit
            </button>
          )}
          <button
            type="button"
            onClick={handleSavePlan}
            disabled={saveLoading}
            className="rounded-lg bg-emerald-700 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-600 disabled:opacity-50"
          >
            {saveLoading ? "Saving…" : "Save plan"}
          </button>
        </div>
        {saveError && <p className="mt-3 text-sm text-red-600">{saveError}</p>}
        {result.is_saved && (
          <p className="mt-2 text-xs text-emerald-700">
            Saved plan{result.updated_at ? ` · last updated ${new Date(result.updated_at).toLocaleString()}` : ""}
          </p>
        )}
      </section>
      <div className="flex flex-wrap gap-3 text-sm text-slate-600">
        <span>Run #{result.id}</span>
        <span>{planLabel}</span>
        <Badge variant={isSolverOk(result.status) ? "success" : "warning"}>
          workload: {result.status}
        </Badge>
        {result.timetable_status && (
          <Badge variant={isSolverOk(result.timetable_status) ? "success" : "warning"}>
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
      <AllocationReportPanel result={result} />
      {(result.timetable_grid ||
        (result.section_timetable_grids?.length ?? 0) > 0 ||
        (result.faculty_timetable_grids?.length ?? 0) > 0 ||
        (result.classroom_timetable_grids?.length ?? 0) > 0 ||
        (result.laboratory_timetable_grids?.length ?? 0) > 0) && (
        <TimetableResults result={result} facultyRoster={facultyRoster} />
      )}
      <section>
        <div className="mb-3 flex items-center justify-between gap-2">
          <h2 className="text-lg font-semibold text-slate-900">Workload assignments</h2>
          {isEditing && (
            <span className="text-xs font-medium uppercase tracking-wide text-amber-700">
              Editing — change faculty, then Save plan
            </span>
          )}
        </div>
        {facultyRoster.data ? (
          <EditableAssignmentsTable
            assignments={isEditing ? draftAssignments : result.assignments}
            faculty={facultyRoster.data}
            editing={isEditing}
            onChange={setDraftAssignments}
          />
        ) : facultyRoster.loading ? (
          <LoadingState message="Loading faculty roster…" />
        ) : (
          <ErrorState message={facultyRoster.error ?? "Faculty roster unavailable."} />
        )}
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

type TimetableTab = "department" | "sections" | "faculty" | "classrooms" | "labs";

function sectionGridKey(batchCode: string, sectionIndex: number): string {
  return `${batchCode}::${sectionIndex}`;
}

function roomGridKey(roomType: string, roomName: string): string {
  return `${roomType}::${roomName}`;
}

function TimetableResults({
  result,
  facultyRoster,
}: {
  result: AllocationRun;
  facultyRoster: ReturnType<typeof useFetch<import("@/types/api").FacultyMember[]>>;
}) {
  const [tab, setTab] = useState<TimetableTab>("sections");
  const [facultyId, setFacultyId] = useState<number | null>(null);
  const [sectionKey, setSectionKey] = useState<string | null>(null);
  const [classroomKey, setClassroomKey] = useState<string | null>(null);
  const [laboratoryKey, setLaboratoryKey] = useState<string | null>(null);

  const facultyById = useMemo(
    () => new Map((facultyRoster.data ?? []).map((member) => [member.id, member])),
    [facultyRoster.data],
  );

  const facultyGrids = result.faculty_timetable_grids ?? [];
  const sectionGrids = result.section_timetable_grids ?? [];
  const classroomGrids = result.classroom_timetable_grids ?? [];
  const laboratoryGrids = result.laboratory_timetable_grids ?? [];

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

  const selectedClassroomGrid = useMemo(() => {
    if (classroomGrids.length === 0) {
      return null;
    }
    const defaultKey = roomGridKey(classroomGrids[0].room_type, classroomGrids[0].room_name);
    const targetKey = classroomKey ?? defaultKey;
    return (
      classroomGrids.find(
        (item) => roomGridKey(item.room_type, item.room_name) === targetKey,
      ) ?? classroomGrids[0]
    );
  }, [classroomGrids, classroomKey]);

  const selectedLaboratoryGrid = useMemo(() => {
    if (laboratoryGrids.length === 0) {
      return null;
    }
    const defaultKey = roomGridKey(laboratoryGrids[0].room_type, laboratoryGrids[0].room_name);
    const targetKey = laboratoryKey ?? defaultKey;
    return (
      laboratoryGrids.find(
        (item) => roomGridKey(item.room_type, item.room_name) === targetKey,
      ) ?? laboratoryGrids[0]
    );
  }, [laboratoryGrids, laboratoryKey]);

  const sectionContactGroups = useMemo(() => {
    if (!selectedSectionGrid || !facultyRoster.data) {
      return [];
    }
    return buildSectionContactGroups(
      selectedSectionGrid.batch_code,
      selectedSectionGrid.section_index,
      selectedSectionGrid.semester_number,
      result.assignments,
      facultyById,
    );
  }, [selectedSectionGrid, facultyRoster.data, result.assignments, facultyById]);

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
        {result.timetable_status && !isSolverOk(result.timetable_status) && (
          <p className="mt-1 text-sm text-amber-700">
            Timetable status: {result.timetable_status}. Section grids may be empty until scheduling
            succeeds.
          </p>
        )}
        {result.timetable_status && isSolverOk(result.timetable_status) && (
          <p className="mt-1 text-sm text-slate-600">
            Greedy timetable across all selected batches (first available slot).
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
        <button
          type="button"
          onClick={() => setTab("classrooms")}
          className={tabClass(tab === "classrooms")}
          disabled={classroomGrids.length === 0}
        >
          By classroom ({classroomGrids.length})
        </button>
        <button
          type="button"
          onClick={() => setTab("labs")}
          className={tabClass(tab === "labs")}
          disabled={laboratoryGrids.length === 0}
        >
          By lab ({laboratoryGrids.length})
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
          <TimetableGridView
            grid={selectedSectionGrid.grid}
            compact
            hideBatch
            footer={
              facultyRoster.loading ? (
                <p className="px-3 py-2 text-xs text-slate-500">Loading faculty contacts…</p>
              ) : facultyRoster.error ? (
                <p className="px-3 py-2 text-xs text-red-600">{facultyRoster.error}</p>
              ) : (
                <ClassFacultyContactsFooter groups={sectionContactGroups} />
              )
            }
          />
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
          <TimetableGridView grid={selectedFacultyGrid.grid} compact hideRoom />
        </div>
      )}
      {tab === "classrooms" && selectedClassroomGrid && (
        <div className="space-y-3">
          <label className="flex flex-wrap items-center gap-2 text-sm text-slate-700">
            Classroom
            <select
              value={roomGridKey(selectedClassroomGrid.room_type, selectedClassroomGrid.room_name)}
              onChange={(e) => setClassroomKey(e.target.value)}
              className="rounded-lg border border-slate-300 bg-white px-3 py-2"
            >
              {classroomGrids.map((item) => (
                <option
                  key={roomGridKey(item.room_type, item.room_name)}
                  value={roomGridKey(item.room_type, item.room_name)}
                >
                  Room {item.room_name}
                </option>
              ))}
            </select>
          </label>
          <TimetableGridView grid={selectedClassroomGrid.grid} compact hideRoom />
        </div>
      )}
      {tab === "labs" && selectedLaboratoryGrid && (
        <div className="space-y-3">
          <label className="flex flex-wrap items-center gap-2 text-sm text-slate-700">
            Laboratory
            <select
              value={roomGridKey(selectedLaboratoryGrid.room_type, selectedLaboratoryGrid.room_name)}
              onChange={(e) => setLaboratoryKey(e.target.value)}
              className="rounded-lg border border-slate-300 bg-white px-3 py-2"
            >
              {laboratoryGrids.map((item) => (
                <option
                  key={roomGridKey(item.room_type, item.room_name)}
                  value={roomGridKey(item.room_type, item.room_name)}
                >
                  Lab {item.room_name}
                </option>
              ))}
            </select>
          </label>
          <TimetableGridView
            grid={selectedLaboratoryGrid.grid}
            compact
            hideRoom
            showLabFaculty
          />
        </div>
      )}
    </section>
  );
}

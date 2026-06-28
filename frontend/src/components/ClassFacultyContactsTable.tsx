import { useMemo } from "react";
import type {
  AllocationAssignment,
  BatchSemesterPlan,
  FacultyMember,
} from "@/types/api";

export interface ClassFacultyContactRow {
  batch_code: string;
  section_index: number;
  semester_number: number;
  course_code: string;
  course_name: string;
  course_type: string;
  kind: string;
  weekly_hours: number;
  faculty_id: number | null;
  faculty_name: string;
  designation: string | null;
  email: string | null;
  phone: string | null;
  cabin_number: string | null;
}

function assignmentToContactRows(
  assignment: AllocationAssignment,
  batchCode: string,
  sectionIndex: number,
  semesterNumber: number,
  facultyById: Map<number, FacultyMember>,
): ClassFacultyContactRow[] {
  const facultyIds = assignment.faculty_ids ?? [];
  const facultyNames = assignment.faculty_names ?? [];
  const pairCount = Math.max(facultyIds.length, facultyNames.length, 1);

  return Array.from({ length: pairCount }, (_, index) => {
    const facultyId = facultyIds[index] ?? null;
    const member = facultyId !== null ? facultyById.get(facultyId) : undefined;
    const facultyName = facultyNames[index] ?? member?.full_name ?? "—";

    return {
      batch_code: batchCode,
      section_index: sectionIndex,
      semester_number: semesterNumber,
      course_code: assignment.course_code,
      course_name: assignment.course_name,
      course_type: assignment.course_type,
      kind: assignment.kind,
      weekly_hours: assignment.weekly_hours,
      faculty_id: facultyId,
      faculty_name: facultyName,
      designation: member?.designation ?? null,
      email: member?.email ?? null,
      phone: member?.phone ?? null,
      cabin_number: member?.cabin_number ?? null,
    };
  });
}

function sortContactRows(rows: ClassFacultyContactRow[]): ClassFacultyContactRow[] {
  return [...rows].sort((left, right) => {
    const courseCompare = left.course_code.localeCompare(right.course_code);
    if (courseCompare !== 0) {
      return courseCompare;
    }
    const kindCompare = left.kind.localeCompare(right.kind);
    if (kindCompare !== 0) {
      return kindCompare;
    }
    return left.faculty_name.localeCompare(right.faculty_name);
  });
}

export function buildSectionContactRows(
  batchCode: string,
  sectionIndex: number,
  semesterNumber: number,
  assignments: AllocationAssignment[],
  facultyById: Map<number, FacultyMember>,
): ClassFacultyContactRow[] {
  const rows = assignments
    .filter(
      (assignment) =>
        assignment.batch_code === batchCode &&
        assignment.section_indices.includes(sectionIndex),
    )
    .flatMap((assignment) =>
      assignmentToContactRows(
        assignment,
        batchCode,
        sectionIndex,
        semesterNumber,
        facultyById,
      ),
    );

  return sortContactRows(rows);
}

export function buildClassFacultyContactRows(
  assignments: AllocationAssignment[],
  batchPlans: BatchSemesterPlan[],
  facultyById: Map<number, FacultyMember>,
): ClassFacultyContactRow[] {
  const rows = batchPlans.flatMap((plan) =>
    Array.from({ length: plan.section_count }, (_, index) =>
      buildSectionContactRows(
        plan.batch_code,
        index + 1,
        plan.semester_number,
        assignments,
        facultyById,
      ),
    ).flat(),
  );

  return rows.sort((left, right) => {
    const batchCompare = left.batch_code.localeCompare(right.batch_code);
    if (batchCompare !== 0) {
      return batchCompare;
    }
    if (left.section_index !== right.section_index) {
      return left.section_index - right.section_index;
    }
    const courseCompare = left.course_code.localeCompare(right.course_code);
    if (courseCompare !== 0) {
      return courseCompare;
    }
    return left.faculty_name.localeCompare(right.faculty_name);
  });
}

interface ClassFacultyContactsFooterProps {
  rows: ClassFacultyContactRow[];
}

/** Compact faculty table meant to sit directly under the timetable grid. */
export function ClassFacultyContactsFooter({ rows }: ClassFacultyContactsFooterProps) {
  if (rows.length === 0) {
    return null;
  }

  return (
    <table className="min-w-full border-collapse text-xs">
      <thead>
        <tr className="bg-slate-100 text-slate-800">
          <th className="border border-slate-300 px-2 py-1.5 text-left font-semibold">Subject</th>
          <th className="border border-slate-300 px-2 py-1.5 text-left font-semibold">
            Course code
          </th>
          <th className="border border-slate-300 px-2 py-1.5 text-left font-semibold">Session</th>
          <th className="border border-slate-300 px-2 py-1.5 text-left font-semibold">Faculty</th>
          <th className="border border-slate-300 px-2 py-1.5 text-left font-semibold">
            Designation
          </th>
          <th className="border border-slate-300 px-2 py-1.5 text-left font-semibold">Email</th>
          <th className="border border-slate-300 px-2 py-1.5 text-left font-semibold">Phone</th>
          <th className="border border-slate-300 px-2 py-1.5 text-left font-semibold">Cabin</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr
            key={`${row.course_code}-${row.kind}-${row.faculty_id ?? row.faculty_name}`}
            className="bg-white hover:bg-slate-50"
          >
            <td className="border border-slate-300 px-2 py-1.5">{row.course_name}</td>
            <td className="border border-slate-300 px-2 py-1.5 font-mono">{row.course_code}</td>
            <td className="border border-slate-300 px-2 py-1.5 capitalize">{row.kind}</td>
            <td className="border border-slate-300 px-2 py-1.5 font-medium">{row.faculty_name}</td>
            <td className="border border-slate-300 px-2 py-1.5">{row.designation ?? "—"}</td>
            <td className="border border-slate-300 px-2 py-1.5">
              {row.email ? (
                <a href={`mailto:${row.email}`} className="text-sky-700 hover:underline">
                  {row.email}
                </a>
              ) : (
                "—"
              )}
            </td>
            <td className="border border-slate-300 px-2 py-1.5">{row.phone ?? "—"}</td>
            <td className="border border-slate-300 px-2 py-1.5">{row.cabin_number ?? "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

interface SectionFacultyContactsFooterProps {
  batchCode: string;
  sectionIndex: number;
  semesterNumber: number;
  assignments: AllocationAssignment[];
  faculty: FacultyMember[];
}

export function SectionFacultyContactsFooter({
  batchCode,
  sectionIndex,
  semesterNumber,
  assignments,
  faculty,
}: SectionFacultyContactsFooterProps) {
  const facultyById = useMemo(
    () => new Map(faculty.map((member) => [member.id, member])),
    [faculty],
  );

  const rows = useMemo(
    () =>
      buildSectionContactRows(
        batchCode,
        sectionIndex,
        semesterNumber,
        assignments,
        facultyById,
      ),
    [batchCode, sectionIndex, semesterNumber, assignments, facultyById],
  );

  return <ClassFacultyContactsFooter rows={rows} />;
}

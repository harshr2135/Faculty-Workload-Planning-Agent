import { useMemo } from "react";
import type {
  AllocationAssignment,
  BatchSemesterPlan,
  FacultyMember,
} from "@/types/api";

export interface ClassFacultyContactFacultyDetail {
  faculty_id: number | null;
  faculty_name: string;
  designation: string | null;
  email: string | null;
  phone: string | null;
  cabin_number: string | null;
}

export interface ClassFacultyContactGroup {
  batch_code: string;
  section_index: number;
  semester_number: number;
  course_code: string;
  course_name: string;
  course_type: string;
  kind: string;
  weekly_hours: number;
  lab_sub_batch: string | null;
  faculty: ClassFacultyContactFacultyDetail[];
}

/** @deprecated Use ClassFacultyContactGroup for grouped rendering. */
export interface ClassFacultyContactRow extends ClassFacultyContactFacultyDetail {
  batch_code: string;
  section_index: number;
  semester_number: number;
  course_code: string;
  course_name: string;
  course_type: string;
  kind: string;
  weekly_hours: number;
  lab_sub_batch: string | null;
}

function assignmentToContactGroup(
  assignment: AllocationAssignment,
  batchCode: string,
  sectionIndex: number,
  semesterNumber: number,
  facultyById: Map<number, FacultyMember>,
): ClassFacultyContactGroup {
  const facultyIds = assignment.faculty_ids ?? [];
  const facultyNames = assignment.faculty_names ?? [];
  const pairCount = Math.max(facultyIds.length, facultyNames.length, 1);

  const faculty = Array.from({ length: pairCount }, (_, index) => {
    const facultyId = facultyIds[index] ?? null;
    const member = facultyId !== null ? facultyById.get(facultyId) : undefined;
    const facultyName = facultyNames[index] ?? member?.full_name ?? "—";

    return {
      faculty_id: facultyId,
      faculty_name: facultyName,
      designation: member?.designation ?? null,
      email: member?.email ?? null,
      phone: member?.phone ?? null,
      cabin_number: member?.cabin_number ?? null,
    };
  });

  return {
    batch_code: batchCode,
    section_index: sectionIndex,
    semester_number: semesterNumber,
    course_code: assignment.course_code,
    course_name: assignment.course_name,
    course_type: assignment.course_type,
    kind: assignment.kind,
    lab_sub_batch: assignment.lab_sub_batch ?? null,
    weekly_hours: assignment.weekly_hours,
    faculty,
  };
}

function sortContactGroups(groups: ClassFacultyContactGroup[]): ClassFacultyContactGroup[] {
  return [...groups].sort((left, right) => {
    const courseCompare = left.course_code.localeCompare(right.course_code);
    if (courseCompare !== 0) {
      return courseCompare;
    }
    const kindCompare = left.kind.localeCompare(right.kind);
    if (kindCompare !== 0) {
      return kindCompare;
    }
    const batchCompare = (left.lab_sub_batch ?? "").localeCompare(right.lab_sub_batch ?? "");
    if (batchCompare !== 0) {
      return batchCompare;
    }
    const leftName = left.faculty[0]?.faculty_name ?? "";
    const rightName = right.faculty[0]?.faculty_name ?? "";
    return leftName.localeCompare(rightName);
  });
}

export function buildSectionContactGroups(
  batchCode: string,
  sectionIndex: number,
  semesterNumber: number,
  assignments: AllocationAssignment[],
  facultyById: Map<number, FacultyMember>,
): ClassFacultyContactGroup[] {
  const groups = assignments
    .filter(
      (assignment) =>
        assignment.batch_code === batchCode &&
        assignment.section_indices.includes(sectionIndex),
    )
    .map((assignment) =>
      assignmentToContactGroup(
        assignment,
        batchCode,
        sectionIndex,
        semesterNumber,
        facultyById,
      ),
    );

  return sortContactGroups(groups);
}

/** @deprecated Use buildSectionContactGroups for merged multi-faculty rows. */
export function buildSectionContactRows(
  batchCode: string,
  sectionIndex: number,
  semesterNumber: number,
  assignments: AllocationAssignment[],
  facultyById: Map<number, FacultyMember>,
): ClassFacultyContactRow[] {
  return buildSectionContactGroups(
    batchCode,
    sectionIndex,
    semesterNumber,
    assignments,
    facultyById,
  ).flatMap((group) =>
    group.faculty.map((member) => ({
      batch_code: group.batch_code,
      section_index: group.section_index,
      semester_number: group.semester_number,
      course_code: group.course_code,
      course_name: group.course_name,
      course_type: group.course_type,
      kind: group.kind,
      weekly_hours: group.weekly_hours,
      lab_sub_batch: group.lab_sub_batch,
      ...member,
    })),
  );
}

export function buildClassFacultyContactGroups(
  assignments: AllocationAssignment[],
  batchPlans: BatchSemesterPlan[],
  facultyById: Map<number, FacultyMember>,
): ClassFacultyContactGroup[] {
  const groups = batchPlans.flatMap((plan) =>
    Array.from({ length: plan.section_count }, (_, index) =>
      buildSectionContactGroups(
        plan.batch_code,
        index + 1,
        plan.semester_number,
        assignments,
        facultyById,
      ),
    ).flat(),
  );

  return groups.sort((left, right) => {
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
    const leftName = left.faculty[0]?.faculty_name ?? "";
    const rightName = right.faculty[0]?.faculty_name ?? "";
    return leftName.localeCompare(rightName);
  });
}

interface ClassFacultyContactsFooterProps {
  groups: ClassFacultyContactGroup[];
}

/** Compact faculty table meant to sit directly under the timetable grid. */
export function ClassFacultyContactsFooter({ groups }: ClassFacultyContactsFooterProps) {
  if (groups.length === 0) {
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
          <th className="border border-slate-300 px-2 py-1.5 text-left font-semibold">
            Course type
          </th>
          <th className="border border-slate-300 px-2 py-1.5 text-left font-semibold">Session</th>
          <th className="border border-slate-300 px-2 py-1.5 text-left font-semibold">Lab batch</th>
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
        {groups.map((group) => {
          const groupKey = `${group.course_code}-${group.kind}-${group.lab_sub_batch ?? ""}`;
          const rowSpan = group.faculty.length;

          return group.faculty.map((member, index) => (
            <tr
              key={`${groupKey}-${member.faculty_id ?? member.faculty_name}-${index}`}
              className="bg-white hover:bg-slate-50"
            >
              {index === 0 && (
                <>
                  <td
                    rowSpan={rowSpan}
                    className="border border-slate-300 px-2 py-1.5 align-middle"
                  >
                    {group.course_name}
                  </td>
                  <td
                    rowSpan={rowSpan}
                    className="border border-slate-300 px-2 py-1.5 align-middle font-mono"
                  >
                    {group.course_code}
                  </td>
                  <td
                    rowSpan={rowSpan}
                    className="border border-slate-300 px-2 py-1.5 align-middle font-medium text-slate-700"
                  >
                    {group.course_type}
                  </td>
                  <td
                    rowSpan={rowSpan}
                    className="border border-slate-300 px-2 py-1.5 align-middle capitalize"
                  >
                    {group.kind}
                  </td>
                  <td
                    rowSpan={rowSpan}
                    className="border border-slate-300 px-2 py-1.5 align-middle"
                  >
                    {group.lab_sub_batch ?? "—"}
                  </td>
                </>
              )}
              <td className="border border-slate-300 px-2 py-1.5 font-medium">
                {member.faculty_name}
              </td>
              <td className="border border-slate-300 px-2 py-1.5">{member.designation ?? "—"}</td>
              <td className="border border-slate-300 px-2 py-1.5">
                {member.email ? (
                  <a href={`mailto:${member.email}`} className="text-sky-700 hover:underline">
                    {member.email}
                  </a>
                ) : (
                  "—"
                )}
              </td>
              <td className="border border-slate-300 px-2 py-1.5">{member.phone ?? "—"}</td>
              <td className="border border-slate-300 px-2 py-1.5">{member.cabin_number ?? "—"}</td>
            </tr>
          ));
        })}
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

  const groups = useMemo(
    () =>
      buildSectionContactGroups(
        batchCode,
        sectionIndex,
        semesterNumber,
        assignments,
        facultyById,
      ),
    [batchCode, sectionIndex, semesterNumber, assignments, facultyById],
  );

  return <ClassFacultyContactsFooter groups={groups} />;
}

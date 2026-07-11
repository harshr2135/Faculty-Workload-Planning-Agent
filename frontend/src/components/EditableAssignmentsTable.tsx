import type { AllocationAssignment, FacultyMember } from "@/types/api";
import {
  DataTable,
  DataTableBody,
  DataTableCell,
  DataTableHead,
  DataTableHeaderCell,
  EmptyRow,
} from "@/components/ui/DataTable";

const LAB_FACULTY_COUNT = 2;

interface EditableAssignmentsTableProps {
  assignments: AllocationAssignment[];
  faculty: FacultyMember[];
  editing: boolean;
  onChange: (assignments: AllocationAssignment[]) => void;
}

function updateFacultyForSlot(
  assignments: AllocationAssignment[],
  slotId: string,
  facultyIds: number[],
  faculty: FacultyMember[],
): AllocationAssignment[] {
  const facultyById = new Map(faculty.map((member) => [member.id, member]));
  return assignments.map((row) => {
    if (row.slot_id !== slotId) {
      return row;
    }
    const names = facultyIds.map(
      (id) => facultyById.get(id)?.full_name ?? `Faculty #${id}`,
    );
    return { ...row, faculty_ids: facultyIds, faculty_names: names };
  });
}

function FacultySelect({
  value,
  onChange,
  faculty,
  excludeIds = [],
}: {
  value: number | null;
  onChange: (value: number) => void;
  faculty: FacultyMember[];
  excludeIds?: number[];
}) {
  return (
    <select
      value={value ?? ""}
      onChange={(event) => onChange(Number(event.target.value))}
      className="w-full min-w-[10rem] rounded border border-slate-300 bg-white px-2 py-1 text-xs"
    >
      <option value="" disabled>
        Select faculty
      </option>
      {faculty
        .filter((member) => !excludeIds.includes(member.id) || member.id === value)
        .map((member) => (
          <option key={member.id} value={member.id}>
            {member.full_name}
          </option>
        ))}
    </select>
  );
}

export function EditableAssignmentsTable({
  assignments,
  faculty,
  editing,
  onChange,
}: EditableAssignmentsTableProps) {
  return (
    <DataTable>
      <DataTableHead>
        <DataTableHeaderCell>Batch</DataTableHeaderCell>
        <DataTableHeaderCell>Course</DataTableHeaderCell>
        <DataTableHeaderCell>Type</DataTableHeaderCell>
        <DataTableHeaderCell>Kind</DataTableHeaderCell>
        <DataTableHeaderCell>Sections</DataTableHeaderCell>
        <DataTableHeaderCell>Lab batch</DataTableHeaderCell>
        <DataTableHeaderCell>Hrs/wk</DataTableHeaderCell>
        <DataTableHeaderCell>Faculty</DataTableHeaderCell>
      </DataTableHead>
      <DataTableBody>
        {assignments.length === 0 ? (
            <EmptyRow colSpan={8} message="No assignments." />
        ) : (
          assignments.map((row) => (
            <tr key={row.slot_id} className="hover:bg-slate-50">
              <DataTableCell className="font-mono text-xs">{row.batch_code}</DataTableCell>
              <DataTableCell>
                <div className="font-mono text-xs">{row.course_code}</div>
                <div className="text-slate-600">{row.course_name}</div>
              </DataTableCell>
              <DataTableCell>{row.course_type}</DataTableCell>
              <DataTableCell>{row.kind}</DataTableCell>
              <DataTableCell>{row.section_indices.join(", ")}</DataTableCell>
              <DataTableCell>{row.lab_sub_batch ?? "—"}</DataTableCell>
              <DataTableCell>{row.weekly_hours}</DataTableCell>
              <DataTableCell>
                {editing ? (
                  row.kind === "lab" ? (
                    <div className="flex flex-col gap-1">
                      {Array.from({ length: LAB_FACULTY_COUNT }, (_, index) => {
                        const currentId = row.faculty_ids[index] ?? null;
                        const otherIds = row.faculty_ids.filter((_, i) => i !== index);
                        return (
                          <FacultySelect
                            key={`${row.slot_id}-${index}`}
                            value={currentId}
                            excludeIds={otherIds}
                            faculty={faculty}
                            onChange={(facultyId) => {
                              const nextIds = [...row.faculty_ids];
                              while (nextIds.length < LAB_FACULTY_COUNT) {
                                nextIds.push(faculty[0]?.id ?? 0);
                              }
                              nextIds[index] = facultyId;
                              onChange(
                                updateFacultyForSlot(assignments, row.slot_id, nextIds, faculty),
                              );
                            }}
                          />
                        );
                      })}
                    </div>
                  ) : (
                    <FacultySelect
                      value={row.faculty_ids[0] ?? null}
                      faculty={faculty}
                      onChange={(facultyId) =>
                        onChange(
                          updateFacultyForSlot(assignments, row.slot_id, [facultyId], faculty),
                        )
                      }
                    />
                  )
                ) : (
                  row.faculty_names.join(" · ")
                )}
              </DataTableCell>
            </tr>
          ))
        )}
      </DataTableBody>
    </DataTable>
  );
}

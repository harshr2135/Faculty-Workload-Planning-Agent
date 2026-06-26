import { useMemo, useState } from "react";
import { fetchCourses, fetchSemesters } from "@/api/courses";
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
import { Badge } from "@/components/ui/Badge";
import { useFetch } from "@/hooks/useFetch";

export default function CoursesPage() {
  const [semester, setSemester] = useState<number | "all">("all");
  const semesters = useFetch(fetchSemesters);
  const semesterFilter = semester === "all" ? undefined : semester;
  const courses = useFetch(() => fetchCourses(semesterFilter), [semester]);

  const loading = semesters.loading || courses.loading;
  const error = semesters.error || courses.error;

  const semesterOptions = useMemo(
    () => semesters.data?.map((s) => s.semester_number) ?? [],
    [semesters.data],
  );

  return (
    <>
      <PageHeader
        title="Courses"
        description="Subjects per semester with lecture and lab hours"
        action={
          <select
            value={semester}
            onChange={(e) =>
              setSemester(e.target.value === "all" ? "all" : Number(e.target.value))
            }
            className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
          >
            <option value="all">All semesters</option>
            {semesterOptions.map((n) => (
              <option key={n} value={n}>
                Semester {n}
              </option>
            ))}
          </select>
        }
      />
      {loading && <LoadingState />}
      {error && (
        <ErrorState
          message={error}
          onRetry={() => {
            semesters.reload();
            courses.reload();
          }}
        />
      )}
      {!loading && !error && courses.data && (
        <DataTable>
          <DataTableHead>
            <DataTableHeaderCell>Code</DataTableHeaderCell>
            <DataTableHeaderCell>Subject</DataTableHeaderCell>
            <DataTableHeaderCell>Semester</DataTableHeaderCell>
            <DataTableHeaderCell>Year</DataTableHeaderCell>
            <DataTableHeaderCell>Sections</DataTableHeaderCell>
            <DataTableHeaderCell>Credits</DataTableHeaderCell>
            <DataTableHeaderCell>Lectures/wk</DataTableHeaderCell>
            <DataTableHeaderCell>Lab hrs</DataTableHeaderCell>
          </DataTableHead>
          <DataTableBody>
            {courses.data.length === 0 ? (
              <EmptyRow colSpan={8} message="No courses found." />
            ) : (
              courses.data.map((course) => (
                <tr key={course.id} className="hover:bg-slate-50">
                  <DataTableCell className="font-mono text-xs">{course.course_code}</DataTableCell>
                  <DataTableCell>
                    <div className="font-medium text-slate-900">{course.name}</div>
                  </DataTableCell>
                  <DataTableCell>Sem {course.semester_number}</DataTableCell>
                  <DataTableCell>{course.year_label}</DataTableCell>
                  <DataTableCell>{course.section_count}</DataTableCell>
                  <DataTableCell>{course.credits}</DataTableCell>
                  <DataTableCell>{course.lectures_per_week}</DataTableCell>
                  <DataTableCell>
                    {course.has_lab ? (
                      <Badge variant="info">{course.practical_hours}h continuous</Badge>
                    ) : (
                      "—"
                    )}
                  </DataTableCell>
                </tr>
              ))
            )}
          </DataTableBody>
        </DataTable>
      )}
    </>
  );
}

import { useMemo, useState } from "react";
import { fetchCourses, fetchSemesters, fetchStudentBatches } from "@/api/courses";
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
  const [batch, setBatch] = useState<string | "all">("all");
  const semesters = useFetch(fetchSemesters);
  const batches = useFetch(fetchStudentBatches);
  const semesterFilter = semester === "all" ? undefined : semester;
  const batchFilter = batch === "all" ? undefined : batch;
  const courses = useFetch(
    () => fetchCourses(semesterFilter, batchFilter),
    [semester, batch],
  );

  const loading = semesters.loading || batches.loading || courses.loading;
  const error = semesters.error || batches.error || courses.error;

  const semesterOptions = useMemo(
    () => semesters.data?.map((s) => s.semester_number) ?? [],
    [semesters.data],
  );

  const batchOptions = useMemo(
    () => batches.data?.map((b) => b.batch_code) ?? [],
    [batches.data],
  );

  return (
    <>
      <PageHeader
        title="Courses"
        description="Subjects per student batch and semester (PEC/SEC use lecture halls)"
        action={
          <div className="flex flex-wrap gap-2">
            <select
              value={batch}
              onChange={(e) => setBatch(e.target.value === "all" ? "all" : e.target.value)}
              className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
            >
              <option value="all">All batches</option>
              {batchOptions.map((code) => (
                <option key={code} value={code}>
                  Batch {code}
                </option>
              ))}
            </select>
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
          </div>
        }
      />
      {loading && <LoadingState />}
      {error && (
        <ErrorState
          message={error}
          onRetry={() => {
            semesters.reload();
            batches.reload();
            courses.reload();
          }}
        />
      )}
      {!loading && !error && courses.data && (
        <DataTable>
          <DataTableHead>
            <DataTableHeaderCell>Code</DataTableHeaderCell>
            <DataTableHeaderCell>Subject</DataTableHeaderCell>
            <DataTableHeaderCell>Batch</DataTableHeaderCell>
            <DataTableHeaderCell>Type</DataTableHeaderCell>
            <DataTableHeaderCell>Semester</DataTableHeaderCell>
            <DataTableHeaderCell>Year</DataTableHeaderCell>
            <DataTableHeaderCell>Credits</DataTableHeaderCell>
            <DataTableHeaderCell>Lectures/wk</DataTableHeaderCell>
            <DataTableHeaderCell>Lab hrs</DataTableHeaderCell>
          </DataTableHead>
          <DataTableBody>
            {courses.data.length === 0 ? (
              <EmptyRow colSpan={9} message="No courses found." />
            ) : (
              courses.data.map((course) => (
                <tr key={course.id} className="hover:bg-slate-50">
                  <DataTableCell className="font-mono text-xs">{course.course_code}</DataTableCell>
                  <DataTableCell>
                    <div className="font-medium text-slate-900">{course.name}</div>
                  </DataTableCell>
                  <DataTableCell>{course.batch_code}</DataTableCell>
                  <DataTableCell>
                    <Badge variant={course.requires_lecture_hall ? "warning" : "default"}>
                      {course.course_type}
                      {course.requires_lecture_hall ? " · LH" : ""}
                    </Badge>
                  </DataTableCell>
                  <DataTableCell>Sem {course.semester_number}</DataTableCell>
                  <DataTableCell>{course.year_label}</DataTableCell>
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

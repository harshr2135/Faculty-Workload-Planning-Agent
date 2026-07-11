import { useEffect, useMemo, useRef, useState } from "react";
import { fetchCourses } from "@/api/courses";
import type { Course } from "@/types/api";

export function normalizePecGroup(value: string): string {
  return value.trim().toUpperCase().replace(/\s+/g, " ");
}

export function isPecCourseType(courseType: string): boolean {
  const normalized = normalizePecGroup(courseType);
  return normalized === "PEC" || /^PEC \d+$/.test(normalized);
}

/** batch_code → course_code → student_count */
export type PecEnrollmentMap = Record<string, Record<string, number>>;

interface PecCourseEnrollmentsProps {
  batchCode: string;
  semesterNumber: number;
  enabled: boolean;
  enrollments: Record<string, number>;
  onChange: (courseCode: string, studentCount: number) => void;
  onCoursesLoaded?: (courses: Course[]) => void;
}

function parseStudentCount(raw: string): number {
  if (raw.trim() === "") {
    return 0;
  }
  const parsed = Number.parseInt(raw, 10);
  return Number.isFinite(parsed) ? Math.max(0, parsed) : 0;
}

export function PecCourseEnrollments({
  batchCode,
  semesterNumber,
  enabled,
  enrollments,
  onChange,
  onCoursesLoaded,
}: PecCourseEnrollmentsProps) {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const onCoursesLoadedRef = useRef(onCoursesLoaded);

  useEffect(() => {
    onCoursesLoadedRef.current = onCoursesLoaded;
  }, [onCoursesLoaded]);

  useEffect(() => {
    if (!enabled) {
      setCourses([]);
      setLoading(false);
      setError(null);
      return;
    }

    let active = true;
    setLoading(true);
    setError(null);

    fetchCourses(semesterNumber, batchCode)
      .then((rows) => {
        if (!active) {
          return;
        }
        const pecCourses = rows
          .filter((course) => isPecCourseType(course.course_type))
          .sort((left, right) => {
            const groupCompare = normalizePecGroup(left.course_type).localeCompare(
              normalizePecGroup(right.course_type),
              undefined,
              { numeric: true },
            );
            if (groupCompare !== 0) {
              return groupCompare;
            }
            return left.course_code.localeCompare(right.course_code);
          });
        setCourses(pecCourses);
        onCoursesLoadedRef.current?.(pecCourses);
      })
      .catch((err) => {
        if (!active) {
          return;
        }
        setError(err instanceof Error ? err.message : "Could not load PEC courses.");
        setCourses([]);
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [batchCode, semesterNumber, enabled]);

  const groupedCourses = useMemo(() => {
    const groups = new Map<string, Course[]>();
    for (const course of courses) {
      const key = normalizePecGroup(course.course_type);
      const bucket = groups.get(key) ?? [];
      bucket.push(course);
      groups.set(key, bucket);
    }
    return [...groups.entries()].sort(([left], [right]) =>
      left.localeCompare(right, undefined, { numeric: true }),
    );
  }, [courses]);

  const activeCount = useMemo(
    () => courses.filter((course) => (enrollments[course.course_code] ?? 0) > 0).length,
    [courses, enrollments],
  );

  if (!enabled) {
    return null;
  }

  if (loading) {
    return <p className="text-xs text-slate-500">Loading PEC electives…</p>;
  }

  if (error) {
    return <p className="text-xs text-red-600">{error}</p>;
  }

  if (groupedCourses.length === 0) {
    return (
      <p className="text-xs text-slate-500">
        No PEC electives for semester {semesterNumber} (PEC starts from semester 5).
      </p>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-sm font-medium text-slate-800">
            PEC electives · semester {semesterNumber}
          </p>
          <p className="text-xs text-slate-500">
            Enter student counts for electives offered this semester. Only courses with count &gt; 0
            are included in allocation.
          </p>
        </div>
        <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
          {activeCount} / {courses.length} active
        </span>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {groupedCourses.map(([groupLabel, groupCourses]) => {
          const poolTotal = groupCourses.reduce(
            (sum, course) => sum + (enrollments[course.course_code] ?? 0),
            0,
          );
          const poolActive = groupCourses.filter(
            (course) => (enrollments[course.course_code] ?? 0) > 0,
          ).length;

          return (
            <div
              key={groupLabel}
              className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm"
            >
              <div className="flex items-center justify-between border-b border-indigo-100 bg-indigo-50 px-3 py-2">
                <h4 className="text-xs font-semibold uppercase tracking-wide text-indigo-900">
                  {groupLabel}
                </h4>
                <span className="text-[11px] text-indigo-700">
                  {poolActive} active · {poolTotal} students
                </span>
              </div>
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50 text-left text-slate-600">
                    <th className="px-2 py-1.5 font-medium">Code</th>
                    <th className="px-2 py-1.5 font-medium">Course</th>
                    <th className="w-20 px-2 py-1.5 text-right font-medium">Students</th>
                  </tr>
                </thead>
                <tbody>
                  {groupCourses.map((course) => {
                    const count = enrollments[course.course_code] ?? 0;
                    const isActive = count > 0;
                    const needsLectureHall = count > 150;

                    return (
                      <tr
                        key={course.course_code}
                        className={`border-b border-slate-50 last:border-b-0 ${
                          isActive ? "bg-emerald-50/60" : "bg-white"
                        }`}
                      >
                        <td className="whitespace-nowrap px-2 py-1.5 font-mono text-slate-700">
                          {course.course_code}
                        </td>
                        <td className="px-2 py-1.5 text-slate-800">
                          <span className="line-clamp-2" title={course.name}>
                            {course.name}
                          </span>
                          {needsLectureHall && (
                            <span className="mt-0.5 block text-[10px] text-amber-700">
                              Lecture hall (&gt;150)
                            </span>
                          )}
                        </td>
                        <td className="px-2 py-1.5 text-right">
                          <input
                            type="number"
                            min={0}
                            step={1}
                            inputMode="numeric"
                            value={count === 0 ? "" : count}
                            placeholder="0"
                            onChange={(event) => {
                              onChange(course.course_code, parseStudentCount(event.target.value));
                            }}
                            onBlur={(event) => {
                              onChange(course.course_code, parseStudentCount(event.target.value));
                            }}
                            className={`w-full rounded border px-1.5 py-1 text-right tabular-nums ${
                              isActive
                                ? "border-emerald-300 bg-white"
                                : "border-slate-200 bg-slate-50"
                            }`}
                            aria-label={`Students enrolled in ${course.name}`}
                          />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function buildPecEnrollmentsPayload(
  batchCode: string,
  courses: Course[],
  enrollments: PecEnrollmentMap,
): { course_code: string; student_count: number }[] {
  const batchEnrollments = enrollments[batchCode] ?? {};
  return courses
    .filter((course) => isPecCourseType(course.course_type))
    .map((course) => ({
      course_code: course.course_code,
      student_count: batchEnrollments[course.course_code] ?? 0,
    }));
}

/** @deprecated Alias kept for older imports */
export const PecGroupEnrollments = PecCourseEnrollments;

/** @deprecated Use buildPecEnrollmentsPayload */
export function buildPecGroupEnrollmentsPayload(
  batchCode: string,
  courses: Course[],
  enrollments: PecEnrollmentMap,
): { course_code: string; student_count: number }[] {
  return buildPecEnrollmentsPayload(batchCode, courses, enrollments);
}

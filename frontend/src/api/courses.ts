import { apiGet } from "./client";
import type { Course, Semester, StudentBatch } from "@/types/api";

export function fetchCourses(semester?: number, batch?: string): Promise<Course[]> {
  const params = new URLSearchParams();
  if (semester !== undefined) params.set("semester", String(semester));
  if (batch) params.set("batch", batch);
  const query = params.toString() ? `?${params.toString()}` : "";
  return apiGet<Course[]>(`/courses${query}`);
}

export function fetchSemesters(): Promise<Semester[]> {
  return apiGet<Semester[]>("/semesters");
}

export function fetchStudentBatches(): Promise<StudentBatch[]> {
  return apiGet<StudentBatch[]>("/student-batches");
}

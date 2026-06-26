import { apiGet } from "./client";
import type { Course, Semester } from "@/types/api";

export function fetchCourses(semester?: number): Promise<Course[]> {
  const query = semester ? `?semester=${semester}` : "";
  return apiGet<Course[]>(`/courses${query}`);
}

export function fetchSemesters(): Promise<Semester[]> {
  return apiGet<Semester[]>("/semesters");
}

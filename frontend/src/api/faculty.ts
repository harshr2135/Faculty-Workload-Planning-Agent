import { apiGet } from "./client";
import type { FacultyMember } from "@/types/api";

export function fetchFaculty(): Promise<FacultyMember[]> {
  return apiGet<FacultyMember[]>("/faculty");
}

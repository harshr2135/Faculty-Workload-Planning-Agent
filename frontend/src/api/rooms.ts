import { apiGet } from "./client";
import type { Classroom, Laboratory } from "@/types/api";

export function fetchClassrooms(): Promise<Classroom[]> {
  return apiGet<Classroom[]>("/classrooms");
}

export function fetchLaboratories(): Promise<Laboratory[]> {
  return apiGet<Laboratory[]>("/laboratories");
}

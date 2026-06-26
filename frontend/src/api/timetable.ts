import { apiGet } from "./client";
import type { TimetableOverview } from "@/types/api";

export function fetchTimetableOverview(): Promise<TimetableOverview> {
  return apiGet<TimetableOverview>("/timetable/overview");
}

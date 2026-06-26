import { apiGet, apiPost } from "./client";
import type { AllocationRun, BatchSemesterPlanInput } from "@/types/api";

export interface AllocationRunRequest {
  batch_plans?: BatchSemesterPlanInput[];
  batch_codes?: string[];
  batch_code?: string;
  semester_number?: number;
  max_time_seconds?: number;
  schedule_timetable?: boolean;
}

export function runAllocation(body: AllocationRunRequest): Promise<AllocationRun> {
  return apiPost<AllocationRun>("/allocations/run", body);
}

export function fetchAllocationRun(runId: number): Promise<AllocationRun> {
  return apiGet<AllocationRun>(`/allocations/${runId}`);
}

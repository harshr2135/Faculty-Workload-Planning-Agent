import { apiGet, apiPatch, apiPost } from "./client";
import type { AllocationAssignment, AllocationRun, BatchSemesterPlanInput } from "@/types/api";

export interface AllocationRunRequest {
  batch_plans?: BatchSemesterPlanInput[];
  batch_codes?: string[];
  batch_code?: string;
  semester_number?: number;
  max_time_seconds?: number;
  schedule_timetable?: boolean;
}

export interface AllocationRunSummary {
  id: number;
  plan_name: string;
  is_saved: boolean;
  batch_codes: string[];
  batch_label: string;
  status: string;
  timetable_status: string | null;
  assignment_count: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface AllocationRunUpdateRequest {
  plan_name?: string;
  is_saved?: boolean;
  assignments?: AllocationAssignment[];
}

export function runAllocation(body: AllocationRunRequest): Promise<AllocationRun> {
  return apiPost<AllocationRun>("/allocations/run", body);
}

export function fetchAllocationRuns(savedOnly = false): Promise<AllocationRunSummary[]> {
  const query = savedOnly ? "?saved_only=true" : "";
  return apiGet<AllocationRunSummary[]>(`/allocations${query}`);
}

export function fetchAllocationRun(runId: number): Promise<AllocationRun> {
  return apiGet<AllocationRun>(`/allocations/${runId}`);
}

export function updateAllocationRun(
  runId: number,
  body: AllocationRunUpdateRequest,
): Promise<AllocationRun> {
  return apiPatch<AllocationRun>(`/allocations/${runId}`, body);
}

export function defaultMaxTimeSeconds(_batchCount: number): number {
  return 120;
}

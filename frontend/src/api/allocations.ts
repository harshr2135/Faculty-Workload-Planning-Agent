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

export type ReportMode =
  | "template"
  | "llm_summary"
  | "llm_full_facts"
  | "llm_full_raw";

export interface BatchReportRequest {
  batch_code: string;
  semester_number: number;
  report_mode?: ReportMode;
  /** @deprecated Use report_mode: "llm_summary" instead */
  use_ai_narrative?: boolean;
}

export interface BatchReportResponse {
  run_id: number;
  batch_code: string;
  semester_number: number;
  plan_name: string | null;
  generated_at: string;
  markdown: string;
  narrative_source: string;
}

export function generateBatchReport(
  runId: number,
  body: BatchReportRequest,
): Promise<BatchReportResponse> {
  return apiPost<BatchReportResponse>(`/allocations/${runId}/reports/batch-summary`, body);
}

export interface AllBatchesReportRequest {
  report_mode?: ReportMode;
}

export interface BatchReportSection {
  batch_code: string;
  semester_number: number;
  narrative_source: string;
}

export interface AllBatchesReportResponse {
  run_id: number;
  plan_name: string | null;
  generated_at: string;
  batch_count: number;
  markdown: string;
  sections: BatchReportSection[];
}

export function generateAllBatchesReport(
  runId: number,
  body: AllBatchesReportRequest = {},
): Promise<AllBatchesReportResponse> {
  return apiPost<AllBatchesReportResponse>(`/allocations/${runId}/reports/all-batches`, body);
}

export function defaultMaxTimeSeconds(_batchCount: number): number {
  return 120;
}

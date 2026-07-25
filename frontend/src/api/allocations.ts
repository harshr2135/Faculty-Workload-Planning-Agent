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

export type TimetableExportPack = "faculty" | "students" | "rooms";
export type TimetableExportFormat = "xlsx" | "pdf";

export type FacultyTimetableMailStatus = "sent" | "skipped" | "failed";

export interface FacultyTimetableMailDetail {
  faculty_id: number;
  full_name: string;
  email: string | null;
  status: FacultyTimetableMailStatus;
  message: string;
}

export interface FacultyTimetableMailResult {
  run_id: number;
  recipient_count: number;
  sent: number;
  skipped: number;
  failed: number;
  details: FacultyTimetableMailDetail[];
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

/** Email each faculty with teaching load their personal timetable PDF. */
export function emailFacultyTimetables(runId: number): Promise<FacultyTimetableMailResult> {
  return apiPost<FacultyTimetableMailResult>(
    `/allocations/${runId}/email/faculty-timetables`,
    {},
  );
}

/** Download one timetable pack (faculty | students | rooms) as Excel or PDF. */
export async function downloadTimetableExport(
  runId: number,
  pack: TimetableExportPack,
  format: TimetableExportFormat = "xlsx",
): Promise<void> {
  const response = await fetch(
    `${API_BASE}/allocations/${runId}/export/timetable/${pack}?format=${format}`,
  );
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // ignore parse errors
    }
    throw new Error(detail || `Export failed (${response.status})`);
  }
  const blob = await response.blob();
  const disposition = response.headers.get("Content-Disposition") ?? "";
  const match = /filename="([^"]+)"/i.exec(disposition);
  const filename = match?.[1] ?? `AIML_Timetable_${pack}_run${runId}.${format}`;
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
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

/** SSE event payloads from the report streaming endpoints. */
export type ReportStreamEvent =
  | {
      type: "meta";
      run_id: number;
      batch_code?: string;
      semester_number?: number;
      plan_name?: string | null;
      generated_at?: string;
      batch_count?: number;
      scope?: "single" | "all";
    }
  | { type: "chunk"; text: string }
  | {
      type: "batch_start";
      batch_code: string;
      semester_number: number;
      index: number;
      total: number;
    }
  | {
      type: "done";
      narrative_source: string;
      sections?: BatchReportSection[];
    }
  | { type: "error"; message: string };

export interface StreamReportHandlers {
  onEvent: (event: ReportStreamEvent) => void;
  signal?: AbortSignal;
}

async function consumeReportSse(path: string, body: unknown, handlers: StreamReportHandlers): Promise<void> {
  const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify(body),
      signal: handlers.signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      return;
    }
    throw new Error(
      "Could not reach the API while streaming the report. Check that the backend is running.",
    );
  }

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) detail = payload.detail;
    } catch {
      // ignore parse errors
    }
    throw new Error(detail || "Report stream request failed.");
  }

  if (!response.body) {
    throw new Error("Report stream returned an empty body.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });

    // SSE frames are separated by a blank line.
    let separatorIndex = buffer.indexOf("\n\n");
    while (separatorIndex >= 0) {
      const frame = buffer.slice(0, separatorIndex);
      buffer = buffer.slice(separatorIndex + 2);
      const dataLines = frame
        .split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).trimStart());
      if (dataLines.length > 0) {
        const payload = dataLines.join("\n");
        try {
          handlers.onEvent(JSON.parse(payload) as ReportStreamEvent);
        } catch {
          // ignore malformed frames
        }
      }
      separatorIndex = buffer.indexOf("\n\n");
    }
  }
}

export function streamBatchReport(
  runId: number,
  body: BatchReportRequest,
  handlers: StreamReportHandlers,
): Promise<void> {
  return consumeReportSse(`/allocations/${runId}/reports/batch-summary/stream`, body, handlers);
}

export function streamAllBatchesReport(
  runId: number,
  body: AllBatchesReportRequest,
  handlers: StreamReportHandlers,
): Promise<void> {
  return consumeReportSse(`/allocations/${runId}/reports/all-batches/stream`, body, handlers);
}

export function defaultMaxTimeSeconds(_batchCount: number): number {
  return 120;
}

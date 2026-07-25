import { useEffect, useMemo, useRef, useState, type UIEvent } from "react";
import {
  streamAllBatchesReport,
  streamBatchReport,
  type BatchReportSection,
  type ReportStreamEvent,
} from "@/api/allocations";
import type { AllocationRun, BatchSemesterPlan } from "@/types/api";
import { MarkdownRenderer } from "./MarkdownRenderer";

type ViewMode = "formatted" | "source";
type ReportScope = "single" | "all";

interface AllocationReportPanelProps {
  result: AllocationRun;
}

function planKey(plan: BatchSemesterPlan): string {
  return `${plan.batch_code}::${plan.semester_number}`;
}

function downloadTextFile(filename: string, content: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function narrativeSourceLabel(source: string): string {
  switch (source) {
    case "llm_full_facts":
      return "AI-generated report";
    case "llm_unavailable":
      return "AI unavailable — template fallback";
    case "template":
      return "Template";
    case "all_batches":
      return "All batches — AI-generated";
    default:
      return source;
  }
}

function allBatchesSourceLabel(sections: BatchReportSection[]): string {
  const count = sections.length;
  const anyFallback = sections.some((section) => section.narrative_source === "llm_unavailable");
  if (anyFallback) {
    return `All batches (${count}) — some used template fallback`;
  }
  return `All batches (${count}) — AI-generated`;
}

export function AllocationReportPanel({ result }: AllocationReportPanelProps) {
  const plans = result.batch_plans ?? [];
  const defaultKey = plans[0] ? planKey(plans[0]) : "";
  const [selectedKey, setSelectedKey] = useState(defaultKey);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [sourceDisplay, setSourceDisplay] = useState<string | null>(null);
  const [reportScope, setReportScope] = useState<ReportScope>("single");
  const [viewMode, setViewMode] = useState<ViewMode>("formatted");
  const [streamStatus, setStreamStatus] = useState<string | null>(null);
  const reportRef = useRef<HTMLDivElement>(null);
  const sourceRef = useRef<HTMLPreElement>(null);
  const stickToBottomRef = useRef(true);
  const abortRef = useRef<AbortController | null>(null);

  const selectedPlan = useMemo(
    () => plans.find((plan) => planKey(plan) === selectedKey) ?? plans[0],
    [plans, selectedKey],
  );

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  useEffect(() => {
    if (!loading || !stickToBottomRef.current) {
      return;
    }
    const container = viewMode === "formatted" ? reportRef.current : sourceRef.current;
    if (!container) {
      return;
    }
    container.scrollTop = container.scrollHeight;
  }, [markdown, loading, viewMode]);

  function handleReportScroll(event: UIEvent<HTMLElement>) {
    const el = event.currentTarget;
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    // Stay pinned while streaming unless the user scrolls up to read earlier content.
    stickToBottomRef.current = distanceFromBottom < 48;
  }

  function beginStream() {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    stickToBottomRef.current = true;
    setLoading(true);
    setError(null);
    setMarkdown("");
    setSourceDisplay(null);
    setStreamStatus("Starting…");
    return controller;
  }

  function handleStreamEvent(event: ReportStreamEvent, scope: ReportScope) {
    if (event.type === "meta") {
      setStreamStatus(scope === "all" ? "Writing cover & consolidated table…" : "Generating…");
      return;
    }
    if (event.type === "batch_start") {
      setStreamStatus(
        `Batch ${event.index}/${event.total}: ${event.batch_code} · sem ${event.semester_number}`,
      );
      return;
    }
    if (event.type === "chunk") {
      setMarkdown((prev) => `${prev ?? ""}${event.text}`);
      return;
    }
    if (event.type === "done") {
      if (event.sections && event.sections.length > 0) {
        setSourceDisplay(allBatchesSourceLabel(event.sections));
      } else {
        setSourceDisplay(narrativeSourceLabel(event.narrative_source));
      }
      setStreamStatus(null);
      return;
    }
    if (event.type === "error") {
      setError(event.message);
      setStreamStatus(null);
    }
  }

  async function handleGenerate() {
    if (!selectedPlan) {
      return;
    }
    const controller = beginStream();
    setReportScope("single");
    try {
      await streamBatchReport(
        result.id,
        {
          batch_code: selectedPlan.batch_code,
          semester_number: selectedPlan.semester_number,
          report_mode: "llm_full_facts",
        },
        {
          signal: controller.signal,
          onEvent: (event) => handleStreamEvent(event, "single"),
        },
      );
    } catch (err) {
      if (!(err instanceof DOMException && err.name === "AbortError")) {
        setError(err instanceof Error ? err.message : "Could not generate report.");
        setMarkdown(null);
      }
    } finally {
      setLoading(false);
      setStreamStatus(null);
    }
  }

  async function handleGenerateAll() {
    const controller = beginStream();
    setReportScope("all");
    try {
      await streamAllBatchesReport(
        result.id,
        { report_mode: "llm_full_facts" },
        {
          signal: controller.signal,
          onEvent: (event) => handleStreamEvent(event, "all"),
        },
      );
    } catch (err) {
      if (!(err instanceof DOMException && err.name === "AbortError")) {
        setError(err instanceof Error ? err.message : "Could not generate combined report.");
        setMarkdown(null);
      }
    } finally {
      setLoading(false);
      setStreamStatus(null);
    }
  }

  function handleDownloadMarkdown() {
    if (!markdown) {
      return;
    }
    const filename =
      reportScope === "all"
        ? `allocation-run-${result.id}-all-batches.md`
        : `allocation-${selectedPlan?.batch_code}-sem${selectedPlan?.semester_number}.md`;
    downloadTextFile(filename, markdown, "text/markdown;charset=utf-8");
  }

  function handlePrintPdf() {
    if (!markdown) {
      return;
    }
    const printWindow = window.open("", "_blank", "width=900,height=700");
    if (!printWindow) {
      setError("Could not open the print window. Please allow pop-ups for this site and try again.");
      return;
    }
    const title =
      reportScope === "all"
        ? `Allocation report — all batches (run ${result.id})`
        : `Allocation report ${selectedPlan?.batch_code} sem ${selectedPlan?.semester_number}`;
    const body = reportRef.current?.innerHTML ?? "";
    printWindow.document.write(`<!DOCTYPE html>
<html>
  <head>
    <title>${title}</title>
    <style>
      body { font-family: Georgia, "Times New Roman", serif; max-width: 820px; margin: 2rem auto; line-height: 1.5; color: #111; padding: 0 1rem; }
      h1 { font-size: 1.6rem; margin: 0 0 0.5rem; border-bottom: 2px solid #222; padding-bottom: 0.35rem; }
      h2 { font-size: 1.15rem; margin: 1.5rem 0 0.5rem; border-bottom: 1px solid #ccc; padding-bottom: 0.25rem; }
      h3 { font-size: 1rem; margin: 1rem 0 0.4rem; }
      p, li { font-size: 0.95rem; }
      ul, ol { margin: 0.5rem 0; padding-left: 1.4rem; }
      table { width: 100%; border-collapse: collapse; margin: 0.75rem 0; font-size: 0.85rem; }
      th, td { border: 1px solid #bbb; padding: 0.4rem 0.55rem; text-align: left; vertical-align: top; }
      th { background: #f0f0f0; }
      tr:nth-child(even) td { background: #fafafa; }
      hr { border: none; border-top: 1px solid #ccc; margin: 1.5rem 0; }
      blockquote { border-left: 3px solid #ccc; margin: 0.75rem 0; padding-left: 0.75rem; color: #555; font-style: italic; }
      @media print { body { margin: 0; } }
    </style>
  </head>
  <body onload="window.focus(); window.print();">${body}</body>
</html>`);
    printWindow.document.close();
  }

  if (plans.length === 0) {
    return null;
  }

  const hasMarkdown = markdown !== null && markdown.length > 0;

  return (
    <section className="ui-section">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold tracking-tight text-slate-900">Department report</h2>
          <p className="mt-1 text-sm leading-relaxed text-slate-500">
            Generate an AI-written, HOD-ready summary for a batch and semester from this
            allocation run. Figures are grounded in the deterministic allocation facts.
            Text streams live as the model writes.
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-sm text-slate-700">
          Batch & semester
          <select
            value={selectedKey}
            onChange={(event) => setSelectedKey(event.target.value)}
            className="ui-select"
            disabled={loading}
          >
            {plans.map((plan) => (
              <option key={planKey(plan)} value={planKey(plan)}>
                {plan.batch_code} · sem {plan.semester_number} ({plan.section_count} sections)
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          onClick={handleGenerate}
          disabled={loading}
          className="ui-btn-primary"
        >
          {loading && reportScope === "single" ? "Streaming…" : "Generate report"}
        </button>
        {plans.length > 1 && (
          <button
            type="button"
            onClick={handleGenerateAll}
            disabled={loading}
            className="ui-btn-secondary"
          >
            {loading && reportScope === "all"
              ? "Streaming…"
              : `Generate for all batches (${plans.length})`}
          </button>
        )}
      </div>

      {plans.length > 1 && (
        <p className="mt-2 text-xs text-slate-500">
          "All batches" streams one combined document: cover and consolidated faculty table first,
          then each batch in order.
        </p>
      )}

      {streamStatus && (
        <p className="mt-3 text-sm text-slate-600" aria-live="polite">
          {streamStatus}
          <span className="ml-1 inline-block h-2 w-2 animate-pulse rounded-full bg-emerald-500 align-middle" />
        </p>
      )}

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      {hasMarkdown && (
        <div className="mt-4 space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <div className="inline-flex overflow-hidden rounded-xl border border-slate-300 shadow-sm">
              <button
                type="button"
                onClick={() => setViewMode("formatted")}
                className={`px-3 py-1.5 text-sm font-medium transition ${
                  viewMode === "formatted"
                    ? "bg-slate-900 text-white"
                    : "bg-white text-slate-700 hover:bg-slate-50"
                }`}
              >
                Formatted
              </button>
              <button
                type="button"
                onClick={() => setViewMode("source")}
                className={`px-3 py-1.5 text-sm font-medium transition ${
                  viewMode === "source"
                    ? "bg-slate-900 text-white"
                    : "bg-white text-slate-700 hover:bg-slate-50"
                }`}
              >
                Markdown source
              </button>
            </div>
            <button
              type="button"
              onClick={handleDownloadMarkdown}
              disabled={loading}
              className="ui-btn-secondary px-3 py-1.5"
            >
              Download Markdown
            </button>
            <button
              type="button"
              onClick={handlePrintPdf}
              disabled={loading}
              className="ui-btn-secondary px-3 py-1.5"
            >
              Print / Save as PDF
            </button>
            {sourceDisplay && (
              <span className="self-center text-xs text-slate-500">
                Source: {sourceDisplay}
              </span>
            )}
          </div>
          <div
            ref={reportRef}
            onScroll={handleReportScroll}
            className={
              viewMode === "formatted"
                ? "max-h-[36rem] overflow-auto rounded-xl border border-slate-200 bg-white p-6 shadow-inner"
                : "hidden"
            }
          >
            <MarkdownRenderer content={markdown ?? ""} />
          </div>
          {viewMode === "source" && (
            <pre
              ref={sourceRef}
              onScroll={handleReportScroll}
              className="max-h-[36rem] overflow-auto rounded-xl border border-slate-200 bg-slate-50 p-4 text-xs leading-relaxed text-slate-800 whitespace-pre-wrap"
            >
              {markdown}
            </pre>
          )}
        </div>
      )}
    </section>
  );
}

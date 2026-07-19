import { useMemo, useRef, useState } from "react";
import { generateAllBatchesReport, generateBatchReport } from "@/api/allocations";
import type { BatchReportSection } from "@/api/allocations";
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
  const reportRef = useRef<HTMLDivElement>(null);

  const selectedPlan = useMemo(
    () => plans.find((plan) => planKey(plan) === selectedKey) ?? plans[0],
    [plans, selectedKey],
  );

  async function handleGenerate() {
    if (!selectedPlan) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const report = await generateBatchReport(result.id, {
        batch_code: selectedPlan.batch_code,
        semester_number: selectedPlan.semester_number,
        report_mode: "llm_full_facts",
      });
      setMarkdown(report.markdown);
      setSourceDisplay(narrativeSourceLabel(report.narrative_source));
      setReportScope("single");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not generate report.");
      setMarkdown(null);
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateAll() {
    setLoading(true);
    setError(null);
    try {
      const report = await generateAllBatchesReport(result.id, {
        report_mode: "llm_full_facts",
      });
      setMarkdown(report.markdown);
      setSourceDisplay(allBatchesSourceLabel(report.sections));
      setReportScope("all");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not generate combined report.");
      setMarkdown(null);
    } finally {
      setLoading(false);
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

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Department report</h2>
          <p className="text-sm text-slate-600">
            Generate an AI-written, HOD-ready summary for a batch and semester from this
            allocation run. Figures are grounded in the deterministic allocation facts.
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-sm text-slate-700">
          Batch & semester
          <select
            value={selectedKey}
            onChange={(event) => setSelectedKey(event.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-2"
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
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
        >
          {loading ? "Generating…" : "Generate report"}
        </button>
        {plans.length > 1 && (
          <button
            type="button"
            onClick={handleGenerateAll}
            disabled={loading}
            className="rounded-lg border border-slate-900 px-4 py-2 text-sm font-medium text-slate-900 hover:bg-slate-100 disabled:opacity-50"
          >
            {loading ? "Generating…" : `Generate for all batches (${plans.length})`}
          </button>
        )}
      </div>

      {plans.length > 1 && (
        <p className="mt-2 text-xs text-slate-500">
          "All batches" produces one combined document covering every batch/semester in this run
          (one AI call per batch).
        </p>
      )}

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      {markdown && (
        <div className="mt-4 space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <div className="inline-flex overflow-hidden rounded-lg border border-slate-300">
              <button
                type="button"
                onClick={() => setViewMode("formatted")}
                className={`px-3 py-1.5 text-sm ${
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
                className={`px-3 py-1.5 text-sm ${
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
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
            >
              Download Markdown
            </button>
            <button
              type="button"
              onClick={handlePrintPdf}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
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
            className={
              viewMode === "formatted"
                ? "max-h-[36rem] overflow-auto rounded-lg border border-slate-200 bg-white p-6"
                : "hidden"
            }
          >
            <MarkdownRenderer content={markdown} />
          </div>
          {viewMode === "source" && (
            <pre className="max-h-[36rem] overflow-auto rounded-lg border border-slate-200 bg-slate-50 p-4 text-xs leading-relaxed text-slate-800 whitespace-pre-wrap">
              {markdown}
            </pre>
          )}
        </div>
      )}
    </section>
  );
}


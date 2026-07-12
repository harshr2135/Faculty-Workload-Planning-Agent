import { useMemo, useState } from "react";
import { generateBatchReport } from "@/api/allocations";
import type { ReportMode } from "@/api/allocations";
import type { AllocationRun, BatchSemesterPlan } from "@/types/api";

interface AllocationReportPanelProps {
  result: AllocationRun;
}

const REPORT_MODE_OPTIONS: { value: ReportMode; label: string; hint: string }[] = [
  {
    value: "template",
    label: "Template (deterministic)",
    hint: "Python-built report — no AI",
  },
  {
    value: "llm_summary",
    label: "AI: executive summary only",
    hint: "Template report with LLM-written summary paragraph",
  },
  {
    value: "llm_full_facts",
    label: "AI: full report (A — facts JSON)",
    hint: "LLM writes entire report from pre-aggregated facts",
  },
  {
    value: "llm_full_raw",
    label: "AI: full report (B — raw JSON)",
    hint: "LLM writes entire report from raw assignments & timetable",
  },
];

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

function simpleMarkdownToHtml(markdown: string): string {
  const escaped = markdown
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  return escaped
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/^- (.+)$/gm, "<li>$1</li>")
    .replace(/\n\n/g, "</p><p>")
    .replace(/\|/g, " | ");
}

function narrativeSourceLabel(source: string): string {
  switch (source) {
    case "template":
      return "Template";
    case "llm":
      return "AI summary only";
    case "llm_full_facts":
      return "AI full report (facts)";
    case "llm_full_raw":
      return "AI full report (raw)";
    case "llm_unavailable":
      return "AI unavailable — template fallback";
    default:
      return source;
  }
}

export function AllocationReportPanel({ result }: AllocationReportPanelProps) {
  const plans = result.batch_plans ?? [];
  const defaultKey = plans[0] ? planKey(plans[0]) : "";
  const [selectedKey, setSelectedKey] = useState(defaultKey);
  const [reportMode, setReportMode] = useState<ReportMode>("template");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [narrativeSource, setNarrativeSource] = useState<string | null>(null);

  const selectedPlan = useMemo(
    () => plans.find((plan) => planKey(plan) === selectedKey) ?? plans[0],
    [plans, selectedKey],
  );

  const selectedModeHint = REPORT_MODE_OPTIONS.find((opt) => opt.value === reportMode)?.hint ?? "";

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
        report_mode: reportMode,
      });
      setMarkdown(report.markdown);
      setNarrativeSource(report.narrative_source);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not generate report.");
      setMarkdown(null);
    } finally {
      setLoading(false);
    }
  }

  function handleDownloadMarkdown() {
    if (!markdown || !selectedPlan) {
      return;
    }
    downloadTextFile(
      `allocation-${selectedPlan.batch_code}-sem${selectedPlan.semester_number}.md`,
      markdown,
      "text/markdown;charset=utf-8",
    );
  }

  function handlePrintPdf() {
    if (!markdown || !selectedPlan) {
      return;
    }
    const printWindow = window.open("", "_blank", "noopener,noreferrer,width=900,height=700");
    if (!printWindow) {
      return;
    }
    const body = simpleMarkdownToHtml(markdown);
    printWindow.document.write(`<!DOCTYPE html>
<html>
  <head>
    <title>Allocation report ${selectedPlan.batch_code} sem ${selectedPlan.semester_number}</title>
    <style>
      body { font-family: Georgia, serif; max-width: 820px; margin: 2rem auto; line-height: 1.5; color: #111; }
      h1 { font-size: 1.5rem; margin-bottom: 0.5rem; }
      h2 { font-size: 1.1rem; margin-top: 1.5rem; border-bottom: 1px solid #ddd; padding-bottom: 0.25rem; }
      p, li { font-size: 0.95rem; }
      li { margin-left: 1rem; }
    </style>
  </head>
  <body><p>${body}</p></body>
</html>`);
    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
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
            Generate an HOD-ready summary for a batch and semester from this allocation run.
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
        <label className="flex flex-col gap-1 text-sm text-slate-700">
          Report mode
          <select
            value={reportMode}
            onChange={(event) => setReportMode(event.target.value as ReportMode)}
            className="min-w-[16rem] rounded-lg border border-slate-300 bg-white px-3 py-2"
          >
            {REPORT_MODE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
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
      </div>

      {selectedModeHint && (
        <p className="mt-2 text-xs text-slate-500">{selectedModeHint}</p>
      )}

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      {markdown && (
        <div className="mt-4 space-y-3">
          <div className="flex flex-wrap gap-2">
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
            {narrativeSource && (
              <span className="self-center text-xs text-slate-500">
                Source: {narrativeSourceLabel(narrativeSource)}
              </span>
            )}
          </div>
          <pre className="max-h-[28rem] overflow-auto rounded-lg border border-slate-200 bg-slate-50 p-4 text-xs leading-relaxed text-slate-800 whitespace-pre-wrap">
            {markdown}
          </pre>
        </div>
      )}
    </section>
  );
}

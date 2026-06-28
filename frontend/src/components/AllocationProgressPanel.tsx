import { useEffect, useState } from "react";
import type { AllocationRunProgress } from "@/types/api";

const PHASE_CHECKLIST: { phase: string; title: string }[] = [
  { phase: "preparing", title: "Prepare data" },
  { phase: "workload_solver", title: "Faculty workload (CP-SAT)" },
  { phase: "timetable_build", title: "Build timetable events" },
  { phase: "timetable_solver", title: "Schedule time slots (CP-SAT)" },
  { phase: "timetable_rooms", title: "Assign rooms" },
  { phase: "finalizing", title: "Save results" },
];

function formatElapsed(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}m ${secs}s`;
}

function phaseIndex(phase: string): number {
  return PHASE_CHECKLIST.findIndex((item) => item.phase === phase);
}

export interface AllocationProgressPanelProps {
  runId: number;
  progress: AllocationRunProgress | null;
  startedAt: string | null;
  fallbackMessage?: string;
}

export function AllocationProgressPanel({
  runId,
  progress,
  startedAt,
  fallbackMessage,
}: AllocationProgressPanelProps) {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    if (!startedAt) {
      return;
    }
    const startMs = Date.parse(startedAt);
    if (Number.isNaN(startMs)) {
      return;
    }
    const tick = () => {
      setElapsedSeconds(Math.max(0, Math.floor((Date.now() - startMs) / 1000)));
    };
    tick();
    const timer = window.setInterval(tick, 1000);
    return () => window.clearInterval(timer);
  }, [startedAt]);

  const percent = progress?.percent ?? 5;
  const label = progress?.label ?? fallbackMessage ?? "Starting allocation run…";
  const step = progress?.step ?? 1;
  const totalSteps = progress?.total_steps ?? 6;
  const currentPhaseIndex = progress ? phaseIndex(progress.phase) : 0;

  return (
    <section
      className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
      aria-live="polite"
      aria-busy="true"
    >
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-sm font-medium text-slate-900">Run #{runId} in progress</p>
          <p className="mt-1 text-sm text-slate-600">
            Step {step} of {totalSteps}
            {startedAt && elapsedSeconds > 0 && (
              <span className="text-slate-400"> · {formatElapsed(elapsedSeconds)} elapsed</span>
            )}
          </p>
        </div>
        <span className="text-sm font-semibold tabular-nums text-emerald-700">{percent}%</span>
      </div>

      <div className="mb-2 h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-emerald-600 transition-all duration-500 ease-out"
          style={{ width: `${percent}%` }}
          role="progressbar"
          aria-valuenow={percent}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Allocation progress"
        />
      </div>
      <p className="mb-5 text-sm text-slate-700">{label}</p>

      <ol className="grid gap-2 sm:grid-cols-2">
        {PHASE_CHECKLIST.map((item, index) => {
          const done = currentPhaseIndex > index;
          const active = currentPhaseIndex === index;
          return (
            <li
              key={item.phase}
              className={`flex items-center gap-2 rounded-md border px-3 py-2 text-sm ${
                active
                  ? "border-emerald-200 bg-emerald-50 text-emerald-900"
                  : done
                    ? "border-slate-200 bg-slate-50 text-slate-600"
                    : "border-slate-100 text-slate-400"
              }`}
            >
              <span
                className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-xs font-medium ${
                  done
                    ? "bg-emerald-600 text-white"
                    : active
                      ? "border-2 border-emerald-600 text-emerald-700"
                      : "border border-slate-300"
                }`}
                aria-hidden
              >
                {done ? "✓" : index + 1}
              </span>
              <span>{item.title}</span>
              {active && (
                <span className="ml-auto h-4 w-4 animate-spin rounded-full border-2 border-emerald-300 border-t-emerald-700" />
              )}
            </li>
          );
        })}
      </ol>
    </section>
  );
}

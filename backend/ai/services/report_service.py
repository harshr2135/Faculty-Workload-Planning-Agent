"""Orchestrates batch report generation with optional LLM narrative."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

from backend.ai.llm.client import (
    ai_narrative_available,
    generate_executive_summary,
    generate_full_report_markdown,
    stream_full_report_markdown,
)
from backend.schemas.allocation import AllocationRunRead
from backend.schemas.allocation_report import (
    AllBatchesReportResponse,
    BatchReportResponse,
    BatchReportSection,
    ReportMode,
)
from backend.services.allocation_report_service import (
    build_batch_raw_payload,
    generate_batch_report,
    render_run_faculty_allocation_markdown,
)


def format_sse(event: dict[str, Any]) -> str:
    """Serialize one SSE `data:` frame (JSON payload)."""
    return f"data: {json.dumps(event, default=str)}\n\n"


async def build_batch_report(
    run: AllocationRunRead,
    *,
    batch_code: str,
    semester_number: int,
    report_mode: ReportMode = ReportMode.TEMPLATE,
    include_faculty_allocation: bool = True,
) -> BatchReportResponse:
    if report_mode == ReportMode.TEMPLATE:
        return generate_batch_report(
            run,
            batch_code=batch_code,
            semester_number=semester_number,
            include_faculty_allocation=include_faculty_allocation,
        )

    if not ai_narrative_available():
        base = generate_batch_report(
            run,
            batch_code=batch_code,
            semester_number=semester_number,
            include_faculty_allocation=include_faculty_allocation,
        )
        return base.model_copy(update={"narrative_source": "llm_unavailable"})

    if report_mode == ReportMode.LLM_SUMMARY:
        return await _build_summary_enhanced_report(
            run,
            batch_code=batch_code,
            semester_number=semester_number,
            include_faculty_allocation=include_faculty_allocation,
        )

    generated_at = datetime.now(timezone.utc).isoformat()

    if report_mode == ReportMode.LLM_FULL_FACTS:
        base = generate_batch_report(
            run,
            batch_code=batch_code,
            semester_number=semester_number,
            include_faculty_allocation=False,
        )
        payload = json.dumps(base.facts.model_dump(), indent=2, default=str)
        markdown = await generate_full_report_markdown(
            payload, mode="facts", generated_at=generated_at
        )
        narrative_source = "llm_full_facts"
    elif report_mode == ReportMode.LLM_FULL_RAW:
        payload_dict = build_batch_raw_payload(run, batch_code=batch_code, semester_number=semester_number)
        payload = json.dumps(payload_dict, indent=2, default=str)
        markdown = await generate_full_report_markdown(
            payload, mode="raw", generated_at=generated_at
        )
        narrative_source = "llm_full_raw"
    else:
        base = generate_batch_report(
            run,
            batch_code=batch_code,
            semester_number=semester_number,
            include_faculty_allocation=include_faculty_allocation,
        )
        return base

    if not markdown:
        base = generate_batch_report(
            run,
            batch_code=batch_code,
            semester_number=semester_number,
            include_faculty_allocation=include_faculty_allocation,
        )
        return base.model_copy(update={"narrative_source": "llm_unavailable"})

    return generate_batch_report(
        run,
        batch_code=batch_code,
        semester_number=semester_number,
        markdown_override=markdown,
        narrative_source=narrative_source,
        include_faculty_allocation=include_faculty_allocation,
    )


async def stream_batch_report_events(
    run: AllocationRunRead,
    *,
    batch_code: str,
    semester_number: int,
    report_mode: ReportMode = ReportMode.LLM_FULL_FACTS,
    include_faculty_allocation: bool = True,
) -> AsyncIterator[dict[str, Any]]:
    """Yield SSE event dicts for a single-batch report (meta / chunk / done / error)."""
    generated_at = datetime.now(timezone.utc).isoformat()
    yield {
        "type": "meta",
        "run_id": run.id,
        "batch_code": batch_code,
        "semester_number": semester_number,
        "plan_name": run.plan_name,
        "generated_at": generated_at,
        "scope": "single",
    }

    try:
        async for event in _stream_batch_report_body(
            run,
            batch_code=batch_code,
            semester_number=semester_number,
            report_mode=report_mode,
            generated_at=generated_at,
            include_faculty_allocation=include_faculty_allocation,
        ):
            yield event
    except ValueError as exc:
        yield {"type": "error", "message": str(exc)}


async def _stream_batch_report_body(
    run: AllocationRunRead,
    *,
    batch_code: str,
    semester_number: int,
    report_mode: ReportMode,
    generated_at: str,
    include_faculty_allocation: bool,
) -> AsyncIterator[dict[str, Any]]:
    if report_mode == ReportMode.TEMPLATE:
        base = generate_batch_report(
            run,
            batch_code=batch_code,
            semester_number=semester_number,
            include_faculty_allocation=include_faculty_allocation,
        )
        yield {"type": "chunk", "text": base.markdown}
        yield {"type": "done", "narrative_source": "template"}
        return

    if not ai_narrative_available():
        base = generate_batch_report(
            run,
            batch_code=batch_code,
            semester_number=semester_number,
            include_faculty_allocation=include_faculty_allocation,
        )
        yield {"type": "chunk", "text": base.markdown}
        yield {"type": "done", "narrative_source": "llm_unavailable"}
        return

    if report_mode == ReportMode.LLM_SUMMARY:
        report = await _build_summary_enhanced_report(
            run,
            batch_code=batch_code,
            semester_number=semester_number,
            include_faculty_allocation=include_faculty_allocation,
        )
        yield {"type": "chunk", "text": report.markdown}
        yield {"type": "done", "narrative_source": report.narrative_source}
        return

    # Emit run-wide faculty allocation once up front (skipped when already covered by
    # the all-batches cover section).
    if include_faculty_allocation:
        faculty_md = render_run_faculty_allocation_markdown(run)
        yield {"type": "chunk", "text": f"{faculty_md.strip()}\n\n"}

    mode = "facts" if report_mode == ReportMode.LLM_FULL_FACTS else "raw"
    narrative_source = "llm_full_facts" if mode == "facts" else "llm_full_raw"

    if mode == "facts":
        base = generate_batch_report(
            run,
            batch_code=batch_code,
            semester_number=semester_number,
            include_faculty_allocation=False,
        )
        payload = json.dumps(base.facts.model_dump(), indent=2, default=str)
    else:
        payload_dict = build_batch_raw_payload(run, batch_code=batch_code, semester_number=semester_number)
        payload = json.dumps(payload_dict, indent=2, default=str)

    produced_any = False
    async for delta in stream_full_report_markdown(
        payload, mode=mode, generated_at=generated_at
    ):
        produced_any = True
        yield {"type": "chunk", "text": delta}

    if not produced_any:
        base = generate_batch_report(
            run,
            batch_code=batch_code,
            semester_number=semester_number,
            include_faculty_allocation=False,
        )
        yield {"type": "chunk", "text": base.markdown}
        yield {"type": "done", "narrative_source": "llm_unavailable"}
        return

    yield {"type": "done", "narrative_source": narrative_source}


async def stream_all_batches_report_events(
    run: AllocationRunRead,
    *,
    report_mode: ReportMode = ReportMode.LLM_FULL_FACTS,
) -> AsyncIterator[dict[str, Any]]:
    """Yield SSE events for a combined report, streaming each batch sequentially."""
    generated_at = datetime.now(timezone.utc).isoformat()
    plans = run.batch_plans
    if not plans:
        yield {
            "type": "error",
            "message": f"Allocation run #{run.id} has no batch/semester plans to report on.",
        }
        return

    yield {
        "type": "meta",
        "run_id": run.id,
        "plan_name": run.plan_name,
        "generated_at": generated_at,
        "batch_count": len(plans),
        "scope": "all",
    }

    plan_line = run.plan_name or f"Run #{run.id}"
    cover = "\n".join(
        [
            "# Department Workload Report — All Batches",
            "",
            f"**Plan:** {plan_line}  ",
            f"**Generated:** {generated_at}  ",
            f"**Batches covered:** {len(plans)}",
        ]
    )
    consolidated_md = render_run_faculty_allocation_markdown(run)
    yield {"type": "chunk", "text": f"{cover}\n\n---\n\n{consolidated_md.strip()}\n"}

    sections: list[BatchReportSection] = []
    for index, plan in enumerate(plans):
        separator = "\n\n---\n\n"
        yield {"type": "chunk", "text": separator}
        yield {
            "type": "batch_start",
            "batch_code": plan.batch_code,
            "semester_number": plan.semester_number,
            "index": index + 1,
            "total": len(plans),
        }

        narrative_source = "template"
        batch_buffer: list[str] = []
        async for event in stream_batch_report_events(
            run,
            batch_code=plan.batch_code,
            semester_number=plan.semester_number,
            report_mode=report_mode,
            include_faculty_allocation=False,
        ):
            event_type = event.get("type")
            if event_type == "meta":
                continue
            if event_type == "chunk":
                text = str(event.get("text") or "")
                batch_buffer.append(text)
                yield {"type": "chunk", "text": text}
            elif event_type == "done":
                narrative_source = str(event.get("narrative_source") or "template")
            elif event_type == "error":
                yield event
                return

        sections.append(
            BatchReportSection(
                batch_code=plan.batch_code,
                semester_number=plan.semester_number,
                narrative_source=narrative_source,
            )
        )

    yield {
        "type": "done",
        "narrative_source": "all_batches",
        "sections": [section.model_dump() for section in sections],
    }


async def build_all_batches_report(
    run: AllocationRunRead,
    *,
    report_mode: ReportMode = ReportMode.LLM_FULL_FACTS,
) -> AllBatchesReportResponse:
    """Generate a single combined report covering every batch/semester in the run."""
    generated_at = datetime.now(timezone.utc).isoformat()
    plans = run.batch_plans

    if not plans:
        raise ValueError(f"Allocation run #{run.id} has no batch/semester plans to report on.")

    reports = await asyncio.gather(
        *(
            build_batch_report(
                run,
                batch_code=plan.batch_code,
                semester_number=plan.semester_number,
                report_mode=report_mode,
                include_faculty_allocation=False,
            )
            for plan in plans
        )
    )

    plan_line = run.plan_name or f"Run #{run.id}"
    cover = [
        "# Department Workload Report — All Batches",
        "",
        f"**Plan:** {plan_line}  ",
        f"**Generated:** {generated_at}  ",
        f"**Batches covered:** {len(reports)}",
    ]
    consolidated_md = render_run_faculty_allocation_markdown(run)
    body_parts = [report.markdown.strip() for report in reports]
    parts = ["\n".join(cover), consolidated_md, *body_parts]
    markdown = "\n\n---\n\n".join(part.strip() for part in parts) + "\n"

    sections = [
        BatchReportSection(
            batch_code=report.batch_code,
            semester_number=report.semester_number,
            narrative_source=report.narrative_source,
        )
        for report in reports
    ]

    return AllBatchesReportResponse(
        run_id=run.id,
        plan_name=run.plan_name,
        generated_at=generated_at,
        batch_count=len(reports),
        markdown=markdown,
        sections=sections,
    )


async def _build_summary_enhanced_report(
    run: AllocationRunRead,
    *,
    batch_code: str,
    semester_number: int,
    include_faculty_allocation: bool = True,
) -> BatchReportResponse:
    base = generate_batch_report(
        run,
        batch_code=batch_code,
        semester_number=semester_number,
        include_faculty_allocation=include_faculty_allocation,
    )
    summary = await generate_executive_summary(
        json.dumps(base.facts.model_dump(), indent=2, default=str)
    )
    if summary:
        return generate_batch_report(
            run,
            batch_code=batch_code,
            semester_number=semester_number,
            executive_summary=summary,
            narrative_source="llm",
            include_faculty_allocation=include_faculty_allocation,
        )
    return base.model_copy(update={"narrative_source": "llm_unavailable"})

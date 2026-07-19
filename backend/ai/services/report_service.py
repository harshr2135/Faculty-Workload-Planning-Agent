"""Orchestrates batch report generation with optional LLM narrative."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from backend.ai.llm.client import (
    ai_narrative_available,
    generate_executive_summary,
    generate_full_report_markdown,
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
    build_consolidated_faculty_rows,
    generate_batch_report,
    render_consolidated_faculty_markdown,
)


async def build_batch_report(
    run: AllocationRunRead,
    *,
    batch_code: str,
    semester_number: int,
    report_mode: ReportMode = ReportMode.TEMPLATE,
) -> BatchReportResponse:
    if report_mode == ReportMode.TEMPLATE:
        return generate_batch_report(run, batch_code=batch_code, semester_number=semester_number)

    if not ai_narrative_available():
        base = generate_batch_report(run, batch_code=batch_code, semester_number=semester_number)
        return base.model_copy(update={"narrative_source": "llm_unavailable"})

    if report_mode == ReportMode.LLM_SUMMARY:
        return await _build_summary_enhanced_report(run, batch_code=batch_code, semester_number=semester_number)

    generated_at = datetime.now(timezone.utc).isoformat()

    if report_mode == ReportMode.LLM_FULL_FACTS:
        base = generate_batch_report(run, batch_code=batch_code, semester_number=semester_number)
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
        base = generate_batch_report(run, batch_code=batch_code, semester_number=semester_number)
        return base

    if not markdown:
        base = generate_batch_report(run, batch_code=batch_code, semester_number=semester_number)
        return base.model_copy(update={"narrative_source": "llm_unavailable"})

    return generate_batch_report(
        run,
        batch_code=batch_code,
        semester_number=semester_number,
        markdown_override=markdown,
        narrative_source=narrative_source,
    )


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
    consolidated_md = render_consolidated_faculty_markdown(
        build_consolidated_faculty_rows(run)
    )
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
) -> BatchReportResponse:
    base = generate_batch_report(run, batch_code=batch_code, semester_number=semester_number)
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
        )
    return base.model_copy(update={"narrative_source": "llm_unavailable"})


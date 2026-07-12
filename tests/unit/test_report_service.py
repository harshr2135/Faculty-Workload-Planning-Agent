"""Unit tests for report service mode routing."""

from unittest.mock import AsyncMock, patch

import pytest

from backend.ai.services.report_service import build_batch_report
from backend.schemas.allocation import (
    AllocationRunRead,
    BatchSemesterPlanRead,
    SlotAssignmentRead,
)
from backend.schemas.allocation_report import ReportMode


def _minimal_run() -> AllocationRunRead:
    return AllocationRunRead(
        id=1,
        plan_name="Test plan",
        is_saved=False,
        batch_plans=[
            BatchSemesterPlanRead(
                batch_code="2023-27",
                semester_number=5,
                section_count=2,
                working_days=["monday", "friday"],
            )
        ],
        batch_codes=["2023-27"],
        batch_code="2023-27",
        semester_number=5,
        section_count=2,
        status="feasible",
        objective_value=0,
        assignment_count=1,
        faculty_count=1,
        timetable_entry_count=0,
        violations=[],
        messages=[],
        timetable_messages=[],
        assignments=[
            SlotAssignmentRead(
                slot_id="s1",
                course_id=1,
                batch_code="2023-27",
                course_code="23AM3501",
                course_name="ML",
                course_type="IPCC",
                kind="theory",
                section_indices=[1],
                weekly_hours=3,
                faculty_ids=[1],
                faculty_names=["Dr Alpha"],
            )
        ],
        faculty_summaries=[],
        timetable_entries=[],
    )


@pytest.mark.asyncio
async def test_template_mode_uses_python_renderer() -> None:
    report = await build_batch_report(
        _minimal_run(),
        batch_code="2023-27",
        semester_number=5,
        report_mode=ReportMode.TEMPLATE,
    )
    assert report.narrative_source == "template"
    assert "Department Workload Summary" in report.markdown


@pytest.mark.asyncio
@patch("backend.ai.services.report_service.ai_narrative_available", return_value=True)
@patch(
    "backend.ai.services.report_service.generate_full_report_markdown",
    new_callable=AsyncMock,
)
async def test_llm_full_facts_mode(mock_full: AsyncMock, _available: object) -> None:
    mock_full.return_value = "# AI Report\n\nFull facts body."
    report = await build_batch_report(
        _minimal_run(),
        batch_code="2023-27",
        semester_number=5,
        report_mode=ReportMode.LLM_FULL_FACTS,
    )
    assert report.narrative_source == "llm_full_facts"
    assert report.markdown == "# AI Report\n\nFull facts body."
    mock_full.assert_awaited_once()
    assert mock_full.await_args.kwargs["mode"] == "facts"


@pytest.mark.asyncio
@patch("backend.ai.services.report_service.ai_narrative_available", return_value=True)
@patch(
    "backend.ai.services.report_service.generate_full_report_markdown",
    new_callable=AsyncMock,
)
async def test_llm_full_raw_mode(mock_full: AsyncMock, _available: object) -> None:
    mock_full.return_value = "# Raw AI Report\n\nFrom assignments."
    report = await build_batch_report(
        _minimal_run(),
        batch_code="2023-27",
        semester_number=5,
        report_mode=ReportMode.LLM_FULL_RAW,
    )
    assert report.narrative_source == "llm_full_raw"
    assert "Raw AI Report" in report.markdown
    mock_full.assert_awaited_once()
    assert mock_full.await_args.kwargs["mode"] == "raw"


@pytest.mark.asyncio
@patch("backend.ai.services.report_service.ai_narrative_available", return_value=False)
async def test_llm_mode_falls_back_when_ai_unavailable(_available: object) -> None:
    report = await build_batch_report(
        _minimal_run(),
        batch_code="2023-27",
        semester_number=5,
        report_mode=ReportMode.LLM_FULL_FACTS,
    )
    assert report.narrative_source == "llm_unavailable"
    assert "Department Workload Summary" in report.markdown

"""Unit tests for report service mode routing."""

from unittest.mock import AsyncMock, patch

import pytest

from backend.ai.services.report_service import build_all_batches_report, build_batch_report
from backend.schemas.allocation import (
    AllocationRunRead,
    BatchSemesterPlanRead,
    FacultyWorkloadSummaryRead,
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


def _multi_batch_run() -> AllocationRunRead:
    run = _minimal_run()
    return run.model_copy(
        update={
            "batch_plans": [
                *run.batch_plans,
                BatchSemesterPlanRead(
                    batch_code="2022-26",
                    semester_number=7,
                    section_count=3,
                    working_days=["monday", "friday"],
                ),
            ],
            "batch_codes": ["2023-27", "2022-26"],
            "faculty_summaries": [
                FacultyWorkloadSummaryRead(
                    faculty_id=1,
                    full_name="Dr Alpha",
                    designation_key="professor",
                    theory_weekly_hours=3,
                    lab_weekly_hours=0,
                    total_weekly_hours=3,
                    theory_course_count=1,
                    lab_course_count=0,
                    lab_session_count=0,
                ),
                FacultyWorkloadSummaryRead(
                    faculty_id=2,
                    full_name="Dr Beta",
                    designation_key="assistant_professor",
                    theory_weekly_hours=3,
                    lab_weekly_hours=0,
                    total_weekly_hours=3,
                    theory_course_count=1,
                    lab_course_count=0,
                    lab_session_count=0,
                ),
            ],
            "assignments": [
                *run.assignments,
                SlotAssignmentRead(
                    slot_id="s2",
                    course_id=2,
                    batch_code="2022-26",
                    course_code="23AM4501",
                    course_name="NLP",
                    course_type="IPCC",
                    kind="theory",
                    section_indices=[1],
                    weekly_hours=3,
                    faculty_ids=[2],
                    faculty_names=["Dr Beta"],
                ),
            ],
        }
    )


@pytest.mark.asyncio
async def test_all_batches_report_combines_every_plan() -> None:
    response = await build_all_batches_report(
        _multi_batch_run(),
        report_mode=ReportMode.TEMPLATE,
    )
    assert response.batch_count == 2
    assert len(response.sections) == 2
    assert {s.batch_code for s in response.sections} == {"2023-27", "2022-26"}
    assert "Department Workload Report — All Batches" in response.markdown
    assert "2023-27" in response.markdown
    assert "2022-26" in response.markdown


@pytest.mark.asyncio
async def test_all_batches_report_includes_consolidated_faculty_table() -> None:
    response = await build_all_batches_report(
        _multi_batch_run(),
        report_mode=ReportMode.TEMPLATE,
    )
    assert "Consolidated faculty workload (all batches)" in response.markdown
    # Consolidated section lists each faculty's batches; Dr Alpha teaches 2023-27, Dr Beta 2022-26.
    assert "Dr Alpha" in response.markdown
    assert "Dr Beta" in response.markdown


@pytest.mark.asyncio
async def test_all_batches_report_rejects_empty_run() -> None:
    empty = _minimal_run().model_copy(update={"batch_plans": []})
    try:
        await build_all_batches_report(empty, report_mode=ReportMode.TEMPLATE)
        raised = False
    except ValueError:
        raised = True
    assert raised


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


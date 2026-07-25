"""Unit tests for report service mode routing."""

from unittest.mock import AsyncMock, patch

import pytest

from backend.ai.services.report_service import (
    build_all_batches_report,
    build_batch_report,
    format_sse,
    stream_all_batches_report_events,
    stream_batch_report_events,
)
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
    assert "Overall faculty allocation" in response.markdown
    # Consolidated section lists each faculty's batches; Dr Alpha teaches 2023-27, Dr Beta 2022-26.
    assert "Dr Alpha" in response.markdown
    assert "Dr Beta" in response.markdown
    assert "Faculty teaching by batch" in response.markdown
    assert "AICTE max h" in response.markdown
    assert "not per batch" in response.markdown
    # Faculty allocation appears once at the top, not as a repeated per-batch hours table.
    assert response.markdown.count("## Overall faculty allocation") == 1
    assert "Faculty workload (this batch" not in response.markdown
    # No batch-scoped policy-warnings heading; warnings only appear when the run has them.
    assert "Policy warnings (run-wide)" not in response.markdown
    assert "## Policy warnings" not in response.markdown.split("## Overall faculty allocation")[0]


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
    assert "Overall faculty allocation" in report.markdown
    assert "Full facts body." in report.markdown
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


def test_format_sse_wraps_json_data_frame() -> None:
    frame = format_sse({"type": "chunk", "text": "Hello"})
    assert frame.startswith("data: ")
    assert frame.endswith("\n\n")
    assert '"type": "chunk"' in frame
    assert '"text": "Hello"' in frame


@pytest.mark.asyncio
async def test_stream_batch_report_template_emits_chunk_and_done() -> None:
    events = [
        event
        async for event in stream_batch_report_events(
            _minimal_run(),
            batch_code="2023-27",
            semester_number=5,
            report_mode=ReportMode.TEMPLATE,
        )
    ]
    assert events[0]["type"] == "meta"
    assert events[0]["scope"] == "single"
    assert any(event["type"] == "chunk" and "Department Workload Summary" in event["text"] for event in events)
    assert events[-1] == {"type": "done", "narrative_source": "template"}


@pytest.mark.asyncio
@patch("backend.ai.services.report_service.ai_narrative_available", return_value=True)
async def test_stream_batch_report_yields_llm_deltas(_available: object) -> None:
    async def _fake_stream(*_args: object, **_kwargs: object):
        for piece in ("# Live", " report", "\n\nBody"):
            yield piece

    with patch(
        "backend.ai.services.report_service.stream_full_report_markdown",
        side_effect=_fake_stream,
    ):
        events = [
            event
            async for event in stream_batch_report_events(
                _minimal_run(),
                batch_code="2023-27",
                semester_number=5,
                report_mode=ReportMode.LLM_FULL_FACTS,
            )
        ]

    chunks = [event["text"] for event in events if event["type"] == "chunk"]
    joined = "".join(chunks)
    assert "Overall faculty allocation" in joined
    assert "# Live report\n\nBody" in joined
    assert events[-1] == {"type": "done", "narrative_source": "llm_full_facts"}


@pytest.mark.asyncio
@patch("backend.ai.services.report_service.ai_narrative_available", return_value=False)
async def test_stream_all_batches_emits_cover_then_batches(_available: object) -> None:
    events = [
        event
        async for event in stream_all_batches_report_events(
            _multi_batch_run(),
            report_mode=ReportMode.LLM_FULL_FACTS,
        )
    ]
    assert events[0]["type"] == "meta"
    assert events[0]["scope"] == "all"
    assert events[0]["batch_count"] == 2
    joined = "".join(event["text"] for event in events if event["type"] == "chunk")
    assert "Department Workload Report — All Batches" in joined
    assert "Overall faculty allocation" in joined
    assert "Faculty teaching by batch" in joined
    batch_starts = [event for event in events if event["type"] == "batch_start"]
    assert len(batch_starts) == 2
    assert events[-1]["type"] == "done"
    assert len(events[-1]["sections"]) == 2
    assert joined.count("## Overall faculty allocation") == 1


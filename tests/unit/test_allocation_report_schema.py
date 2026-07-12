"""Tests for batch report request schema."""

from backend.schemas.allocation_report import BatchReportRequest, ReportMode


def test_legacy_use_ai_narrative_maps_to_llm_summary() -> None:
    req = BatchReportRequest(
        batch_code="2023-27",
        semester_number=5,
        use_ai_narrative=True,
    )
    assert req.report_mode == ReportMode.LLM_SUMMARY


def test_explicit_report_mode_not_overridden_by_legacy_flag() -> None:
    req = BatchReportRequest(
        batch_code="2023-27",
        semester_number=5,
        report_mode=ReportMode.LLM_FULL_RAW,
        use_ai_narrative=True,
    )
    assert req.report_mode == ReportMode.LLM_FULL_RAW

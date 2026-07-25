"""Schemas for batch allocation summary reports."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class ReportMode(str, Enum):
    """How the batch summary report is produced."""

    TEMPLATE = "template"
    LLM_SUMMARY = "llm_summary"
    LLM_FULL_FACTS = "llm_full_facts"
    LLM_FULL_RAW = "llm_full_raw"


class BatchReportRequest(BaseModel):
    batch_code: str = Field(examples=["2023-27"])
    semester_number: int = Field(ge=1, le=12, examples=[5])
    report_mode: ReportMode = Field(
        default=ReportMode.TEMPLATE,
        description=(
            "template: Python-built report; llm_summary: AI executive summary only; "
            "llm_full_facts: AI writes full report from aggregated facts JSON; "
            "llm_full_raw: AI writes full report from raw assignments/timetable JSON."
        ),
    )
    use_ai_narrative: bool = Field(
        default=False,
        description="Deprecated. When true and report_mode is template, uses llm_summary.",
    )

    @model_validator(mode="after")
    def _resolve_legacy_ai_flag(self) -> BatchReportRequest:
        if self.use_ai_narrative and self.report_mode == ReportMode.TEMPLATE:
            self.report_mode = ReportMode.LLM_SUMMARY
        return self


class PecReportRow(BaseModel):
    course_code: str
    course_name: str
    course_type: str
    pec_pool_number: int | None = None
    student_count: int
    scheduled: bool
    room_type: str | None = None


class FacultyTeachingAssignment(BaseModel):
    """One teaching assignment for a faculty member within a batch."""

    batch_code: str
    course_code: str
    course_name: str
    kind: str
    weekly_hours: int
    lab_sub_batch: str | None = None
    section_indices: list[int] = Field(default_factory=list)


class FacultyReportRow(BaseModel):
    faculty_id: int
    full_name: str
    designation_key: str | None
    designation_label: str = "—"
    # Hours / counts for this batch only.
    theory_hours: int
    lab_hours: int
    # Teaching load (theory + lab/2); theory/lab remain contact hours.
    total_hours: float
    theory_courses: int
    lab_sessions: int
    # Run-wide totals (all batches in the allocation) — AICTE policy scope.
    overall_theory_hours: int = 0
    overall_lab_hours: int = 0
    overall_total_hours: float = 0
    overall_theory_courses: int = 0
    overall_lab_sessions: int = 0
    max_weekly_hours: float | None = None


class ConsolidatedFacultyRow(BaseModel):
    """Faculty workload aggregated across every batch/semester in a run."""

    faculty_id: int
    full_name: str
    designation_key: str | None
    designation_label: str = "—"
    theory_hours: int
    lab_hours: int
    # Teaching load (theory + lab/2); theory/lab remain contact hours.
    total_hours: float
    batch_codes: list[str]
    theory_courses: int
    lab_sessions: int
    max_weekly_hours: float | None = None
    teaching_assignments: list[FacultyTeachingAssignment] = Field(default_factory=list)


class BatchReportFacts(BaseModel):
    run_id: int
    plan_name: str | None
    is_saved: bool
    batch_code: str
    semester_number: int
    section_count: int
    working_days: list[str]
    workload_status: str
    timetable_status: str | None
    assignment_count: int
    timetable_entry_count: int
    unique_courses: int
    theory_sessions: int
    lab_sessions: int
    faculty_assigned: int
    workload_hours_min: int
    workload_hours_max: int
    workload_hours_avg: float
    classrooms_used: list[str]
    laboratories_used: list[str]
    lecture_halls_used: list[str]
    pec_rows: list[PecReportRow]
    faculty_rows: list[FacultyReportRow]
    violation_messages: list[str]
    timetable_messages: list[str]


class BatchReportResponse(BaseModel):
    run_id: int
    batch_code: str
    semester_number: int
    plan_name: str | None
    generated_at: str
    markdown: str
    facts: BatchReportFacts
    narrative_source: str = Field(
        description="template | llm | llm_full_facts | llm_full_raw | llm_unavailable",
    )


class AllBatchesReportRequest(BaseModel):
    report_mode: ReportMode = Field(
        default=ReportMode.LLM_FULL_FACTS,
        description="Report mode applied to every batch/semester in the run.",
    )


class BatchReportSection(BaseModel):
    batch_code: str
    semester_number: int
    narrative_source: str


class AllBatchesReportResponse(BaseModel):
    run_id: int
    plan_name: str | None
    generated_at: str
    batch_count: int
    markdown: str
    sections: list[BatchReportSection]

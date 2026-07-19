"""Deterministic batch allocation summary reports for HOD review."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean

from backend.core.domain.course_type_config import is_pec_course_type, pec_pool_number
from backend.core.domain.pec_config import pec_requires_lecture_hall
from backend.core.domain.policy_config import designation_label_for
from backend.schemas.allocation import (
    AllocationRunRead,
    BatchSemesterPlanRead,
    FacultyWorkloadSummaryRead,
    SlotAssignmentRead,
    TimetableEntryRead,
)
from backend.schemas.allocation_report import (
    BatchReportFacts,
    BatchReportResponse,
    ConsolidatedFacultyRow,
    FacultyReportRow,
    PecReportRow,
)


@dataclass(frozen=True)
class _BatchSlice:
    plan: BatchSemesterPlanRead
    assignments: list[SlotAssignmentRead]
    entries: list[TimetableEntryRead]


def generate_batch_report(
    run: AllocationRunRead,
    *,
    batch_code: str,
    semester_number: int,
    executive_summary: str | None = None,
    markdown_override: str | None = None,
    narrative_source: str = "template",
) -> BatchReportResponse:
    slice_ = _slice_run(run, batch_code, semester_number)
    facts = _build_facts(run, slice_)
    generated_at = datetime.now(timezone.utc).isoformat()
    markdown = markdown_override or _render_markdown(
        facts, generated_at=generated_at, executive_summary=executive_summary
    )
    return BatchReportResponse(
        run_id=run.id,
        batch_code=batch_code,
        semester_number=semester_number,
        plan_name=run.plan_name,
        generated_at=generated_at,
        markdown=markdown,
        facts=facts,
        narrative_source=narrative_source,
    )


def _slice_run(
    run: AllocationRunRead,
    batch_code: str,
    semester_number: int,
) -> _BatchSlice:
    plan = next(
        (
            item
            for item in run.batch_plans
            if item.batch_code == batch_code and item.semester_number == semester_number
        ),
        None,
    )
    if plan is None:
        raise ValueError(
            f"Batch {batch_code} semester {semester_number} is not part of allocation run #{run.id}."
        )

    assignments = [row for row in run.assignments if row.batch_code == batch_code]
    entries = [row for row in run.timetable_entries if row.batch_code == batch_code]
    return _BatchSlice(plan=plan, assignments=assignments, entries=entries)


def build_batch_raw_payload(
    run: AllocationRunRead,
    batch_code: str,
    semester_number: int,
) -> dict[str, object]:
    """Raw allocation slice for LLM full-report mode (Option B)."""
    slice_ = _slice_run(run, batch_code, semester_number)
    batch_course_codes = {row.course_code for row in slice_.assignments}
    violations = [
        row.model_dump()
        for row in run.violations
        if row.course_code is None or row.course_code in batch_course_codes
    ]
    return {
        "run_id": run.id,
        "plan_name": run.plan_name,
        "is_saved": run.is_saved,
        "workload_status": run.status,
        "timetable_status": run.timetable_status,
        "batch_plan": slice_.plan.model_dump(),
        "assignments": [row.model_dump() for row in slice_.assignments],
        "timetable_entries": [row.model_dump() for row in slice_.entries],
        "faculty_summaries": [row.model_dump() for row in run.faculty_summaries],
        "violations": violations,
        "timetable_messages": list(run.timetable_messages),
    }


def build_consolidated_faculty_rows(run: AllocationRunRead) -> list[ConsolidatedFacultyRow]:
    """Aggregate each faculty member's workload across every batch/semester in the run."""
    summary_by_id = {row.faculty_id: row for row in run.faculty_summaries}
    stats: dict[int, dict[str, object]] = defaultdict(
        lambda: {
            "theory_hours": 0,
            "lab_hours": 0,
            "theory_courses": set(),
            "lab_sessions": set(),
            "batches": set(),
        }
    )

    for assignment in run.assignments:
        session_key = (
            assignment.batch_code,
            assignment.course_code,
            assignment.kind,
            assignment.lab_sub_batch or "",
        )
        for faculty_id in assignment.faculty_ids:
            bucket = stats[faculty_id]
            if assignment.batch_code:
                batches = bucket["batches"]
                assert isinstance(batches, set)
                batches.add(assignment.batch_code)
            if assignment.kind == "lab":
                bucket["lab_hours"] = int(bucket["lab_hours"]) + assignment.weekly_hours
                lab_sessions = bucket["lab_sessions"]
                assert isinstance(lab_sessions, set)
                lab_sessions.add(session_key)
            else:
                bucket["theory_hours"] = int(bucket["theory_hours"]) + assignment.weekly_hours
                theory_courses = bucket["theory_courses"]
                assert isinstance(theory_courses, set)
                theory_courses.add((assignment.batch_code, assignment.course_code))

    rows: list[ConsolidatedFacultyRow] = []
    for faculty_id, bucket in stats.items():
        summary = summary_by_id.get(faculty_id)
        theory_hours = int(bucket["theory_hours"])
        lab_hours = int(bucket["lab_hours"])
        theory_courses = bucket["theory_courses"]
        lab_sessions = bucket["lab_sessions"]
        batches = bucket["batches"]
        assert isinstance(theory_courses, set)
        assert isinstance(lab_sessions, set)
        assert isinstance(batches, set)
        rows.append(
            ConsolidatedFacultyRow(
                faculty_id=faculty_id,
                full_name=summary.full_name if summary else f"Faculty #{faculty_id}",
                designation_key=summary.designation_key if summary else None,
                designation_label=designation_label_for(summary.designation_key if summary else None),
                theory_hours=theory_hours,
                lab_hours=lab_hours,
                total_hours=theory_hours + lab_hours,
                batch_codes=sorted(batches),
                theory_courses=len(theory_courses),
                lab_sessions=len(lab_sessions),
            )
        )

    return sorted(rows, key=lambda row: (-row.total_hours, row.full_name))


def render_consolidated_faculty_markdown(rows: list[ConsolidatedFacultyRow]) -> str:
    """Render the run-wide faculty workload distribution as a markdown section."""
    lines = ["## Consolidated faculty workload (all batches)", ""]
    if not rows:
        lines.append("_No faculty assignments recorded for this run._")
        return "\n".join(lines)

    lines.append(
        "_Each faculty member's total teaching load across every batch and semester in this run._"
    )
    lines.append("")
    lines.append(
        "| Faculty | Designation | Theory h | Lab h | Total h | Batches | Theory courses | Lab sessions |"
    )
    lines.append("| --- | --- | ---: | ---: | ---: | --- | ---: | ---: |")
    for row in rows:
        designation = row.designation_label
        batches = ", ".join(row.batch_codes) or "—"
        lines.append(
            f"| {row.full_name} | {designation} | {row.theory_hours} | {row.lab_hours} | "
            f"{row.total_hours} | {batches} | {row.theory_courses} | {row.lab_sessions} |"
        )
    return "\n".join(lines)


def _build_facts(run: AllocationRunRead, slice_: _BatchSlice) -> BatchReportFacts:
    theory_sessions = sum(1 for row in slice_.assignments if row.kind == "theory")
    lab_sessions = sum(1 for row in slice_.assignments if row.kind == "lab")
    course_codes = {row.course_code for row in slice_.assignments}

    faculty_rows = _faculty_rows_for_batch(slice_.assignments, run.faculty_summaries)
    totals = [row.total_hours for row in faculty_rows]

    classrooms: set[str] = set()
    laboratories: set[str] = set()
    lecture_halls: set[str] = set()
    for entry in slice_.entries:
        if entry.room_type == "none" or not entry.room_name or entry.room_name == "—":
            continue
        if entry.room_type == "classroom":
            classrooms.add(entry.room_name)
        elif entry.room_type == "laboratory":
            laboratories.add(entry.room_name)
        elif entry.room_type == "lecture_hall":
            lecture_halls.add(entry.room_name)

    pec_rows = _pec_rows(slice_)
    batch_course_codes = {row.course_code for row in slice_.assignments}
    violation_messages = [
        row.message
        for row in run.violations
        if row.course_code is None or row.course_code in batch_course_codes
    ]

    return BatchReportFacts(
        run_id=run.id,
        plan_name=run.plan_name,
        is_saved=run.is_saved,
        batch_code=slice_.plan.batch_code,
        semester_number=slice_.plan.semester_number,
        section_count=slice_.plan.section_count,
        working_days=list(slice_.plan.working_days),
        workload_status=run.status,
        timetable_status=run.timetable_status,
        assignment_count=len(slice_.assignments),
        timetable_entry_count=len(slice_.entries),
        unique_courses=len(course_codes),
        theory_sessions=theory_sessions,
        lab_sessions=lab_sessions,
        faculty_assigned=len(faculty_rows),
        workload_hours_min=min(totals) if totals else 0,
        workload_hours_max=max(totals) if totals else 0,
        workload_hours_avg=round(mean(totals), 1) if totals else 0.0,
        classrooms_used=sorted(classrooms),
        laboratories_used=sorted(laboratories),
        lecture_halls_used=sorted(lecture_halls),
        pec_rows=pec_rows,
        faculty_rows=faculty_rows,
        violation_messages=violation_messages,
        timetable_messages=list(run.timetable_messages),
    )


def _faculty_rows_for_batch(
    assignments: list[SlotAssignmentRead],
    summaries: list[FacultyWorkloadSummaryRead],
) -> list[FacultyReportRow]:
    summary_by_id = {row.faculty_id: row for row in summaries}
    stats: dict[int, dict[str, int | set[str] | set[tuple[str, str]]]] = defaultdict(
        lambda: {
            "theory_hours": 0,
            "lab_hours": 0,
            "theory_courses": set(),
            "lab_sessions": set(),
        }
    )

    for assignment in assignments:
        session_key = (assignment.course_code, assignment.kind, assignment.lab_sub_batch or "")
        for faculty_id in assignment.faculty_ids:
            bucket = stats[faculty_id]
            if assignment.kind == "lab":
                bucket["lab_hours"] = int(bucket["lab_hours"]) + assignment.weekly_hours
                cast_sessions = bucket["lab_sessions"]
                assert isinstance(cast_sessions, set)
                cast_sessions.add(session_key)
            else:
                bucket["theory_hours"] = int(bucket["theory_hours"]) + assignment.weekly_hours
                cast_courses = bucket["theory_courses"]
                assert isinstance(cast_courses, set)
                cast_courses.add(assignment.course_code)

    rows: list[FacultyReportRow] = []
    for faculty_id, bucket in stats.items():
        summary = summary_by_id.get(faculty_id)
        theory_hours = int(bucket["theory_hours"])
        lab_hours = int(bucket["lab_hours"])
        theory_courses = bucket["theory_courses"]
        lab_sessions = bucket["lab_sessions"]
        assert isinstance(theory_courses, set)
        assert isinstance(lab_sessions, set)
        rows.append(
            FacultyReportRow(
                faculty_id=faculty_id,
                full_name=summary.full_name if summary else f"Faculty #{faculty_id}",
                designation_key=summary.designation_key if summary else None,
                designation_label=designation_label_for(summary.designation_key if summary else None),
                theory_hours=theory_hours,
                lab_hours=lab_hours,
                total_hours=theory_hours + lab_hours,
                theory_courses=len(theory_courses),
                lab_sessions=len(lab_sessions),
            )
        )

    return sorted(rows, key=lambda row: (-row.total_hours, row.full_name))


def _course_metadata(slice_: _BatchSlice) -> dict[str, tuple[str, str]]:
    """course_code → (course_name, course_type) from assignments and timetable."""
    meta: dict[str, tuple[str, str]] = {}
    for assignment in slice_.assignments:
        meta[assignment.course_code] = (assignment.course_name, assignment.course_type)
    for entry in slice_.entries:
        meta.setdefault(entry.course_code, (entry.course_name, entry.course_type))
    return meta


def _pec_rows(slice_: _BatchSlice) -> list[PecReportRow]:
    scheduled_codes = {row.course_code for row in slice_.assignments}
    room_by_course: dict[str, str] = {}
    for entry in slice_.entries:
        if entry.room_type and entry.room_type != "none":
            room_by_course.setdefault(entry.course_code, entry.room_type)

    metadata = _course_metadata(slice_)
    seen_codes: set[str] = set()
    rows: list[PecReportRow] = []

    def append_row(
        *,
        course_code: str,
        course_name: str,
        course_type: str,
        student_count: int,
        scheduled: bool,
    ) -> None:
        code = course_code.strip().upper()
        if code in seen_codes:
            return
        seen_codes.add(code)
        name = course_name.strip() or metadata.get(code, ("", ""))[0]
        ctype = course_type.strip() or metadata.get(code, ("", ""))[1]
        rows.append(
            PecReportRow(
                course_code=code,
                course_name=name or "—",
                course_type=ctype or "PEC",
                pec_pool_number=pec_pool_number(ctype) if ctype else None,
                student_count=student_count,
                scheduled=scheduled,
                room_type=room_by_course.get(code),
            )
        )

    for pec in slice_.plan.pec_enrollments:
        append_row(
            course_code=pec.course_code,
            course_name=pec.course_name,
            course_type=pec.course_type,
            student_count=pec.student_count,
            scheduled=pec.course_code.strip().upper() in scheduled_codes,
        )

    for assignment in slice_.assignments:
        if not is_pec_course_type(assignment.course_type):
            continue
        append_row(
            course_code=assignment.course_code,
            course_name=assignment.course_name,
            course_type=assignment.course_type,
            student_count=0,
            scheduled=True,
        )

    return sorted(
        rows,
        key=lambda row: (
            row.pec_pool_number if row.pec_pool_number is not None else 99,
            row.course_code,
        ),
    )


def _render_pec_sections(facts: BatchReportFacts) -> list[str]:
    lines: list[str] = ["## PEC electives", ""]
    if not facts.pec_rows:
        lines.append("_No PEC electives recorded for this batch/semester._")
        lines.append("")
        return lines

    pools: dict[int, list[PecReportRow]] = {}
    for row in facts.pec_rows:
        pool_key = row.pec_pool_number if row.pec_pool_number is not None else 0
        pools.setdefault(pool_key, []).append(row)

    for pool_key in sorted(pools.keys()):
        pool_label = f"PEC {pool_key}" if pool_key else "PEC"
        lines.append(f"### {pool_label}")
        lines.append("")
        lines.append("| # | Course code | Course name | Students | Scheduled | Room |")
        lines.append("| ---: | --- | --- | ---: | --- | --- |")
        for index, row in enumerate(pools[pool_key], start=1):
            room_hint = row.room_type or ("—" if not row.scheduled else "TBD")
            if row.scheduled and row.student_count > 0 and pec_requires_lecture_hall(row.student_count):
                room_hint = row.room_type or "lecture_hall (>150 students)"
            scheduled = "Yes" if row.scheduled else "No"
            lines.append(
                f"| {index} | {row.course_code} | {row.course_name} | "
                f"{row.student_count} | {scheduled} | {room_hint} |"
            )
        lines.append("")

    return lines


def _default_executive_summary(facts: BatchReportFacts) -> str:
    saved = "saved " if facts.is_saved else ""
    tt = facts.timetable_status or "not scheduled"
    return (
        f"This {saved}allocation plan (run #{facts.run_id}) covers batch **{facts.batch_code}**, "
        f"semester **{facts.semester_number}** ({facts.section_count} sections). "
        f"**{facts.unique_courses}** courses were assigned across **{facts.assignment_count}** "
        f"workload slots ({facts.theory_sessions} theory, {facts.lab_sessions} lab). "
        f"**{facts.faculty_assigned}** faculty received teaching assignments. "
        f"Workload status: **{facts.workload_status}**; timetable: **{tt}**. "
        f"Weekly teaching hours range from **{facts.workload_hours_min}** to "
        f"**{facts.workload_hours_max}** (average **{facts.workload_hours_avg}**)."
    )


def _render_markdown(
    facts: BatchReportFacts,
    *,
    generated_at: str,
    executive_summary: str | None = None,
) -> str:
    summary = executive_summary or _default_executive_summary(facts)
    working_days = ", ".join(day.capitalize() for day in facts.working_days) or "—"
    plan_line = facts.plan_name or f"Run #{facts.run_id}"

    lines = [
        f"# Department Workload Summary — {facts.batch_code} · Semester {facts.semester_number}",
        "",
        f"**Plan:** {plan_line}  ",
        f"**Generated:** {generated_at}  ",
        f"**Sections:** {facts.section_count} · **Working days:** {working_days}",
        "",
        "## Executive summary",
        "",
        summary,
        "",
        "## Course coverage",
        "",
        f"- Unique courses scheduled: **{facts.unique_courses}**",
        f"- Theory workload slots: **{facts.theory_sessions}**",
        f"- Laboratory workload slots: **{facts.lab_sessions}**",
        f"- Timetable entries: **{facts.timetable_entry_count}**",
        "",
    ]

    lines.extend(_render_pec_sections(facts))

    lines.extend(
        [
            "## Faculty workload",
            "",
            "| Faculty | Designation | Theory h | Lab h | Total h | Theory courses | Lab sessions |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in facts.faculty_rows:
        lines.append(
            f"| {row.full_name} | {row.designation_label} | {row.theory_hours} | {row.lab_hours} | "
            f"{row.total_hours} | {row.theory_courses} | {row.lab_sessions} |"
        )
    lines.append("")

    lines.extend(["## Laboratory & room utilization", ""])
    lines.append(f"- Classrooms used: {', '.join(facts.classrooms_used) or '—'}")
    lines.append(f"- Laboratories used: {', '.join(facts.laboratories_used) or '—'}")
    lines.append(f"- Lecture halls used: {', '.join(facts.lecture_halls_used) or '—'}")
    lines.append("")

    if facts.violation_messages:
        lines.extend(["## Policy warnings", ""])
        for message in facts.violation_messages:
            lines.append(f"- {message}")
        lines.append("")

    if facts.timetable_messages:
        lines.extend(["## Timetable notes", ""])
        for message in facts.timetable_messages:
            lines.append(f"- {message}")
        lines.append("")

    lines.extend(
        [
            "## Advisory notes",
            "",
            "_The following are planning suggestions only — not applied automatically._",
            "",
            "- Review faculty at the upper end of the workload range for burnout risk.",
            "- Confirm PEC electives with zero enrollment are intentionally excluded next semester.",
            "- Validate dual-faculty lab pairings against department lab incharge preferences.",
            "",
            "---",
            "",
            f"_Report generated from allocation run #{facts.run_id}. "
            "Figures are computed from stored assignments and timetable entries._",
        ]
    )
    return "\n".join(lines)

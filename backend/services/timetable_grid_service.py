"""Build day × period timetable grid from allocation entries."""

from __future__ import annotations

from datetime import time

from backend.core.domain.timetable_config import AIML_DAILY_SCHEDULE, DailyPeriodDefinition
from backend.schemas.allocation import (
    BatchSemesterPlanRead,
    FacultyTimetableGridRead,
    FacultyWorkloadSummaryRead,
    SectionTimetableGridRead,
    TimetableEntryRead,
    TimetableGridCellRead,
    TimetableGridItemRead,
    TimetableGridPeriodRead,
    TimetableGridRead,
    TimetableGridRowRead,
)

DAY_ORDER = ("monday", "tuesday", "wednesday", "thursday", "friday")
BREAK_LETTERS = ("B", "R", "E", "A", "K")
LUNCH_LETTERS = ("L", "U", "N", "C", "H")


def _non_teaching_cell_label(slot_type: str, day: str, active_days: list[str]) -> str:
    if slot_type == "break":
        if len(active_days) == len(DAY_ORDER) and day in DAY_ORDER:
            return BREAK_LETTERS[DAY_ORDER.index(day)]
        return "BREAK"
    if slot_type == "lunch":
        if len(active_days) == len(DAY_ORDER) and day in DAY_ORDER:
            return LUNCH_LETTERS[DAY_ORDER.index(day)]
        return "LUNCH"
    return ""


def _format_clock(value: time) -> str:
    hour = value.hour
    minute = value.minute
    if hour == 0:
        display_hour = 12
    elif hour > 12:
        display_hour = hour - 12
    else:
        display_hour = hour
    return f"{display_hour}:{minute:02d}"


def _column_header(period: DailyPeriodDefinition) -> str:
    start = _format_clock(period.start_time)
    end = _format_clock(period.end_time)
    return f"{start} - {end}"


def _build_period_columns() -> list[TimetableGridPeriodRead]:
    columns: list[TimetableGridPeriodRead] = []
    for period in AIML_DAILY_SCHEDULE:
        fixed_label: str | None = None
        if period.slot_type == "break":
            fixed_label = "BREAK"
        elif period.slot_type == "lunch":
            fixed_label = "LUNCH"
        columns.append(
            TimetableGridPeriodRead(
                sort_order=period.sort_order,
                period_number=period.period_number,
                slot_type=period.slot_type,
                label=period.label,
                start_time=_format_clock(period.start_time),
                end_time=_format_clock(period.end_time),
                column_header=_column_header(period),
                fixed_label=fixed_label,
            )
        )
    return columns



def build_timetable_grid(
    entries: list[TimetableEntryRead],
    allowed_days: tuple[str, ...] | None = None,
) -> TimetableGridRead:
    periods = _build_period_columns()
    days = list(DAY_ORDER) if allowed_days is None else [day for day in DAY_ORDER if day in allowed_days]

    rows: list[TimetableGridRowRead] = []
    for day in days:
        cells: list[TimetableGridCellRead] = []
        for period in AIML_DAILY_SCHEDULE:
            if period.slot_type != "teaching":
                cells.append(
                    TimetableGridCellRead(
                        day=day,
                        sort_order=period.sort_order,
                        period_number=period.period_number,
                        slot_type=period.slot_type,
                        fixed_label=_non_teaching_cell_label(period.slot_type, day, days),
                        items=[],
                    )
                )
                continue

            period_number = period.period_number
            assert period_number is not None
            cell_entries = [
                entry
                for entry in entries
                if entry.day == day
                and period_number in entry.period_numbers
                and entry.period_numbers[0] == period_number
            ]
            cells.append(
                TimetableGridCellRead(
                    day=day,
                    sort_order=period.sort_order,
                    period_number=period_number,
                    slot_type=period.slot_type,
                    fixed_label=None,
                    items=[
                        TimetableGridItemRead(
                            batch_code=entry.batch_code,
                            course_code=entry.course_code,
                            course_name=entry.course_name,
                            course_type=entry.course_type,
                            kind=entry.kind,
                            section_indices=entry.section_indices,
                            faculty_names=entry.faculty_names,
                            room_name=entry.room_name,
                            room_type=entry.room_type,
                            period_label=entry.period_label,
                        )
                        for entry in cell_entries
                    ],
                )
            )
        rows.append(TimetableGridRowRead(day=day, cells=cells))

    return TimetableGridRead(periods=periods, rows=rows)


def build_faculty_timetable_grids(
    entries: list[TimetableEntryRead],
    faculty_summaries: list[FacultyWorkloadSummaryRead],
) -> list[FacultyTimetableGridRead]:
    faculty_with_hours = [
        summary
        for summary in faculty_summaries
        if summary.total_weekly_hours > 0
    ]
    grids: list[FacultyTimetableGridRead] = []
    for summary in faculty_with_hours:
        faculty_entries = [
            entry for entry in entries if summary.faculty_id in entry.faculty_ids
        ]
        if not faculty_entries:
            continue
        grids.append(
            FacultyTimetableGridRead(
                faculty_id=summary.faculty_id,
                faculty_name=summary.full_name,
                grid=build_timetable_grid(faculty_entries),
            )
        )
    return grids


def _section_targets(
    entries: list[TimetableEntryRead],
    batch_plans: list[BatchSemesterPlanRead],
) -> list[tuple[str, int, int, tuple[str, ...]]]:
    """Return sorted (batch_code, section_index, semester_number, working_days)."""
    plan_by_batch = {plan.batch_code: plan for plan in batch_plans}
    seen: set[tuple[str, int]] = set()
    targets: list[tuple[str, int, int, tuple[str, ...]]] = []

    for plan in batch_plans:
        for section in range(1, plan.section_count + 1):
            key = (plan.batch_code, section)
            if key in seen:
                continue
            seen.add(key)
            targets.append(
                (plan.batch_code, section, plan.semester_number, tuple(plan.working_days))
            )

    for entry in entries:
        plan = plan_by_batch.get(entry.batch_code)
        for section in entry.section_indices:
            key = (entry.batch_code, section)
            if key in seen:
                continue
            seen.add(key)
            working_days = tuple(plan.working_days) if plan else DAY_ORDER
            semester_number = plan.semester_number if plan else 0
            targets.append((entry.batch_code, section, semester_number, working_days))

    return sorted(targets, key=lambda item: (item[0], item[1]))


def _entry_matches_section(
    entry: TimetableEntryRead,
    batch_code: str,
    section_index: int,
) -> bool:
    return entry.batch_code == batch_code and section_index in entry.section_indices


def build_section_timetable_grids(
    entries: list[TimetableEntryRead],
    batch_plans: list[BatchSemesterPlanRead],
) -> list[SectionTimetableGridRead]:
    grids: list[SectionTimetableGridRead] = []
    for batch_code, section_index, semester_number, working_days in _section_targets(
        entries,
        batch_plans,
    ):
        section_entries = [
            entry
            for entry in entries
            if _entry_matches_section(entry, batch_code, section_index)
        ]
        grids.append(
            SectionTimetableGridRead(
                batch_code=batch_code,
                section_index=section_index,
                semester_number=semester_number,
                grid=build_timetable_grid(section_entries, allowed_days=working_days),
            )
        )
    return grids

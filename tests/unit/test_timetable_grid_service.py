"""Unit tests for timetable grid builder."""

from backend.schemas.allocation import FacultyWorkloadSummaryRead, TimetableEntryRead
from backend.services.timetable_grid_service import (
    build_faculty_timetable_grids,
    build_section_timetable_grids,
    build_timetable_grid,
)


def _sample_entry(**overrides: object) -> TimetableEntryRead:
    payload = {
        "event_id": "evt-1",
        "slot_id": "slot-1",
        "batch_code": "2023-27",
        "course_code": "AIML301",
        "course_name": "Machine Learning",
        "course_type": "PCC",
        "kind": "theory",
        "section_indices": [1],
        "faculty_ids": [10],
        "faculty_names": ["Dr A"],
        "day": "monday",
        "period_numbers": [1],
        "period_label": "P1",
        "room_type": "classroom",
        "room_name": "424",
        "start_time": "08:30",
        "end_time": "09:25",
    }
    payload.update(overrides)
    return TimetableEntryRead(**payload)


def test_grid_has_nine_columns_including_break_and_lunch() -> None:
    grid = build_timetable_grid([_sample_entry()])
    assert len(grid.periods) == 9
    assert grid.periods[2].slot_type == "break"
    assert grid.periods[2].fixed_label == "BREAK"
    assert grid.periods[5].slot_type == "lunch"
    assert grid.periods[0].column_header == "8:30 - 9:25"
    assert grid.periods[6].column_header == "1:50 - 2:40"


def test_break_column_spells_break_down_the_week() -> None:
    grid = build_timetable_grid([])
    monday_break = grid.rows[0].cells[2]
    friday_break = grid.rows[4].cells[2]
    assert monday_break.fixed_label == "B"
    assert friday_break.fixed_label == "K"


def test_partial_week_shows_full_break_label() -> None:
    grid = build_timetable_grid([], allowed_days=("thursday", "friday"))
    assert grid.rows[0].cells[2].fixed_label == "BREAK"
    assert grid.rows[1].cells[5].fixed_label == "LUNCH"


def test_faculty_grid_filters_entries() -> None:
    entries = [
        _sample_entry(faculty_ids=[10], faculty_names=["Dr A"]),
        _sample_entry(
            event_id="evt-2",
            faculty_ids=[20],
            faculty_names=["Dr B"],
            day="tuesday",
            period_numbers=[2],
        ),
    ]
    summaries = [
        FacultyWorkloadSummaryRead(
            faculty_id=10,
            full_name="Dr A",
            designation_key="assistant_professor",
            theory_weekly_hours=3,
            lab_weekly_hours=0,
            total_weekly_hours=3,
            theory_course_count=1,
            lab_course_count=0,
            lab_session_count=0,
        ),
        FacultyWorkloadSummaryRead(
            faculty_id=20,
            full_name="Dr B",
            designation_key="assistant_professor",
            theory_weekly_hours=3,
            lab_weekly_hours=0,
            total_weekly_hours=3,
            theory_course_count=1,
            lab_course_count=0,
            lab_session_count=0,
        ),
    ]
    grids = build_faculty_timetable_grids(entries, summaries)
    assert len(grids) == 2
    assert len(grids[0].grid.rows[0].cells[0].items) == 1
    assert grids[0].grid.rows[1].cells[1].items == []


def test_section_grids_per_batch_and_section() -> None:
    from backend.schemas.allocation import BatchSemesterPlanRead

    entries = [
        _sample_entry(section_indices=[1], period_numbers=[1]),
        _sample_entry(
            event_id="evt-2",
            batch_code="2023-27",
            section_indices=[2],
            day="tuesday",
            period_numbers=[2],
        ),
        _sample_entry(
            event_id="evt-3",
            batch_code="2022-26",
            section_indices=[1, 2],
            course_code="22AM4701",
            day="thursday",
            period_numbers=[3],
        ),
    ]
    batch_plans = [
        BatchSemesterPlanRead(
            batch_code="2023-27",
            semester_number=5,
            section_count=2,
            working_days=["monday", "tuesday", "wednesday", "thursday", "friday"],
        ),
        BatchSemesterPlanRead(
            batch_code="2022-26",
            semester_number=7,
            section_count=2,
            working_days=["thursday", "friday"],
        ),
    ]
    grids = build_section_timetable_grids(entries, batch_plans)
    assert len(grids) == 4
    sec1 = next(g for g in grids if g.batch_code == "2023-27" and g.section_index == 1)
    sec2_26 = next(g for g in grids if g.batch_code == "2022-26" and g.section_index == 2)
    assert len(sec1.grid.rows) == 5
    assert len(sec1.grid.rows[0].cells[0].items) == 1
    assert len(sec2_26.grid.rows) == 2
    assert sec2_26.grid.rows[0].day == "thursday"

"""Tests for roomless course timetable scheduling."""

from backend.optimization.engine.room_assigner import TimeSlotAssignment, assign_rooms_greedy
from backend.optimization.models.timetable_problem import (
    PeriodInfo,
    RoomInput,
    RoomKind,
    ScheduleEvent,
    TimetableProblem,
)
from backend.optimization.preprocessing.schedule_event_builder import build_schedule_events
from backend.optimization.models.solution import SlotAssignment


def test_ug_research_project_skips_room_assignment() -> None:
    assignment = SlotAssignment(
        slot_id="2023-27-23AM3710-T-S1",
        course_id=1,
        batch_code="2023-27",
        working_days=("monday", "tuesday", "wednesday", "thursday", "friday"),
        course_code="23AM3710",
        course_name="UG Research Project",
        course_type="PEC 5",
        kind="theory",
        section_indices=[1],
        weekly_hours=1,
        faculty_ids=[1],
        faculty_names=["Dr Guide"],
        requires_lecture_hall=False,
    )
    events = build_schedule_events([assignment])
    assert len(events) == 1
    assert events[0].room_kind == RoomKind.NONE

    problem = TimetableProblem(
        batch_codes=("2023-27",),
        working_days=("monday", "tuesday", "wednesday", "thursday", "friday"),
        teaching_periods=(1, 2, 3, 4, 5, 6, 7),
        period_info=tuple(
            PeriodInfo(number, f"P{number}", "08:00", "09:00") for number in range(1, 8)
        ),
        classrooms=(RoomInput(1, "C1", RoomKind.CLASSROOM),),
        lecture_halls=(),
        laboratories=(),
        events=tuple(events),
        consecutive_blocks={1: ((1,), (2,), (3,), (4,), (5,), (6,), (7,))},
    )
    entries = assign_rooms_greedy(
        problem,
        [TimeSlotAssignment(event_index=0, day="monday", period_block=(3,))],
        {info.period_number: info for info in problem.period_info},
    )
    assert entries is not None
    assert len(entries) == 1
    assert entries[0].room_type == RoomKind.NONE.value
    assert entries[0].room_name == "—"

"""Unit tests for greedy room assignment (timetable phase 2)."""

from backend.optimization.engine.room_assigner import TimeSlotAssignment, assign_rooms_greedy
from backend.optimization.models.timetable_problem import (
    PeriodInfo,
    RoomInput,
    RoomKind,
    ScheduleEvent,
    TimetableProblem,
)
from backend.optimization.preprocessing.schedule_event_builder import build_consecutive_block_index

WORKING_DAYS = ("monday", "tuesday")


def test_assign_rooms_greedy_uses_distinct_rooms_for_same_period() -> None:
    events = (
        ScheduleEvent(
            event_id="A-W1",
            slot_id="A-T",
            batch_code="2023-27",
            working_days=WORKING_DAYS,
            course_id=1,
            course_code="A101",
            course_name="Course A",
            course_type="PCC",
            kind="theory",
            section_indices=(1,),
            faculty_ids=(1,),
            faculty_names=("Dr A",),
            duration_periods=1,
            room_kind=RoomKind.CLASSROOM,
        ),
        ScheduleEvent(
            event_id="B-W1",
            slot_id="B-T",
            batch_code="2023-27",
            working_days=WORKING_DAYS,
            course_id=2,
            course_code="B101",
            course_name="Course B",
            course_type="PCC",
            kind="theory",
            section_indices=(2,),
            faculty_ids=(2,),
            faculty_names=("Dr B",),
            duration_periods=1,
            room_kind=RoomKind.CLASSROOM,
        ),
    )
    problem = TimetableProblem(
        batch_codes=("2023-27",),
        working_days=WORKING_DAYS,
        teaching_periods=(1, 2),
        period_info=(
            PeriodInfo(1, "1st", "08:30", "09:25"),
            PeriodInfo(2, "2nd", "09:25", "10:20"),
        ),
        classrooms=(
            RoomInput(1, "424", RoomKind.CLASSROOM),
            RoomInput(2, "431", RoomKind.CLASSROOM),
        ),
        lecture_halls=(),
        laboratories=(),
        events=events,
        consecutive_blocks=build_consecutive_block_index(1),
    )
    assignments = [
        TimeSlotAssignment(event_index=0, day="monday", period_block=(1,)),
        TimeSlotAssignment(event_index=1, day="monday", period_block=(1,)),
    ]
    period_lookup = {info.period_number: info for info in problem.period_info}
    entries = assign_rooms_greedy(problem, assignments, period_lookup)
    assert entries is not None
    assert len(entries) == 2
    assert entries[0].room_name != entries[1].room_name


def test_assign_rooms_greedy_fails_when_no_room_left() -> None:
    events = (
        ScheduleEvent(
            event_id="A-W1",
            slot_id="A-T",
            batch_code="2023-27",
            working_days=WORKING_DAYS,
            course_id=1,
            course_code="A101",
            course_name="Course A",
            course_type="PCC",
            kind="theory",
            section_indices=(1,),
            faculty_ids=(1,),
            faculty_names=("Dr A",),
            duration_periods=1,
            room_kind=RoomKind.CLASSROOM,
        ),
        ScheduleEvent(
            event_id="B-W1",
            slot_id="B-T",
            batch_code="2023-27",
            working_days=WORKING_DAYS,
            course_id=2,
            course_code="B101",
            course_name="Course B",
            course_type="PCC",
            kind="theory",
            section_indices=(2,),
            faculty_ids=(2,),
            faculty_names=("Dr B",),
            duration_periods=1,
            room_kind=RoomKind.CLASSROOM,
        ),
    )
    problem = TimetableProblem(
        batch_codes=("2023-27",),
        working_days=WORKING_DAYS,
        teaching_periods=(1,),
        period_info=(PeriodInfo(1, "1st", "08:30", "09:25"),),
        classrooms=(RoomInput(1, "424", RoomKind.CLASSROOM),),
        lecture_halls=(),
        laboratories=(),
        events=events,
        consecutive_blocks=build_consecutive_block_index(1),
    )
    assignments = [
        TimeSlotAssignment(event_index=0, day="monday", period_block=(1,)),
        TimeSlotAssignment(event_index=1, day="monday", period_block=(1,)),
    ]
    period_lookup = {info.period_number: info for info in problem.period_info}
    assert assign_rooms_greedy(problem, assignments, period_lookup) is None

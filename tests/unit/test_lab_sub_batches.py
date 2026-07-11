"""Unit tests for lab B1/B2 sub-batch rules."""

from backend.core.domain.lab_config import LAB_SESSION_HOURS, LAB_SUB_BATCHES
from backend.optimization.engine.timetable_cpsat_solver import TimetableCpsatSolver
from backend.optimization.models.solution import SolverStatus
from backend.optimization.models.timetable_problem import (
    PeriodInfo,
    RoomInput,
    RoomKind,
    ScheduleEvent,
    TimetableProblem,
)
from backend.optimization.preprocessing.lab_scheduling import section_busy_key, section_busy_keys
from backend.optimization.preprocessing.schedule_event_builder import build_consecutive_block_index
from backend.optimization.preprocessing.slot_builder import build_assignment_slots


def _course(**overrides: object) -> object:
    from backend.optimization.models.problem_definition import CourseInput

    payload = {
        "id": 1,
        "batch_code": "2024-28",
        "semester_number": 3,
        "section_count": 2,
        "working_days": ("monday", "tuesday", "wednesday", "thursday", "friday"),
        "course_code": "24AM2301",
        "name": "Sample Lab Course",
        "course_type": "PCC",
        "lectures_per_week": 3,
        "practical_hours": 2,
        "requires_lecture_hall": False,
    }
    payload.update(overrides)
    return CourseInput(**payload)


def test_lab_slots_split_into_b1_and_b2() -> None:
    course = _course()
    slots = build_assignment_slots(
        courses=[course],
        eligibility={course.id: (1, 2)},
        matched_ids={course.id: (1, 2)},
        fallback_flags={course.id: False},
    )
    lab_slots = [slot for slot in slots if slot.kind.value == "lab"]
    assert len(lab_slots) == 2 * course.section_count
    assert {slot.lab_sub_batch for slot in lab_slots} == set(LAB_SUB_BATCHES)
    assert all(slot.weekly_hours == LAB_SESSION_HOURS for slot in lab_slots)
    assert lab_slots[0].slot_id.endswith("-B1")


def test_lab_sub_batches_allow_same_section_parallel() -> None:
    event_b1 = ScheduleEvent(
        event_id="b1",
        slot_id="slot-b1",
        batch_code="2024-28",
        working_days=("monday",),
        course_id=1,
        course_code="C",
        course_name="C",
        course_type="PCC",
        kind="lab",
        section_indices=(1,),
        faculty_ids=(1,),
        faculty_names=("Dr A",),
        duration_periods=2,
        room_kind=RoomKind.LABORATORY,
        lab_sub_batch="B1",
    )
    event_b2 = ScheduleEvent(
        event_id="b2",
        slot_id="slot-b2",
        batch_code="2024-28",
        working_days=("monday",),
        course_id=1,
        course_code="C",
        course_name="C",
        course_type="PCC",
        kind="lab",
        section_indices=(1,),
        faculty_ids=(2,),
        faculty_names=("Dr B",),
        duration_periods=2,
        room_kind=RoomKind.LABORATORY,
        lab_sub_batch="B2",
    )
    assert section_busy_key(event_b1, 1) != section_busy_key(event_b2, 1)
    assert not set(section_busy_keys(event_b1, 1)) & set(section_busy_keys(event_b2, 1))


def test_b1_and_b2_different_subjects_may_run_at_same_time() -> None:
    working_days = ("monday", "tuesday", "wednesday", "thursday", "friday")
    events = (
        ScheduleEvent(
            event_id="course-a-b1",
            slot_id="slot-a-b1",
            batch_code="2024-28",
            working_days=working_days,
            course_id=1,
            course_code="24AM2301",
            course_name="Lab Course A",
            course_type="PCC",
            kind="lab",
            section_indices=(1,),
            faculty_ids=(1, 2),
            faculty_names=("Dr A", "Dr B"),
            duration_periods=2,
            room_kind=RoomKind.LABORATORY,
            lab_sub_batch="B1",
        ),
        ScheduleEvent(
            event_id="course-b-b2",
            slot_id="slot-b-b2",
            batch_code="2024-28",
            working_days=working_days,
            course_id=2,
            course_code="24AM2302",
            course_name="Lab Course B",
            course_type="PCC",
            kind="lab",
            section_indices=(1,),
            faculty_ids=(3, 4),
            faculty_names=("Dr C", "Dr D"),
            duration_periods=2,
            room_kind=RoomKind.LABORATORY,
            lab_sub_batch="B2",
        ),
    )
    problem = TimetableProblem(
        batch_codes=("2024-28",),
        working_days=working_days,
        teaching_periods=(1, 2, 3, 4, 5, 6, 7),
        period_info=(
            PeriodInfo(1, "1st", "08:30", "09:25"),
            PeriodInfo(2, "2nd", "09:25", "10:20"),
            PeriodInfo(3, "3rd", "10:45", "11:40"),
            PeriodInfo(4, "4th", "11:40", "12:35"),
        ),
        classrooms=(),
        lecture_halls=(),
        laboratories=(
            RoomInput(1, "508", RoomKind.LABORATORY),
            RoomInput(2, "509", RoomKind.LABORATORY),
        ),
        events=events,
        consecutive_blocks=build_consecutive_block_index(2),
    )
    solution = TimetableCpsatSolver().solve(problem)
    assert solution.status == SolverStatus.FEASIBLE
    assert len(solution.entries) == 2
    by_batch = {entry.lab_sub_batch: entry for entry in solution.entries}
    assert by_batch["B1"].course_code == "24AM2301"
    assert by_batch["B2"].course_code == "24AM2302"
    assert by_batch["B1"].day == by_batch["B2"].day
    assert by_batch["B1"].period_numbers == by_batch["B2"].period_numbers


def test_theory_blocks_lab_sub_batch_for_same_section() -> None:
    working_days = ("monday",)
    events = (
        ScheduleEvent(
            event_id="theory-s1",
            slot_id="slot-theory",
            batch_code="2024-28",
            working_days=working_days,
            course_id=10,
            course_code="24AM2303",
            course_name="Theory",
            course_type="PCC",
            kind="theory",
            section_indices=(1,),
            faculty_ids=(5,),
            faculty_names=("Dr E",),
            duration_periods=1,
            room_kind=RoomKind.CLASSROOM,
        ),
        ScheduleEvent(
            event_id="lab-b1",
            slot_id="slot-lab-b1",
            batch_code="2024-28",
            working_days=working_days,
            course_id=1,
            course_code="24AM2301",
            course_name="Lab Course A",
            course_type="PCC",
            kind="lab",
            section_indices=(1,),
            faculty_ids=(1, 2),
            faculty_names=("Dr A", "Dr B"),
            duration_periods=2,
            room_kind=RoomKind.LABORATORY,
            lab_sub_batch="B1",
        ),
    )
    problem = TimetableProblem(
        batch_codes=("2024-28",),
        working_days=working_days,
        teaching_periods=(1, 2, 3, 4),
        period_info=(
            PeriodInfo(1, "1st", "08:30", "09:25"),
            PeriodInfo(2, "2nd", "09:25", "10:20"),
            PeriodInfo(3, "3rd", "10:45", "11:40"),
            PeriodInfo(4, "4th", "11:40", "12:35"),
        ),
        classrooms=(RoomInput(1, "C1", RoomKind.CLASSROOM),),
        lecture_halls=(),
        laboratories=(RoomInput(2, "508", RoomKind.LABORATORY),),
        events=events,
        consecutive_blocks=build_consecutive_block_index(2),
    )
    solution = TimetableCpsatSolver().solve(problem)
    assert solution.status == SolverStatus.FEASIBLE
    theory = next(entry for entry in solution.entries if entry.kind == "theory")
    lab = next(entry for entry in solution.entries if entry.kind == "lab")
    assert not (set(theory.period_numbers) & set(lab.period_numbers) and theory.day == lab.day)


def _lab_pair_problem(*, laboratories: tuple[RoomInput, ...]) -> TimetableProblem:
    working_days = ("monday", "tuesday", "wednesday", "thursday", "friday")
    events = (
        ScheduleEvent(
            event_id="b1-lab",
            slot_id="slot-b1",
            batch_code="2024-28",
            working_days=working_days,
            course_id=1,
            course_code="C1",
            course_name="Course",
            course_type="PCC",
            kind="lab",
            section_indices=(1,),
            faculty_ids=(1, 2),
            faculty_names=("Dr A", "Dr B"),
            duration_periods=2,
            room_kind=RoomKind.LABORATORY,
            lab_sub_batch="B1",
        ),
        ScheduleEvent(
            event_id="b2-lab",
            slot_id="slot-b2",
            batch_code="2024-28",
            working_days=working_days,
            course_id=1,
            course_code="C1",
            course_name="Course",
            course_type="PCC",
            kind="lab",
            section_indices=(1,),
            faculty_ids=(3, 4),
            faculty_names=("Dr C", "Dr D"),
            duration_periods=2,
            room_kind=RoomKind.LABORATORY,
            lab_sub_batch="B2",
        ),
    )
    return TimetableProblem(
        batch_codes=("2024-28",),
        working_days=working_days,
        teaching_periods=(1, 2, 3, 4, 5, 6, 7),
        period_info=(
            PeriodInfo(1, "1st", "08:30", "09:25"),
            PeriodInfo(2, "2nd", "09:25", "10:20"),
            PeriodInfo(3, "3rd", "10:45", "11:40"),
            PeriodInfo(4, "4th", "11:40", "12:35"),
        ),
        classrooms=(),
        lecture_halls=(),
        laboratories=laboratories,
        events=events,
        consecutive_blocks=build_consecutive_block_index(2),
    )


def test_both_b1_and_b2_scheduled_with_one_lab_at_different_times() -> None:
    problem = _lab_pair_problem(
        laboratories=(RoomInput(1, "508", RoomKind.LABORATORY),),
    )
    solution = TimetableCpsatSolver().solve(problem)
    assert solution.status == SolverStatus.FEASIBLE
    assert len(solution.entries) == 2
    sub_batches = {entry.lab_sub_batch for entry in solution.entries}
    assert sub_batches == {"B1", "B2"}


def test_both_b1_and_b2_infeasible_without_laboratories() -> None:
    problem = _lab_pair_problem(laboratories=())
    solution = TimetableCpsatSolver().solve(problem)
    assert solution.status == SolverStatus.INFEASIBLE

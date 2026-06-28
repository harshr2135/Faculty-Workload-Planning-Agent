"""Unit tests for timetable solvers (CP-SAT legacy + greedy default)."""

from backend.optimization.engine.greedy_timetable_scheduler import GreedyTimetableScheduler
from backend.optimization.engine.timetable_cpsat_solver import TimetableCpsatSolver
from backend.optimization.models.solution import SolverStatus
from backend.optimization.models.timetable_problem import (
    FixedTimetablePlacement,
    PeriodInfo,
    RoomInput,
    RoomKind,
    ScheduleEvent,
    TimetableProblem,
)
from backend.optimization.preprocessing.schedule_event_builder import build_consecutive_block_index

WORKING_DAYS = ("monday", "tuesday", "wednesday", "thursday", "friday")


def _tiny_timetable_problem() -> TimetableProblem:
    events = (
        ScheduleEvent(
            event_id="A-T-S1-W1",
            slot_id="A-T-S1",
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
            event_id="B-T-S1-W1",
            slot_id="B-T-S1",
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
    return TimetableProblem(
        batch_codes=("2023-27",),
        working_days=WORKING_DAYS,
        teaching_periods=(1, 2, 3, 4, 5, 6, 7),
        period_info=(
            PeriodInfo(1, "1st", "08:30", "09:25"),
            PeriodInfo(2, "2nd", "09:25", "10:20"),
        ),
        classrooms=(RoomInput(1, "424", RoomKind.CLASSROOM),),
        lecture_halls=(RoomInput(10, "LH-1", RoomKind.LECTURE_HALL),),
        laboratories=(RoomInput(20, "508", RoomKind.LABORATORY),),
        events=events,
        consecutive_blocks=build_consecutive_block_index(1),
    )


def test_greedy_timetable_places_all_events() -> None:
    solution = GreedyTimetableScheduler().schedule(_tiny_timetable_problem())
    assert solution.status == SolverStatus.FEASIBLE
    assert len(solution.entries) == 2


def test_timetable_solver_allows_multiple_sessions_same_day_when_few_working_days() -> None:
    """4th year: 3 weekly lectures but only Thu–Fri must remain feasible."""
    working_days = ("thursday", "friday")
    events = tuple(
        ScheduleEvent(
            event_id=f"PEC-T-LH1-W{session}",
            slot_id="PEC-T-LH1",
            batch_code="2022-26",
            working_days=working_days,
            course_id=1,
            course_code="22AM4702",
            course_name="Quantum Computing",
            course_type="PEC",
            kind="theory",
            section_indices=(1, 2),
            faculty_ids=(1,),
            faculty_names=("Dr A",),
            duration_periods=1,
            room_kind=RoomKind.LECTURE_HALL,
            session_index=session,
        )
        for session in range(1, 4)
    )
    period_info = tuple(
        PeriodInfo(number, f"P{number}", "08:30", "09:25")
        for number in range(1, 8)
    )
    problem = TimetableProblem(
        batch_codes=("2022-26",),
        working_days=working_days,
        teaching_periods=tuple(range(1, 8)),
        period_info=period_info,
        classrooms=(RoomInput(1, "424", RoomKind.CLASSROOM),),
        lecture_halls=(RoomInput(10, "LH-1", RoomKind.LECTURE_HALL),),
        laboratories=(RoomInput(20, "508", RoomKind.LABORATORY),),
        events=events,
        consecutive_blocks=build_consecutive_block_index(1),
    )
    solution = GreedyTimetableScheduler().schedule(problem)
    assert solution.status == SolverStatus.FEASIBLE
    assert len(solution.entries) == 3


def test_greedy_timetable_across_two_batches() -> None:
    batch_a = ScheduleEvent(
        event_id="A-W1",
        slot_id="A-T",
        batch_code="2022-26",
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
    )
    batch_b = ScheduleEvent(
        event_id="B-W1",
        slot_id="B-T",
        batch_code="2023-27",
        working_days=WORKING_DAYS,
        course_id=2,
        course_code="B101",
        course_name="Course B",
        course_type="PCC",
        kind="theory",
        section_indices=(1,),
        faculty_ids=(2,),
        faculty_names=("Dr B",),
        duration_periods=1,
        room_kind=RoomKind.CLASSROOM,
    )
    problem = TimetableProblem(
        batch_codes=("2022-26", "2023-27"),
        working_days=WORKING_DAYS,
        teaching_periods=(1, 2),
        period_info=(
            PeriodInfo(1, "1st", "08:30", "09:25"),
            PeriodInfo(2, "2nd", "09:25", "10:20"),
        ),
        classrooms=(RoomInput(1, "424", RoomKind.CLASSROOM),),
        lecture_halls=(),
        laboratories=(),
        events=(batch_a, batch_b),
        consecutive_blocks=build_consecutive_block_index(1),
    )
    solution = GreedyTimetableScheduler().schedule(problem)
    assert solution.status == SolverStatus.FEASIBLE
    assert len(solution.entries) == 2
    assert "Greedy" in solution.messages[0]


def test_cpsat_fixed_placement_still_supported() -> None:
    problem = _tiny_timetable_problem()
    fixed = FixedTimetablePlacement(
        day="monday",
        period_block=(1,),
        room_id=10,
        faculty_ids=(1,),
        batch_code="2022-26",
        section_indices=(1,),
    )
    constrained = TimetableProblem(
        batch_codes=problem.batch_codes,
        working_days=problem.working_days,
        teaching_periods=problem.teaching_periods,
        period_info=problem.period_info,
        classrooms=problem.classrooms,
        lecture_halls=problem.lecture_halls,
        laboratories=problem.laboratories,
        events=problem.events[:1],
        consecutive_blocks=problem.consecutive_blocks,
        fixed_placements=(fixed,),
    )
    solution = TimetableCpsatSolver().solve(constrained)
    assert solution.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
    assert solution.entries[0].day != "monday" or solution.entries[0].period_numbers != [1]

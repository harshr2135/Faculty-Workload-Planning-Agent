"""Tests for PEC pool timetable scheduling (parallel timing disabled)."""

from backend.optimization.engine.timetable_cpsat_solver import TimetableCpsatSolver
from backend.optimization.models.solution import SolverStatus
from backend.optimization.models.timetable_problem import (
    PeriodInfo,
    RoomInput,
    RoomKind,
    ScheduleEvent,
    TimetableProblem,
)
from backend.optimization.preprocessing.schedule_event_builder import build_consecutive_block_index


def _pec_event(
    *,
    event_id: str,
    course_code: str,
    faculty_ids: tuple[int, ...],
    session_index: int = 1,
    room_kind: RoomKind = RoomKind.CLASSROOM,
    section_indices: tuple[int, ...] = (1,),
) -> ScheduleEvent:
    return ScheduleEvent(
        event_id=event_id,
        slot_id=f"{course_code}-T-S1-W{session_index}",
        batch_code="2023-27",
        working_days=("monday", "tuesday", "wednesday", "thursday", "friday"),
        course_id=1,
        course_code=course_code,
        course_name=course_code,
        course_type="PEC 2",
        kind="theory",
        section_indices=section_indices,
        faculty_ids=faculty_ids,
        faculty_names=tuple(f"Dr {faculty_id}" for faculty_id in faculty_ids),
        duration_periods=1,
        room_kind=room_kind,
        session_index=session_index,
    )


def test_pec_pool_electives_schedule_independently() -> None:
    """PEC electives in the same pool may use different weekly time slots."""
    working_days = ("monday", "tuesday", "wednesday", "thursday", "friday")
    events = (
        _pec_event(event_id="pec-a", course_code="23AM3605", faculty_ids=(1, 2), section_indices=(1,)),
        _pec_event(event_id="pec-b", course_code="23AM3606", faculty_ids=(3, 4), section_indices=(2,)),
    )
    problem = TimetableProblem(
        batch_codes=("2023-27",),
        working_days=working_days,
        teaching_periods=(1, 2, 3, 4, 5, 6, 7),
        period_info=tuple(
            PeriodInfo(number, f"P{number}", "08:00", "09:00") for number in range(1, 8)
        ),
        classrooms=tuple(
            RoomInput(index, f"C{index}", RoomKind.CLASSROOM) for index in range(1, 6)
        ),
        lecture_halls=(),
        laboratories=(),
        events=events,
        consecutive_blocks=build_consecutive_block_index(1),
    )
    solution = TimetableCpsatSolver().solve(problem)
    assert solution.status == SolverStatus.FEASIBLE
    assert len(solution.entries) == 2

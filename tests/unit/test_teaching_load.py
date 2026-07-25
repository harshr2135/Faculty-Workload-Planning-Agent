"""Unit tests for AICTE teaching-load conversion."""

from backend.core.domain.teaching_load import (
    format_teaching_load_hours,
    slot_teaching_load_hours,
    teaching_load_hours,
)
from backend.optimization.engine.cpsat_solver import WorkloadCpsatSolver
from backend.optimization.models.problem_definition import (
    AssignmentSlot,
    BatchPlanInput,
    FacultyInput,
    SlotKind,
    WorkloadProblem,
)
from backend.optimization.models.solution import SolverStatus


WORKING_DAYS = ("monday", "tuesday", "wednesday", "thursday", "friday")


def test_teaching_load_half_weights_lab_and_tutorial() -> None:
    assert teaching_load_hours(theory_contact_hours=8, lab_contact_hours=8) == 12
    assert teaching_load_hours(theory_contact_hours=0, lab_contact_hours=2) == 1
    assert teaching_load_hours(tutorial_contact_hours=4) == 2
    assert slot_teaching_load_hours("theory", 3) == 3
    assert slot_teaching_load_hours("lab", 2) == 1
    assert slot_teaching_load_hours("tutorial", 2) == 1
    assert format_teaching_load_hours(4.0) == "4"
    assert format_teaching_load_hours(4.5) == "4.5"


def _faculty(fid: int, *, max_weekly_hours: float) -> FacultyInput:
    return FacultyInput(
        id=fid,
        full_name=f"Dr {fid}",
        designation_key="assistant_professor",
        designation_label="Assistant Professor",
        min_weekly_hours=0,
        max_weekly_hours=max_weekly_hours,
        min_theory_courses=0,
        min_lab_courses=0,
        min_lab_sessions=None,
        max_lab_sessions=None,
    )


def _lab_slot(*, hours: int = 2, eligible: tuple[int, ...] = (1,)) -> AssignmentSlot:
    return AssignmentSlot(
        slot_id="2023-27-LAB-B1",
        course_id=50,
        batch_code="2023-27",
        working_days=WORKING_DAYS,
        course_code="LAB1",
        course_name="Lab",
        course_type="PCC",
        kind=SlotKind.LAB,
        section_indices=(1,),
        weekly_hours=hours,
        eligible_faculty_ids=eligible,
        specialization_matched_ids=eligible,
        fallback_required=False,
        lab_sub_batch="B1",
    )


def test_cpsat_lab_counts_half_toward_weekly_cap() -> None:
    # Cap of 1 teaching-load hour: a 2-hour lab counts as 1 → feasible.
    # Under 1:1 contact counting this would require a cap of 2.
    faculty = (_faculty(1, max_weekly_hours=1),)
    problem = WorkloadProblem(
        batch_plans=(BatchPlanInput("2023-27", 5, 1, WORKING_DAYS),),
        lab_faculty_per_session=1,
        faculty=faculty,
        courses=(),
        slots=(_lab_slot(hours=2, eligible=(1,)),),
        lab_tutorial_hours_per_teaching_hour=2,
    )
    solution = WorkloadCpsatSolver().solve(problem)

    assert solution.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
    assert solution.faculty_summaries[0].lab_weekly_hours == 2
    assert solution.faculty_summaries[0].total_weekly_hours == 1.0

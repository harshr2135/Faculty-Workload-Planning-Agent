"""Unit tests for CP-SAT workload solver."""

from backend.optimization.engine.cpsat_solver import WorkloadCpsatSolver
from backend.optimization.models.problem_definition import (
    AssignmentSlot,
    BatchPlanInput,
    CourseInput,
    FacultyInput,
    SlotKind,
    WorkloadProblem,
)
from backend.optimization.models.solution import SolverStatus

WORKING_DAYS = ("monday", "tuesday", "wednesday", "thursday", "friday")


def _tiny_problem() -> WorkloadProblem:
    faculty = (
        FacultyInput(
            id=1,
            full_name="Dr A",
            designation_key="assistant_professor",
            designation_label="Assistant Professor",
            min_weekly_hours=0,
            max_weekly_hours=24,
            min_theory_courses=0,
            min_lab_courses=0,
            min_lab_sessions=None,
            max_lab_sessions=None,
        ),
        FacultyInput(
            id=2,
            full_name="Dr B",
            designation_key="assistant_professor",
            designation_label="Assistant Professor",
            min_weekly_hours=0,
            max_weekly_hours=24,
            min_theory_courses=0,
            min_lab_courses=0,
            min_lab_sessions=None,
            max_lab_sessions=None,
        ),
    )
    courses = (
        CourseInput(
            id=10,
            batch_code="2023-27",
            semester_number=5,
            section_count=1,
            working_days=WORKING_DAYS,
            course_code="TST101",
            name="Test Course",
            course_type="PCC",
            lectures_per_week=3,
            practical_hours=2,
            requires_lecture_hall=False,
        ),
    )
    slots = (
        AssignmentSlot(
            slot_id="2023-27-TST101-T-S1",
            course_id=10,
            batch_code="2023-27",
            working_days=WORKING_DAYS,
            course_code="TST101",
            course_name="Test Course",
            course_type="PCC",
            kind=SlotKind.THEORY,
            section_indices=(1,),
            weekly_hours=3,
            eligible_faculty_ids=(1, 2),
            specialization_matched_ids=(1,),
            fallback_required=False,
        ),
        AssignmentSlot(
            slot_id="2023-27-TST101-L-S1",
            course_id=10,
            batch_code="2023-27",
            working_days=WORKING_DAYS,
            course_code="TST101",
            course_name="Test Course",
            course_type="PCC",
            kind=SlotKind.LAB,
            section_indices=(1,),
            weekly_hours=2,
            eligible_faculty_ids=(1, 2),
            specialization_matched_ids=(1, 2),
            fallback_required=False,
        ),
    )
    return WorkloadProblem(
        batch_plans=(
            BatchPlanInput(
                batch_code="2023-27",
                semester_number=5,
                section_count=1,
                working_days=WORKING_DAYS,
            ),
        ),
        lab_faculty_per_session=2,
        faculty=faculty,
        courses=courses,
        slots=slots,
    )


def test_cpsat_solver_finds_feasible_assignment() -> None:
    solution = WorkloadCpsatSolver().solve(_tiny_problem())
    assert solution.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
    assert len(solution.assignments) == 2
    theory = next(a for a in solution.assignments if a.kind == "theory")
    lab = next(a for a in solution.assignments if a.kind == "lab")
    assert len(theory.faculty_ids) == 1
    assert len(lab.faculty_ids) == 2

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


def _faculty(fid: int, *, max_weekly_hours: float = 40, max_lab_sessions: int | None = None) -> FacultyInput:
    return FacultyInput(
        id=fid,
        full_name=f"Dr {fid}",
        designation_key="professor" if max_weekly_hours <= 10 else "assistant_professor",
        designation_label="Professor" if max_weekly_hours <= 10 else "Assistant Professor",
        min_weekly_hours=0,
        max_weekly_hours=max_weekly_hours,
        min_theory_courses=0,
        min_lab_courses=0,
        min_lab_sessions=None,
        max_lab_sessions=max_lab_sessions,
    )


def _theory_slot(section: int, *, eligible: tuple[int, ...]) -> AssignmentSlot:
    return AssignmentSlot(
        slot_id=f"2023-27-C101-T-S{section}",
        course_id=10,
        batch_code="2023-27",
        working_days=WORKING_DAYS,
        course_code="C101",
        course_name="Course",
        course_type="PCC",
        kind=SlotKind.THEORY,
        section_indices=(section,),
        weekly_hours=3,
        eligible_faculty_ids=eligible,
        specialization_matched_ids=eligible,
        fallback_required=False,
    )


def _distinct_theory_slot(course_id: int, hours: int, *, eligible: tuple[int, ...]) -> AssignmentSlot:
    """One theory slot for a unique course (no cross-section duplicate penalty)."""
    return AssignmentSlot(
        slot_id=f"2023-27-C{course_id}-T-S1",
        course_id=course_id,
        batch_code="2023-27",
        working_days=WORKING_DAYS,
        course_code=f"C{course_id}",
        course_name="Course",
        course_type="PCC",
        kind=SlotKind.THEORY,
        section_indices=(1,),
        weekly_hours=hours,
        eligible_faculty_ids=eligible,
        specialization_matched_ids=eligible,
        fallback_required=False,
    )


def _problem_from(faculty: tuple[FacultyInput, ...], slots: tuple[AssignmentSlot, ...]) -> WorkloadProblem:
    return WorkloadProblem(
        batch_plans=(BatchPlanInput("2023-27", 5, 2, WORKING_DAYS),),
        lab_faculty_per_session=2,
        faculty=faculty,
        courses=(),
        slots=slots,
    )


def test_cpsat_preserves_lab_sub_batch() -> None:
    solution = WorkloadCpsatSolver().solve(_tiny_problem())
    # The tiny problem's lab slot has no sub-batch, but the field must round-trip (not dropped).
    lab = next(a for a in solution.assignments if a.kind == "lab")
    assert hasattr(lab, "lab_sub_batch")


def test_cpsat_hard_max_weekly_hours_is_infeasible_when_exceeded() -> None:
    # Single professor capped at 10h cannot legally cover four 3h sections (12h).
    # Hard cap -> no feasible assignment.
    faculty = (_faculty(1, max_weekly_hours=10),)
    slots = tuple(_theory_slot(section, eligible=(1,)) for section in (1, 2, 3, 4))
    solution = WorkloadCpsatSolver().solve(_problem_from(faculty, slots))

    assert solution.status == SolverStatus.INFEASIBLE


def test_cpsat_hard_max_weekly_hours_spreads_within_caps() -> None:
    # Two professors capped at 10h each; four 3h sections (12h total) fit only if the load
    # is split (e.g. 2 + 2 sections = 6h each) rather than piled onto one faculty.
    faculty = (_faculty(1, max_weekly_hours=10), _faculty(2, max_weekly_hours=10))
    slots = tuple(_theory_slot(section, eligible=(1, 2)) for section in (1, 2, 3, 4))
    solution = WorkloadCpsatSolver().solve(_problem_from(faculty, slots))

    assert solution.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
    for summary in solution.faculty_summaries:
        assert summary.total_weekly_hours <= 10


def test_cpsat_preserves_cap_ratio_in_allocation() -> None:
    # Faculty caps 4 and 2 (ratio 2:1); three 1-hour courses (3h) with slack under both caps.
    # Proportional balancing splits load to keep equal utilization: 2h and 1h (each at 50%),
    # preserving the 2:1 cap ratio rather than piling onto either one.
    faculty = (_faculty(1, max_weekly_hours=4), _faculty(2, max_weekly_hours=2))
    slots = tuple(
        _distinct_theory_slot(course_id=100 + i, hours=1, eligible=(1, 2)) for i in range(3)
    )
    solution = WorkloadCpsatSolver().solve(_problem_from(faculty, slots))

    assert solution.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
    load = {s.faculty_id: s.total_weekly_hours for s in solution.faculty_summaries}
    assert load[1] == 2
    assert load[2] == 1


def _matched_slot(course_id: int, *, eligible: tuple[int, ...], matched: tuple[int, ...]) -> AssignmentSlot:
    return AssignmentSlot(
        slot_id=f"2023-27-C{course_id}-T-S1",
        course_id=course_id,
        batch_code="2023-27",
        working_days=WORKING_DAYS,
        course_code=f"C{course_id}",
        course_name="Course",
        course_type="PCC",
        kind=SlotKind.THEORY,
        section_indices=(1,),
        weekly_hours=1,
        eligible_faculty_ids=eligible,
        specialization_matched_ids=matched,
        fallback_required=False,
    )


def test_cpsat_specialization_beats_proportional_balance() -> None:
    # Faculty 1 (cap 4) is the only specialist for both courses; faculty 2 (cap 2) is an
    # eligible but non-matching option. Proportional balance would prefer to offload a course
    # to #2, but specialization dominates, so the specialist keeps both.
    faculty = (_faculty(1, max_weekly_hours=4), _faculty(2, max_weekly_hours=2))
    slots = tuple(
        _matched_slot(course_id, eligible=(1, 2), matched=(1,)) for course_id in (201, 202)
    )
    solution = WorkloadCpsatSolver().solve(_problem_from(faculty, slots))

    assert solution.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
    load = {s.faculty_id: s.total_weekly_hours for s in solution.faculty_summaries}
    assert load[1] == 2
    assert load[2] == 0


def test_cpsat_prefers_distinct_faculty_per_section() -> None:
    # Two eligible faculty, two sections of the same course -> each section a distinct faculty.
    faculty = (_faculty(1), _faculty(2))
    slots = (_theory_slot(1, eligible=(1, 2)), _theory_slot(2, eligible=(1, 2)))
    solution = WorkloadCpsatSolver().solve(_problem_from(faculty, slots))

    assert solution.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
    assigned = [a.faculty_ids[0] for a in solution.assignments if a.kind == "theory"]
    assert set(assigned) == {1, 2}

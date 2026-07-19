"""Unit tests for greedy workload allocator."""

from backend.optimization.engine.greedy_workload_allocator import GreedyWorkloadAllocator
from backend.optimization.models.problem_definition import (
    AssignmentSlot,
    BatchPlanInput,
    FacultyInput,
    SlotKind,
    WorkloadProblem,
)
from backend.optimization.models.solution import SolverStatus


def test_greedy_assigns_distinct_faculty_per_theory_section() -> None:
    faculty = tuple(
        FacultyInput(
            faculty_id,
            f"Dr {faculty_id}",
            "assistant_professor",
            "Assistant Professor",
            0,
            40,
            0,
            0,
            None,
            None,
        )
        for faculty_id in (1, 2, 3)
    )
    slots = tuple(
        AssignmentSlot(
            slot_id=f"2023-27-C101-T-S{section}",
            course_id=1,
            batch_code="2023-27",
            working_days=("monday", "tuesday", "wednesday", "thursday", "friday"),
            course_code="C101",
            course_name="Course",
            course_type="PCC",
            kind=SlotKind.THEORY,
            section_indices=(section,),
            weekly_hours=3,
            eligible_faculty_ids=(1, 2, 3),
            specialization_matched_ids=(1, 2, 3),
            fallback_required=False,
        )
        for section in (1, 2, 3)
    )
    problem = WorkloadProblem(
        batch_plans=(
            BatchPlanInput("2023-27", 5, 2, ("monday", "tuesday", "wednesday", "thursday", "friday")),
        ),
        lab_faculty_per_session=2,
        faculty=faculty,
        courses=(),
        slots=slots,
    )
    solution = GreedyWorkloadAllocator().allocate(problem)
    assert solution.status == SolverStatus.FEASIBLE
    assigned = {tuple(assignment.section_indices): assignment.faculty_ids[0] for assignment in solution.assignments}
    assert len(set(assigned.values())) == 3


def test_greedy_assigns_theory_slot() -> None:
    problem = WorkloadProblem(
        batch_plans=(
            BatchPlanInput("2023-27", 5, 2, ("monday", "tuesday", "wednesday", "thursday", "friday")),
        ),
        lab_faculty_per_session=2,
        faculty=(
            FacultyInput(
                1,
                "Dr A",
                "professor",
                "Professor",
                0,
                40,
                0,
                0,
                None,
                None,
            ),
        ),
        courses=(),
        slots=(
            AssignmentSlot(
                slot_id="2023-27-C101-T-S1",
                course_id=1,
                batch_code="2023-27",
                working_days=("monday", "tuesday", "wednesday", "thursday", "friday"),
                course_code="C101",
                course_name="Course",
                course_type="PCC",
                kind=SlotKind.THEORY,
                section_indices=(1,),
                weekly_hours=3,
                eligible_faculty_ids=(1,),
                specialization_matched_ids=(1,),
                fallback_required=False,
            ),
        ),
    )
    solution = GreedyWorkloadAllocator().allocate(problem)
    assert solution.status == SolverStatus.FEASIBLE
    assert solution.assignments[0].faculty_ids == [1]


def _theory_slot(section: int, *, weekly_hours: int = 3, eligible: tuple[int, ...] = (1,)) -> AssignmentSlot:
    return AssignmentSlot(
        slot_id=f"2023-27-C101-T-S{section}",
        course_id=1,
        batch_code="2023-27",
        working_days=("monday", "tuesday", "wednesday", "thursday", "friday"),
        course_code="C101",
        course_name="Course",
        course_type="PCC",
        kind=SlotKind.THEORY,
        section_indices=(section,),
        weekly_hours=weekly_hours,
        eligible_faculty_ids=eligible,
        specialization_matched_ids=eligible,
        fallback_required=False,
    )


def _lab_slot(index: int, *, eligible: tuple[int, ...]) -> AssignmentSlot:
    return AssignmentSlot(
        slot_id=f"2023-27-C201-L-S{index}",
        course_id=2,
        batch_code="2023-27",
        working_days=("monday", "tuesday", "wednesday", "thursday", "friday"),
        course_code="C201",
        course_name="Lab",
        course_type="PCC",
        kind=SlotKind.LAB,
        section_indices=(index,),
        weekly_hours=2,
        eligible_faculty_ids=eligible,
        specialization_matched_ids=eligible,
        fallback_required=False,
        lab_sub_batch="B1",
    )


def _problem(faculty: tuple[FacultyInput, ...], slots: tuple[AssignmentSlot, ...]) -> WorkloadProblem:
    return WorkloadProblem(
        batch_plans=(
            BatchPlanInput("2023-27", 5, 2, ("monday", "tuesday", "wednesday", "thursday", "friday")),
        ),
        lab_faculty_per_session=2,
        faculty=faculty,
        courses=(),
        slots=slots,
    )


def test_greedy_hard_max_weekly_hours_blocks_overage() -> None:
    # Professor capped at 10 weekly hours; four 3-hour theory sections (12 hrs) must be staffed
    # by the only eligible faculty. Hard maximum: no legal assignment exists → infeasible.
    faculty = (FacultyInput(1, "Dr A", "professor", "Professor", 0, 10, 0, 0, None, None),)
    slots = tuple(_theory_slot(section) for section in (1, 2, 3, 4))
    solution = GreedyWorkloadAllocator().allocate(_problem(faculty, slots))

    assert solution.status == SolverStatus.INFEASIBLE
    assert any(v.code == "workload_capacity_exceeded" for v in solution.violations)


def test_greedy_flags_min_theory_courses_not_met() -> None:
    # Assistant Professor requires 2 theory courses but only one is available.
    faculty = (FacultyInput(1, "Dr A", "assistant_professor", "Assistant Professor", 0, 40, 2, 0, None, None),)
    solution = GreedyWorkloadAllocator().allocate(_problem(faculty, (_theory_slot(1),)))

    assert solution.status == SolverStatus.FEASIBLE
    assert any(v.code == "min_theory_courses_not_met" for v in solution.violations)


def test_greedy_soft_max_lab_sessions_prefers_under_cap() -> None:
    # Faculty 1 prefers at most 1 lab session; with two other faculty available, the
    # soft cap keeps faculty 1 within limit rather than overloading them.
    faculty = (
        FacultyInput(1, "Dr A", "associate_professor", "Associate Professor", 0, 40, 0, 0, None, 1),
        FacultyInput(2, "Dr B", "assistant_professor", "Assistant Professor", 0, 40, 0, 0, None, 5),
        FacultyInput(3, "Dr C", "assistant_professor", "Assistant Professor", 0, 40, 0, 0, None, 5),
    )
    slots = (_lab_slot(1, eligible=(1, 2, 3)), _lab_slot(2, eligible=(1, 2, 3)))
    solution = GreedyWorkloadAllocator().allocate(_problem(faculty, slots))

    assert solution.status == SolverStatus.FEASIBLE
    faculty_1_labs = sum(1 for a in solution.assignments if 1 in a.faculty_ids)
    assert faculty_1_labs <= 1


def test_greedy_soft_max_lab_sessions_flags_overage_when_forced() -> None:
    # Only two faculty, both cap 1, but two labs need 2 faculty each → each must take 2.
    # Soft cap: allocation succeeds and flags the overage.
    faculty = (
        FacultyInput(1, "Dr A", "associate_professor", "Associate Professor", 0, 40, 0, 0, None, 1),
        FacultyInput(2, "Dr B", "associate_professor", "Associate Professor", 0, 40, 0, 0, None, 1),
    )
    slots = (_lab_slot(1, eligible=(1, 2)), _lab_slot(2, eligible=(1, 2)))
    solution = GreedyWorkloadAllocator().allocate(_problem(faculty, slots))

    assert solution.status == SolverStatus.FEASIBLE
    assert any(v.code == "max_lab_sessions_exceeded" for v in solution.violations)

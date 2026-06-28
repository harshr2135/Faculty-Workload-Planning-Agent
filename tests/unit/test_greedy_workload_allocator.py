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

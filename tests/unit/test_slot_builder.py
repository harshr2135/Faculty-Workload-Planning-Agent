"""Unit tests for section group builder."""

from backend.optimization.models.problem_definition import CourseInput
from backend.optimization.preprocessing.slot_builder import build_assignment_slots, build_section_groups


def test_build_section_groups_five_sections() -> None:
    assert build_section_groups(5) == [[1, 2, 3], [4, 5]]


def test_build_section_groups_four_sections() -> None:
    assert build_section_groups(4) == [[1, 2], [3, 4]]


def test_build_section_groups_two_sections() -> None:
    assert build_section_groups(2) == [[1, 2]]


def test_sec_courses_do_not_generate_lab_slots() -> None:
    course = CourseInput(
        id=99,
        batch_code="2024-28",
        semester_number=3,
        section_count=4,
        working_days=("monday", "tuesday", "wednesday", "thursday", "friday"),
        course_code="24AM2SEC",
        name="Skill Enhancement",
        course_type="SEC",
        lectures_per_week=2,
        practical_hours=2,
        requires_lecture_hall=True,
    )
    assert course.has_lab is False
    slots = build_assignment_slots(
        courses=[course],
        eligibility={course.id: (1, 2)},
        matched_ids={course.id: (1, 2)},
        fallback_flags={course.id: False},
    )
    assert all(slot.kind.value != "lab" for slot in slots)
    assert all(slot.course_type == "SEC" for slot in slots)


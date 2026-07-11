"""Tests for PEC lecture-hall threshold rules."""

from backend.core.domain.pec_config import (
    PEC_LECTURE_HALL_STUDENT_THRESHOLD,
    delivery_requires_lecture_hall,
    pec_requires_lecture_hall,
)
from backend.optimization.models.problem_definition import CourseInput, SlotKind
from backend.optimization.preprocessing.schedule_event_builder import build_schedule_events
from backend.optimization.preprocessing.slot_builder import build_assignment_slots
from backend.optimization.models.solution import SlotAssignment
from backend.optimization.models.timetable_problem import RoomKind


def test_pec_uses_lecture_hall_above_threshold() -> None:
    assert pec_requires_lecture_hall(PEC_LECTURE_HALL_STUDENT_THRESHOLD) is False
    assert pec_requires_lecture_hall(PEC_LECTURE_HALL_STUDENT_THRESHOLD + 1) is True
    assert delivery_requires_lecture_hall("PEC 2", 151) is True
    assert delivery_requires_lecture_hall("PEC 2", 150) is False


def test_sec_always_uses_lecture_hall() -> None:
    assert delivery_requires_lecture_hall("SEC", 0) is True
    assert delivery_requires_lecture_hall("SEC", 20) is True


def test_pec_slot_builder_uses_classroom_for_small_enrollment() -> None:
    course = CourseInput(
        id=1,
        batch_code="2023-27",
        semester_number=6,
        section_count=4,
        working_days=("monday", "tuesday", "wednesday", "thursday", "friday"),
        course_code="23AM3605",
        name="Explainable AI",
        course_type="PEC 2",
        lectures_per_week=3,
        practical_hours=0,
        requires_lecture_hall=False,
    )
    slots = build_assignment_slots(
        courses=[course],
        eligibility={course.id: (1, 2)},
        matched_ids={course.id: (1, 2)},
        fallback_flags={course.id: False},
    )
    theory_slots = [slot for slot in slots if slot.kind == SlotKind.THEORY]
    assert len(theory_slots) == 4
    assert all(not slot.requires_lecture_hall for slot in theory_slots)
    assert all("-T-S" in slot.slot_id for slot in theory_slots)


def test_pec_slot_builder_uses_lecture_hall_for_large_enrollment() -> None:
    course = CourseInput(
        id=2,
        batch_code="2023-27",
        semester_number=6,
        section_count=4,
        working_days=("monday", "tuesday", "wednesday", "thursday", "friday"),
        course_code="23AM3606",
        name="Reinforcement Learning",
        course_type="PEC 2",
        lectures_per_week=3,
        practical_hours=0,
        requires_lecture_hall=True,
    )
    slots = build_assignment_slots(
        courses=[course],
        eligibility={course.id: (1, 2)},
        matched_ids={course.id: (1, 2)},
        fallback_flags={course.id: False},
    )
    theory_slots = [slot for slot in slots if slot.kind == SlotKind.THEORY]
    assert len(theory_slots) == 2
    assert all(slot.requires_lecture_hall for slot in theory_slots)
    assert all("-T-LH" in slot.slot_id for slot in theory_slots)


def test_schedule_event_uses_classroom_for_small_pec() -> None:
    assignment = SlotAssignment(
        slot_id="2023-27-23AM3605-T-S1",
        batch_code="2023-27",
        working_days=("monday",),
        course_id=1,
        course_code="23AM3605",
        course_name="Explainable AI",
        course_type="PEC 2",
        kind="theory",
        section_indices=[1],
        weekly_hours=1,
        faculty_ids=[1],
        faculty_names=["Dr A"],
        requires_lecture_hall=False,
    )
    events = build_schedule_events([assignment])
    assert events[0].room_kind == RoomKind.CLASSROOM

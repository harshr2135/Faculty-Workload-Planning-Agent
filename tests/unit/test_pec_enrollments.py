"""Tests for per-course PEC enrollment filtering in allocation."""

from backend.schemas.allocation import BatchSemesterPlan, PecCourseEnrollment
from backend.services.allocation_service import _include_course_for_plan


class _CourseStub:
    def __init__(self, course_code: str, course_type: str) -> None:
        self.course_code = course_code
        self.course_type = course_type


def test_non_pec_course_always_included() -> None:
    plan = BatchSemesterPlan(
        batch_code="2023-27",
        semester_number=5,
        pec_enrollments=[PecCourseEnrollment(course_code="23AM3507", student_count=0)],
    )
    course = _CourseStub("23AM2301", "IPCC")
    assert _include_course_for_plan(course, plan) is True


def test_pec_course_excluded_when_count_zero() -> None:
    plan = BatchSemesterPlan(
        batch_code="2023-27",
        semester_number=6,
        pec_enrollments=[
            PecCourseEnrollment(course_code="23AM3605", student_count=0),
            PecCourseEnrollment(course_code="23AM3606", student_count=35),
            PecCourseEnrollment(course_code="23AM3607", student_count=20),
        ],
    )
    assert _include_course_for_plan(_CourseStub("23AM3605", "PEC 2"), plan) is False
    assert _include_course_for_plan(_CourseStub("23AM3606", "PEC 2"), plan) is True
    assert _include_course_for_plan(_CourseStub("23AM3607", "PEC 3"), plan) is True


def test_pec_included_when_no_enrollment_payload() -> None:
    plan = BatchSemesterPlan(batch_code="2023-27", semester_number=5)
    assert _include_course_for_plan(_CourseStub("23AM3507", "PEC 1"), plan) is True

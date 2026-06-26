"""Faculty eligibility per course from specialization similarity rules."""

from __future__ import annotations

from backend.core.domain.specialization_matcher import specialization_matches_course
from backend.optimization.models.problem_definition import CourseInput, FacultyInput


def build_course_eligibility(
    courses: list[CourseInput],
    faculty: list[FacultyInput],
    faculty_specializations: dict[int, list[str]],
    fallback_faculty_ids: set[int],
) -> tuple[dict[int, tuple[int, ...]], dict[int, tuple[int, ...]], dict[int, bool]]:
    """
    Return (eligible_ids, matched_ids, fallback_required) keyed by course_id.
    """
    eligible: dict[int, tuple[int, ...]] = {}
    matched: dict[int, tuple[int, ...]] = {}
    fallback_flags: dict[int, bool] = {}

    for course in courses:
        matched_ids: list[int] = []
        for member in faculty:
            specs = faculty_specializations.get(member.id, [])
            is_match, _ = specialization_matches_course(specs, course.name)
            if is_match:
                matched_ids.append(member.id)

        if matched_ids:
            eligible_ids = matched_ids
            fallback_flags[course.id] = False
        else:
            eligible_ids = sorted(fallback_faculty_ids)
            fallback_flags[course.id] = True

        eligible[course.id] = tuple(eligible_ids)
        matched[course.id] = tuple(matched_ids)

    return eligible, matched, fallback_flags


def fallback_faculty_ids_from_roster(faculty: list[FacultyInput]) -> set[int]:
    return {
        member.id
        for member in faculty
        if member.designation_key == "assistant_professor"
    }

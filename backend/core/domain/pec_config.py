"""PEC elective delivery rules (enrollment thresholds, room choice)."""

from __future__ import annotations

import re

from backend.core.domain.course_type_config import is_pec_course_type, normalize_course_type

PEC_GROUP_PATTERN = re.compile(r"^PEC\s+\d+$")

# PEC courses with more than this many enrolled students use a lecture hall.
PEC_LECTURE_HALL_STUDENT_THRESHOLD = 150


def normalize_pec_group(value: str) -> str:
    return normalize_course_type(value)


def is_pec_group(value: str) -> bool:
    normalized = normalize_pec_group(value)
    return normalized == "PEC" or bool(PEC_GROUP_PATTERN.match(normalized))


def pec_requires_lecture_hall(student_count: int) -> bool:
    return student_count > PEC_LECTURE_HALL_STUDENT_THRESHOLD


def delivery_requires_lecture_hall(course_type: str, student_count: int = 0) -> bool:
    """Whether theory sessions for this course are scheduled in a lecture hall."""
    normalized = normalize_course_type(course_type)
    if normalized == "SEC":
        return True
    if is_pec_course_type(normalized):
        return pec_requires_lecture_hall(student_count)
    return False


def pec_pool_label(course_type: str) -> str | None:
    """Return the PEC pool label (e.g. PEC 2) when applicable."""
    if not is_pec_course_type(course_type):
        return None
    return normalize_pec_group(course_type)


def pec_parallel_time_key(
    batch_code: str,
    course_type: str,
    session_index: int,
) -> tuple[str, str, int] | None:
    """Group key for PEC electives that must share the same weekly time slot."""
    pool = pec_pool_label(course_type)
    if pool is None:
        return None
    return (batch_code, pool, session_index)

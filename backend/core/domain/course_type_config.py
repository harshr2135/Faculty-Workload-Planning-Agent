"""Course type definitions and delivery venue rules."""

from __future__ import annotations

# PEC / SEC are taught in college lecture halls with 2–3 sections combined.
LECTURE_HALL_COURSE_TYPES: frozenset[str] = frozenset({"PEC", "SEC"})

# IPCC, PCC, BSC, HSMC use department classrooms (one section per room slot).
CLASSROOM_COURSE_TYPES: frozenset[str] = frozenset({"IPCC", "PCC", "BSC", "HSMC"})

KNOWN_COURSE_TYPES: frozenset[str] = LECTURE_HALL_COURSE_TYPES | CLASSROOM_COURSE_TYPES


def normalize_course_type(value: str) -> str:
    return value.strip().upper()


def uses_lecture_hall(course_type: str) -> bool:
    return normalize_course_type(course_type) in LECTURE_HALL_COURSE_TYPES


def validate_course_type(value: str) -> str:
    normalized = normalize_course_type(value)
    if normalized not in KNOWN_COURSE_TYPES:
        raise ValueError(
            f"Unknown course type '{value}'. Expected one of: "
            f"{', '.join(sorted(KNOWN_COURSE_TYPES))}."
        )
    return normalized

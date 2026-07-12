"""Course type definitions and delivery venue rules."""

from __future__ import annotations

import re

# PEC / SEC are taught in college lecture halls with 2–3 sections combined.
LECTURE_HALL_COURSE_TYPES: frozenset[str] = frozenset({"PEC", "SEC"})

# SEC is theory-only in lecture halls; no laboratory practicals.
LAB_EXCLUDED_COURSE_TYPES: frozenset[str] = frozenset({"SEC"})

# Self-directed work — faculty may be assigned but no physical room is reserved.
ROOMLESS_COURSE_NAMES: frozenset[str] = frozenset({"UG RESEARCH PROJECT"})

# IPCC, PCC, BSC, HSMC use department classrooms (one section per room slot).
CLASSROOM_COURSE_TYPES: frozenset[str] = frozenset({"IPCC", "PCC", "BSC", "HSMC"})

KNOWN_COURSE_TYPES: frozenset[str] = LECTURE_HALL_COURSE_TYPES | CLASSROOM_COURSE_TYPES

# Elective pools in the catalog: PEC 1 … PEC 5 (student picks one subject per pool).
PEC_GROUP_PATTERN = re.compile(r"^PEC\s+\d+$")


def normalize_course_type(value: str) -> str:
    return " ".join(value.strip().upper().split())


def normalize_course_name(value: str) -> str:
    return " ".join(value.strip().upper().split())


def is_roomless_course(course_name: str) -> bool:
    """Courses where students work independently and no room is allocated."""
    return normalize_course_name(course_name) in ROOMLESS_COURSE_NAMES


def requires_room_allocation(course_name: str) -> bool:
    return not is_roomless_course(course_name)


def is_pec_course_type(course_type: str) -> bool:
    normalized = normalize_course_type(course_type)
    return normalized == "PEC" or bool(PEC_GROUP_PATTERN.match(normalized))


def pec_pool_number(course_type: str) -> int | None:
    """Extract pool index from types like PEC 1 … PEC 5."""
    normalized = normalize_course_type(course_type)
    if normalized == "PEC":
        return None
    match = re.search(r"PEC\s+(\d+)", normalized)
    return int(match.group(1)) if match else None


def uses_lecture_hall(course_type: str) -> bool:
    normalized = normalize_course_type(course_type)
    return normalized in LECTURE_HALL_COURSE_TYPES or is_pec_course_type(normalized)


def supports_lab_practicals(course_type: str, practical_hours: int) -> bool:
    """Whether the course type may receive B1/B2 laboratory sessions."""
    if practical_hours <= 0:
        return False
    return normalize_course_type(course_type) not in LAB_EXCLUDED_COURSE_TYPES


def validate_course_type(value: str) -> str:
    normalized = normalize_course_type(value)
    if normalized in KNOWN_COURSE_TYPES:
        return normalized
    if is_pec_course_type(normalized):
        return normalized
    raise ValueError(
        f"Unknown course type '{value}'. Expected one of: "
        f"{', '.join(sorted(KNOWN_COURSE_TYPES))}, or PEC 1 … PEC N."
    )

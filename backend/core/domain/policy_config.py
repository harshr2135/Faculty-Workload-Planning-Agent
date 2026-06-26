"""AICTE and department workload policy definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DesignationPolicyDefinition:
    designation_key: str
    designation_label: str
    min_theory_courses: int
    min_lab_courses: int
    min_weekly_hours: float
    max_weekly_hours: float
    min_lab_sessions: int | None
    max_lab_sessions: int | None
    match_keywords: tuple[str, ...]


AIML_DESIGNATION_POLICIES: list[DesignationPolicyDefinition] = [
    DesignationPolicyDefinition(
        designation_key="assistant_professor",
        designation_label="Assistant Professor",
        min_theory_courses=2,
        min_lab_courses=4,
        min_weekly_hours=22.0,
        max_weekly_hours=24.0,
        min_lab_sessions=4,
        max_lab_sessions=5,
        match_keywords=("assistant professor",),
    ),
    DesignationPolicyDefinition(
        designation_key="associate_professor",
        designation_label="Associate Professor",
        min_theory_courses=2,
        min_lab_courses=2,
        min_weekly_hours=20.0,
        max_weekly_hours=22.0,
        min_lab_sessions=2,
        max_lab_sessions=3,
        match_keywords=("associate professor",),
    ),
    DesignationPolicyDefinition(
        designation_key="professor",
        designation_label="Professor",
        min_theory_courses=1,
        min_lab_courses=0,
        min_weekly_hours=6.0,
        max_weekly_hours=10.0,
        min_lab_sessions=None,
        max_lab_sessions=None,
        match_keywords=("professor",),
    ),
    DesignationPolicyDefinition(
        designation_key="chairperson",
        designation_label="Professor and Chairperson",
        min_theory_courses=1,
        min_lab_courses=0,
        min_weekly_hours=6.0,
        max_weekly_hours=10.0,
        min_lab_sessions=None,
        max_lab_sessions=None,
        match_keywords=("chairperson", "chairpe"),
    ),
]

LAB_FACULTY_PER_SESSION = 2

PLANNING_POLICY_DEFINITIONS: list[tuple[str, str, str | None]] = [
    (
        "specialization_matching_strategy",
        "similarity",
        "Match faculty to courses by inferring keywords from the course title and "
        "comparing similar specialization terms (no manual mapping table required).",
    ),
    (
        "specialization_fallback_designation",
        "assistant_professor",
        "If no faculty member has a similar specialization for a course, "
        "eligible assignees are Assistant Professors.",
    ),
    (
        "lab_session_continuity_rule",
        "enabled",
        "Practical hours must be scheduled as one continuous block in a laboratory.",
    ),
    (
        "lab_faculty_per_session",
        str(LAB_FACULTY_PER_SESSION),
        "Each laboratory session must have exactly two faculty members allocated.",
    ),
    (
        "theory_hours_spread_rule",
        "enabled",
        "Weekly lecture hours may be spread across the working days for that student year.",
    ),
    (
        "timetable_fixed_for_semester",
        "enabled",
        "Once the weekly timetable grid is set, the same day/slot/room pattern is "
        "followed for the entire semester.",
    ),
]


def resolve_designation_key(designation: str) -> str | None:
    """Map a faculty designation string to a policy key (most specific match first)."""
    normalized = designation.strip().lower()
    if not normalized:
        return None

    # Chairperson before generic professor.
    if "chair" in normalized:
        return "chairperson"
    if "assistant professor" in normalized:
        return "assistant_professor"
    if "associate professor" in normalized:
        return "associate_professor"
    if "professor" in normalized:
        return "professor"
    return None

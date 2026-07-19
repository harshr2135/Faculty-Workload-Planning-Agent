"""AICTE and department workload policy definitions."""

from __future__ import annotations

from dataclasses import dataclass

# Sentinel used when a designation has no weekly-hour cap (e.g. unmatched designations).
UNLIMITED_MAX_WEEKLY_HOURS = 999.0


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


# AICTE-based per-designation workload rules for the AIML department.
#   - Weekly-hour maximums are HARD: no faculty member is ever assigned beyond the cap,
#     even if that leaves a course uncovered (surfaced as an infeasible allocation).
#   - Lab-session maximums are SOFT: the allocator prefers to stay within them but will
#     exceed them when necessary; overages are reported as violations.
#   - Minimums (theory courses, lab sessions) are SOFT targets reported as violations.
#   - Weekly-hour maximums use the upper bound of the AICTE range.
#   - Lab minima/maxima are measured in scheduled lab SESSIONS (B1/B2 counted separately).
AIML_DESIGNATION_POLICIES: list[DesignationPolicyDefinition] = [
    DesignationPolicyDefinition(
        designation_key="assistant_professor",
        designation_label="Assistant Professor",
        min_theory_courses=2,
        min_lab_courses=0,
        min_weekly_hours=0.0,
        max_weekly_hours=24.0,
        min_lab_sessions=4,
        max_lab_sessions=5,
        match_keywords=("assistant professor",),
    ),
    DesignationPolicyDefinition(
        designation_key="associate_professor",
        designation_label="Associate Professor",
        min_theory_courses=2,
        min_lab_courses=0,
        min_weekly_hours=0.0,
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
        min_weekly_hours=0.0,
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
        min_weekly_hours=0.0,
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
        "lab_max_capacity",
        "35",
        "Maximum students per laboratory session (AIML lab rooms).",
    ),
    (
        "lab_sub_batches",
        "B1,B2",
        "Each section is split into two lab sub-batches (B1 and B2) for practical sessions.",
    ),
    (
        "lab_session_hours",
        "2",
        "Each lab sub-batch receives one 2-hour continuous session per week.",
    ),
    (
        "lab_sub_batches_required",
        "enabled",
        "Both B1 and B2 sub-batches must receive one 2-hour lab session per week for each lab course.",
    ),
    (
        "lab_parallel_sub_batches",
        "enabled",
        "B1 and B2 from the same section may attend different lab subjects at the same time.",
    ),
    (
        "sec_no_lab",
        "enabled",
        "SEC (Skill Enhancement Course) subjects are theory-only; no laboratory sessions.",
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
    (
        "lecture_hall_combined_sections_min",
        "2",
        "PEC and SEC sessions combine at least two sections from the same batch in a lecture hall.",
    ),
    (
        "lecture_hall_combined_sections_max",
        "3",
        "PEC and SEC sessions combine at most three sections from the same batch in a lecture hall.",
    ),
    (
        "pec_lecture_hall_student_threshold",
        "150",
        "PEC electives with more than 150 enrolled students are scheduled in lecture halls; "
        "otherwise department classrooms.",
    ),
    (
        "pec_parallel_pool_timing",
        "disabled",
        "When enabled, all active electives in the same PEC pool (e.g. PEC 2) are scheduled "
        "at the same time. Currently disabled.",
    ),
    (
        "roomless_course_delivery",
        "UG Research Project",
        "Courses listed here are scheduled without reserving a classroom or lab "
        "(students work independently).",
    ),
    (
        "pec_sec_lecture_hall_delivery",
        "enabled",
        "SEC courses always use lecture halls; PEC room choice depends on enrollment.",
    ),
]


_DESIGNATION_LABELS_BY_KEY: dict[str, str] = {
    policy.designation_key: policy.designation_label for policy in AIML_DESIGNATION_POLICIES
}


def designation_label_for(designation_key: str | None) -> str:
    """Human-readable designation label for a policy key (e.g. 'Assistant Professor').

    Falls back to a prettified key for unknown values and "—" when no key is set.
    """
    if not designation_key:
        return "—"
    return _DESIGNATION_LABELS_BY_KEY.get(
        designation_key, designation_key.replace("_", " ").title()
    )


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

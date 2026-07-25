"""AICTE teaching-load conversion (contact hours → counted teaching hours).

Rule: two laboratory / tutorial contact hours count as one teaching hour.
Theory / lecture hours count one-for-one. Timetable contact hours are unchanged;
only designation weekly-hour caps and utilization use teaching load.
"""

from __future__ import annotations

from backend.core.domain.policy_config import LAB_TUTORIAL_HOURS_PER_TEACHING_HOUR

_HALF_WEIGHT_KINDS = frozenset({"lab", "tutorial"})


def lab_tutorial_hours_per_teaching_hour(
    override: int | None = None,
) -> int:
    """Return the conversion denominator (default 2 → half weight for lab/tutorial)."""
    value = LAB_TUTORIAL_HOURS_PER_TEACHING_HOUR if override is None else override
    return max(1, int(value))


def slot_teaching_load_hours(
    kind: str,
    contact_hours: int | float,
    *,
    hours_per_teaching_hour: int | None = None,
) -> float:
    """Convert one assignment's contact hours into teaching-load hours."""
    denom = lab_tutorial_hours_per_teaching_hour(hours_per_teaching_hour)
    hours = float(contact_hours)
    if kind.lower() in _HALF_WEIGHT_KINDS:
        return hours / denom
    return hours


def teaching_load_hours(
    *,
    theory_contact_hours: int | float = 0,
    lab_contact_hours: int | float = 0,
    tutorial_contact_hours: int | float = 0,
    hours_per_teaching_hour: int | None = None,
) -> float:
    """Aggregate teaching load from contact-hour buckets."""
    denom = lab_tutorial_hours_per_teaching_hour(hours_per_teaching_hour)
    return (
        float(theory_contact_hours)
        + (float(lab_contact_hours) + float(tutorial_contact_hours)) / denom
    )


def format_teaching_load_hours(hours: float) -> str:
    """Compact display for reports (prefer integers when exact)."""
    if float(hours).is_integer():
        return str(int(hours))
    return f"{hours:g}"

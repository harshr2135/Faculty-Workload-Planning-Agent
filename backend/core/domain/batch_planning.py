"""Default semester mapping for cohort planning cycles."""

from __future__ import annotations

from backend.core.domain.aiml_config import BATCH_PLANNING_SEMESTER, STUDENT_BATCH_CODES


def default_planning_semester(batch_code: str) -> int:
    """Return the configured planning-semester default for a student batch."""
    return BATCH_PLANNING_SEMESTER.get(batch_code, 5)


def default_batch_plans() -> list[tuple[str, int]]:
    """All configured batches with their default planning semesters."""
    return [(code, default_planning_semester(code)) for code in STUDENT_BATCH_CODES]

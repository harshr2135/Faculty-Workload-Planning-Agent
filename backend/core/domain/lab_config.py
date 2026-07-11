"""Laboratory session rules (capacity, sub-batches, duration)."""

from __future__ import annotations

# Each lab room holds at most this many students per session.
LAB_MAX_CAPACITY = 35

# Every theory section splits lab cohorts into two groups for practicals.
LAB_SUB_BATCHES: tuple[str, ...] = ("B1", "B2")

LAB_PRIMARY_SUB_BATCH = "B1"
LAB_SECONDARY_SUB_BATCH = "B2"

# One continuous 2-period block per sub-batch per week (both B1 and B2 required).
LAB_SESSION_HOURS = 2

# Used to derive sub-batch size when section enrollment is not stored per section.
DEFAULT_STUDENTS_PER_SECTION = 70

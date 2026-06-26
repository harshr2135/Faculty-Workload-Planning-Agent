"""Teaching-period helpers for timetable scheduling."""

from __future__ import annotations

from backend.core.domain.timetable_config import AIML_DAILY_SCHEDULE


def teaching_period_numbers() -> list[int]:
    return [
        period.period_number
        for period in AIML_DAILY_SCHEDULE
        if period.period_number is not None
    ]


def consecutive_teaching_blocks(duration: int) -> list[tuple[int, ...]]:
    """Return valid same-day period tuples; blocks cannot cross break or lunch."""
    if duration <= 0:
        return []

    indexed = [
        (index, period.period_number)
        for index, period in enumerate(AIML_DAILY_SCHEDULE)
        if period.period_number is not None
    ]

    blocks: list[tuple[int, ...]] = []
    for start in range(len(indexed) - duration + 1):
        schedule_indices = [indexed[start + offset][0] for offset in range(duration)]
        if any(
            schedule_indices[offset + 1] - schedule_indices[offset] != 1
            for offset in range(duration - 1)
        ):
            continue
        blocks.append(tuple(indexed[start + offset][1] for offset in range(duration)))
    return blocks


def period_window_label(period_numbers: tuple[int, ...]) -> str:
    if not period_numbers:
        return ""
    by_number = {
        period.period_number: period
        for period in AIML_DAILY_SCHEDULE
        if period.period_number is not None
    }
    first = by_number[period_numbers[0]]
    last = by_number[period_numbers[-1]]
    return f"{first.label} ({first.start_time.strftime('%H:%M')}–{last.end_time.strftime('%H:%M')})"

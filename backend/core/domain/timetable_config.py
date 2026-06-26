"""Daily timetable period definitions for AIML."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import Literal

SlotType = Literal["teaching", "break", "lunch"]


@dataclass(frozen=True)
class DailyPeriodDefinition:
  sort_order: int
  period_number: int | None
  label: str
  start_time: time
  end_time: time
  slot_type: SlotType


# 4th hour confirmed: 11:40–12:35 (official AIML timetable).
AIML_DAILY_SCHEDULE: list[DailyPeriodDefinition] = [
    DailyPeriodDefinition(1, 1, "1st hour", time(8, 30), time(9, 25), "teaching"),
    DailyPeriodDefinition(2, 2, "2nd hour", time(9, 25), time(10, 20), "teaching"),
    DailyPeriodDefinition(3, None, "Break", time(10, 20), time(10, 45), "break"),
    DailyPeriodDefinition(4, 3, "3rd hour", time(10, 45), time(11, 40), "teaching"),
    DailyPeriodDefinition(5, 4, "4th hour", time(11, 40), time(12, 35), "teaching"),
    DailyPeriodDefinition(6, None, "Lunch", time(12, 35), time(13, 50), "lunch"),
    DailyPeriodDefinition(7, 5, "5th hour", time(13, 50), time(14, 40), "teaching"),
    DailyPeriodDefinition(8, 6, "6th hour", time(14, 40), time(15, 30), "teaching"),
    DailyPeriodDefinition(9, 7, "7th hour", time(15, 30), time(16, 20), "teaching"),
]

TEACHING_PERIODS_PER_DAY = sum(
    1 for period in AIML_DAILY_SCHEDULE if period.slot_type == "teaching"
)

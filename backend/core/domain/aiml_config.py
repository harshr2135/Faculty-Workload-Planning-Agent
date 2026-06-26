"""AIML department planning constants."""

from __future__ import annotations

from dataclasses import dataclass

DEPARTMENT_NAME = "AI&ML"

CLASSROOM_NUMBERS = ["424", "431", "432", "433", "439"]
LABORATORY_NUMBERS = ["508", "509", "510"]

WEEKDAYS_MON_FRI = ["monday", "tuesday", "wednesday", "thursday", "friday"]
WEEKDAYS_THU_FRI = ["thursday", "friday"]


@dataclass(frozen=True)
class YearLevelConfig:
    year_level: int
    label: str
    section_count: int
    working_days: list[str]
    semester_numbers: list[int]


AIML_YEAR_LEVELS: list[YearLevelConfig] = [
    YearLevelConfig(2, "2nd Year", 5, WEEKDAYS_MON_FRI, [3, 4]),
    YearLevelConfig(3, "3rd Year", 4, WEEKDAYS_MON_FRI, [5, 6]),
    YearLevelConfig(4, "4th Year", 2, WEEKDAYS_THU_FRI, [7]),
]

SEMESTER_TO_YEAR_LEVEL: dict[int, int] = {
    semester: config.year_level
    for config in AIML_YEAR_LEVELS
    for semester in config.semester_numbers
}

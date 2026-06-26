"""Pydantic schemas for timetable slots."""

from datetime import time

from pydantic import BaseModel, ConfigDict, Field


class TimeSlotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sort_order: int
    period_number: int | None
    label: str
    start_time: time
    end_time: time
    slot_type: str
    duration_minutes: int
    is_teaching_slot: bool


class TimetableOverviewRead(BaseModel):
    teaching_periods_per_day: int
    total_periods_in_day: int
    slots: list[TimeSlotRead] = Field(default_factory=list)

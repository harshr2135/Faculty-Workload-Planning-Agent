"""Pydantic schemas for workload policies."""

from pydantic import BaseModel, ConfigDict


class DesignationPolicyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    designation_key: str
    designation_label: str
    min_theory_courses: int
    min_lab_courses: int
    min_weekly_hours: float
    max_weekly_hours: float
    min_lab_sessions: int | None
    max_lab_sessions: int | None


class PlanningPolicyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    policy_key: str
    policy_value: str
    description: str | None


class PolicyOverviewRead(BaseModel):
    designation_policies: list[DesignationPolicyRead]
    planning_policies: list[PlanningPolicyRead]

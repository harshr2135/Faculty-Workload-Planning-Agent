"""Policy seed and read services."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.domain.aiml_config import DEPARTMENT_NAME
from backend.core.domain.policy_config import (
    AIML_DESIGNATION_POLICIES,
    PLANNING_POLICY_DEFINITIONS,
)
from backend.models import Department, DesignationWorkloadPolicy, PlanningPolicy
from backend.schemas.policy import PolicyOverviewRead


class PolicySeedService:
    async def seed_aiml_policies(self, session: AsyncSession) -> dict[str, int]:
        result = await session.execute(
            select(Department).where(Department.name == DEPARTMENT_NAME)
        )
        department = result.scalar_one_or_none()
        if department is None:
            raise ValueError(
                f"Department '{DEPARTMENT_NAME}' not found. Run seed_aiml_master_data first."
            )

        designation_created = 0
        for policy_def in AIML_DESIGNATION_POLICIES:
            existing = await session.scalar(
                select(DesignationWorkloadPolicy.id).where(
                    DesignationWorkloadPolicy.department_id == department.id,
                    DesignationWorkloadPolicy.designation_key == policy_def.designation_key,
                )
            )
            if existing is None:
                session.add(
                    DesignationWorkloadPolicy(
                        department_id=department.id,
                        designation_key=policy_def.designation_key,
                        designation_label=policy_def.designation_label,
                        min_theory_courses=policy_def.min_theory_courses,
                        min_lab_courses=policy_def.min_lab_courses,
                        min_weekly_hours=policy_def.min_weekly_hours,
                        max_weekly_hours=policy_def.max_weekly_hours,
                        min_lab_sessions=policy_def.min_lab_sessions,
                        max_lab_sessions=policy_def.max_lab_sessions,
                    )
                )
                designation_created += 1
            else:
                row = await session.get(DesignationWorkloadPolicy, existing)
                if row is not None:
                    row.designation_label = policy_def.designation_label
                    row.min_theory_courses = policy_def.min_theory_courses
                    row.min_lab_courses = policy_def.min_lab_courses
                    row.min_weekly_hours = policy_def.min_weekly_hours
                    row.max_weekly_hours = policy_def.max_weekly_hours
                    row.min_lab_sessions = policy_def.min_lab_sessions
                    row.max_lab_sessions = policy_def.max_lab_sessions

        planning_created = 0
        for key, value, description in PLANNING_POLICY_DEFINITIONS:
            existing = await session.scalar(
                select(PlanningPolicy.id).where(
                    PlanningPolicy.department_id == department.id,
                    PlanningPolicy.policy_key == key,
                )
            )
            if existing is None:
                session.add(
                    PlanningPolicy(
                        department_id=department.id,
                        policy_key=key,
                        policy_value=value,
                        description=description,
                    )
                )
                planning_created += 1
            else:
                row = await session.get(PlanningPolicy, existing)
                if row is not None:
                    row.policy_value = value
                    row.description = description

        await session.flush()
        return {
            "designation_policies_created": designation_created,
            "planning_policies_created": planning_created,
        }


class PolicyService:
    async def get_overview(self, session: AsyncSession) -> PolicyOverviewRead:
        dept_result = await session.execute(
            select(Department).where(Department.name == DEPARTMENT_NAME)
        )
        department = dept_result.scalar_one_or_none()
        if department is None:
            return PolicyOverviewRead(designation_policies=[], planning_policies=[])

        designation_result = await session.execute(
            select(DesignationWorkloadPolicy)
            .where(DesignationWorkloadPolicy.department_id == department.id)
            .order_by(DesignationWorkloadPolicy.designation_key)
        )
        planning_result = await session.execute(
            select(PlanningPolicy)
            .where(PlanningPolicy.department_id == department.id)
            .order_by(PlanningPolicy.policy_key)
        )

        from backend.schemas.policy import DesignationPolicyRead, PlanningPolicyRead

        return PolicyOverviewRead(
            designation_policies=[
                DesignationPolicyRead.model_validate(row)
                for row in designation_result.scalars().all()
            ],
            planning_policies=[
                PlanningPolicyRead.model_validate(row)
                for row in planning_result.scalars().all()
            ],
        )

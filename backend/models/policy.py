"""Workload policy ORM models."""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin


class DesignationWorkloadPolicy(Base, TimestampMixin):
    """AICTE-style workload rules per faculty designation."""

    __tablename__ = "designation_workload_policies"
    __table_args__ = (
        UniqueConstraint(
            "department_id",
            "designation_key",
            name="uq_designation_policies_dept_key",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    designation_key: Mapped[str] = mapped_column(String(50), nullable=False)
    designation_label: Mapped[str] = mapped_column(String(100), nullable=False)
    min_theory_courses: Mapped[int] = mapped_column(Integer, nullable=False)
    min_lab_courses: Mapped[int] = mapped_column(Integer, nullable=False)
    min_weekly_hours: Mapped[float] = mapped_column(Float, nullable=False)
    max_weekly_hours: Mapped[float] = mapped_column(Float, nullable=False)
    min_lab_sessions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_lab_sessions: Mapped[int | None] = mapped_column(Integer, nullable=True)

    department: Mapped["Department"] = relationship(back_populates="designation_policies")


class PlanningPolicy(Base, TimestampMixin):
    """Department-wide planning rules (text or coded values)."""

    __tablename__ = "planning_policies"
    __table_args__ = (
        UniqueConstraint(
            "department_id",
            "policy_key",
            name="uq_planning_policies_dept_key",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    policy_key: Mapped[str] = mapped_column(String(100), nullable=False)
    policy_value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    department: Mapped["Department"] = relationship(back_populates="planning_policies")

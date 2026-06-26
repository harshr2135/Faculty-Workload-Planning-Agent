"""Faculty member and specialization ORM models."""

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin


class FacultyMember(Base, TimestampMixin):
    __tablename__ = "faculty_members"
    __table_args__ = (UniqueConstraint("email", name="uq_faculty_members_email"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    serial_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    designation: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cabin_number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    department: Mapped["Department"] = relationship(back_populates="faculty_members")
    specializations: Mapped[list["FacultySpecialization"]] = relationship(
        back_populates="faculty_member",
        cascade="all, delete-orphan",
        order_by="FacultySpecialization.name",
    )


class FacultySpecialization(Base, TimestampMixin):
    __tablename__ = "faculty_specializations"
    __table_args__ = (
        UniqueConstraint(
            "faculty_member_id",
            "name",
            name="uq_faculty_specializations_member_name",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    faculty_member_id: Mapped[int] = mapped_column(
        ForeignKey("faculty_members.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    faculty_member: Mapped[FacultyMember] = relationship(back_populates="specializations")

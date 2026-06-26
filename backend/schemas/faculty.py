"""Pydantic schemas for faculty API."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class FacultySpecializationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class FacultyMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    serial_number: int | None
    full_name: str
    designation: str
    department: str
    email: EmailStr
    phone: str | None
    cabin_number: str | None
    specializations: list[FacultySpecializationRead] = Field(default_factory=list)


class FacultyImportResult(BaseModel):
    created: int
    updated: int
    total_rows: int
    departments: list[str]
    errors: list[str] = Field(default_factory=list)

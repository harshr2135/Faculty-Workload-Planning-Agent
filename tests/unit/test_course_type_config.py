"""Unit tests for course type rules."""

import pytest

from backend.core.domain.course_type_config import (
    is_pec_course_type,
    is_roomless_course,
    requires_room_allocation,
    uses_lecture_hall,
    validate_course_type,
)


def test_validate_pec_elective_groups() -> None:
    assert validate_course_type("PEC 1") == "PEC 1"
    assert validate_course_type("pec 2") == "PEC 2"
    assert validate_course_type("PEC 5") == "PEC 5"


def test_pec_groups_use_lecture_halls() -> None:
    assert is_pec_course_type("PEC 1") is True
    assert uses_lecture_hall("PEC 3") is True
    assert uses_lecture_hall("SEC") is True
    assert uses_lecture_hall("PCC") is False


def test_unknown_course_type_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown course type"):
        validate_course_type("PEC X")


def test_ug_research_project_is_roomless() -> None:
    assert is_roomless_course("UG Research Project") is True
    assert is_roomless_course("ug  research   project") is True
    assert requires_room_allocation("Deep Learning") is True
    assert requires_room_allocation("UG Research Project") is False

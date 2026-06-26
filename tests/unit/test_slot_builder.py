"""Unit tests for section group builder."""

from backend.optimization.preprocessing.slot_builder import build_section_groups


def test_build_section_groups_five_sections() -> None:
    assert build_section_groups(5) == [[1, 2, 3], [4, 5]]


def test_build_section_groups_four_sections() -> None:
    assert build_section_groups(4) == [[1, 2], [3, 4]]


def test_build_section_groups_two_sections() -> None:
    assert build_section_groups(2) == [[1, 2]]

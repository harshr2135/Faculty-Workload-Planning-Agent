"""Unit tests for consecutive teaching period blocks."""

from backend.optimization.preprocessing.period_utils import consecutive_teaching_blocks


def test_consecutive_blocks_duration_one() -> None:
    assert consecutive_teaching_blocks(1) == [(1,), (2,), (3,), (4,), (5,), (6,), (7,)]


def test_consecutive_blocks_duration_two_skips_lunch_gap() -> None:
    blocks = consecutive_teaching_blocks(2)
    assert (4, 5) not in blocks
    assert (3, 4) in blocks
    assert (5, 6) in blocks

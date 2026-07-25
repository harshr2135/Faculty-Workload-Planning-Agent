"""Unit tests for allocation edit helpers."""

from backend.services.allocation_edit_service import (
    recompute_faculty_summaries,
    sync_timetable_entry_faculty,
)


def test_recompute_faculty_summaries_after_edit() -> None:
    assignments = [
        {
            "slot_id": "slot-1",
            "course_id": 1,
            "kind": "theory",
            "weekly_hours": 3,
            "faculty_ids": [10],
        },
        {
            "slot_id": "slot-2",
            "course_id": 2,
            "kind": "lab",
            "weekly_hours": 2,
            "faculty_ids": [10, 20],
        },
    ]

    class Member:
        def __init__(self, member_id: int, full_name: str, designation: str) -> None:
            self.id = member_id
            self.full_name = full_name
            self.designation = designation

    faculty_by_id = {
        10: Member(10, "Dr A", "Assistant Professor"),
        20: Member(20, "Dr B", "Professor"),
    }

    summaries = recompute_faculty_summaries(assignments, faculty_by_id)
    by_id = {row["faculty_id"]: row for row in summaries}

    assert by_id[10]["theory_weekly_hours"] == 3
    assert by_id[10]["lab_weekly_hours"] == 2
    # Teaching load: 3 theory + 2 lab / 2 = 4
    assert by_id[10]["total_weekly_hours"] == 4
    assert by_id[20]["lab_weekly_hours"] == 2
    assert by_id[20]["total_weekly_hours"] == 1


def test_sync_timetable_entry_faculty() -> None:
    assignments = [
        {
            "slot_id": "slot-1",
            "faculty_ids": [99],
            "faculty_names": ["Dr New"],
        }
    ]
    entries = [
        {
            "event_id": "evt-1",
            "slot_id": "slot-1",
            "faculty_ids": [1],
            "faculty_names": ["Dr Old"],
        }
    ]

    synced = sync_timetable_entry_faculty(entries, assignments)
    assert synced[0]["faculty_ids"] == [99]
    assert synced[0]["faculty_names"] == ["Dr New"]

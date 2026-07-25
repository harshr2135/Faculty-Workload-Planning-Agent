"""Apply manual edits to stored allocation runs."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.domain.policy_config import resolve_designation_key
from backend.models import FacultyMember
from backend.schemas.allocation import SlotAssignmentRead


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _assignment_key(assignment: dict) -> str:
    return str(assignment["slot_id"])


def apply_assignment_updates(
    assignments: list[dict],
    updates: list[SlotAssignmentRead],
) -> list[dict]:
    """Replace faculty on matching slot assignments."""
    by_slot = {_assignment_key(item): item for item in assignments}
    for update in updates:
        key = update.slot_id
        if key not in by_slot:
            msg = f"Unknown assignment slot '{update.slot_id}'."
            raise ValueError(msg)
        row = by_slot[key]
        row["faculty_ids"] = list(update.faculty_ids)
        row["faculty_names"] = list(update.faculty_names)
    return list(by_slot.values())


def sync_timetable_entry_faculty(
    timetable_entries: list[dict],
    assignments: list[dict],
) -> list[dict]:
    """Keep timetable faculty in sync with edited workload assignments."""
    faculty_by_slot = {
        row["slot_id"]: (list(row["faculty_ids"]), list(row["faculty_names"]))
        for row in assignments
    }
    synced: list[dict] = []
    for entry in timetable_entries:
        updated = dict(entry)
        slot_id = updated.get("slot_id")
        if slot_id in faculty_by_slot:
            faculty_ids, faculty_names = faculty_by_slot[slot_id]
            updated["faculty_ids"] = faculty_ids
            updated["faculty_names"] = faculty_names
        synced.append(updated)
    return synced


def recompute_faculty_summaries(
    assignments: list[dict],
    faculty_by_id: dict[int, FacultyMember],
) -> list[dict]:
    """Rebuild faculty workload summaries from assignment rows."""
    from backend.core.domain.teaching_load import teaching_load_hours

    aggregates: dict[int, dict] = {}

    def ensure_faculty(faculty_id: int) -> dict:
        if faculty_id not in aggregates:
            member = faculty_by_id.get(faculty_id)
            aggregates[faculty_id] = {
                "faculty_id": faculty_id,
                "full_name": member.full_name if member else f"Faculty #{faculty_id}",
                "designation_key": (
                    resolve_designation_key(member.designation) if member else None
                ),
                "theory_weekly_hours": 0,
                "lab_weekly_hours": 0,
                "total_weekly_hours": 0.0,
                "theory_course_count": 0,
                "lab_course_count": 0,
                "lab_session_count": 0,
                "_theory_courses": set(),
                "_lab_courses": set(),
            }
        return aggregates[faculty_id]

    for assignment in assignments:
        course_id = assignment.get("course_id")
        weekly_hours = int(assignment.get("weekly_hours") or 0)
        is_lab = assignment.get("kind") == "lab"
        for faculty_id in assignment.get("faculty_ids") or []:
            summary = ensure_faculty(int(faculty_id))
            if is_lab:
                summary["lab_weekly_hours"] += weekly_hours
                summary["lab_session_count"] += 1
                if course_id is not None:
                    summary["_lab_courses"].add(course_id)
            else:
                summary["theory_weekly_hours"] += weekly_hours
                if course_id is not None:
                    summary["_theory_courses"].add(course_id)

    summaries: list[dict] = []
    for summary in aggregates.values():
        theory_courses = summary.pop("_theory_courses")
        lab_courses = summary.pop("_lab_courses")
        summary["theory_course_count"] = len(theory_courses)
        summary["lab_course_count"] = len(lab_courses)
        summary["total_weekly_hours"] = teaching_load_hours(
            theory_contact_hours=summary["theory_weekly_hours"],
            lab_contact_hours=summary["lab_weekly_hours"],
        )
        summaries.append(summary)

    return sorted(summaries, key=lambda row: row["full_name"].lower())


async def load_faculty_lookup(session: AsyncSession) -> dict[int, FacultyMember]:
    result = await session.execute(select(FacultyMember))
    members = result.scalars().all()
    return {member.id: member for member in members}


def apply_faculty_names(
    assignments: list[dict],
    faculty_by_id: dict[int, FacultyMember],
) -> list[dict]:
    updated: list[dict] = []
    for assignment in assignments:
        row = dict(assignment)
        names: list[str] = []
        for faculty_id in row.get("faculty_ids") or []:
            member = faculty_by_id.get(int(faculty_id))
            names.append(member.full_name if member else f"Faculty #{faculty_id}")
        row["faculty_names"] = names
        updated.append(row)
    return updated


def touch_plan_metadata(payload: dict, *, plan_name: str | None, is_saved: bool | None) -> dict:
    updated = dict(payload)
    if plan_name is not None:
        updated["plan_name"] = plan_name.strip()
    if is_saved is not None:
        updated["is_saved"] = is_saved
    updated["updated_at"] = _utc_now_iso()
    return updated

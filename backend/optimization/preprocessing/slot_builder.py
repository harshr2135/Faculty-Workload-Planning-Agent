"""Build theory and lab assignment slots from courses and section rules."""

from __future__ import annotations

from backend.core.domain.lab_config import LAB_SESSION_HOURS, LAB_SUB_BATCHES
from backend.optimization.models.problem_definition import AssignmentSlot, CourseInput, SlotKind


def build_section_groups(
    section_count: int,
    min_size: int = 2,
    max_size: int = 3,
) -> list[list[int]]:
    """Pack section numbers into LH groups of 2–3 students."""
    if section_count <= 0:
        return []
    if section_count < min_size:
        return [list(range(1, section_count + 1))]

    groups: list[list[int]] = []
    start = 1
    remaining = section_count
    while remaining > 0:
        if remaining <= max_size:
            groups.append(list(range(start, start + remaining)))
            break
        if remaining == max_size + 1:
            size = 2
        else:
            size = max_size
        groups.append(list(range(start, start + size)))
        start += size
        remaining -= size
    return groups


def build_assignment_slots(
    courses: list[CourseInput],
    eligibility: dict[int, tuple[int, ...]],
    matched_ids: dict[int, tuple[int, ...]],
    fallback_flags: dict[int, bool],
    lecture_hall_min_sections: int = 2,
    lecture_hall_max_sections: int = 3,
) -> list[AssignmentSlot]:
    slots: list[AssignmentSlot] = []

    for course in courses:
        eligible = eligibility.get(course.id, ())
        matched = matched_ids.get(course.id, ())
        fallback = fallback_flags.get(course.id, False)
        section_count = course.section_count

        if course.requires_lecture_hall:
            groups = build_section_groups(
                section_count,
                min_size=lecture_hall_min_sections,
                max_size=lecture_hall_max_sections,
            )
            for index, group in enumerate(groups, start=1):
                slots.append(
                    AssignmentSlot(
                        slot_id=f"{course.batch_code}-{course.course_code}-T-LH{index}",
                        course_id=course.id,
                        batch_code=course.batch_code,
                        working_days=course.working_days,
                        course_code=course.course_code,
                        course_name=course.name,
                        course_type=course.course_type,
                        kind=SlotKind.THEORY,
                        section_indices=tuple(group),
                        weekly_hours=course.lectures_per_week,
                        eligible_faculty_ids=eligible,
                        specialization_matched_ids=matched,
                        fallback_required=fallback,
                        requires_lecture_hall=True,
                    )
                )
        else:
            for section in range(1, section_count + 1):
                slots.append(
                    AssignmentSlot(
                        slot_id=f"{course.batch_code}-{course.course_code}-T-S{section}",
                        course_id=course.id,
                        batch_code=course.batch_code,
                        working_days=course.working_days,
                        course_code=course.course_code,
                        course_name=course.name,
                        course_type=course.course_type,
                        kind=SlotKind.THEORY,
                        section_indices=(section,),
                        weekly_hours=course.lectures_per_week,
                        eligible_faculty_ids=eligible,
                        specialization_matched_ids=matched,
                        fallback_required=fallback,
                        requires_lecture_hall=False,
                    )
                )

        if course.has_lab:
            lab_hours = max(LAB_SESSION_HOURS, course.practical_hours)
            for section in range(1, section_count + 1):
                for sub_batch in LAB_SUB_BATCHES:
                    slots.append(
                        AssignmentSlot(
                            slot_id=f"{course.batch_code}-{course.course_code}-L-S{section}-{sub_batch}",
                            course_id=course.id,
                            batch_code=course.batch_code,
                            working_days=course.working_days,
                            course_code=course.course_code,
                            course_name=course.name,
                            course_type=course.course_type,
                            kind=SlotKind.LAB,
                            section_indices=(section,),
                            weekly_hours=lab_hours,
                            lab_sub_batch=sub_batch,
                            eligible_faculty_ids=eligible,
                            specialization_matched_ids=matched,
                            fallback_required=fallback,
                        )
                    )

    return slots

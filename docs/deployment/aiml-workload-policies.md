# AIML Workload Policies (AICTE)

Configurable workload rules for the optimization engine.

## Designation policies (seeded)

| Designation | Min theory | Min lab courses | Max weekly hours | Lab sessions |
|-------------|------------|-----------------|------------------|--------------|
| Assistant Professor | 2 | 4 | 16 | — (uncapped) |
| Associate Professor | 2 | 2 | 12 | — (uncapped) |
| Professor | 1 | 0 | 8 | — |
| Professor & Chairperson | 1 | 0 | 4 | — |

## Planning rules

| Policy key | Value | Meaning |
|------------|-------|---------|
| `lab_tutorial_hours_per_teaching_hour` | `2` | Two lab/tutorial contact hours count as **one** teaching hour toward weekly caps (theory is 1:1) |
| `specialization_matching_strategy` | `similarity` | Infer course keywords and match similar faculty specializations (no manual mapping table) |
| `specialization_fallback_designation` | `assistant_professor` | If no faculty has a similar specialization, assign an Assistant Professor |
| `lab_session_continuity_rule` | enabled | Labs run as one continuous block (`practical_hours`) |
| `lab_faculty_per_session` | `2` | **Two faculty members** must be allocated per laboratory session |
| `theory_hours_spread_rule` | enabled | Lecture hours spread across working days per year level |
| `timetable_fixed_for_semester` | enabled | Weekly timetable grid is fixed for the entire semester once set |

## Specialization similarity (no manual mapping)

The planner infers required expertise from each **course title** and matches faculty **domain specializations** using synonym groups (e.g. Machine Learning ↔ Data Science, Deep Learning ↔ Generative AI).

- Module: `backend/core/domain/specialization_matcher.py`
- Preview: `GET /api/v1/courses/specialization-matches?semester=5`

## Designation matching

Faculty `designation` strings are mapped automatically:

- Contains `chair` → chairperson policy  
- `Assistant Professor` → assistant policy  
- `Associate Professor` → associate policy  
- `Professor` (otherwise) → professor policy  

Helper: `backend/core/domain/policy_config.resolve_designation_key()`

## Seed & API

```powershell
python scripts/db/seed_aiml_master_data.py
```

Or:

- `POST /api/v1/policies/seed-aiml`
- `GET /api/v1/policies`

## Optimizer usage (future)

Constraints will read `designation_workload_policies` for min/max hours and lab limits, and `planning_policies` for specialization fallback when building the candidate faculty set per course.

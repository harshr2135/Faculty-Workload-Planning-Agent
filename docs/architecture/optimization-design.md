# Optimization Engine Design

## Location

`backend/optimization/` — fully isolated from AI and API layers.

## Workflow

1. **Preprocessing** — normalize data, detect pre-solve conflicts
2. **Problem Builder** — create CP-SAT variables and constraints
3. **Solver** — Google OR-Tools CP-SAT
4. **Postprocessing** — validate solution, build conflict report, emit explainability payload

## Constraint Modules

- Teaching hours (AICTE limits)
- Laboratory limits
- **Dual faculty per lab session** (`lab_faculty_per_session = 2`)
- **Specialization similarity matching** (course title ↔ faculty specialization groups; Assistant Professor fallback)
- **Semester-fixed weekly timetable** (day/slot/room pattern unchanged for the full semester)
- Timetable conflicts
- Leave / availability
- Research commitments
- Administrative duties
- PhD supervision

## Specialization matching (preprocessing)

No manual `course_specializations` table. During preprocessing:

1. `infer_course_keywords(course.name)` extracts terms and synonym-group keywords.
2. `specialization_matches_course()` compares faculty specialization strings to those keywords.
3. If no match, candidate pool = Assistant Professors (`specialization_fallback_designation` policy).

Module: `backend/core/domain/specialization_matcher.py`  
Preview API: `GET /api/v1/courses/specialization-matches`

## Timetable model

Once the weekly grid is solved, the same assignment repeats every week of the semester (`timetable_fixed_for_semester` policy). The optimizer assigns `(section, day, slot, room)` tuples once per semester, not per week.

**Slice 2 implementation:** `TimetableCpsatSolver` runs after workload assignment. Each theory hour and each continuous lab block becomes a `ScheduleEvent` placed on `(day, period_block, room)` with conflict checks for faculty, rooms, and sections.

Modules:
- `optimization/preprocessing/schedule_event_builder.py`
- `optimization/preprocessing/period_utils.py` (continuous blocks respect break/lunch)
- `optimization/engine/timetable_cpsat_solver.py`

## Laboratory assignments

Each lab session variable must have exactly **two** faculty assignees. Continuous block duration comes from `courses.practical_hours`.

## Lecture hall scheduling (PEC / SEC)

- Six college lecture halls (`LH-1` … `LH-6`), each fitting **2–3 combined sections** from the same student batch.
- Course types `PEC` and `SEC` use `requires_lecture_hall = true`; IPCC/PCC/BSC/HSMC use department classrooms.
- Optimizer must assign section groups to a single LH slot (not split across rooms).

## Output Contract

`OptimizationSolution` includes assignments, violations, fairness metrics, and structured facts for the AI explanation layer.

# AIML Master Data & Course Import

## What gets stored

### Classrooms (theory)
Rooms allocated to AIML: **424, 431, 432, 433, 439**

### Laboratories
Rooms allocated to AIML: **508, 509, 510**

### Academic year rules

| Student year | Semesters | Sections | Working days |
|--------------|-----------|----------|--------------|
| 2nd Year | 3, 4 | 5 | Monday–Friday |
| 3rd Year | 5, 6 | 4 | Monday–Friday |
| 4th Year | 7 | 2 | Thursday, Friday only |

### Course fields (from `Courses.xlsx`)

| Excel column | DB field | Meaning |
|--------------|----------|---------|
| Semester | `semester_number` | 3–7 for AIML |
| Subject | `name` | Course title |
| Course Code | `course_code` | Unique code |
| Credits | `credits` | Credit value |
| Number of lectures per week | `lectures_per_week` | Classroom hours/week (spread across working days) |
| Practical | `practical_hours` | **Continuous** lab block duration (0 = no lab) |

## CLI — seed + import (recommended)

```powershell
# Seeds classrooms, labs, semesters, year rules, then imports courses
python scripts/db/import_courses.py "C:\Users\Jyothi\Downloads\Courses.xlsx"
```

Seed only (no courses):

```powershell
python scripts/db/seed_aiml_master_data.py
```

## API

After `uvicorn backend.main:app --reload`:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/department/seed-aiml` | Seed rooms + semester structure |
| POST | `/api/v1/courses/import` | Upload `Courses.xlsx` |
| GET | `/api/v1/courses` | List courses (`?semester=5` optional) |
| GET | `/api/v1/classrooms` | List classrooms |
| GET | `/api/v1/laboratories` | List laboratories |
| GET | `/api/v1/semesters` | List semesters with year rules |
| GET | `/api/v1/academic-year-levels` | Year-level section & working-day config |

## Planning notes (for future optimizer)

- `lectures_per_week` can be split across the year’s `working_days` (e.g. 3 hrs over 5 days for 2nd year).
- `practical_hours` must be scheduled as one **continuous** block in a laboratory.
- Section counts multiply workload: each course runs once per section per semester.

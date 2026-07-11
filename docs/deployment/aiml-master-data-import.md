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
| *(first column)* | `batch_code` | Student cohort, e.g. `2023-27` |
| Semester | `semester_number` | 3–7 for AIML |
| Course Type | `course_type` | IPCC, PCC, PEC, PEC 1 … PEC 5, SEC, BSC, HSMC |
| Subject | `name` | Course title |
| Course Code | `course_code` | Unique per batch |
| Credits | `credits` | Credit value |
| Number of lectures per week | `lectures_per_week` | Classroom hours/week |
| Practical | `practical_hours` | Continuous lab block (0 = no lab) |

### Student batches (updated catalog)

Three cohorts in the file: **2022-26**, **2023-27**, **2024-28** — 81 course rows total across sem 3–7.

### Lecture halls (college-wide)

Six halls: **LH-1 … LH-6**. Each accommodates **2–3 sections combined** from the same batch.

| Course type | Venue | Scheduling |
|-------------|-------|--------------|
| **PEC**, **SEC** | Lecture hall | 2–3 sections of the same batch combined for one session |
| IPCC, PCC, BSC, HSMC | Department classroom | One section per room slot (default) |

IPCC courses may still have practical hours (lab in department laboratories).

## CLI — seed + import (recommended)

```powershell
# Seeds classrooms, labs, lecture halls, batches, semesters, then imports courses
python scripts/db/import_courses.py "data/master/Courses.xlsx" --replace
```

Use `--replace` when uploading a new catalog to remove old course rows first.

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
| GET | `/api/v1/courses` | List courses (`?semester=5&batch=2023-27`) |
| GET | `/api/v1/student-batches` | List student cohorts |
| GET | `/api/v1/lecture-halls` | List college lecture halls |
| GET | `/api/v1/classrooms` | List classrooms |
| GET | `/api/v1/laboratories` | List laboratories |
| GET | `/api/v1/semesters` | List semesters with year rules |
| GET | `/api/v1/academic-year-levels` | Year-level section & working-day config |

## Planning notes (for future optimizer)

- **PEC / SEC** → college lecture hall; optimizer groups **2–3 sections** of the same batch per session.
- **IPCC / PCC / BSC / HSMC** → department classrooms (424, 431, …).

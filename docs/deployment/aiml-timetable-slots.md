# AIML Daily Timetable Periods

Standard teaching day for AIML workload planning. Each **working day** repeats this template (working days vary by student year — see `academic_year_levels.working_days`).

## Schedule

| Order | Period | Time | Type |
|-------|--------|------|------|
| 1 | 1st hour | 08:30 – 09:25 | teaching |
| 2 | 2nd hour | 09:25 – 10:20 | teaching |
| 3 | Break | 10:20 – 10:45 | break |
| 4 | 3rd hour | 10:45 – 11:40 | teaching |
| 5 | 4th hour | 11:40 – 12:35 | teaching |
| 6 | Lunch | 12:35 – 13:50 | lunch |
| 7 | 5th hour | 13:50 – 14:40 | teaching |
| 8 | 6th hour | 14:40 – 15:30 | teaching |
| 9 | 7th hour | 15:30 – 16:20 | teaching |

**7 teaching periods** per day (~55 minutes each).

> Note: 4th hour is **11:40–12:35** (follows 3rd hour). If your official timetable differs, update `backend/core/domain/timetable_config.py`.

## Planning rules (for optimizer)

- **Theory (`lectures_per_week`)**: spread across the year’s working days using teaching slots only.
- **Lab (`practical_hours`)**: one **continuous** block of that many hours in a laboratory (508/509/510).
- **2nd / 3rd year**: Mon–Fri → up to 7 slots × 5 days = 35 teaching slots/week (per room).
- **4th year**: Thu–Fri only → up to 7 slots × 2 days = 14 teaching slots/week.

## Seed & API

```powershell
python scripts/db/seed_aiml_master_data.py   # includes timetable slots
```

Or API only:

- `POST /api/v1/timetable/seed-aiml`
- `GET /api/v1/timetable/slots`
- `GET /api/v1/timetable/slots?teaching_only=true`
- `GET /api/v1/timetable/overview`

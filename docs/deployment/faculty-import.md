# Faculty Excel Import

Import AIML faculty data from `.xlsx` into PostgreSQL.

## Expected Excel columns

| Column | Required |
|--------|----------|
| Sl. No | Optional |
| Name | Yes |
| Designation | Yes |
| Department | Yes |
| Email ID | Yes (unique) |
| Phone Number | Optional |
| Domain Specialization | Optional (comma-separated) |
| Cabin Number | Optional |

## Option 1 — CLI script (recommended for first import)

1. Start PostgreSQL:
   ```powershell
   docker compose up -d postgres
   ```

2. Run import:
   ```powershell
   python scripts/db/import_faculty.py "C:\path\to\AIML_Faculties_Details.xlsx"
   ```

Re-running the same file **updates** existing faculty by email and refreshes specializations.

## Option 2 — API upload

1. Start the API:
   ```powershell
   uvicorn backend.main:app --reload
   ```

2. Upload via Swagger UI: `http://localhost:8000/docs`
   - Endpoint: `POST /api/v1/faculty/import`
   - Attach your `.xlsx` file

3. List imported faculty:
   - `GET /api/v1/faculty`

## Database tables

- `departments` — e.g. `AI&ML`
- `faculty_members` — profile fields from Excel
- `faculty_specializations` — one row per specialization (split from Domain Specialization)

## Note on PostgreSQL port

Docker PostgreSQL runs on **port 15432** (not 5432) to avoid conflict with a local PostgreSQL installation on Windows. Configure `FWP_DATABASE_URL` in `.env` accordingly.

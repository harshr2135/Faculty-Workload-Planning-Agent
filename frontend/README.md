# Frontend

React + TypeScript + TailwindCSS admin interface.

## Structure

| Path | Purpose |
|------|---------|
| `src/api/` | Typed REST client |
| `src/components/` | UI components by domain |
| `src/pages/` | Route-level views |
| `src/hooks/` | Custom React hooks |
| `src/store/` | Global state |
| `src/types/` | TypeScript interfaces |

## Development

```bash
# Terminal 1 — backend (from project root)
docker compose up -d postgres
uvicorn backend.main:app --reload

# Terminal 2 — frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

Ensure `frontend/.env` contains `VITE_API_BASE_URL=/api/v1` (uses Vite proxy to the backend).

Pages: Dashboard, Faculty, Courses, Classrooms, Laboratories, Timetable, Policies.

API requests are proxied: `/api` → `http://127.0.0.1:8000` (see `vite.config.ts`).

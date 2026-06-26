# Faculty Workload Planning Agent

AI-powered decision support system for university department administrators to allocate faculty workload fairly, efficiently, and transparently.

## Architecture

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, Redis, Google OR-Tools (CP-SAT)
- **Frontend:** React, TypeScript, TailwindCSS
- **AI Layer:** LangChain — explanations only (no optimization)
- **Deployment:** Docker, Docker Compose

## Project Structure

```
├── backend/          # FastAPI application (Clean Architecture)
├── frontend/         # React admin UI
├── database/         # Migrations, seeds, schemas
├── configs/          # Environment-tier YAML configuration
├── docs/             # Architecture, ADRs, runbooks
├── infra/            # Docker, CI/CD, monitoring
├── scripts/          # Setup and operational scripts
└── tests/            # Unit, integration, e2e tests
```

## Quick Start (coming soon)

1. Copy `.env.example` to `.env` and configure values
2. Start services: `docker compose up -d`
3. Run migrations: `scripts/db/migrate.sh`
4. Start backend: `scripts/dev/run-backend.sh`
5. Start frontend: `scripts/dev/run-frontend.sh`

## Documentation

See [`docs/architecture/overview.md`](docs/architecture/overview.md) for system design.

## License

NVIDIA Capstone Project — see LICENSE file.

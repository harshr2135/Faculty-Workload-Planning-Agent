# Database

Schema migrations, seed data, and ERD definitions.

## Structure

| Path | Purpose |
|------|---------|
| `migrations/versions/` | Alembic revision files |
| `seeds/dev/` | Development sample data |
| `seeds/reference/` | AICTE policy templates, course categories |
| `schemas/` | ERD source (dbml) |
| `scripts/` | Backup and restore utilities |

## Usage

Migrations are run via `scripts/db/migrate.sh` after Alembic is configured.

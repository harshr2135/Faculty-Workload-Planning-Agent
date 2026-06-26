# Infrastructure

Docker images, compose overrides, CI/CD pipelines, and observability stack.

## Structure

| Path | Purpose |
|------|---------|
| `docker/` | Dockerfiles for api, frontend, worker |
| `compose/` | Environment-specific compose overrides |
| `kubernetes/` | Future K8s manifests |
| `monitoring/` | Prometheus alerts, Grafana dashboards |
| `ci-cd/github/workflows/` | GitHub Actions pipelines |

## Local Development

Root `docker-compose.yml` starts PostgreSQL and Redis. Full stack compose files will be added during implementation.

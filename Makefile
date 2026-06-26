.PHONY: help setup up down migrate test lint

help:
	@echo "Faculty Workload Planning Agent"
	@echo ""
	@echo "  make setup    - Initialize dev environment"
	@echo "  make up       - Start postgres + redis"
	@echo "  make down     - Stop services"
	@echo "  make migrate  - Run database migrations"
	@echo "  make test     - Run unit tests"
	@echo "  make lint     - Run ruff linter"

setup:
	bash scripts/setup/init-dev.sh

up:
	docker compose up -d postgres redis

down:
	docker compose down

migrate:
	bash scripts/db/migrate.sh

test:
	pytest tests/unit -v

lint:
	ruff check backend tests

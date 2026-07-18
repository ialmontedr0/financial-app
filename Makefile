.PHONY: install dev run test test-unit test-api test-cov lint lint-fix format format-check typecheck migrate migrate-create migrate-down db-create redis-start observability clean ci help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	uv sync --all-extras

dev: ## Run development server
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run: ## Run production server
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

test: ## Run all tests
	uv run pytest -v

test-unit: ## Run unit tests only
	uv run pytest -m unit -v

test-api: ## Run API tests only
	uv run pytest -m api -v

test-cov: ## Run tests with coverage
	uv run pytest --cov=app --cov-report=html --cov-report=term-missing

lint: ## Run linter
	uv run ruff check backend/ tests/

lint-fix: ## Auto-fix linting issues
	uv run ruff check --fix backend/ tests/

format: ## Format code
	uv run ruff format backend/ tests/
	uv run ruff check --fix backend/ tests/

format-check: ## Check formatting without changing
	uv run ruff format --check backend/ tests/

typecheck: ## Run type checker
	uv run mypy -p app

check: lint typecheck test ## Run all checks (lint + typecheck + test)

migrate: ## Run alembic migrations
	uv run alembic upgrade head

migrate-create: ## Create new migration (usage: make migrate-create MSG="description")
	uv run alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Rollback last migration
	uv run alembic downgrade -1

db-create: ## Create databases
	psql -U postgres -c "CREATE DATABASE fip;" 2>/dev/null || true
	psql -U postgres -c "CREATE DATABASE fip_test;" 2>/dev/null || true

redis-start: ## Start Redis server
	redis-server --daemonize yes

observability: ## Start observability stack (Prometheus, Grafana, Jaeger)
	docker compose -f docker-compose.observability.yml up -d

clean: ## Clean cache files
	Remove-Item -Recurse -Force -ErrorAction SilentlyContinue .pytest_cache, .mypy_cache, .ruff_cache, htmlcov, coverage.xml, .coverage
	Get-ChildItem -Recurse -Directory -Filter __pycache__ -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

ci: ## Run CI checks locally (lint + typecheck + test)
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) test-cov

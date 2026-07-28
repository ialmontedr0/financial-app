# Financial Intelligence Platform — Backend

Enterprise-grade personal financial management API built with FastAPI + Clean Architecture + DDD.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Runtime | Python 3.14 |
| Framework | FastAPI |
| ORM | SQLAlchemy 2.x (async) |
| Database | PostgreSQL 17+ |
| Migrations | Alembic |
| Cache / Queues | Redis 7 |
| Validation | Pydantic v2 |
| Auth | JWT + OAuth2 + MFA (TOTP) |
| AI/ML | PyTorch, scikit-learn, XGBoost, LightGBM |
| Monitoring | Prometheus, Grafana, OpenTelemetry, Sentry |
| Logging | structlog (structured, JSON in production) |
| Testing | pytest, pytest-asyncio, factory-boy |
| Linting | Ruff, mypy (strict) |
| CI/CD | GitHub Actions |
| Deploy | Railway / systemd |

## Architecture

Clean Architecture + Domain-Driven Design with 4 layers:

```
api/           # Presentation — FastAPI routers
application/   # Use cases — one class per use case
domain/        # Business entities, value objects, domain rules
infrastructure/# ORM models, repositories, external services
```

### Rules

- Business logic never in routers
- No SQL in routers or services
- No business rules in ORM models
- All modules remain independent (no circular deps)

## Features

### Core Financial Management
- Multi-currency transactions, accounts, wallets, categories
- Income & expense tracking with recurring schedules
- Budget management with threshold alerts
- Credit/debit card management with spending limits
- Loan tracking with amortization schedules
- Financial goals with progress simulations

### AI & Intelligence
- Transaction auto-classification (scikit-learn)
- Expense & income prediction (XGBoost/LightGBM)
- Anomaly detection (PyTorch AutoEncoder + Isolation Forest)
- Personalized recommendations with explainable AI
- Spending habit analysis and risk assessment
- Savings optimization with simulations
- Financial health scoring

### Analytics
- KPI dashboards (monthly, portfolio)
- Spending trends and income trends
- Category breakdowns and cash flow
- Net worth tracking
- Spending heatmaps

### Automation
- Rule-based automation engine
- Event-driven triggers and actions

### Security
- JWT with short-lived access tokens (15min) + refresh tokens (7d)
- OAuth2 (Google, GitHub)
- MFA (TOTP via Authenticator apps)
- bcrypt password hashing with rehashing
- Rate limiting (Redis sliding window)
- RBAC with hierarchical permissions
- Security headers middleware
- Audit logging

### Notifications
- Email (SMTP / SendGrid)
- Telegram bot
- Discord webhooks
- Generic webhook support
- Push notifications (configurable)

### Observability
- Prometheus metrics (custom + auto-instrumented)
- Grafana dashboards
- OpenTelemetry tracing (Jaeger)
- Sentry error tracking
- Structured JSON logging

## Project Structure

```
backend/
  app/
    api/v1/        # 24 route modules (auth, users, accounts, wallets, transactions, etc.)
    application/   # ~230 use cases across all domains
    domain/        # 18 domain modules with value objects
    infrastructure/# 46 ORM models, 24 repositories, services (cache, email, security, etc.)
    ai/            # ML models, recommendation engine, risk assessment
    middleware/    # Error handler, rate limiter, request logger, security headers
    core/         # Configuration (pydantic-settings), logging
    audit/        # Audit trail service
    automation/   # Rule engine
    notifications/# Multi-channel notification service
  migrations/     # 21 Alembic migration files
  tests/          # Unit, API, and integration tests
```

## Quick Start

```bash
# Prerequisites: Python 3.14, PostgreSQL, Redis, uv

# Clone and enter backend directory
cd fip-backend

# Copy environment file
cp .env.example .env
# Edit .env with your local PostgreSQL and Redis URLs

# Sync dependencies
uv sync

# Run database migrations
uv run alembic upgrade head

# Seed initial data (categories, roles)
uv run python -c "from app.infrastructure.seed.category_seed import seed_categories; from app.infrastructure.db.session import async_session_factory; import asyncio; asyncio.run(seed_categories(async_session_factory))"
uv run python -c "from app.infrastructure.seed.role_seed import seed_roles; from app.infrastructure.db.session import async_session_factory; import asyncio; asyncio.run(seed_roles(async_session_factory))"

# Start development server
uv run uvicorn app.main:app --reload --port 8080
```

API docs: http://localhost:8080/docs

## Environment Variables

Key variables (see `.env.example` for full list):

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection (supports `postgresql://` — auto-adds `+asyncpg`) |
| `REDIS_URL` | Yes | Redis connection |
| `SECRET_KEY` | Yes | JWT signing key (generate with `openssl rand -hex 32`) |
| `CORS_ORIGINS` | No | JSON array or comma-separated origins (default: localhost) |
| `SENTRY_DSN` | No | Sentry error tracking |
| `ENVIRONMENT` | No | `development`, `staging`, or `production` |

## Testing

```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/api/v1/health/test_health.py -v
```

## Deployment

### Railway (auto-deploy)
Push to `main` triggers Railway deploy via GitHub Actions.

### Manual (systemd)
```bash
# Build and deploy
uv sync --frozen
alembic upgrade head
systemctl restart fip-api
```

### CI/CD Pipelines
- **ci.yml**: Lint + typecheck + tests on every PR/push
- **deploy-backend.yml**: Railway deploy on main push
- **deploy.yml**: SSH deploy to VPS
- **security-scan.yml**: Weekly dependency/vulnerability scan

## API Endpoints

All endpoints under `/api/v1`. OpenAPI docs at `/docs` (disabled in production).

| Module | Base Path | Description |
|--------|-----------|-------------|
| Health | `/health` | Health, readiness, liveness probes |
| Auth | `/auth` | Register, login, MFA, refresh, password reset |
| Users | `/users` | Profile, preferences |
| Accounts | `/accounts` | Financial accounts CRUD |
| Wallets | `/wallets` | Wallet grouping with accounts |
| Categories | `/categories` | Categories + subcategories |
| Transactions | `/transactions` | Full transaction management with recurring, OCR, attachments |
| Incomes | `/incomes` | Income records, sources, schedules, recurring |
| Expenses | `/expenses` | Expenses, subscriptions, services, card bills |
| Budgets | `/budgets` | Budgets with alerts and auto-adjust |
| Cards | `/cards` | Credit cards, bills, spending limits |
| Debit Cards | `/debit-cards` | Debit card management |
| Loans | `/loans` | Loans, amortization, early payoff simulation |
| Goals | `/goals` | Financial goals with predictions and simulations |
| Analytics | `/analytics` | KPIs, trends, cash flow, heatmaps |
| AI | `/ai` | Classification, prediction, anomalies, recommendations |
| Automations | `/automations/rules` | Automation rules and execution logs |
| Notifications | `/notifications` | User notifications and preferences |
| Imports | `/imports` | File import (CSV, bank exports) |
| Exports | `/exports` | Data export (CSV, Excel, PDF) |
| Admin | `/admin` | User/role/permission management, audit logs |

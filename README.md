# Financial Intelligence Platform — Backend

API de gestion financiera personal con arquitectura empresarial, construida con FastAPI + Clean Architecture + DDD.

## Stack Tecnologico

| Capa | Tecnologia |
|-------|-----------|
| Runtime | Python 3.14 |
| Framework | FastAPI |
| ORM | SQLAlchemy 2.x (asincrono) |
| Base de Datos | PostgreSQL 17+ |
| Migraciones | Alembic |
| Cache / Colas | Redis 7 |
| Validacion | Pydantic v2 |
| Autenticacion | JWT + OAuth2 + MFA (TOTP) |
| IA/ML | PyTorch, scikit-learn, XGBoost, LightGBM |
| Monitoreo | Prometheus, Grafana, OpenTelemetry, Sentry |
| Logging | structlog (estructurado, JSON en produccion) |
| Pruebas | pytest, pytest-asyncio, factory-boy |
| Linting | Ruff, mypy (estricto) |
| CI/CD | GitHub Actions |
| Deploy | Railway / systemd |

## Arquitectura

Clean Architecture + Domain-Driven Design con 4 capas:

```
api/           # Presentacion — Routers de FastAPI
application/   # Casos de uso — una clase por caso de uso
domain/        # Entidades de negocio, value objects, reglas de dominio
infrastructure/# Modelos ORM, repositorios, servicios externos
```

### Reglas

- La logica de negocio nunca va en los routers
- No hay SQL en routers ni servicios
- No hay reglas de negocio en los modelos ORM
- Todos los modulos son independientes (sin dependencias circulares)

## Funcionalidades

### Gestion Financiera Principal
- Transacciones multi-moneda, cuentas, carteras, categorias
- Seguimiento de ingresos y gastos con programacion recurrente
- Presupuestos con alertas de umbral
- Tarjetas de credito/debito con limites de gasto
- Prestamos con tabla de amortizacion
- Metas financieras con simulaciones de progreso

### IA e Inteligencia
- Clasificacion automatica de transacciones (scikit-learn)
- Prediccion de gastos e ingresos (XGBoost/LightGBM)
- Deteccion de anomalias (AutoEncoder PyTorch + Isolation Forest)
- Recomendaciones personalizadas con IA explicable
- Analisis de habitos de gasto y evaluacion de riesgos
- Optimizacion de ahorros con simulaciones
- Puntaje de salud financiera

### Analitica
- KPIs mensuales y de portafolio
- Tendencias de gastos e ingresos
- Desglose por categorias y flujo de caja
- Seguimiento de patrimonio neto
- Mapas de calor de gastos

### Automatizacion
- Motor de reglas automatizadas
- Disparadores y acciones basados en eventos

### Seguridad
- JWT con tokens de acceso de corta duracion (15min) + tokens de refresco (7d)
- OAuth2 (Google, GitHub)
- MFA (TOTP via apps Authenticator)
- Hashing de contrasenas con bcrypt y re-hashing
- Limitacion de tasa (ventana deslizante en Redis)
- RBAC con permisos jerarquicos
- Middleware de headers de seguridad
- Registro de auditoria

### Notificaciones
- Correo electronico (SMTP / SendGrid)
- Bot de Telegram
- Webhooks de Discord
- Soporte para webhooks genericos
- Notificaciones push (configurable)

### Observabilidad
- Metricas de Prometheus (personalizadas + auto-instrumentadas)
- Dashboards de Grafana
- Trazado con OpenTelemetry (Jaeger)
- Seguimiento de errores con Sentry
- Logging estructurado en JSON

## Estructura del Proyecto

```
backend/
  app/
    api/v1/        # 24 modulos de rutas (auth, users, accounts, wallets, transactions, etc.)
    application/   # ~230 casos de uso en todos los dominios
    domain/        # 18 modulos de dominio con value objects
    infrastructure/# 46 modelos ORM, 24 repositorios, servicios (cache, email, seguridad, etc.)
    ai/            # Modelos ML, motor de recomendaciones, evaluacion de riesgos
    middleware/    # Manejador de errores, limitador de tasa, logger, headers de seguridad
    core/          # Configuracion (pydantic-settings), logging
    audit/         # Servicio de pista de auditoria
    automation/    # Motor de reglas
    notifications/# Servicio de notificaciones multi-canal
  migrations/     # 21 archivos de migracion Alembic
  tests/          # Pruebas unitarias, API y de integracion
```

## Inicio Rapido

```bash
# Prerrequisitos: Python 3.14, PostgreSQL, Redis, uv

# Clonar y entrar al directorio
cd fip-backend

# Copiar archivo de entorno
cp .env.example .env
# Edita .env con tus URLs de PostgreSQL y Redis

# Sincronizar dependencias
uv sync

# Ejecutar migraciones
uv run alembic upgrade head

# Sembrar datos iniciales (categorias, roles)
uv run python -c "from app.infrastructure.seed.category_seed import seed_categories; from app.infrastructure.db.session import async_session_factory; import asyncio; asyncio.run(seed_categories(async_session_factory))"
uv run python -c "from app.infrastructure.seed.role_seed import seed_roles; from app.infrastructure.db.session import async_session_factory; import asyncio; asyncio.run(seed_roles(async_session_factory))"

# Iniciar servidor de desarrollo
uv run uvicorn app.main:app --reload --port 8080
```

Documentacion de la API: http://localhost:8080/docs

## Variables de Entorno

Variables principales (ver `.env.example` para la lista completa):

| Variable | Requerida | Descripcion |
|----------|-----------|-------------|
| `DATABASE_URL` | Si | Conexion a PostgreSQL (soporta `postgresql://` — agrega `+asyncpg` automaticamente) |
| `REDIS_URL` | Si | Conexion a Redis |
| `SECRET_KEY` | Si | Clave para firmar JWT (genera con `openssl rand -hex 32`) |
| `CORS_ORIGINS` | No | JSON array u origenes separados por coma (default: localhost) |
| `SENTRY_DSN` | No | DSN de Sentry para seguimiento de errores |
| `ENVIRONMENT` | No | `development`, `staging` o `production` |

## Pruebas

```bash
# Ejecutar todas las pruebas
uv run pytest

# Con cobertura
uv run pytest --cov=app --cov-report=html

# Ejecutar un archivo especifico
uv run pytest tests/api/v1/health/test_health.py -v
```

## Deploy

### Railway (auto-deploy)
Push a `main` dispara el deploy en Railway via GitHub Actions.

### Manual (systemd)
```bash
# Compilar y desplegar
uv sync --frozen
alembic upgrade head
systemctl restart fip-api
```

### Pipelines de CI/CD
- **ci.yml**: Lint + typecheck + pruebas en cada PR/push
- **deploy-backend.yml**: Deploy a Railway en push a main
- **deploy.yml**: Deploy SSH a VPS
- **security-scan.yml**: Escaneo semanal de dependencias/vulnerabilidades

## Decisiones de Arquitectura

### Restricciones de integridad referencial (FKs) — desviación deliberada

El `GUIDE.md` (Parcial 21) solicita migrar estas claves foráneas de `ON DELETE SET NULL` a `ON DELETE CASCADE`:

- `transactions.account_id` → `financial_account.id`
- `budgets.category_id` → `category.id`
- `goals.account_id` → `financial_account.id`

**Decisión (business decision):** se mantiene `ON DELETE SET NULL` en las tres claves.

**Motivo:** la plataforma trata las transacciones y las metas como historial financiero que no debe perderse. Eliminar una cuenta, una categoría o una meta no debe borrar en cascada sus transacciones ni sus objetivos; en su lugar, los registros quedan huérfanos (`NULL`) y conservan el dato para auditoría y analítica histórica.

**Consecuencia:** al eliminar un padre (cuenta/categoría), los hijos quedan con `NULL` en la FK. Los casos de uso de lectura ya toleran esta condición (los modelos declaran las columnas como `nullable=True`). No se requiere migración; la restricción actual de `SET NULL` ya existe en la base de datos.

**Si en el futuro se requiere borrado en cascada:** generar una migración Alembic que ejecute `op.drop_constraint(...)` + `op.create_foreign_key(..., ondelete="CASCADE")` para cada FK listada arriba (ver `FIP_GUIA_PENDIENTES.md`, Parcial 21, para los pasos exactos).

## Endpoints de la API

Todos los endpoints bajo `/api/v1`. Documentacion OpenAPI en `/docs` (deshabilitado en produccion).

| Modulo | Ruta Base | Descripcion |
|--------|-----------|-------------|
| Health | `/health` | Health, readiness, liveness probes |
| Auth | `/auth` | Registro, login, MFA, refresco, restablecer contrasena |
| Users | `/users` | Perfil, preferencias |
| Accounts | `/accounts` | CRUD de cuentas financieras |
| Wallets | `/wallets` | Agrupacion de cuentas en carteras |
| Categories | `/categories` | Categorias y subcategorias |
| Transactions | `/transactions` | Gestion completa de transacciones con recurrencia, OCR, adjuntos |
| Incomes | `/incomes` | Registros de ingresos, fuentes, programacion, recurrencia |
| Expenses | `/expenses` | Gastos, suscripciones, servicios, facturas de tarjeta |
| Budgets | `/budgets` | Presupuestos con alertas y auto-ajuste |
| Cards | `/cards` | Tarjetas de credito, facturas, limites de gasto |
| Debit Cards | `/debit-cards` | Gestion de tarjetas de debito |
| Loans | `/loans` | Prestamos, amortizacion, simulacion de pago anticipado |
| Goals | `/goals` | Metas financieras con predicciones y simulaciones |
| Analytics | `/analytics` | KPIs, tendencias, flujo de caja, mapas de calor |
| AI | `/ai` | Clasificacion, prediccion, anomalias, recomendaciones |
| Automations | `/automations/rules` | Reglas de automatizacion y registros de ejecucion |
| Notifications | `/notifications` | Notificaciones y preferencias del usuario |
| Imports | `/imports` | Importacion de archivos (CSV, exportaciones bancarias) |
| Exports | `/exports` | Exportacion de datos (CSV, Excel, PDF) |
| Admin | `/admin` | Gestion de usuarios, roles, permisos, registros de auditoria |

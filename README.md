# Caravan HR Portal 2.0

Корпоративный HR-портал: FastAPI backend, Next.js PWA, Expo mobile shell и общие TypeScript-пакеты.

## Структура

```text
apps/api        FastAPI API
apps/web        Next.js PWA
apps/mobile     Expo mobile shell
packages        shared-types, ui-core, api-client
infra           Docker, Nginx, Prometheus/Grafana
docs            проектная и юридическая документация
```

## Быстрый старт

```bash
docker compose -f infra/docker/docker-compose.dev.yml up -d

cd apps/api
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest tests -q

cd ../..
corepack pnpm install --frozen-lockfile
corepack pnpm run lint
corepack pnpm run typecheck
corepack pnpm run build
```

## Backend

Основные endpoint'ы под префиксом `/api/v1`:

**Auth и сотрудники (Stage 1):**
- `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout`, `GET /api/v1/auth/me`
- `GET /api/v1/employees`, `GET /api/v1/dashboard`
- `GET /health`, `GET /api/v1/health`

**Отпуска и согласование (Stage 2):**
- `GET/POST /api/v1/vacations`, `GET/PATCH/DELETE /api/v1/vacations/{id}`
- `GET /api/v1/vacations/types`, `GET /api/v1/vacations/balance`, `GET /api/v1/vacations/check-overlap`
- `GET /api/v1/approvals/vacations`, `POST /api/v1/approvals/vacations/{id}/approve|reject`
- `GET /api/v1/notifications`, `GET /api/v1/notifications/unread-count`, `POST /api/v1/notifications/{id}/read`, `POST /api/v1/notifications/read-all`

SQLAdmin смонтирован на `/admin/ui`; доступ разрешается только активным пользователям с ролью `admin`.

## Frontend

Web-приложение собирается как static export для текущей схемы Nginx:

```bash
corepack pnpm --filter @corp-portal/web run build
```

Детальная страница отпуска использует статический маршрут `/vacations/detail?id=<id>`, чтобы не ломать `output: export`.

## Проверки

Актуальный минимальный набор:

```bash
cd apps/api
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy app

cd ../..
corepack pnpm run lint
corepack pnpm run typecheck
corepack pnpm run build
docker compose -f infra/docker/docker-compose.dev.yml config
docker compose -f infra/docker/docker-compose.yml config
```

Юридические требования и детализация пункта 8 ТЗ вынесены в [docs/LEGAL_COMPLIANCE.md](docs/LEGAL_COMPLIANCE.md).

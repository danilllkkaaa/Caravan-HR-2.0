# Техническое задание
## Корпоративный портал сотрудника (PWA + Mobile)

**Версия документа:** 1.0
**Дата:** Май 2026
**Целевая нагрузка:** 3 500 – 5 000 активных пользователей
**Пиковая нагрузка:** ~3 000 одновременных событий вход/выход в окно 08:00–09:30

---

## Содержание

1. [Анализ исходных требований и ключевые правки](#1-анализ)
2. [Архитектура системы](#2-архитектура)
3. [Финальный технологический стек](#3-стек)
4. [Структура монорепозитория](#4-монорепо)
5. [Модель данных](#5-модель-данных)
6. [API: дизайн и контракты](#6-api)
7. [Аутентификация и авторизация](#7-auth)
8. [Интеграции (Hikvision, 1С:ЗУП)](#8-интеграции)
9. [Функциональные модули](#9-модули)
10. [PWA-конфигурация](#10-pwa)
11. [Мобильное приложение](#11-mobile)
12. [Производительность и оптимизация](#12-производительность)
13. [Масштабируемость](#13-масштабируемость)
14. [Безопасность](#14-безопасность)
15. [Инфраструктура и DevOps](#15-devops)
16. [Мониторинг и логирование](#16-мониторинг)
17. [План разработки по этапам](#17-этапы)

---

<a id="1-анализ"></a>
## 1. Анализ исходных требований и ключевые правки

Исходные данные проработаны хорошо, но есть **семь моментов, которые лучше зафиксировать на старте**, иначе они станут техдолгом через 3–6 месяцев.

### 1.1. FastAPI vs Django — выбираем FastAPI

В исходниках указано «FastAPI или Django». На проекте нужно выбрать одно и не смешивать.

**Решение: FastAPI 0.110+ на async-стеке.**

Обоснование:
- Нативная async-модель критична для двух сценариев: пиковые вебхуки Hikvision (3 000 событий за 90 минут) и параллельные запросы к 1С (медленный внешний сервис).
- Pydantic v2 + автогенерируемая OpenAPI-схема → бесплатный типизированный TypeScript-клиент для веба и мобилы.
- Django ORM + sync-views плохо ложатся на интеграционно-тяжёлый бэкенд.

**Что мы теряем от Django и чем заменяем:**
- Django Admin → `SQLAdmin` (FastAPI-нативная админка) + кастомные административные эндпоинты.
- Django Auth → собственный модуль на `python-jose` + `passlib[bcrypt]`.
- Django Migrations → `Alembic` (де-факто стандарт для SQLAlchemy).

### 1.2. Cookie-сессии vs JWT — гибридная схема

В исходниках: «сессии в cookie». Для PWA это работает, но **React Native плохо живёт с cookie-based auth** (нужны костыли через `CookieManager`, ломается при SSR-сценариях).

**Решение: единая JWT-схема для веба и мобилы.**

- **Access token:** JWT, TTL 15 минут, в памяти приложения (не в localStorage!).
- **Refresh token:** opaque-токен (UUID), TTL 30 дней, хранится:
  - На вебе — в `HttpOnly; Secure; SameSite=Lax` cookie.
  - В мобильном — в `expo-secure-store` (iOS Keychain / Android Keystore).
- Refresh-токены хранятся в БД с привязкой к устройству → можно отзывать сессии и иметь список «мои устройства».
- Эндпоинт `/auth/refresh` ротирует refresh-токен при каждом использовании (защита от кражи).

### 1.3. VPS 4 vCPU / 8 GB RAM — недостаточно для прод-нагрузки

Расчёт для 5 000 пользователей с пиком утром:
- ~3 000 событий Hikvision за 90 минут = ~33 событий/мин (терпимо).
- При входе все 3 000 человек открывают PWA в течение часа = ~50 RPS базово, пики до 200 RPS.
- 1С-синхронизация (cron) + Celery + Postgres + Redis + Nginx на одной машине = борьба за CPU.

**Решение: production — минимум одна из двух конфигураций.**

| Вариант | Состав | Когда выбирать |
|---|---|---|
| **A. Один мощный VPS** | 8 vCPU / 16 GB RAM / 200 GB NVMe | Старт, до 5 000 пользователей, ограниченный бюджет |
| **B. Разделение по узлам** | App (4 vCPU/8 GB) + DB (4 vCPU/16 GB) + Redis (2 vCPU/4 GB) | После 5 000 пользователей или нужна высокая доступность |

Указанные в исходниках 4 vCPU / 8 GB оставляем **только для dev/staging**.

### 1.4. Hikvision-вебхук — буферизация обязательна

Прямая запись в Postgres на каждое событие = риск всплеска latency и блокировок в утренний пик.

**Решение:** вебхук Hikvision → Nginx → лёгкий FastAPI-эндпоинт, который **только** валидирует и кладёт в Redis Stream (`attendance:raw`). Celery-воркер разгребает поток батчами по 50–100 событий и пишет в Postgres одним `COPY` или `INSERT … ON CONFLICT`.

Выгода: даже если Postgres на секунду тормознёт, события не теряются и не блокируют ответ Hikvision.

### 1.5. Синхронизация 1С:ЗУП — стратегия по типам данных

| Данные | Стратегия | Частота |
|---|---|---|
| Справочник сотрудников | Pull, инкрементально по `LastModifiedDate` | Каждые 15 мин |
| Подразделения, должности | Pull, full sync | Раз в сутки, 02:00 |
| Графики работы | Pull | Каждые 30 мин |
| Расчётный листок | Pull on-demand с кешем 1 час | По запросу пользователя |
| Балансы отпусков | Pull | Каждые 30 мин |

Все sync-задачи в Celery Beat. При недоступности 1С — экспоненциальный backoff (1, 2, 4, 8, 16 мин), алерт в Sentry после 3 неудач подряд.

### 1.6. Хранение файлов (больничные листы) — S3-совместимое хранилище

В исходниках не указано, где хранятся PDF/JPG больничных листов. На диске VPS — плохо (бэкапы, миграции, ACL).

**Решение:** MinIO в Docker, S3-совместимый API. Бакеты:
- `sick-leaves` (приватный, доступ только через presigned URL, TTL 5 мин).
- `material-aid-docs` (для будущих заявок на матпомощь).
- `avatars` (публичный, опционально).

### 1.7. Бэкапы — встроить в архитектуру сразу

- **Postgres:** `pg_dump` каждые 6 часов + WAL-archiving (`wal-g`) для PITR. Хранение в отдельном объектном хранилище (Yandex Object Storage / Selectel S3).
- **MinIO:** репликация в облачный S3 раз в сутки.
- **Retention:** дневные бэкапы — 14 дней, недельные — 3 месяца, месячные — 1 год.

### 1.8. Резюме изменений к исходному ТЗ

| Было | Стало |
|---|---|
| FastAPI **или** Django | FastAPI (фиксируем) |
| Cookie-сессии | JWT (access + refresh), refresh в cookie на вебе и в SecureStore в мобилке |
| VPS 4/8 | Dev: 4/8, Prod: 8/16+ (или разделение на узлы) |
| Hikvision → прямая запись в БД | Hikvision → Redis Stream → Celery → Postgres |
| Файлы на диске (неявно) | MinIO (S3-совместимый) с presigned URL |
| Бэкапы не описаны | pg_dump + WAL archiving + offsite |

---

<a id="2-архитектура"></a>
## 2. Архитектура системы

### 2.1. Высокоуровневая схема

```
            ┌──────────────────┐         ┌──────────────────┐
            │  Mobile (Expo)   │         │  PWA (Next.js)   │
            └────────┬─────────┘         └────────┬─────────┘
                     │                            │
                     └──────────┬─────────────────┘
                                │   HTTPS
                                ▼
                       ┌────────────────┐
                       │  Nginx (TLS,   │
                       │  rate limit,   │
                       │  gzip, cache)  │
                       └────────┬───────┘
                                │
            ┌───────────────────┼───────────────────────┐
            │                   │                       │
            ▼                   ▼                       ▼
    ┌──────────────┐    ┌──────────────┐       ┌──────────────┐
    │ FastAPI API  │    │ Hikvision    │       │ SQLAdmin     │
    │ (uvicorn × N)│    │ webhook      │       │ (admin UI)   │
    └──────┬───────┘    │ ingest svc   │       └──────┬───────┘
           │            └──────┬───────┘              │
           │                   │                      │
           └─────┬─────────────┼──────────────────────┘
                 │             │
                 │             ▼
                 │      ┌────────────┐
                 │      │ Redis      │  ◄── Streams, Cache, Pub/Sub
                 │      │ (7.x)      │
                 │      └─────┬──────┘
                 │            │
                 ▼            ▼
          ┌──────────────────────────┐
          │   Celery Workers (× M)   │
          │   + Celery Beat          │
          └──────┬───────────────────┘
                 │
       ┌─────────┼──────────┬────────────┐
       │         │          │            │
       ▼         ▼          ▼            ▼
   ┌────────┐ ┌────┐  ┌──────────┐  ┌──────────┐
   │Postgres│ │MinIO│ │ 1С:ЗУП   │  │Hikvision │
   │  16    │ │     │ │ HTTP API │  │  ISAPI   │
   └────────┘ └────┘  └──────────┘  └──────────┘
```

### 2.2. Принципы архитектуры бэкенда

Используем **слоистую архитектуру (Clean Architecture lite)**. Достаточно для масштаба проекта, не превращаем в DDD-оверкилл.

```
app/
├── api/              # Presentation: FastAPI routers, dependencies, schemas (Pydantic)
├── application/      # Use-cases / services: бизнес-логика
├── domain/           # Доменные модели (dataclasses), интерфейсы репозиториев
├── infrastructure/   # Реализация: SQLAlchemy repos, Redis, Hikvision/1C clients
├── workers/          # Celery tasks
├── core/             # Config, logging, security, exceptions
└── main.py
```

**Правила зависимостей:**
- `api` зависит от `application`.
- `application` зависит от `domain` (через интерфейсы) и НЕ зависит от `infrastructure`.
- `infrastructure` реализует интерфейсы `domain`.
- `workers` зависят от `application`.

**Что это даёт:**
- Бизнес-логика тестируется без БД и HTTP.
- Замена 1С с REST на SOAP или Hikvision на другую СКУД = только новый адаптер в `infrastructure`.

### 2.3. Слой презентации

- Все эндпоинты — версионированные: `/api/v1/...`.
- Стандартный формат ошибок:
  ```json
  {
    "error": {
      "code": "VACATION_OVERLAP",
      "message": "Заявление пересекается с одобренным отпуском",
      "details": { "conflicting_request_id": 142 }
    }
  }
  ```
- Все списки — пагинированные (cursor-based для длинных историй, offset для коротких).
- Все эндпоинты документированы в OpenAPI (`/docs` в dev, отключён в prod).

### 2.4. Деплой-топология (production, рекомендуемая)

```
┌─────────────────────────────────────────────────────┐
│  VPS-1 (App): 8 vCPU / 16 GB RAM / 200 GB NVMe     │
│  ┌────────────────────────────────────────────┐    │
│  │  Docker Compose:                            │    │
│  │  • nginx                                    │    │
│  │  • api (uvicorn, 4 workers)                 │    │
│  │  • celery-worker (concurrency=8)            │    │
│  │  • celery-beat                              │    │
│  │  • minio                                    │    │
│  │  • prometheus + grafana + loki              │    │
│  └────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  VPS-2 (Data): 4 vCPU / 16 GB RAM / 200 GB NVMe    │
│  • PostgreSQL 16 (с tuning под профиль OLTP)        │
│  • Redis 7 (maxmemory 4 GB, allkeys-lru)            │
│  • wal-g (PITR backups → offsite S3)                │
└─────────────────────────────────────────────────────┘
```

Для старта допустимо всё на одном VPS 8/16, разделить позднее без изменения кода (Docker Compose → отдельные хосты).

---

<a id="3-стек"></a>
## 3. Финальный технологический стек

### 3.1. Бэкенд

| Компонент | Версия | Назначение |
|---|---|---|
| Python | 3.12 | Рантайм |
| FastAPI | 0.110+ | Web-фреймворк |
| Uvicorn | 0.27+ | ASGI-сервер (за Nginx) |
| Pydantic | 2.x | Валидация и сериализация |
| SQLAlchemy | 2.0+ (async) | ORM |
| Alembic | 1.13+ | Миграции БД |
| asyncpg | 0.29+ | Postgres-драйвер (async) |
| Celery | 5.3+ | Фоновые задачи |
| Redis-py | 5.x | Кеш, очереди, стримы |
| python-jose | — | JWT |
| passlib[bcrypt] | — | Хеширование паролей |
| httpx | 0.27+ | HTTP-клиент (1С, Hikvision) — async |
| minio | 7.x | S3-клиент |
| structlog | 24.x | Структурное логирование |
| sentry-sdk | 1.40+ | Error tracking |
| pytest, pytest-asyncio | — | Тесты |
| ruff, mypy | — | Линт + типы |
| SQLAdmin | 0.16+ | Админ-панель |

### 3.2. Web-фронтенд (PWA)

| Компонент | Версия | Назначение |
|---|---|---|
| Next.js | 14 (App Router) | React-фреймворк |
| React | 18.2+ | UI |
| TypeScript | 5.4+ | Типы |
| Tailwind CSS | 3.4+ | Стили |
| TanStack Query | 5.x | Server state |
| Zustand | 4.5+ | Client state |
| React Hook Form + Zod | — | Формы + валидация |
| next-pwa | — | PWA (service worker, manifest) |
| date-fns | 3.x | Даты |
| lucide-react | — | Иконки |

**Почему Next.js, а не Vite+React:** App Router даёт серверные компоненты для нечасто меняющихся страниц (профиль, справочники), что снижает bundle size — критично для PWA на слабых телефонах.

### 3.3. Мобильное приложение

| Компонент | Версия | Назначение |
|---|---|---|
| Expo SDK | 50+ | Платформа |
| React Native | 0.73+ | Рантайм |
| Expo Router | 3.x | Навигация |
| TypeScript | 5.4+ | Типы |
| TanStack Query | 5.x | Server state (тот же, что на вебе) |
| Zustand | 4.5+ | Client state |
| expo-secure-store | — | Хранение токенов |
| expo-notifications | — | Push |
| react-native-reanimated | 3.x | Анимации |
| react-hook-form + zod | — | Формы |
| date-fns | 3.x | Даты |

### 3.4. Инфраструктура

| Компонент | Версия | Назначение |
|---|---|---|
| PostgreSQL | 16 | Основная БД |
| Redis | 7 | Кеш, очереди Celery, стримы Hikvision |
| MinIO | latest | S3-совместимое хранилище |
| Nginx | 1.25+ | Reverse proxy, TLS, статика |
| Docker + Compose | — | Контейнеризация |
| Prometheus | — | Метрики |
| Grafana | — | Дашборды |
| Loki | — | Логи |
| Sentry | — | Ошибки (cloud) |
| GitHub Actions | — | CI/CD |
| Fastlane | — | Публикация в сторы |

---

<a id="4-монорепо"></a>
## 4. Структура монорепозитория

**Инструмент:** `pnpm` + `Turborepo` (для frontend-частей) + отдельная Python-папка для бэкенда.

```
corp-portal/
├── apps/
│   ├── api/                  # FastAPI бэкенд (Python)
│   │   ├── app/
│   │   │   ├── api/v1/
│   │   │   ├── application/
│   │   │   ├── domain/
│   │   │   ├── infrastructure/
│   │   │   ├── workers/
│   │   │   └── core/
│   │   ├── tests/
│   │   ├── alembic/
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   │
│   ├── web/                  # Next.js PWA
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   ├── public/
│   │   ├── next.config.js
│   │   └── package.json
│   │
│   └── mobile/               # Expo
│       ├── app/              # Expo Router screens
│       ├── components/
│       ├── lib/
│       ├── assets/
│       └── package.json
│
├── packages/
│   ├── api-client/           # Сгенерированный из OpenAPI TS-клиент
│   │   ├── src/
│   │   └── package.json
│   │
│   ├── shared-types/         # Доменные типы (Vacation, Employee и т.д.)
│   │   ├── src/
│   │   └── package.json
│   │
│   ├── ui-core/              # Хуки, сторы, утилиты (не зависит от RN/web)
│   │   ├── src/
│   │   │   ├── hooks/        # useVacations, useTimesheet, useAuth
│   │   │   ├── stores/       # authStore, notificationStore
│   │   │   └── utils/        # форматирование дат, расчёты
│   │   └── package.json
│   │
│   ├── ui-web/               # React-компоненты только для веба
│   └── ui-mobile/            # React Native-компоненты
│
├── infra/
│   ├── docker/
│   │   ├── docker-compose.yml         # prod
│   │   ├── docker-compose.dev.yml
│   │   └── docker-compose.staging.yml
│   ├── nginx/
│   │   ├── nginx.conf
│   │   └── conf.d/
│   ├── grafana/
│   │   └── dashboards/
│   └── prometheus/
│       └── prometheus.yml
│
├── scripts/
│   ├── generate-api-client.sh   # запускает openapi-typescript-codegen
│   ├── backup-db.sh
│   └── deploy.sh
│
├── .github/
│   └── workflows/
│       ├── api-ci.yml
│       ├── web-ci.yml
│       ├── mobile-ci.yml
│       └── deploy.yml
│
├── turbo.json
├── pnpm-workspace.yaml
└── README.md
```

**Ключевая идея:** `packages/api-client` и `packages/ui-core` используются **и** в `web`, **и** в `mobile`. Это даёт реальное переиспользование (~40–50% кода), а не маркетинговое.

**Что генерируется автоматически:**
- При изменении OpenAPI-схемы бэкенда → запуск `generate-api-client.sh` → новый типизированный клиент → web и mobile получают обновления через `pnpm install`.

---

<a id="5-модель-данных"></a>
## 5. Модель данных

### 5.1. Основные таблицы

#### `users` — учётные записи (аутентификация)
| Поле | Тип | Описание |
|---|---|---|
| id | UUID PK | |
| email | citext UNIQUE | |
| password_hash | text | bcrypt |
| is_active | bool | |
| failed_login_attempts | int | Для лока после N попыток |
| locked_until | timestamptz NULL | |
| created_at, updated_at | timestamptz | |

#### `employees` — профиль сотрудника
| Поле | Тип | Описание |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK → users | UNIQUE |
| external_id_1c | varchar(64) | Ключ из 1С (для sync) |
| personnel_number | varchar(32) | Табельный номер |
| first_name, last_name, middle_name | varchar | |
| birth_date | date NULL | (план) |
| iin | varchar(12) NULL | (план, шифровать) |
| phone | varchar(32) | |
| department_id | UUID FK → departments | |
| position_id | UUID FK → positions | |
| manager_id | UUID FK → employees NULL | |
| role | enum: employee/manager/hr/admin | |
| hire_date | date | |
| work_location_id | UUID FK → work_locations NULL | |
| avatar_url | text NULL | |
| status | enum: at_work/at_home/on_vacation/on_sick_leave/on_business_trip | (план) |
| sync_hash | varchar(64) | Хеш данных из 1С для оптимизации sync |
| created_at, updated_at | timestamptz | |

Индексы: `(department_id)`, `(manager_id)`, `(external_id_1c)`, `(personnel_number)`.

#### `departments`
| Поле | Тип |
|---|---|
| id | UUID PK |
| external_id_1c | varchar(64) UNIQUE |
| name | varchar(255) |
| parent_id | UUID FK → departments NULL |
| head_id | UUID FK → employees NULL |

#### `positions`
| Поле | Тип |
|---|---|
| id | UUID PK |
| external_id_1c | varchar(64) UNIQUE |
| name | varchar(255) |

#### `work_locations` (план: для админок Алматы/Алмалы)
| Поле | Тип |
|---|---|
| id | UUID PK |
| external_id_1c | varchar(64) |
| name | varchar(255) |
| city | varchar(128) |
| hr_employee_id | UUID FK → employees NULL |

#### `vacation_balances`
| Поле | Тип |
|---|---|
| id | UUID PK |
| employee_id | UUID FK |
| year | int |
| total_days | numeric(5,2) |
| used_days | numeric(5,2) |
| remaining_days | numeric(5,2) GENERATED ALWAYS |
| sync_source | enum: '1c'/'manual' |
| updated_at | timestamptz |

UNIQUE `(employee_id, year)`.

#### `vacation_types`
| Поле | Тип |
|---|---|
| id | UUID PK |
| code | varchar (`annual`, `unpaid`, `study`, `parental`, ...) |
| name | varchar |
| is_paid | bool |
| requires_documents | bool |

#### `vacation_requests`
| Поле | Тип |
|---|---|
| id | UUID PK |
| employee_id | UUID FK |
| vacation_type_id | UUID FK |
| start_date | date |
| end_date | date |
| days_count | int GENERATED |
| comment | text NULL |
| status | enum: `draft/pending/approved/rejected/cancelled` |
| approver_id | UUID FK → employees NULL |
| approver_comment | text NULL |
| approved_at | timestamptz NULL |
| created_at, updated_at | timestamptz |

Индексы: `(employee_id, status)`, `(approver_id, status)`, `(start_date, end_date)`.

Бизнес-инвариант (проверяется в коде, **и** в БД через триггер): не должно быть пересечения approved-заявок одного сотрудника.

#### `sick_leaves`
| Поле | Тип |
|---|---|
| id | UUID PK |
| employee_id | UUID FK |
| start_date | date |
| end_date | date NULL | NULL пока больничный открыт |
| open_comment | text NULL |
| close_comment | text NULL |
| document_url | text NULL | S3-путь к скану |
| status | enum: `open/closed` |
| closed_by | UUID FK → employees NULL | (план: HR может закрыть) |
| created_at, updated_at | timestamptz |

Индексы: `(employee_id, status)`.

#### `attendance_events` — сырые события с Hikvision
| Поле | Тип |
|---|---|
| id | bigserial PK |
| employee_id | UUID FK NULL | NULL если не смогли сматчить |
| hikvision_person_id | varchar | |
| event_at | timestamptz | |
| event_type | enum: `entry/exit` |
| device_id | varchar | |
| raw_payload | jsonb | Полный исходный JSON для отладки |
| processed | bool DEFAULT false |
| created_at | timestamptz |

Индексы: `(employee_id, event_at DESC)`, `(processed) WHERE processed = false`.

**Партиционирование:** по `event_at` по месяцам. С 5 000 сотрудников × 2 события × 22 рабочих дня = 220 000 строк/месяц. Через год — 2.6 млн, партиции упрощают чистку старых данных.

#### `timesheet_entries` — нормализованный табель
| Поле | Тип |
|---|---|
| id | UUID PK |
| employee_id | UUID FK |
| date | date |
| first_entry_at | timestamptz NULL |
| last_exit_at | timestamptz NULL |
| worked_minutes | int |
| status | enum: `work/overtime/partial/weekend/holiday/absence/vacation/sick` |
| schedule_minutes | int NULL | Норма из графика 1С |
| created_at, updated_at | timestamptz |

UNIQUE `(employee_id, date)`. Считается Celery-задачей раз в час из `attendance_events` + графика.

#### `notifications`
| Поле | Тип |
|---|---|
| id | UUID PK |
| employee_id | UUID FK |
| type | enum: `approved/rejected/info/reminder/sharepoint_link` |
| title | varchar(255) |
| body | text |
| payload | jsonb NULL | Например, `{request_id: ..., sharepoint_url: ...}` |
| read_at | timestamptz NULL |
| created_at | timestamptz |

Индексы: `(employee_id, created_at DESC)`, `(employee_id) WHERE read_at IS NULL`.

#### `refresh_tokens`
| Поле | Тип |
|---|---|
| id | UUID PK |
| user_id | UUID FK |
| token_hash | varchar(64) | SHA-256 от токена |
| device_info | jsonb | UA, platform, app_version |
| expires_at | timestamptz |
| revoked_at | timestamptz NULL |
| created_at | timestamptz |

Индексы: `(user_id, revoked_at)`, `(token_hash)`.

#### `audit_log`
| Поле | Тип |
|---|---|
| id | bigserial PK |
| actor_id | UUID FK → users |
| action | varchar | `vacation.approve`, `sick_leave.close`, `user.login` |
| target_type | varchar | `vacation_request`, `employee`, ... |
| target_id | varchar | |
| changes | jsonb | Diff before/after |
| ip | inet |
| created_at | timestamptz |

Партиционирование по месяцам.

### 5.2. Будущие таблицы (план)

- `business_trips` (id, employee_id, destination, start_date, end_date, purpose, status, created_by, ...)
- `tax_deductions` (id, employee_id, type, status, documents, ...)
- `material_aid_requests` (id, employee_id, reason, amount, documents, status, ...)
- `family_members` (id, employee_id, relation, name, birth_date) — из ЗУП
- `education_records` (id, employee_id, institution, degree, year, source: '1c'/'manual')
- `certificates` (id, employee_id, name, issued_at, expires_at, document_url)
- `payroll_slips` (employee_id, period, gross, deductions, net, breakdown_json) — кеш из ЗУП
- `work_schedules` (id, employee_id, date, planned_minutes) — из ЗУП

### 5.3. Конвенции

- Все PK — `UUID v7` (упорядоченные по времени, лучше для индексов).
- `created_at`, `updated_at` — везде, `updated_at` обновляется триггером.
- Soft delete не используем; для архивации — флаг `is_archived` где нужно.
- Все enum-поля — нативные Postgres enum, а не varchar.

---

<a id="6-api"></a>
## 6. API: дизайн и контракты

### 6.1. Общие правила

- **Базовый путь:** `/api/v1`
- **Формат:** JSON only.
- **Времена:** ISO 8601 в UTC (`2026-05-18T08:30:00Z`). Часовой пояс пользователя — на клиенте.
- **Пагинация:**
  - Cursor для длинных списков (события, уведомления): `?cursor=...&limit=20`.
  - Offset для коротких (сотрудники отдела): `?page=1&page_size=50`.
- **Сортировка:** `?sort=-created_at` (минус = desc).
- **Фильтрация:** query-параметры (`?status=pending&from=2026-01-01`).
- **Rate limiting:** Nginx + middleware: 100 RPM на пользователя, 20 RPM на /auth/*, 5/мин на /auth/login.

### 6.2. Перечень эндпоинтов

#### Auth
| Метод | Путь | Описание |
|---|---|---|
| POST | `/auth/login` | email + password → access + refresh |
| POST | `/auth/refresh` | refresh → new access + new refresh (ротация) |
| POST | `/auth/logout` | Отзыв текущего refresh |
| POST | `/auth/logout-all` | Отзыв всех refresh пользователя |
| GET | `/auth/me` | Текущий профиль |
| GET | `/auth/sessions` | Список устройств |
| DELETE | `/auth/sessions/{id}` | Завершить сессию |

#### Главная
| Метод | Путь | Описание |
|---|---|---|
| GET | `/dashboard` | Агрегат: профиль + баланс + сегодняшний табель + 3 последние уведомления |

Один запрос вместо четырёх — экономит latency на мобиле.

#### Отпуска
| Метод | Путь | Описание |
|---|---|---|
| GET | `/vacations` | Свои заявления + фильтры |
| POST | `/vacations` | Создать заявление |
| GET | `/vacations/{id}` | Детально |
| PATCH | `/vacations/{id}` | Только пока draft |
| DELETE | `/vacations/{id}` | Отозвать (если pending) |
| GET | `/vacations/types` | Справочник типов |
| GET | `/vacations/balance` | Баланс на год |
| GET | `/vacations/check-overlap` | Проверка пересечений ?start=...&end=... |

#### Согласование (manager/admin)
| Метод | Путь | Описание |
|---|---|---|
| GET | `/approvals/vacations` | Очередь заявок на одобрение |
| POST | `/approvals/vacations/{id}/approve` | Одобрить |
| POST | `/approvals/vacations/{id}/reject` | Отклонить (с комментарием) |

#### Больничные
| Метод | Путь | Описание |
|---|---|---|
| GET | `/sick-leaves` | Свои больничные |
| POST | `/sick-leaves/open` | Открыть |
| POST | `/sick-leaves/{id}/close` | Закрыть (с документом) |
| GET | `/sick-leaves/{id}/document` | presigned URL для скачивания |
| POST | `/sick-leaves/upload-url` | Получить presigned URL на загрузку |

#### Табель
| Метод | Путь | Описание |
|---|---|---|
| GET | `/timesheet?month=2026-05` | Записи за месяц |
| GET | `/timesheet/entries/{id}` | Детально по дню |
| GET | `/timesheet/summary?month=2026-05` | Итоги (отработано/норма/сверхурочно) |

#### Сотрудники
| Метод | Путь | Описание |
|---|---|---|
| GET | `/employees?q=&department_id=&page=` | Список (только свой отдел для employee, свой + подчинённые отделы для manager, всё для admin) |
| GET | `/employees/{id}` | Карточка |
| GET | `/employees/me` | Свой профиль (то же, что /auth/me, но расширенный) |

#### Уведомления
| Метод | Путь | Описание |
|---|---|---|
| GET | `/notifications?cursor=&unread_only=` | Список с курсором |
| GET | `/notifications/unread-count` | Число непрочитанных |
| POST | `/notifications/{id}/read` | Отметить одно |
| POST | `/notifications/read-all` | Отметить все |

#### Hikvision webhook (внутренний)
| Метод | Путь | Описание |
|---|---|---|
| POST | `/webhooks/hikvision/attendance` | Приём событий |

Защищён shared secret + IP whitelist.

#### Admin (роль admin)
| Метод | Путь | Описание |
|---|---|---|
| POST | `/admin/users` | Создать пользователя |
| PATCH | `/admin/users/{id}/role` | Изменить роль |
| POST | `/admin/users/{id}/reset-password` | Сбросить пароль |
| POST | `/admin/sync/1c` | Принудительная синхронизация |
| GET | `/admin/audit-log` | Аудит |

Дополнительно — SQLAdmin на `/admin/ui` для табличного редактирования.

### 6.3. Пример контракта: создание заявления на отпуск

**Request `POST /api/v1/vacations`:**
```json
{
  "vacation_type_id": "01931a2b-...",
  "start_date": "2026-07-01",
  "end_date": "2026-07-14",
  "comment": "Семейный отпуск"
}
```

**Response 201:**
```json
{
  "id": "01931a3c-...",
  "status": "pending",
  "start_date": "2026-07-01",
  "end_date": "2026-07-14",
  "days_count": 14,
  "vacation_type": { "id": "...", "name": "Ежегодный оплачиваемый", "code": "annual" },
  "approver": { "id": "...", "full_name": "Иванов И. И." },
  "created_at": "2026-05-18T10:23:00Z"
}
```

**Возможные ошибки:**
- `400 INSUFFICIENT_BALANCE` — не хватает дней.
- `400 VACATION_OVERLAP` — пересечение с другой заявкой.
- `400 INVALID_DATE_RANGE` — end_date раньше start_date.
- `404 VACATION_TYPE_NOT_FOUND`.

---

<a id="7-auth"></a>
## 7. Аутентификация и авторизация

### 7.1. Поток входа

```
1. Client → POST /auth/login {email, password}
2. Server:
   - Поиск user по email (citext, case-insensitive)
   - Если failed_attempts ≥ 5 и locked_until > now() → 423 Locked
   - bcrypt.verify(password, user.password_hash)
   - При неуспехе: failed_attempts++, если ≥ 5 → locked_until = now() + 15 min
   - При успехе: failed_attempts = 0
   - Генерация:
       access_token = JWT(sub=user_id, role=..., exp=now+15min, jti=uuid)
       refresh_token = uuid4()
   - Сохранение в refresh_tokens: hash(refresh_token), device_info, expires_at = now+30d
3. Server → Client:
   - JSON: {access_token, refresh_expires_at}
   - Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Lax; Path=/api/v1/auth; Max-Age=2592000
   (для мобилы — refresh в JSON, потому что cookie там неудобно)
```

### 7.2. Refresh

```
1. Client → POST /auth/refresh (cookie с refresh ИЛИ Authorization-Refresh header для мобилы)
2. Server:
   - Проверка: токен существует, не revoked, не expired
   - Ротация: старый помечается revoked_at, создаётся новый
   - При попытке использовать revoked refresh → ОТЗЫВ ВСЕХ refresh пользователя (защита от кражи)
3. Server → новые access + refresh
```

### 7.3. Проверка авторизации

FastAPI dependency:
```python
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = decode_jwt(token)  # проверяет exp, signature
    user = await user_repo.get_by_id(payload["sub"])
    if not user.is_active: raise 401
    return user
```

### 7.4. Авторизация (RBAC)

Роли:
- `employee` — свои данные.
- `manager` — свои данные + сотрудники своего отдела + согласование отпусков своих подчинённых.
- `hr` — все сотрудники одной/нескольких «work_locations», управление больничными.
- `admin` — всё.

Реализация: декоратор/dependency `require_role(...)` + проверка контекста (например, manager может видеть сотрудника, только если он его прямой/косвенный руководитель).

```python
@router.post("/approvals/vacations/{id}/approve",
             dependencies=[Depends(require_role("manager", "admin"))])
async def approve(...):
    ...
```

Проверка владения сущностью — на уровне сервиса:
```python
async def approve_vacation(request_id, current_user):
    req = await vacation_repo.get(request_id)
    if current_user.role == "manager" and req.employee.manager_id != current_user.id:
        raise Forbidden("Not your subordinate")
    ...
```

### 7.5. Хранение паролей

- bcrypt cost=12.
- Минимум 8 символов, обязательно цифра + буква.
- При смене пароля — отзыв всех refresh.

### 7.6. Защита от перебора

- 5 неудачных попыток → блок на 15 минут.
- Логирование IP в audit_log.
- На уровне Nginx: `limit_req zone=auth burst=5 nodelay` на `/api/v1/auth/login`.

---

<a id="8-интеграции"></a>
## 8. Интеграции

### 8.1. Hikvision Central — фиксация прихода/ухода

**Поток:**
```
1. Hikvision Central отправляет вебхук → POST /api/v1/webhooks/hikvision/attendance
   Headers: X-Hikvision-Signature: hmac_sha256(body, secret)
   Body: { "personId": "...", "eventType": "entry", "eventTime": "...", "deviceId": "..." }

2. Endpoint (синхронный, мгновенный):
   - Проверка подписи и IP
   - XADD attendance:raw * personId=... eventType=... eventTime=... rawPayload=...
   - Ответ 200 OK сразу (Hikvision не любит >2 сек)

3. Celery-worker (attendance_processor):
   - XREADGROUP attendance:raw GROUP processors consumer-N COUNT 100 BLOCK 5000
   - Батчем 100 событий:
     - Матчинг hikvision_person_id → employee_id (кеш Redis hikvision_map с TTL 1 час)
     - INSERT INTO attendance_events (...) ON CONFLICT DO NOTHING
   - XACK после успешной записи

4. Каждый час (Celery Beat) → timesheet_builder:
   - Берёт events за вчера/сегодня
   - Группирует по (employee_id, date)
   - Заполняет timesheet_entries: first_entry_at = MIN(entry), last_exit_at = MAX(exit), worked_minutes, status
```

**Защита:**
- HMAC-подпись (общий secret).
- Whitelist IP-адресов сервера Hikvision (на Nginx).
- Идемпотентность: `UNIQUE (hikvision_person_id, event_at, event_type)` в БД.

**Возможный отказ:** при отказе Hikvision — события пропадают на стороне СКУД. Решение: ежедневный pull-job, который через ISAPI вытягивает события за вчера и сверяет с БД (закрывает gaps).

### 8.2. 1С:ЗУП — синхронизация

**Эндпоинты в 1С (предполагаемые, согласовать с 1С-командой):**
- `GET /hs/portal/employees?modifiedSince=...` — сотрудники
- `GET /hs/portal/departments` — отделы
- `GET /hs/portal/positions` — должности
- `GET /hs/portal/vacation-balances?year=2026` — балансы
- `GET /hs/portal/schedules?employeeId=...&from=...&to=...` — графики
- `GET /hs/portal/payroll?employeeId=...&period=2026-04` — расчётный лист

**Аутентификация:** Basic Auth + IP whitelist (со стороны 1С) ИЛИ JWT-сервисный токен.

**Стратегия sync:**

```python
@celery_app.task(bind=True, max_retries=5)
def sync_employees(self):
    try:
        last_sync = redis.get("sync:employees:last") or "1970-01-01"
        data = httpx.get(f"{ZUP}/employees?modifiedSince={last_sync}",
                         auth=..., timeout=60).json()
        for emp_data in data:
            upsert_employee(emp_data)  # ON CONFLICT (external_id_1c) DO UPDATE
        redis.set("sync:employees:last", datetime.utcnow().isoformat())
    except (httpx.TimeoutException, httpx.ConnectError) as e:
        raise self.retry(exc=e, countdown=2 ** self.request.retries * 60)
```

**Расписание (Celery Beat):**
- Каждые 15 мин: `sync_employees`, `sync_vacation_balances`.
- Каждые 30 мин: `sync_schedules`.
- Раз в сутки 02:00: `sync_departments`, `sync_positions`, `sync_work_locations`.
- On-demand с кешем: `fetch_payroll_slip(employee_id, period)`.

**Деградация:** если 1С недоступна, портал продолжает работать с последними данными. Пользователю в админке — индикатор «Последняя синхронизация: 2 часа назад».

### 8.3. Корпоративный API (если предусмотрен внешний)

Уточнение: в исходниках «вход через корпоративный API». Возможны две интерпретации:
1. **Корпоративный API — это и есть наш бэкенд** (логичнее). Тогда отдельной интеграции нет.
2. **Внешняя система аутентификации (AD, OAuth-провайдер).** Тогда `/auth/login` проксирует туда, а локально мы только сохраняем `user_id` и роль.

**Рекомендация:** на первом этапе — собственная аутентификация (вариант 1). На втором — интеграция с AD/LDAP через `python-ldap` (sync паролей при логине), либо OAuth/OIDC.

---

<a id="9-модули"></a>
## 9. Функциональные модули

### 9.1. Главная страница

**Что выводится:**
- Приветствие: «Добрый день, Алия!» + дата прописью.
- Баланс отпуска: всего / использовано / остаток + прогресс-бар.
- Сегодняшний день: время прихода, статус (на работе / ушёл / отсутствует).
- Быстрые действия: 4 кнопки (заявление на отпуск, открыть больничный, табель, история).
- Колокольчик: число непрочитанных.

**Один запрос на бэк:** `GET /api/v1/dashboard`. Возвращает агрегат, кешируется в Redis на 60 секунд для конкретного пользователя.

**Производительность:** TanStack Query с `staleTime: 30s`, `refetchInterval: 5min`. Pull-to-refresh на мобиле.

### 9.2. Отпуска

**Список:**
- Фильтры: статус (все / approved / pending / rejected), год.
- Отображение: тип, период, количество дней, статус (цветная точка + текст).
- Группировка по году.
- Бесконечная прокрутка с курсором.

**Создание заявления (мастер):**
1. Выбор типа отпуска (chips из `/vacations/types`).
2. Выбор дат (двойной date picker, валидация: не в прошлом, конец ≥ начала).
3. Превью: «Будет использовано N дней, останется M».
4. Комментарий + подтверждение.
5. POST → создаётся в статусе `pending`, нотификация руководителю.

**Бизнес-правила:**
- За 14 дней до начала минимум (предупреждение, не блок).
- Проверка пересечений с одобренными — на бэке.
- Баланс должен быть ≥ запрашиваемых дней для `paid`-типов.
- Праздничные дни не учитываются в днях отпуска (берутся из справочника `holidays`).

### 9.3. Больничные

**Открытие:**
- Дата начала (по умолчанию — сегодня, можно вчера, не больше 7 дней назад).
- Комментарий (необязательно).
- POST `/sick-leaves/open` → status=`open`, нотификация руководителю + HR.

**Закрытие:**
- Дата окончания (≥ дата начала, ≤ сегодня).
- Загрузка документа: PDF / JPG / PNG, до 10 МБ.
  - Поток: клиент → POST `/sick-leaves/upload-url` → presigned URL → PUT файл в MinIO напрямую → POST `/sick-leaves/{id}/close` с document_key.
  - Это разгружает API-сервер от больших файлов.
- Комментарий.

**Отображение:** список с фильтрами (все / открытые / закрытые), открытые — янтарной полосой.

**План (HR закрывает за сотрудника):** дополнительный POST с тем же контрактом, доступ только для роли `hr`/`admin`.

### 9.4. Табель

**View:**
- Календарь месяца, переключатель неделя/месяц.
- Ячейка дня: цветовая заливка по статусу + значок (если отпуск/больничный).
- Клик по ячейке → bottom sheet с деталями (приход/уход, итог часов).
- Итог месяца сверху: норма / отработано / сверхурочно.

**Источник данных:**
- `timesheet_entries` (заполняется Celery каждый час из `attendance_events` + графика 1С).
- Поверх накладываются `vacation_requests (approved)` и `sick_leaves`.
- Праздники из таблицы `holidays` (синхронизируется с 1С).

**Расчёт `worked_minutes`:**
```
worked_minutes = max(0, last_exit - first_entry - перерывы)
overtime = max(0, worked_minutes - schedule_minutes)
partial = worked_minutes < schedule_minutes * 0.5
```

### 9.5. Сотрудники (для manager/admin)

- Список с поиском (debounced 300 ms).
- Поиск: по ФИО (trigram-индекс), по должности.
- Visibility:
  - `manager` → только свой отдел + подчинённые отделы (рекурсивный CTE).
  - `hr` → сотрудники своих work_locations.
  - `admin` → все.
- Карточка: фото, ФИО, должность, отдел, телефон, email, руководитель.

**Postgres trigram-индекс для поиска:**
```sql
CREATE INDEX employees_fullname_trgm
  ON employees USING gin ((first_name || ' ' || last_name) gin_trgm_ops);
```

### 9.6. Согласование (manager/admin)

- Очередь: `vacation_requests.status = pending AND approver_id = current_user.id`.
- Сортировка: по дате создания (старые сверху).
- Действия: одобрить (без комментария) / отклонить (комментарий обязателен).
- При одобрении: списание дней из `vacation_balances`, нотификация сотруднику.
- При отклонении: нотификация сотруднику с причиной.

### 9.7. Уведомления

**Список:**
- Группировка по дате: «Сегодня», «Вчера», «18 мая».
- Иконка по типу (галочка, крестик, info, колокольчик).
- Клик → переход на связанный экран (заявление, больничный, SharePoint-ссылка во внешний браузер).
- Свайп влево (мобила) — отметить прочитанным.
- Бэйдж на колокольчике обновляется через polling каждые 30 секунд (или WebSocket — см. ниже).

**Push-уведомления (мобила):**
- Expo Notifications.
- Регистрация push-токена при логине: `POST /api/v1/notifications/push-token`.
- При создании уведомления в БД — Celery-задача отправляет push.

**Опционально (этап 2):** WebSocket для real-time бэйджа. Стек: FastAPI WebSocket + Redis pub/sub. Один канал на пользователя.

### 9.8. Профиль

- Шапка: фото, ФИО, должность.
- Блок «Работа»: подразделение, руководитель, табельный номер, дата приёма, место работы.
- Блок «Контакты»: email (read-only), телефон (редактируемый), Telegram (план).
- Блок «Личное» (план): дата рождения, ИИН (маскированный), семейное положение, дети.
- Блок «Образование» (план): из ЗУП + ручное добавление.
- Действия: «Сменить пароль», «Мои устройства», «Выйти».

### 9.9. Админка

**Два уровня:**

1. **SQLAdmin** на `/admin/ui` — для глубокой работы с БД (только `admin`).

2. **Кастомная админка** в основном приложении (для роли `admin` и `hr`):
   - Управление пользователями (создать / заблокировать / сбросить пароль).
   - Назначение ролей.
   - Принудительная синхронизация с 1С.
   - Просмотр audit-log.
   - Привязка HR-аккаунта к work_locations (исходное требование «один HR на Алматы/Алмалы»):
     - Таблица `hr_location_assignments(hr_id, work_location_id)`.
     - HR видит сотрудников всех привязанных к нему локаций.

---

<a id="10-pwa"></a>
## 10. PWA-конфигурация

### 10.1. Manifest

```json
{
  "name": "Корпоративный портал",
  "short_name": "Портал",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#1F2937",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "/icons/icon-512-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ],
  "orientation": "portrait"
}
```

### 10.2. Service Worker (через `next-pwa`)

**Стратегии:**
- `/_next/static/*` → CacheFirst (immutable).
- `/icons/*`, `/fonts/*` → CacheFirst, 30 дней.
- `/api/v1/dashboard`, `/api/v1/vacations`, `/api/v1/timesheet` → NetworkFirst, fallback на кеш (offline-режим read-only).
- `/api/v1/auth/*` → NetworkOnly.

### 10.3. Установка на устройство

- Кастомный prompt «Добавить на главный экран» при выполнении условий (≥2 визита, ≥1 минута).
- iOS: инструкция, как добавить через Safari (на iOS нет программного prompt).

---

<a id="11-mobile"></a>
## 11. Мобильное приложение

### 11.1. Основные особенности

- Expo SDK 50+ (managed workflow, без `eject`).
- Expo Router (file-based, аналог Next.js).
- Поддержка iOS 14+ и Android 8+.
- Push: Expo Notifications.
- Биометрия: `expo-local-authentication` (Face ID / Touch ID / отпечаток для разблокировки приложения, опционально в настройках).

### 11.2. Структура экранов

```
app/
├── (auth)/
│   ├── login.tsx
│   └── _layout.tsx
├── (app)/
│   ├── _layout.tsx           # Bottom tabs
│   ├── index.tsx             # Главная
│   ├── vacations/
│   │   ├── index.tsx
│   │   ├── new.tsx
│   │   └── [id].tsx
│   ├── sick-leaves/
│   ├── timesheet.tsx
│   ├── employees/
│   ├── approvals.tsx         # Только manager/admin
│   ├── notifications.tsx
│   └── profile.tsx
└── _layout.tsx               # Root: auth guard, theme, query client
```

### 11.3. Переиспользование с вебом

- `packages/api-client` — TS-клиент, общий.
- `packages/shared-types` — типы.
- `packages/ui-core` — хуки (`useVacations`, `useDashboard`, ...), Zustand-сторы, утилиты (`formatRelativeDate`, `calculateWorkdays`).
- Различаются только сами компоненты (web использует Tailwind + DOM, mobile — RN-компоненты).

### 11.4. Сборка и публикация

- **EAS Build** (Expo Application Services) для билдов в облаке.
- Профили: `development`, `preview` (internal distribution), `production`.
- Fastlane: автоматическая публикация в App Store / Google Play через GitHub Actions при push в `main` с тегом `mobile-v*`.
- OTA-обновления через `expo-updates` для не-нативных изменений.

---

<a id="12-производительность"></a>
## 12. Производительность и оптимизация

### 12.1. База данных

**Индексы (ключевые):**
- `attendance_events (employee_id, event_at DESC)` — главный запрос «события сотрудника за период».
- `attendance_events (processed) WHERE processed = false` — частичный, для очереди обработки.
- `vacation_requests (employee_id, status)`, `vacation_requests (approver_id, status)`.
- `notifications (employee_id, created_at DESC)`, `notifications (employee_id) WHERE read_at IS NULL`.
- `timesheet_entries (employee_id, date)` UNIQUE.
- Trigram-индексы на `employees.full_name` и `positions.name` для поиска.

**Партиционирование:**
- `attendance_events` — по месяцам (`PARTITION BY RANGE (event_at)`).
- `audit_log` — по месяцам.
- `notifications` — рассмотреть после 1М записей.

**Pooling:**
- `asyncpg` connection pool: min=10, max=30 на инстанс API.
- `pgbouncer` в режиме transaction pooling, если выйдем за 2 инстанса API.

**Настройки Postgres** (для 16 GB RAM):
```
shared_buffers = 4GB
effective_cache_size = 12GB
work_mem = 32MB
maintenance_work_mem = 1GB
random_page_cost = 1.1     # NVMe
max_connections = 200
checkpoint_completion_target = 0.9
wal_buffers = 16MB
```

**N+1 защита:**
- Все списки используют `selectinload` / `joinedload` (SQLAlchemy 2.0 async).
- Pydantic-схемы заранее знают, какие отношения нужны → автоматическая подгрузка.

### 12.2. Кеширование (Redis)

| Что | TTL | Ключ |
|---|---|---|
| `/dashboard` ответ | 60 сек | `cache:dashboard:{user_id}` |
| Справочники (типы отпусков, отделы) | 30 мин | `cache:vacation_types`, `cache:departments` |
| Профиль сотрудника | 5 мин | `cache:employee:{id}` |
| `hikvision_person_id → employee_id` | 1 час | `map:hikvision:{person_id}` |
| Расчётный листок | 1 час | `cache:payroll:{emp}:{period}` |
| Число непрочитанных уведомлений | 30 сек | `cache:unread:{user_id}` |

**Инвалидация:**
- При записи в сущность → `DEL cache:*:{id}` через сервисный слой.
- Не используем write-through; используем cache-aside.

### 12.3. API-уровень

- **Sparse fieldsets** для тяжёлых ресурсов: `?fields=id,name,department`.
- **Single-flight** на тяжёлых запросах через Redis lock (дубли в течение 5 сек ждут одного результата).
- **Response compression:** gzip на Nginx для всех application/json.
- **HTTP/2** на Nginx.
- **ETag** для редко меняющихся справочников.

### 12.4. Фронт

- Server Components в Next.js для статичных страниц (профиль, справочники).
- Динамические импорты тяжёлых компонентов (календарь табеля, графики).
- Image optimization через `next/image`.
- Prefetch на hover/visible для основных маршрутов.
- TanStack Query: `staleTime` и `cacheTime` подобраны по типу данных.
- Bundle splitting: vendor / app / route-level.
- Цель: First Contentful Paint < 1.5s, Time to Interactive < 3s на медленном 4G.

### 12.5. Мобильное приложение

- Lazy loading экранов через Expo Router.
- `react-native-fast-image` для аватаров с кешем.
- FlashList вместо FlatList для длинных списков (события, уведомления).
- TanStack Query persistent cache через `expo-file-system`.

### 12.6. Пиковая нагрузка утром

**Сценарий:** 08:00–09:30, 3 000 сотрудников приходят, открывают приложение, проверяют табель.

**Бутылочные горлышки и решения:**
- Hikvision-вебхуки → Redis Stream, не пишут напрямую в БД (см. п.1.4).
- `/dashboard` → Redis cache 60 сек, разгружает БД.
- Если уведомления через polling — на этот час увеличить interval до 60 сек.
- Nginx с `keepalive` к upstream, чтобы не пересоздавать TCP.

**Расчёт нагрузки:**
- Пиковая RPS на API: 3 000 пользователей × 5 запросов / 90 мин = ~3 RPS среднее, пики до 30–50 RPS.
- FastAPI + uvicorn в 4 workers легко выдаёт 500+ RPS на 4 vCPU.
- Запас по производительности: ~10×.

---

<a id="13-масштабируемость"></a>
## 13. Масштабируемость

### 13.1. Горизонтальное масштабирование

**API:** stateless. Любое число инстансов за Nginx (round-robin или least_conn).
- Состояние сессии — в Redis (refresh-токены) и в JWT (access).
- Файлы — в MinIO (общее хранилище).

**Celery:** добавление воркеров — параметр `--concurrency` или новый процесс.

**Postgres:** primary + read replica → distribute read-heavy endpoints (профили, табель).
- Используем `sqlalchemy.ext.asyncio` с двумя session-factory: `read_session`, `write_session`.

**Redis:** при росте — Redis Cluster или Sentinel.

### 13.2. Что НЕ стоит делать сейчас

- Микросервисы. До 50 000 пользователей — модульный монолит выигрывает.
- Kubernetes. Docker Compose + Ansible покрывают до 10 серверов.
- Kafka. Redis Streams хватает для текущих объёмов.

### 13.3. Точки роста и план

| Рубеж | Что менять |
|---|---|
| 5 000 пользователей | Текущая архитектура, single VPS 8/16 |
| 10 000 | App + DB на разные VPS, добавить read replica |
| 20 000 | 2 инстанса API + pgbouncer, Redis Sentinel |
| 50 000+ | Выделить отдельные сервисы (notifications, attendance), Kubernetes |

---

<a id="14-безопасность"></a>
## 14. Безопасность

Юридические и compliance-требования по персональным данным, больничным документам, ИИН, табелю/Hikvision, 1С, трансграничным передачам, срокам хранения и электронным согласованиям вынесены в отдельный документ: [`docs/LEGAL_COMPLIANCE.md`](docs/LEGAL_COMPLIANCE.md).

### 14.1. OWASP Top 10 — закрытие

- **Injection:** только параметризованные запросы через SQLAlchemy. ORM-инъекций избегаем.
- **Broken Auth:** см. п.7. Bcrypt, ротация refresh, лок после 5 попыток.
- **Sensitive Data Exposure:**
  - TLS 1.2+ обязательно (HSTS).
  - Пароли только bcrypt.
  - ИИН шифруется на уровне приложения (Fernet/AES-GCM, ключ в Vault или env).
  - В логах ИИН маскируется (`123*****901`).
- **XXE:** не парсим XML на входе от пользователей.
- **Broken Access Control:** RBAC + проверка владения сущностью на каждом эндпоинте.
- **Security Misconfiguration:** OpenAPI/docs отключены в prod, debug=False, Sentry не отправляет PII.
- **XSS:** React по умолчанию экранирует; запрет `dangerouslySetInnerHTML` (ESLint-правило).
- **CSRF:** для cookie-сессий — `SameSite=Lax`, double-submit-token для критичных операций.
- **Vulnerable Components:** Dependabot / Renovate, еженедельный аудит `pip-audit`, `pnpm audit`.
- **Insufficient Logging:** structlog + audit_log на все критичные действия.

### 14.2. Сеть

- Nginx — единственная точка входа.
- API, БД, Redis, MinIO — на private network (Docker network или WireGuard).
- Postgres не доступен снаружи (`listen_addresses = '127.0.0.1, 172.x.x.x'`).
- Firewall: только 22 (SSH), 80, 443 наружу.
- SSH: только по ключу, fail2ban, отдельный пользователь без sudo для приложения.

### 14.3. Секреты

- Все секреты через переменные окружения, не в репо.
- `.env.production` — на сервере с правами 600.
- На большом масштабе — HashiCorp Vault или Doppler.

### 14.4. Audit log

- Каждое действие управляющего характера: логин/выход, изменение роли, одобрение/отклонение отпуска, закрытие больничного, ручное изменение баланса.
- Поля: actor, action, target, before/after diff, IP, user-agent, timestamp.
- Доступ к audit_log — только admin.
- Retention: 3 года.

### 14.5. Бэкапы и DR

- Daily pg_dump → S3 (offsite, в другой регион).
- WAL archiving (wal-g) → PITR до любой точки за 7 дней.
- MinIO репликация в S3.
- Тестирование восстановления — раз в квартал.
- Runbook восстановления в репозитории.

---

<a id="15-devops"></a>
## 15. Инфраструктура и DevOps

### 15.1. Docker Compose (production)

```yaml
services:
  nginx:
    image: nginx:1.25-alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./certs:/etc/letsencrypt:ro
      - static:/static:ro
    depends_on: [api]

  api:
    image: ghcr.io/company/portal-api:${VERSION}
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
    env_file: .env.production
    depends_on: [postgres, redis]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s

  celery-worker:
    image: ghcr.io/company/portal-api:${VERSION}
    command: celery -A app.workers.celery_app worker --concurrency=8 -Q default,sync,attendance
    env_file: .env.production
    depends_on: [redis, postgres]

  celery-beat:
    image: ghcr.io/company/portal-api:${VERSION}
    command: celery -A app.workers.celery_app beat
    env_file: .env.production
    depends_on: [redis]

  postgres:
    image: postgres:16-alpine
    volumes: [pgdata:/var/lib/postgresql/data]
    environment:
      POSTGRES_DB: portal
      POSTGRES_USER_FILE: /run/secrets/db_user
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets: [db_user, db_password]

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 4gb --maxmemory-policy allkeys-lru --appendonly yes
    volumes: [redisdata:/data]

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    volumes: [miniodata:/data]
    env_file: .env.minio

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - promdata:/prometheus

  grafana:
    image: grafana/grafana:latest
    volumes: [grafanadata:/var/lib/grafana]

  loki:
    image: grafana/loki:latest
    volumes: [lokidata:/loki]

volumes:
  pgdata: {}
  redisdata: {}
  miniodata: {}
  promdata: {}
  grafanadata: {}
  lokidata: {}
  static: {}

secrets:
  db_user:
    file: ./secrets/db_user.txt
  db_password:
    file: ./secrets/db_password.txt
```

### 15.2. Nginx (фрагмент)

```nginx
upstream api_backend {
    least_conn;
    server api:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

server {
    listen 443 ssl http2;
    server_name portal.company.kz;

    ssl_certificate     /etc/letsencrypt/live/.../fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/.../privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    client_max_body_size 12m;
    gzip on;
    gzip_types application/json text/css application/javascript;

    location /api/v1/auth/login {
        limit_req zone=login burst=3 nodelay;
        proxy_pass http://api_backend;
        include /etc/nginx/proxy_params.conf;
    }

    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://api_backend;
        include /etc/nginx/proxy_params.conf;
    }

    location / {
        # PWA: статика Next.js
        root /static/web;
        try_files $uri $uri/ /index.html;
    }
}
```

### 15.3. CI/CD (GitHub Actions)

**Pipeline `api-ci.yml`:**
1. Push в `main` или PR в `main`, изменения в `apps/api/**`.
2. Установка зависимостей, `ruff check`, `mypy`, `pytest`.
3. Сборка Docker-образа, тег `:sha-...` и `:latest`.
4. Push в GHCR.
5. (Только main) SSH в prod, `docker compose pull api && docker compose up -d api celery-worker`.
6. Healthcheck. Если падает — автоматический rollback на предыдущий тег.

**Pipeline `web-ci.yml`:**
1. Lint, typecheck, тесты.
2. `pnpm build`.
3. Деплой статики на сервер (rsync) или CDN.

**Pipeline `mobile-ci.yml`:**
1. Lint, typecheck.
2. На теге `mobile-v*` → `eas build --profile production --platform all`.
3. Fastlane → загрузка в TestFlight / Google Play Internal Testing.
4. Ручной promotion в production.

### 15.4. Окружения

| Окружение | Назначение | Хост |
|---|---|---|
| local | Разработка | docker-compose.dev.yml |
| staging | Тестирование, превью | staging.portal.company.kz |
| production | Боевое | portal.company.kz |

Каждое — своя БД, свои секреты, свои данные.

---

<a id="16-мониторинг"></a>
## 16. Мониторинг и логирование

### 16.1. Метрики (Prometheus + Grafana)

**Прикладные метрики (через `prometheus-fastapi-instrumentator`):**
- `http_requests_total{method, path, status}`.
- `http_request_duration_seconds{path}` — histogram, p50/p95/p99.
- `db_pool_connections_active`.
- `celery_task_duration{task}`.
- `celery_task_failures{task}`.
- `hikvision_events_processed_total`, `hikvision_events_failed_total`.
- `onec_sync_last_success_timestamp{type}`.

**Системные:** node_exporter (CPU, RAM, disk, network).
**БД:** postgres_exporter (connections, slow queries, locks).
**Redis:** redis_exporter.

**Дашборды Grafana (готовим заранее):**
1. API overview: RPS, latency, errors.
2. Database: queries, locks, replication lag.
3. Celery: tasks per minute, failures, queue length.
4. Hikvision pipeline: events/min, lag, failures.
5. 1C sync: время с последней успешной синхронизации, ошибки.

### 16.2. Алерты (Grafana Alerting / Alertmanager)

- API p99 latency > 2s в течение 5 мин → warning.
- API 5xx rate > 1% в течение 5 мин → critical.
- Celery task failure rate > 5% → critical.
- Hikvision events lag > 5 мин → warning.
- 1С sync не было > 2 часа → warning, > 24 часа → critical.
- Disk usage > 80% → warning, > 90% → critical.
- pg_dump старше 24 часов → critical.

Каналы: Telegram-бот + email + PagerDuty (по желанию).

### 16.3. Логирование

- **Формат:** JSON через `structlog`, поля: `timestamp, level, logger, event, request_id, user_id, ...`.
- **Сбор:** Promtail (читает docker-логи) → Loki → Grafana.
- **Retention:** 30 дней в Loki, важные события — в audit_log БД (3 года).
- **Request tracing:** middleware добавляет `X-Request-ID` (UUID v7), пробрасывает в логи и в response header.

### 16.4. Sentry

- Все необработанные исключения API → Sentry.
- Source maps для веба и мобилы.
- Release tracking по git SHA.
- Performance monitoring (sample rate 0.1 в prod).
- PII scrubbing включён.

### 16.5. Healthchecks

- `GET /health` — простой 200 OK.
- `GET /health/ready` — проверка БД, Redis, MinIO. Используется Nginx upstream и Docker healthcheck.

---

<a id="17-этапы"></a>
## 17. План разработки по этапам

### Этап 0 — Подготовка (1–2 недели)
- Инициализация монорепо, базовая структура.
- Docker Compose dev-окружение (Postgres, Redis, MinIO).
- CI-скелет (lint, test, build).
- Дизайн-система: палитра, типографика, базовые компоненты.

### Этап 1 — MVP бэкенд (3–4 недели)
- Auth (JWT + refresh).
- Модели данных: users, employees, departments, positions.
- API: `/auth/*`, `/employees`, `/dashboard` (упрощённый).
- Базовая админка SQLAdmin.
- Тесты (≥ 70% покрытие критичных модулей).

### Этап 2 — Отпуска и согласование (3–4 недели)
- Модели: vacation_*.
- API: создание, список, согласование.
- Бизнес-правила (балансы, пересечения).
- Уведомления (in-app, без push).

### Этап 3 — Веб-фронтенд MVP (3–4 недели)
- Аутентификация.
- Главная, профиль.
- Отпуска (список, создание).
- Согласование.
- PWA-конфигурация.

### Этап 4 — Больничные + Табель (3–4 недели)
- Sick leaves API + UI.
- Загрузка документов через MinIO.
- Hikvision интеграция: вебхук, обработка через Redis Stream.
- Timesheet builder (Celery).
- Табель UI.

### Этап 5 — 1С интеграция (2–3 недели)
- Sync-задачи (employees, departments, balances, schedules).
- Расчётный листок (on-demand).
- Праздники.

### Этап 6 — Мобильное приложение (4–5 недель)
- Все экраны MVP (главная, отпуска, больничные, табель, уведомления, профиль).
- Push-уведомления.
- Биометрия.
- EAS Build + Fastlane.

### Этап 7 — Безопасность и нагрузка (2 недели)
- Аудит безопасности.
- Нагрузочное тестирование (k6 / Locust).
- Тюнинг Postgres и Nginx.
- DR-учения.

### Этап 8 — Планируемый функционал (по приоритету)
- Командировки.
- Налоговый вычет.
- Материальная помощь.
- Образование и сертификаты.
- Семейное положение и дети.
- SharePoint-ссылки в уведомлениях.
- Статус сотрудника.
- HR-привязка к work_locations.

**Общая длительность MVP (до этапа 7 включительно):** ~5–6 месяцев командой из:
- 2 backend-разработчика,
- 2 frontend-разработчика (1 web, 1 mobile, переключающиеся),
- 1 DevOps / fullstack (часть времени),
- 1 дизайнер (часть времени),
- 1 PM / тестировщик.

---

## Приложение А. Чеклист готовности к production

- [ ] Все секреты вынесены в env, не в коде.
- [ ] TLS-сертификаты установлены, HSTS включён.
- [ ] Бэкапы настроены и протестированы (восстановление).
- [ ] Мониторинг и алерты работают.
- [ ] Sentry получает события.
- [ ] Rate limiting проверен.
- [ ] OWASP-сканер пройден (OWASP ZAP / nuclei).
- [ ] Нагрузочный тест: 200 RPS в течение 10 мин без деградации.
- [ ] Документация API в OpenAPI, runbook для инцидентов.
- [ ] Все миграции применяются на чистой БД без ошибок.
- [ ] Логи структурированы и попадают в Loki.
- [ ] DR-runbook протестирован.
- [ ] Аудит-лог пишется для всех критичных действий.
- [ ] Hikvision и 1С интеграции протестированы на стейдже с реальными API.

## Приложение Б. Открытые вопросы для уточнения

1. **Корпоративный API:** наша внутренняя система или внешняя (AD/LDAP/OIDC)?
2. **Контракт 1С:** есть ли готовые HTTP-сервисы или их нужно разрабатывать со стороны 1С?
3. **Hikvision:** какая версия, поддерживает ли вебхуки или нужно полить через ISAPI?
4. **Multi-tenancy:** один портал на компанию, или несколько юрлиц с изоляцией данных?
5. **Языки интерфейса:** русский, казахский, английский — какие нужны?
6. **Доступность извне:** только из офисной сети (VPN) или из интернета?
7. **Сторы:** App Store + Google Play, или ещё RuStore / AppGallery?
8. **Подписание сертификатов на iOS:** есть ли Apple Developer аккаунт компании?

---

**Конец документа.**

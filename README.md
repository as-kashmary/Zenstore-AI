# ZenStore AI — System Architecture Document

---

## 1. Overview

ZenStore AI is a RESTful backend service that accepts raw product data, enriches it with LLM-generated marketing descriptions, and processes bulk uploads asynchronously. It is built on FastAPI with async SQLAlchemy, secured with JWT authentication, and documented with Swagger (OpenAPI).

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                             │
│          (React/Vue Frontend  |  Swagger UI  |  API Clients)    │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS / REST
┌──────────────────────────▼──────────────────────────────────────┐
│                      API GATEWAY LAYER                          │
│                   FastAPI Application                           │
│    ┌────────────┐  ┌─────────────┐  ┌────────────────────────┐ │
│    │   Auth     │  │  Products   │  │     Batch Upload        │ │
│    │  Router    │  │   Router    │  │       Router            │ │
│    └────────────┘  └─────────────┘  └────────────────────────┘ │
│    ┌──────────────────────────────────────────────────────────┐ │
│    │           Middleware (JWT Auth  |  Perf Logger)          │ │
│    └──────────────────────────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────────┘
                           │
          ┌────────────────┼───────────────────┐
          │                │                   │
┌─────────▼──────┐  ┌──────▼───────┐  ┌───────▼────────┐
│  Service Layer │  │  Task Queue  │  │  Cache Layer   │
│                │  │  (Celery +   │  │   (Redis)      │
│ - AuthService  │  │   Redis)     │  │                │
│ - ProductSvc   │  │              │  │ - Product data │
│ - LLMService   │  │ - AI Task    │  │ - User session │
│ - BatchService │  │ - ImgTask    │  │ - LLM results  │
└────────┬───────┘  └──────┬───────┘  └────────────────┘
         │                 │
┌────────▼─────────────────▼──────────────────────────────────────┐
│                    DATA ACCESS LAYER                            │
│                  (Async SQLAlchemy ORM)                         │
│         Repositories: UserRepo | ProductRepo | BatchRepo        │
└────────────────────────┬────────────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
┌─────────▼──────────┐       ┌──────────▼──────────┐
│   PostgreSQL DB    │       │   External LLM API   │
│  (Primary Store)   │       │  (Groq / Gemini /    │
│                    │       │   OpenAI)            │
└────────────────────┘       └─────────────────────┘
```

---

## 3. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Web Framework** | FastAPI | Async REST API, automatic OpenAPI/Swagger |
| **ORM** | SQLAlchemy 2.x (async) | Async database access with `asyncpg` |
| **Database** | PostgreSQL | Primary persistent store |
| **Task Queue** | Celery | Background AI & image processing tasks |
| **Message Broker** | Redis | Celery broker + result backend |
| **Cache** | Redis | LLM response caching, product cache |
| **LLM API** | Groq (recommended) / Gemini / OpenAI | AI description generation |
| **Auth** | JWT (python-jose) + bcrypt | Authentication & authorization |
| **API Docs** | Swagger UI (built into FastAPI) | Interactive API documentation |
| **Validation** | Pydantic v2 | Request/response schemas |
| **Migrations** | Alembic | Database schema versioning |
| **File Parsing** | Python Generators + csv/json stdlib | Memory-efficient batch file reading |
| **Config** | Pydantic BaseSettings + `.env` | Environment-based configuration |
| **Testing** | pytest + pytest-asyncio + httpx | Async-compatible test suite |
| **Containerization** | Docker + Docker Compose | Local dev & deployment |

---

## 4. Project File Structure

```
zenstore-ai/
│
├── docker-compose.yml               # PostgreSQL + Redis + App + Celery worker
├── Dockerfile
├── .env.example
├── alembic.ini
├── requirements.txt
├── README.md
│
├── alembic/
│   └── versions/                    # Migration files
│
├── app/
│   ├── main.py                      # FastAPI app factory, router registration
│   ├── config.py                    # Pydantic BaseSettings (env vars)
│   ├── dependencies.py              # Shared FastAPI dependencies (DB session, current user)
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py              # /auth endpoints
│   │   │   ├── products.py          # /products endpoints
│   │   │   └── batch.py             # /batch endpoints
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py              # JWT creation, password hashing
│   │   ├── decorators.py            # @performance_logger custom decorator
│   │   └── exceptions.py            # Custom HTTP exceptions
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py                  # SQLAlchemy async engine & session factory
│   │   └── base_class.py            # Declarative base class
│   │
│   ├── models/                      # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── product.py
│   │   └── batch_job.py
│   │
│   ├── schemas/                     # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── product.py
│   │   └── batch.py
│   │
│   ├── repositories/                # Data access layer (OOP-based)
│   │   ├── __init__.py
│   │   ├── base.py                  # Generic async CRUD base class
│   │   ├── user_repository.py
│   │   ├── product_repository.py
│   │   └── batch_repository.py
│   │
│   ├── services/                    # Business logic layer (OOP classes)
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── product_service.py
│   │   ├── llm_service.py           # LLM API calls + caching
│   │   └── batch_service.py         # Generator-based file parser
│   │
│   ├── tasks/                       # Celery task definitions
│   │   ├── __init__.py
│   │   ├── celery_app.py            # Celery app instance
│   │   ├── ai_tasks.py              # LLM generation task
│   │   └── image_tasks.py           # Simulated image processing task
│   │
│   └── cache/
│       ├── __init__.py
│       └── redis_client.py          # Redis cache wrapper (get/set/invalidate)
│
└── tests/
    ├── conftest.py                   # Async test fixtures
    ├── test_auth.py
    ├── test_products.py
    └── test_batch.py
```

---

## 5. Database Schema

### `users`
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| email | VARCHAR (unique) | |
| hashed_password | VARCHAR | bcrypt |
| is_active | BOOLEAN | default true |
| created_at | TIMESTAMP | |

### `products`
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| owner_id | UUID (FK → users.id) | Row-level ownership |
| name | VARCHAR | Raw input |
| description | TEXT | LLM-generated |
| category | VARCHAR | LLM-generated |
| status | ENUM | `pending`, `processing`, `done`, `failed` |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### `batch_jobs`
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| owner_id | UUID (FK → users.id) | |
| filename | VARCHAR | |
| total_rows | INTEGER | |
| processed_rows | INTEGER | |
| status | ENUM | `queued`, `processing`, `done`, `failed` |
| created_at | TIMESTAMP | |

---

## 6. API Endpoints

### Auth — `/api/v1/auth`

| Method | Path | Description | Auth Required |
|---|---|---|---|
| `POST` | `/register` | Register new user | No |
| `POST` | `/login` | Login, receive JWT access + refresh tokens | No |
| `POST` | `/refresh` | Refresh access token | Yes (refresh token) |
| `POST` | `/logout` | Invalidate refresh token | Yes |
| `GET` | `/me` | Get current authenticated user profile | Yes |

### Products — `/api/v1/products`

| Method | Path | Description | Auth Required |
|---|---|---|---|
| `GET` | `/` | List all products (paginated, owner-scoped) | Yes |
| `GET` | `/{product_id}` | Get single product by ID | Yes |
| `POST` | `/` | Add single product → triggers async AI enrichment | Yes |
| `PUT` | `/{product_id}` | Update product fields | Yes |
| `DELETE` | `/{product_id}` | Delete product | Yes |
| `GET` | `/{product_id}/status` | Poll AI processing status | Yes |

### Batch — `/api/v1/batch`

| Method | Path | Description | Auth Required |
|---|---|---|---|
| `POST` | `/upload` | Upload CSV/JSON file → queues background job | Yes |
| `GET` | `/jobs` | List all batch jobs for current user | Yes |
| `GET` | `/jobs/{job_id}` | Get status and progress of a batch job | Yes |
| `DELETE` | `/jobs/{job_id}` | Cancel/delete a batch job | Yes |

---

## 7. Key Design Patterns

### 7.1 OOP — Repository & Service Pattern
Each domain (User, Product, Batch) has a `Repository` class (data access) and a `Service` class (business logic), cleanly separated. A generic `BaseRepository` provides async CRUD operations that all repositories inherit.

### 7.2 Custom Decorator — `@performance_logger`
A reusable decorator defined in `core/decorators.py` that wraps any service or endpoint function, logs execution time, function name, and arguments to the application logger. Applied on critical paths like LLM calls and DB queries.

```python
# Example usage
@performance_logger
async def generate_description(self, product_name: str) -> dict: ...
```

### 7.3 Python Generators — Batch File Parsing
`batch_service.py` uses a generator function to stream-parse large CSV or JSON batch files row-by-row, preventing memory exhaustion for large uploads.

```python
def parse_csv_rows(filepath: str):
    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row  # one product at a time
```

### 7.4 Caching Layer — Redis
`LLMService` checks Redis before calling the external LLM API. Cache key is derived from a hash of the product name. TTL is configurable (default: 24 hours). Product list responses are also cached per user.

### 7.5 Background Tasks — Celery + Redis
- `POST /products/` returns immediately with `status: pending` and a product ID.
- A Celery task is dispatched to call the LLM, update the DB record, and simulate image processing (sleep + status update).
- The frontend can poll `GET /products/{id}/status` until `status: done`.

### 7.6 Data Isolation — Row-Level Ownership
Every query in `ProductRepository` and `BatchRepository` is filtered by `owner_id = current_user.id`. Users can never access another user's data.

---

## 8. Request Flow Diagrams

### Single Product Addition
```
POST /products/
      │
      ▼
JWT Middleware validates token
      │
      ▼
ProductService.create_product()
  → Saves product (status: pending) to DB
  → Dispatches Celery task: generate_ai_description.delay(product_id)
  → Returns 202 Accepted with product_id
      │
      ▼ (async, in Celery worker)
ai_tasks.generate_ai_description(product_id)
  → Check Redis cache (by product name hash)
  → If miss: Call LLM API → store result in Redis
  → Update product record: description, category, status=done
  → Dispatch image_tasks.simulate_image_processing(product_id)
```

### Batch Upload
```
POST /batch/upload (multipart/form-data)
      │
      ▼
Save file to temp storage
Create BatchJob record (status: queued)
Dispatch Celery task: process_batch_file.delay(job_id, filepath)
Return 202 with job_id
      │
      ▼ (in Celery worker)
Generator reads file row by row
For each row:
  → Create product (status: pending)
  → Dispatch individual ai_task
  → Increment BatchJob.processed_rows
Update BatchJob.status = done
```

---

## 9. Security Design

- Passwords hashed with **bcrypt** (no plaintext storage)
- **JWT access tokens** (short TTL: 15–30 min) + **refresh tokens** (longer TTL: 7 days) stored in DB or Redis for revocation
- All routes (except `/auth/register` and `/auth/login`) protected by `Depends(get_current_user)`
- All DB queries scoped to `current_user.id` — no cross-user data leakage
- Input validated by Pydantic before any DB or LLM interaction
- LLM API keys stored in `.env`, never exposed in responses

---

## 10. Development Roadmap

### Phase 1 — Foundation (Days 1–2)
- [ ] Set up project structure, virtual environment, `requirements.txt`
- [ ] Configure Docker Compose (PostgreSQL + Redis)
- [ ] Implement `config.py` with Pydantic BaseSettings
- [ ] Set up async SQLAlchemy engine + session factory
- [ ] Create all ORM models + Alembic migrations
- [ ] Implement `BaseRepository` with generic async CRUD

### Phase 2 — Authentication (Day 3)
- [ ] Build `UserRepository` and `AuthService`
- [ ] Implement JWT creation, validation, refresh logic in `core/security.py`
- [ ] Build `/auth` router: register, login, refresh, logout, me
- [ ] Write `get_current_user` FastAPI dependency
- [ ] Test auth flow end-to-end with Swagger UI

### Phase 3 — Products Core (Days 4–5)
- [ ] Build `ProductRepository` (owner-scoped queries)
- [ ] Build `ProductService` (create, list, get, update, delete)
- [ ] Implement `@performance_logger` decorator
- [ ] Build `/products` router with all endpoints
- [ ] Wire up Swagger request/response schemas

### Phase 4 — LLM & Caching (Day 6)
- [ ] Build `LLMService` with Redis cache check-before-call logic
- [ ] Integrate Groq/Gemini/OpenAI API
- [ ] Prompt engineer the 2-sentence description + category output
- [ ] Unit test LLM service with mocked API responses

### Phase 5 — Background Tasks (Day 7)
- [ ] Set up `celery_app.py` with Redis broker
- [ ] Implement `ai_tasks.generate_ai_description`
- [ ] Implement `image_tasks.simulate_image_processing`
- [ ] Wire `POST /products/` to dispatch tasks and return `202`
- [ ] Implement status polling endpoint

### Phase 6 — Batch Processing (Days 8–9)
- [ ] Implement generator-based CSV/JSON parser in `BatchService`
- [ ] Build `BatchRepository` and `BatchJob` tracking logic
- [ ] Implement `process_batch_file` Celery task
- [ ] Build `/batch` router with upload + job status endpoints
- [ ] Test with large CSV files (1000+ rows)

### Phase 7 — Quality & Hardening (Day 10)
- [ ] Write `pytest` test suite (auth, products, batch)
- [ ] Add error handling and custom exceptions throughout
- [ ] Validate all edge cases (duplicate emails, invalid tokens, missing files)
- [ ] Review and polish Swagger documentation (descriptions, examples)
- [ ] Final Docker Compose run — full system smoke test

---

## 11. Environment Variables (`.env.example`)

```env
# App
APP_ENV=development
SECRET_KEY=your-super-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/zenstore

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM
LLM_PROVIDER=groq         # groq | openai | gemini
GROQ_API_KEY=your-groq-api-key
OPENAI_API_KEY=your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key

# Cache
LLM_CACHE_TTL_SECONDS=86400
```

---

*Architecture version 1.0 — ZenStore AI*

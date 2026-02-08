# Task Tracker - Bug Tracking API

A production-ready backend API for internal bug tracking, built with FastAPI, PostgreSQL, and Redis.

---

## Documentation

| Document                                 | Description                                                       |
| ---------------------------------------- | ----------------------------------------------------------------- |
| [Complete Guide](docs/COMPLETE_GUIDE.md) | Full documentation - setup, API reference, architecture, security |
| [Implementation Plan](.claude/plan.md)   | Original design decisions and architecture rationale              |

### Quick Navigation

- **New to the project?** Start with [Complete Guide](docs/COMPLETE_GUIDE.md)
- **Want to understand the code?** See [Where to Start Reading](#where-to-start-reading-the-code)
- **Setting up locally?** Jump to [Quick Start](#quick-start)
- **API reference?** See [Complete Guide - API Reference](docs/COMPLETE_GUIDE.md#6-api-reference)

---

## Architecture Overview

### Technology Stack

| Component      | Technology     | Justification                                       |
| -------------- | -------------- | --------------------------------------------------- |
| Framework      | FastAPI        | Async-first, automatic OpenAPI docs, built-in DI    |
| Database       | PostgreSQL     | ACID compliance, UUID support, robust enums         |
| ORM            | SQLAlchemy 2.0 | Async support, type hints, powerful queries         |
| Cache/Sessions | Redis          | Token blacklisting, rate limiting, high performance |
| Auth           | JWT (RS256)    | Asymmetric signing, stateless, secure               |
| Hashing        | Argon2         | Password Hashing Competition winner                 |

### Design Patterns

- **Repository Pattern**: Abstracts data access layer for testability
- **Service Layer**: Encapsulates business logic and orchestrates repositories
- **Strategy Pattern**: Interchangeable permission checking algorithms
- **State Machine**: Issue status transitions with validation
- **Dependency Injection**: FastAPI's built-in DI for loose coupling

### Layered Architecture

```
┌─────────────────────────────────────┐
│       API Layer (Routers)           │  ← HTTP request/response
├─────────────────────────────────────┤
│       Middleware Layer              │  ← Auth, Rate Limit, Audit
├─────────────────────────────────────┤
│       Service Layer (Business)      │  ← Business logic, validation
├─────────────────────────────────────┤
│       Repository Layer (Data)       │  ← Database operations
├─────────────────────────────────────┤
│       Model Layer (ORM)             │  ← SQLAlchemy models
└─────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Local Development

1. **Clone and setup**

   ```bash
   git clone <repository-url>
   cd task-tracker
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   ```

2. **Generate RSA keys for JWT**

   ```bash
   python scripts/generate_keys.py
   ```

3. **Configure environment**

   ```bash
   cp .env.example .env
   # Edit .env with your database and Redis URLs
   ```

4. **Run database migrations**

   ```bash
   alembic upgrade head
   ```

5. **Seed sample data (optional)**

   ```bash
   python scripts/seed_data.py
   ```

6. **Start the server**

   ```bash
   uvicorn app.main:app --reload
   ```

7. **Access API documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Docker Development (Recommended)

```bash
# 1. Generate JWT keys
mkdir -p keys
openssl genrsa -out keys/private_key.pem 2048
openssl rsa -in keys/private_key.pem -pubout -out keys/public_key.pem

# 2. Start all services
docker-compose up -d

# 3. Run migrations
docker-compose exec api alembic upgrade head

# 4. Seed sample data (optional)
docker-compose exec api python scripts/seed_data.py

# 5. Verify it's working
curl http://localhost:8000/health

# Access Swagger UI: http://localhost:8000/docs
```

## API Documentation

### Authentication

| Method | Endpoint                | Description          |
| ------ | ----------------------- | -------------------- |
| POST   | `/api/v1/auth/register` | Register new user    |
| POST   | `/api/v1/auth/login`    | Login and get tokens |
| POST   | `/api/v1/auth/refresh`  | Refresh access token |
| POST   | `/api/v1/auth/logout`   | Invalidate tokens    |
| GET    | `/api/v1/auth/me`       | Get current user     |

### Projects

| Method | Endpoint                | Description                   |
| ------ | ----------------------- | ----------------------------- |
| GET    | `/api/v1/projects`      | List projects                 |
| POST   | `/api/v1/projects`      | Create project (Manager+)     |
| GET    | `/api/v1/projects/{id}` | Get project details           |
| PATCH  | `/api/v1/projects/{id}` | Update project (Owner/Admin)  |
| DELETE | `/api/v1/projects/{id}` | Archive project (Owner/Admin) |

### Issues

| Method | Endpoint                       | Description         |
| ------ | ------------------------------ | ------------------- |
| GET    | `/api/v1/projects/{id}/issues` | List project issues |
| POST   | `/api/v1/projects/{id}/issues` | Create issue        |
| GET    | `/api/v1/issues/{id}`          | Get issue details   |
| PATCH  | `/api/v1/issues/{id}`          | Update issue        |
| PATCH  | `/api/v1/issues/{id}/status`   | Change status       |

### Comments

| Method | Endpoint                       | Description                |
| ------ | ------------------------------ | -------------------------- |
| GET    | `/api/v1/issues/{id}/comments` | List comments              |
| POST   | `/api/v1/issues/{id}/comments` | Add comment                |
| PATCH  | `/api/v1/comments/{id}`        | Edit comment (Author only) |

## Security Features

### Authentication & Authorization

- JWT tokens with RS256 (asymmetric) signing
- 15-minute access tokens, 7-day refresh tokens
- Token blacklisting for logout
- Role-based access control (Developer, Manager, Admin)

### Rate Limiting

- Global: 100 requests/minute per IP
- Login: 5 attempts/minute per IP
- Account lockout after repeated failures

### Security Headers

- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security (HSTS)
- Content-Security-Policy

### Input Validation

- Pydantic validation on all inputs
- HTML sanitization for markdown fields
- SQL injection prevention via ORM
- Request body size limits

### Audit Logging

- All authentication events logged
- Permission-sensitive operations tracked
- Request IDs for traceability

## Permission Matrix

| Action          | Developer | Reporter | Assignee | Manager | Admin  |
| --------------- | --------- | -------- | -------- | ------- | ------ |
| View projects   | ✓         | ✓        | ✓        | ✓       | ✓      |
| Create project  | ✗         | ✗        | ✗        | ✓       | ✓      |
| Edit project    | ✗         | ✗        | ✗        | Owner   | ✓      |
| View issues     | ✓         | ✓        | ✓        | ✓       | ✓      |
| Create issue    | ✓         | ✓        | ✓        | ✓       | ✓      |
| Edit issue      | ✗         | ✓        | ✓        | ✓       | ✓      |
| Change assignee | ✗         | ✓        | ✗        | ✓       | ✓      |
| Add comment     | ✓         | ✓        | ✓        | ✓       | ✓      |
| Edit comment    | Author    | Author   | Author   | Author  | Author |

## Issue Status State Machine

```
         ┌─────────────────────────────────────┐
         │                                     │
         ▼                                     │
      [OPEN] ──────► [IN_PROGRESS] ──────► [RESOLVED]
         ▲                                     │
         │                                     ▼
    [REOPENED] ◄────────────────────────── [CLOSED]
         ▲                                     │
         └─────────────────────────────────────┘
```

**Business Rule**: Critical issues cannot be closed without at least one comment.

## Testing

```bash
# Run all tests with coverage
pytest --cov=src/app --cov-report=term-missing

# Run specific test file
pytest tests/integration/test_auth.py -v

# Run with parallel execution
pytest -n auto
```

## Deployment

### Kubernetes

```bash
# Create namespace and apply configs
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# Deploy database and cache
kubectl apply -f k8s/postgres/

# Deploy API
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml
```

### Environment Variables

See `.env.example` for all configuration options.

## Project Structure

```
task-tracker/
├── src/app/
│   ├── api/v1/          # API endpoints
│   ├── config/          # Settings
│   ├── core/            # Database, Redis, security
│   ├── middleware/      # Security headers, rate limit, audit
│   ├── models/          # SQLAlchemy models
│   ├── permissions/     # RBAC checkers
│   ├── repositories/    # Data access layer
│   ├── schemas/         # Pydantic schemas
│   └── services/        # Business logic
├── tests/               # Test suite
├── alembic/             # Database migrations
├── docker/              # Docker configs
├── k8s/                 # Kubernetes manifests
└── scripts/             # Utility scripts
```

### Project Structure

```
1. Configuration     → src/app/config/settings.py      # How app is configured
2. Entry Point       → src/app/main.py                 # How app starts
3. Models            → src/app/models/                 # Data structure
   ├── enums.py      → UserRole, IssueStatus, IssuePriority
   ├── user.py       → User model
   ├── project.py    → Project model (soft delete)
   ├── issue.py      → Issue model (state machine)
   └── comment.py    → Comment model (no delete)

4. Security          → src/app/core/security/          # Authentication
   ├── password.py   → Argon2 hashing
   ├── jwt.py        → RS256 JWT tokens
   └── rate_limiter.py → Sliding window rate limit

5. Business Logic    → src/app/services/               # How features work
   ├── auth_service.py    → Login, register, tokens
   ├── issue_service.py   → Issue CRUD + state machine
   └── project_service.py → Project CRUD + permissions

6. API Endpoints     → src/app/api/v1/                 # REST API
   ├── deps.py       → Dependencies (auth, rate limit)
   ├── auth.py       → Auth endpoints
   ├── projects.py   → Project endpoints
   ├── issues.py     → Issue endpoints
   └── comments.py   → Comment endpoints

7. Permissions       → src/app/permissions/            # Access control
   └── *_permissions.py → Strategy pattern RBAC
```

### Key Concepts by File

| Concept            | File                                       | What You'll Learn                 |
| ------------------ | ------------------------------------------ | --------------------------------- |
| App startup        | `src/app/main.py`                          | Middleware, routes, lifespan      |
| JWT signing        | `src/app/core/security/jwt.py`             | RS256 token creation/verification |
| State machine      | `src/app/models/enums.py:27-50`            | Issue status transitions          |
| RBAC               | `src/app/permissions/issue_permissions.py` | Permission checking               |
| Repository pattern | `src/app/repositories/base.py`             | Generic CRUD operations           |

---

## Sample Credentials (After Seeding)

```bash
# Seed the database first
docker-compose exec api python scripts/seed_data.py
```

| Role      | Email                    | Password     |
| --------- | ------------------------ | ------------ |
| Admin     | admin@tasktracker.com    | Password123! |
| Manager   | manager1@tasktracker.com | Password123! |
| Developer | dev1@tasktracker.com     | Password123! |

---

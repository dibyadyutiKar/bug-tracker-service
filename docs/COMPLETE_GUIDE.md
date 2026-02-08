# Task Tracker - Complete Developer Guide

A comprehensive guide covering setup, architecture, API usage, and deployment.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Development Setup](#2-development-setup)
3. [Production Setup](#3-production-setup)
4. [Project Architecture](#4-project-architecture)
5. [Authentication System](#5-authentication-system)
6. [API Reference](#6-api-reference)
7. [Database Schema](#7-database-schema)
8. [Security Features](#8-security-features)
9. [Testing](#9-testing)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Runtime |
| PostgreSQL | 15+ | Database |
| Redis | 7+ | Caching, sessions, rate limiting |
| Docker | 24+ | Containerization |
| Docker Compose | 2.20+ | Multi-container orchestration |
| Git | 2.40+ | Version control |

### Verify Installation

```bash
python --version      # Python 3.11.x
docker --version      # Docker 24.x.x
docker-compose --version  # Docker Compose v2.x.x
git --version         # git 2.x.x
```

---

## 2. Development Setup

### Option A: Docker Development (Recommended)

This runs everything in containers - no local installations needed except Docker.

#### Step 1: Clone Repository

```bash
git clone <repository-url>
cd task-tracker
```

#### Step 2: Generate RSA Keys for JWT

```bash
# Create keys directory
mkdir -p keys

# Generate RSA key pair
python scripts/generate_keys.py --key-dir ./keys

# Verify keys exist
ls -la keys/
# Should show:
#   private_key.pem (keep secret!)
#   public_key.pem
```

#### Step 3: Create Environment File

```bash
cp .env.example .env
```

Edit `.env` for development:

```bash
# .env (Development)
APP_NAME=task-tracker
APP_ENV=development
DEBUG=true

# Database (Docker service name)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/task_tracker

# Redis (Docker service name)
REDIS_URL=redis://redis:6379/0

# JWT Keys (mounted in container)
JWT_PRIVATE_KEY_PATH=/app/keys/private_key.pem
JWT_PUBLIC_KEY_PATH=/app/keys/public_key.pem

# Security
SECRET_KEY=dev-secret-key-change-in-production
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
```

#### Step 4: Start All Services

```bash
# Start PostgreSQL, Redis, and API
docker-compose up -d

# Check status
docker-compose ps

# Expected output:
# NAME                    STATUS
# task-tracker-api-dev    running (healthy)
# task-tracker-db         running (healthy)
# task-tracker-redis      running (healthy)
```

#### Step 5: Run Database Migrations

```bash
# Create database tables
docker-compose exec api alembic upgrade head

# Verify tables created
docker-compose exec db psql -U postgres -d task_tracker -c "\dt"
```

#### Step 6: Seed Sample Data (Optional)

```bash
docker-compose exec api python scripts/seed_data.py

# Output:
# Created 6 users
# Created 5 projects
# Created 13 issues
# Created 10 comments
#
# Sample Login Credentials:
# Admin:     admin@tasktracker.com / Password123!
# Manager:   manager1@tasktracker.com / Password123!
# Developer: dev1@tasktracker.com / Password123!
```

#### Step 7: Access the API

```bash
# API Base URL
http://localhost:8000

# Swagger Documentation
http://localhost:8000/docs

# ReDoc Documentation
http://localhost:8000/redoc

# Health Check
curl http://localhost:8000/health
```

#### Development Commands

```bash
# View logs (follow mode)
docker-compose logs -f api

# Restart API after code changes (hot reload is enabled)
# No restart needed - uvicorn watches for file changes

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v

# Rebuild after dependency changes
docker-compose build --no-cache api
docker-compose up -d
```

---

### Option B: Local Development (Without Docker)

#### Step 1: Clone and Create Virtual Environment

```bash
git clone <repository-url>
cd task-tracker

# Create virtual environment
python -m venv .venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

#### Step 2: Install Dependencies

```bash
# Install package with dev dependencies
pip install -e ".[dev]"
```

#### Step 3: Start PostgreSQL and Redis

**Option 1: Using Docker for databases only**

```bash
# Start only database services
docker-compose up -d db redis

# Verify
docker-compose ps
```

**Option 2: Local installation**

```bash
# PostgreSQL
# Install via your OS package manager, then:
createdb task_tracker

# Redis
# Install via your OS package manager, then:
redis-server
```

#### Step 4: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` for local development:

```bash
# Database (localhost)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/task_tracker

# Redis (localhost)
REDIS_URL=redis://localhost:6379/0

# JWT Keys (local path)
JWT_PRIVATE_KEY_PATH=./keys/private_key.pem
JWT_PUBLIC_KEY_PATH=./keys/public_key.pem
```

#### Step 5: Generate Keys and Run Migrations

```bash
# Generate RSA keys
python scripts/generate_keys.py

# Run migrations
alembic upgrade head

# Seed data
python scripts/seed_data.py
```

#### Step 6: Start Development Server

```bash
# Run with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the main module
python -m app.main
```

---

## 3. Production Setup

### Option A: Docker Compose Production

#### Step 1: Configure Production Environment

```bash
# Create production env file
cp .env.example .env.production
```

Edit `.env.production`:

```bash
# Application
APP_NAME=task-tracker
APP_ENV=production
DEBUG=false

# Database (use strong password!)
DATABASE_URL=postgresql+asyncpg://postgres:STRONG_PASSWORD_HERE@db:5432/task_tracker

# Redis
REDIS_URL=redis://redis:6379/0

# JWT Keys
JWT_PRIVATE_KEY_PATH=/app/keys/private_key.pem
JWT_PUBLIC_KEY_PATH=/app/keys/public_key.pem

# Security (generate strong secret!)
SECRET_KEY=generate-a-64-character-random-string-here

# CORS (your frontend domain)
CORS_ORIGINS=["https://your-frontend.com"]
ALLOWED_HOSTS=["api.your-domain.com"]

# Workers
WORKERS=4
```

#### Step 2: Generate Production Keys

```bash
# Use 4096-bit keys for production
python scripts/generate_keys.py --key-dir ./keys --key-size 4096
```

#### Step 3: Create SSL Certificates

```bash
# For testing (self-signed)
mkdir -p docker/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/nginx/ssl/key.pem \
  -out docker/nginx/ssl/cert.pem

# For production: use Let's Encrypt or your CA
```

#### Step 4: Start Production Stack

```bash
# Build production image
docker-compose -f docker-compose.yaml build

# Start with production config
docker-compose -f docker-compose.yaml up -d

# Run migrations
docker-compose exec api alembic upgrade head
```

#### Step 5: Verify Production

```bash
# Health check
curl -k https://localhost/health

# Check all services
docker-compose ps
```

---

### Option B: Kubernetes Production

#### Step 1: Create Namespace and Secrets

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create secrets (edit with real values first!)
kubectl apply -f k8s/secrets.yaml

# Create config
kubectl apply -f k8s/configmap.yaml
```

#### Step 2: Deploy Database and Cache

```bash
# Deploy PostgreSQL
kubectl apply -f k8s/postgres/statefulset.yaml

# Wait for ready
kubectl -n task-tracker wait --for=condition=ready pod -l component=postgres --timeout=120s
```

#### Step 3: Deploy API

```bash
# Deploy application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml

# Check status
kubectl -n task-tracker get pods
kubectl -n task-tracker get svc
```

#### Step 4: Run Migrations

```bash
# Get pod name
POD=$(kubectl -n task-tracker get pod -l app=task-tracker -o jsonpath="{.items[0].metadata.name}")

# Run migrations
kubectl -n task-tracker exec $POD -- alembic upgrade head
```

---

## 4. Project Architecture

### Directory Structure

```
task-tracker/
├── src/app/                    # Application source code
│   ├── main.py                 # FastAPI app entry point
│   ├── config/
│   │   └── settings.py         # Environment configuration
│   ├── core/
│   │   ├── database.py         # SQLAlchemy async setup
│   │   ├── redis.py            # Redis connection
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── security/
│   │       ├── password.py     # Argon2 hashing
│   │       ├── jwt.py          # RS256 JWT tokens
│   │       ├── token_blacklist.py  # Token invalidation
│   │       └── rate_limiter.py # Sliding window rate limit
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── issue.py
│   │   └── comment.py
│   ├── schemas/                # Pydantic request/response schemas
│   ├── repositories/           # Data access layer
│   ├── services/               # Business logic layer
│   ├── permissions/            # RBAC permission checkers
│   ├── api/v1/                 # API endpoints
│   │   ├── auth.py
│   │   ├── projects.py
│   │   ├── issues.py
│   │   └── comments.py
│   └── middleware/             # Request middleware
│       ├── security_headers.py
│       ├── rate_limit.py
│       └── audit_log.py
├── tests/                      # Test suite
├── alembic/                    # Database migrations
├── docker/                     # Docker configuration
├── k8s/                        # Kubernetes manifests
├── scripts/                    # Utility scripts
└── keys/                       # JWT RSA keys (gitignored)
```

### Request Flow

```
┌──────────┐     ┌──────────┐     ┌──────────────┐     ┌──────────┐
│  Client  │────►│  Nginx   │────►│  Middleware  │────►│   API    │
└──────────┘     └──────────┘     └──────────────┘     └──────────┘
                       │                  │                  │
                       │           ┌──────┴──────┐           │
                       │           │ Rate Limit  │           │
                       │           │ Auth Check  │           │
                       │           │ Audit Log   │           │
                       │           └─────────────┘           │
                       │                                     │
                       │          ┌──────────────────────────┘
                       │          │
                       │          ▼
                       │     ┌──────────┐     ┌──────────┐     ┌──────────┐
                       │     │ Service  │────►│  Repo    │────►│ Database │
                       │     └──────────┘     └──────────┘     └──────────┘
                       │          │
                       │          │           ┌──────────┐
                       │          └──────────►│  Redis   │
                       │                      └──────────┘
                       │
                       └──────────────────────────────────────────────────┐
                                                                          │
                                                                          ▼
                                                                    ┌──────────┐
                                                                    │ Response │
                                                                    └──────────┘
```

---

## 5. Authentication System

### Overview

- **Algorithm**: RS256 (RSA + SHA-256)
- **Access Token**: 15 minutes expiry
- **Refresh Token**: 7 days expiry
- **Password Hashing**: Argon2id

### Authentication Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                           REGISTRATION                                  │
└────────────────────────────────────────────────────────────────────────┘

Client                                                              Server
  │                                                                    │
  │  POST /api/v1/auth/register                                        │
  │  {                                                                 │
  │    "username": "john",                                             │
  │    "email": "john@example.com",                                    │
  │    "password": "SecurePass123!"                                    │
  │  }                                                                 │
  │ ──────────────────────────────────────────────────────────────────►│
  │                                                                    │
  │                                    1. Validate password complexity │
  │                                    2. Check email/username unique  │
  │                                    3. Hash password with Argon2    │
  │                                    4. Save user to database        │
  │                                                                    │
  │  201 Created                                                       │
  │  {                                                                 │
  │    "id": "uuid",                                                   │
  │    "username": "john",                                             │
  │    "email": "john@example.com",                                    │
  │    "role": "developer"                                             │
  │  }                                                                 │
  │ ◄──────────────────────────────────────────────────────────────────│
  │                                                                    │


┌────────────────────────────────────────────────────────────────────────┐
│                              LOGIN                                      │
└────────────────────────────────────────────────────────────────────────┘

Client                                                              Server
  │                                                                    │
  │  POST /api/v1/auth/login                                           │
  │  {                                                                 │
  │    "email": "john@example.com",                                    │
  │    "password": "SecurePass123!"                                    │
  │  }                                                                 │
  │ ──────────────────────────────────────────────────────────────────►│
  │                                                                    │
  │                                    1. Check rate limit             │
  │                                    2. Check account not locked     │
  │                                    3. Find user by email           │
  │                                    4. Verify password with Argon2  │
  │                                    5. Generate access token (JWT)  │
  │                                    6. Generate refresh token (JWT) │
  │                                    7. Track session in Redis       │
  │                                    8. Update last_login            │
  │                                                                    │
  │  200 OK                                                            │
  │  {                                                                 │
  │    "access_token": "eyJhbGc...",                                   │
  │    "refresh_token": "eyJhbGc...",                                  │
  │    "token_type": "bearer",                                         │
  │    "expires_in": 900                                               │
  │  }                                                                 │
  │ ◄──────────────────────────────────────────────────────────────────│
  │                                                                    │


┌────────────────────────────────────────────────────────────────────────┐
│                        ACCESSING PROTECTED ROUTES                       │
└────────────────────────────────────────────────────────────────────────┘

Client                                                              Server
  │                                                                    │
  │  GET /api/v1/projects                                              │
  │  Authorization: Bearer eyJhbGc...                                  │
  │ ──────────────────────────────────────────────────────────────────►│
  │                                                                    │
  │                                    1. Extract token from header    │
  │                                    2. Verify signature (public key)│
  │                                    3. Check token not expired      │
  │                                    4. Check token not blacklisted  │
  │                                    5. Load user from database      │
  │                                    6. Attach user to request       │
  │                                                                    │
  │  200 OK                                                            │
  │  { "items": [...], "total": 10 }                                   │
  │ ◄──────────────────────────────────────────────────────────────────│
  │                                                                    │


┌────────────────────────────────────────────────────────────────────────┐
│                         TOKEN REFRESH                                   │
└────────────────────────────────────────────────────────────────────────┘

Client                                                              Server
  │                                                                    │
  │  POST /api/v1/auth/refresh                                         │
  │  {                                                                 │
  │    "refresh_token": "eyJhbGc..."                                   │
  │  }                                                                 │
  │ ──────────────────────────────────────────────────────────────────►│
  │                                                                    │
  │                                    1. Verify refresh token         │
  │                                    2. Check not blacklisted        │
  │                                    3. Blacklist old refresh token  │
  │                                    4. Generate new token pair      │
  │                                    5. Track new session            │
  │                                                                    │
  │  200 OK                                                            │
  │  {                                                                 │
  │    "access_token": "eyJhbGc...(new)",                              │
  │    "refresh_token": "eyJhbGc...(new)",                             │
  │    "token_type": "bearer",                                         │
  │    "expires_in": 900                                               │
  │  }                                                                 │
  │ ◄──────────────────────────────────────────────────────────────────│
  │                                                                    │


┌────────────────────────────────────────────────────────────────────────┐
│                              LOGOUT                                     │
└────────────────────────────────────────────────────────────────────────┘

Client                                                              Server
  │                                                                    │
  │  POST /api/v1/auth/logout                                          │
  │  Authorization: Bearer eyJhbGc...                                  │
  │  {                                                                 │
  │    "refresh_token": "eyJhbGc..."                                   │
  │  }                                                                 │
  │ ──────────────────────────────────────────────────────────────────►│
  │                                                                    │
  │                                    1. Blacklist access token       │
  │                                    2. Blacklist refresh token      │
  │                                    3. Remove from active sessions  │
  │                                                                    │
  │  204 No Content                                                    │
  │ ◄──────────────────────────────────────────────────────────────────│
  │                                                                    │
```

### Password Requirements

```
Minimum 8 characters
At least 1 uppercase letter
At least 1 lowercase letter
At least 1 number
At least 1 special character (!@#$%^&*)
```

### JWT Token Structure

```
Access Token Payload:
{
  "sub": "user-uuid",           // User ID
  "email": "john@example.com",  // User email
  "role": "developer",          // User role
  "type": "access",             // Token type
  "jti": "unique-token-id",     // Token ID (for blacklisting)
  "iat": 1699900000,            // Issued at
  "exp": 1699900900             // Expires at (15 min)
}

Refresh Token Payload:
{
  "sub": "user-uuid",
  "email": "john@example.com",
  "role": "developer",
  "type": "refresh",
  "jti": "unique-token-id",
  "iat": 1699900000,
  "exp": 1700504800             // Expires at (7 days)
}
```

---

## 6. API Reference

### Base URL

```
Development: http://localhost:8000/api/v1
Production:  https://api.your-domain.com/api/v1
```

### Authentication Headers

```
Authorization: Bearer <access_token>
```

---

### 6.1 Authentication Endpoints

#### Register User

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "johndoe",
  "email": "john@example.com",
  "role": "developer",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "last_login": null
}
```

**Errors:**
- `409 Conflict`: Email or username already exists
- `422 Unprocessable Entity`: Validation error (weak password, invalid email)

---

#### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Errors:**
- `401 Unauthorized`: Invalid credentials
- `423 Locked`: Account locked (too many failed attempts)
- `429 Too Many Requests`: Rate limit exceeded

---

#### Refresh Token

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

---

#### Get Current User

```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "johndoe",
  "email": "john@example.com",
  "role": "developer",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-15T14:20:00Z"
}
```

---

#### Logout

```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (204 No Content)**

---

#### Logout All Devices

```http
POST /api/v1/auth/logout-all
Authorization: Bearer <access_token>
```

**Response (204 No Content)**

---

#### Change Password

```http
POST /api/v1/auth/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "current_password": "OldPass123!",
  "new_password": "NewSecurePass456!"
}
```

**Response (204 No Content)**

---

### 6.2 Project Endpoints

#### List Projects

```http
GET /api/v1/projects
Authorization: Bearer <access_token>
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| search | string | null | Search in name and description |
| is_archived | boolean | false | Filter by archived status |
| page | integer | 1 | Page number |
| limit | integer | 20 | Items per page (max 100) |
| sort | string | created_at | Sort field: name, created_at, updated_at (prefix with - for desc) |

**Example:**
```http
GET /api/v1/projects?search=mobile&is_archived=false&page=1&limit=10&sort=-created_at
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Mobile App",
      "description": "iOS and Android application",
      "created_by_id": "660e8400-e29b-41d4-a716-446655440000",
      "is_archived": false,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "creator": {
        "id": "660e8400-e29b-41d4-a716-446655440000",
        "username": "manager1",
        "email": "manager1@example.com"
      }
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}
```

---

#### Create Project

**Requires: Manager or Admin role**

```http
POST /api/v1/projects
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "New Project",
  "description": "Project description (optional, max 1000 chars)"
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "New Project",
  "description": "Project description",
  "created_by_id": "660e8400-e29b-41d4-a716-446655440000",
  "is_archived": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Errors:**
- `403 Forbidden`: User is not manager or admin
- `409 Conflict`: Project name already exists

---

#### Get Project

```http
GET /api/v1/projects/{project_id}
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Mobile App",
  "description": "iOS and Android application",
  "created_by_id": "660e8400-e29b-41d4-a716-446655440000",
  "is_archived": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "creator": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "username": "manager1",
    "email": "manager1@example.com"
  },
  "issue_count": 15,
  "open_issue_count": 8
}
```

---

#### Update Project

**Requires: Project owner or Admin**

```http
PATCH /api/v1/projects/{project_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated description"
}
```

**Response (200 OK):** Updated project object

---

#### Archive Project (Soft Delete)

**Requires: Project owner or Admin**

```http
DELETE /api/v1/projects/{project_id}
Authorization: Bearer <access_token>
```

**Response (200 OK):** Archived project object with `is_archived: true`

---

#### Unarchive Project

**Requires: Project owner or Admin**

```http
POST /api/v1/projects/{project_id}/unarchive
Authorization: Bearer <access_token>
```

**Response (200 OK):** Unarchived project object with `is_archived: false`

---

### 6.3 Issue Endpoints

#### List Project Issues

```http
GET /api/v1/projects/{project_id}/issues
Authorization: Bearer <access_token>
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | Filter: open, in_progress, resolved, closed, reopened |
| priority | string | Filter: low, medium, high, critical |
| assignee_id | uuid | Filter by assignee |
| search | string | Search in title and description |
| page | integer | Page number (default: 1) |
| limit | integer | Items per page (default: 20, max: 100) |
| sort | string | Sort: title, status, priority, created_at, updated_at, due_date |

**Example:**
```http
GET /api/v1/projects/{id}/issues?status=open&priority=high&sort=-created_at
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440000",
      "title": "Fix login bug",
      "description": "Users cannot login on mobile",
      "status": "open",
      "priority": "high",
      "project_id": "550e8400-e29b-41d4-a716-446655440000",
      "reporter_id": "660e8400-e29b-41d4-a716-446655440000",
      "assignee_id": "880e8400-e29b-41d4-a716-446655440000",
      "due_date": "2024-01-20",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "reporter": {
        "id": "660e8400-e29b-41d4-a716-446655440000",
        "username": "dev1",
        "email": "dev1@example.com"
      },
      "assignee": {
        "id": "880e8400-e29b-41d4-a716-446655440000",
        "username": "dev2",
        "email": "dev2@example.com"
      }
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

---

#### Create Issue

```http
POST /api/v1/projects/{project_id}/issues
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "Bug in checkout flow",
  "description": "Users see error when clicking Pay button",
  "priority": "high",
  "assignee_id": "880e8400-e29b-41d4-a716-446655440000",
  "due_date": "2024-01-25"
}
```

**Response (201 Created):** Created issue object

---

#### Get Issue Details

```http
GET /api/v1/issues/{issue_id}
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "title": "Fix login bug",
  "description": "Users cannot login on mobile",
  "status": "in_progress",
  "priority": "high",
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "reporter_id": "660e8400-e29b-41d4-a716-446655440000",
  "assignee_id": "880e8400-e29b-41d4-a716-446655440000",
  "due_date": "2024-01-20",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-16T14:20:00Z",
  "reporter": { ... },
  "assignee": { ... },
  "project": { ... },
  "comment_count": 5
}
```

---

#### Update Issue

**Requires: Reporter, Assignee, or Manager/Admin**

```http
PATCH /api/v1/issues/{issue_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "Updated title",
  "description": "Updated description",
  "priority": "critical",
  "due_date": "2024-01-22"
}
```

**Response (200 OK):** Updated issue object

---

#### Change Issue Status

**Requires: Reporter, Assignee, or Manager/Admin**

```http
PATCH /api/v1/issues/{issue_id}/status
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "status": "in_progress"
}
```

**Valid Status Transitions:**
```
open → in_progress → resolved → closed
                            ↘ reopened
                   closed → reopened
               reopened → in_progress
```

**Business Rule:** Critical issues cannot be closed without at least one comment.

**Response (200 OK):** Updated issue object

**Errors:**
- `400 Bad Request`: Invalid status transition
- `400 Bad Request`: Critical issue has no comments

---

#### Assign Issue

**Requires: Reporter or Manager/Admin**

```http
PATCH /api/v1/issues/{issue_id}/assign?assignee_id={user_id}
Authorization: Bearer <access_token>
```

To unassign, omit the `assignee_id` parameter or set to null.

**Response (200 OK):** Updated issue object

---

### 6.4 Comment Endpoints

#### List Issue Comments

```http
GET /api/v1/issues/{issue_id}/comments
Authorization: Bearer <access_token>
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | integer | 1 | Page number |
| limit | integer | 50 | Items per page (max 100) |

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440000",
      "content": "I'll look into this issue today.",
      "issue_id": "770e8400-e29b-41d4-a716-446655440000",
      "author_id": "880e8400-e29b-41d4-a716-446655440000",
      "created_at": "2024-01-15T11:00:00Z",
      "updated_at": "2024-01-15T11:00:00Z",
      "author": {
        "id": "880e8400-e29b-41d4-a716-446655440000",
        "username": "dev2",
        "email": "dev2@example.com"
      },
      "is_edited": false
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 50,
  "total_pages": 1
}
```

---

#### Add Comment

```http
POST /api/v1/issues/{issue_id}/comments
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "content": "Found the root cause. Working on a fix now."
}
```

**Response (201 Created):** Created comment object

**Note:** Comments are automatically sanitized to prevent XSS attacks.

---

#### Edit Comment

**Requires: Comment author only**

```http
PATCH /api/v1/comments/{comment_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "content": "Updated comment content"
}
```

**Response (200 OK):** Updated comment object with `is_edited: true`

**Note:** Comments cannot be deleted (audit trail requirement).

---

## 7. Database Schema

### Entity Relationship Diagram

```
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│      USERS       │       │     PROJECTS     │       │      ISSUES      │
├──────────────────┤       ├──────────────────┤       ├──────────────────┤
│ id (PK, UUID)    │◄──────│ created_by_id    │       │ id (PK, UUID)    │
│ username         │       │ id (PK, UUID)    │◄──────│ project_id (FK)  │
│ email            │       │ name             │       │ reporter_id (FK) │──┐
│ password_hash    │       │ description      │       │ assignee_id (FK) │──┤
│ role             │       │ is_archived      │       │ title            │  │
│ is_active        │       │ created_at       │       │ description      │  │
│ created_at       │       │ updated_at       │       │ status           │  │
│ last_login       │       └──────────────────┘       │ priority         │  │
└──────────────────┘                                  │ due_date         │  │
         │                                            │ created_at       │  │
         │                                            │ updated_at       │  │
         │                                            └──────────────────┘  │
         │                                                     │            │
         │                                                     │            │
         │            ┌──────────────────┐                     │            │
         │            │     COMMENTS     │                     │            │
         │            ├──────────────────┤                     │            │
         │            │ id (PK, UUID)    │                     │            │
         └────────────│ author_id (FK)   │                     │            │
                      │ issue_id (FK)    │◄────────────────────┘            │
                      │ content          │                                  │
                      │ created_at       │                                  │
                      │ updated_at       │                                  │
                      └──────────────────┘                                  │
                                                                            │
                      ┌─────────────────────────────────────────────────────┘
                      │
                      ▼
              (Users table - reporter and assignee relationships)
```

### Tables

#### users
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| username | VARCHAR(50) | UNIQUE, NOT NULL |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL |
| role | ENUM | NOT NULL, DEFAULT 'developer' |
| is_active | BOOLEAN | NOT NULL, DEFAULT true |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() |
| last_login | TIMESTAMP | NULL |

#### projects
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| name | VARCHAR(100) | UNIQUE, NOT NULL |
| description | TEXT | NULL, MAX 1000 |
| created_by_id | UUID | FK → users.id, PROTECT |
| is_archived | BOOLEAN | NOT NULL, DEFAULT false |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

#### issues
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| title | VARCHAR(200) | NOT NULL |
| description | TEXT | NULL, MAX 5000 |
| status | ENUM | NOT NULL, DEFAULT 'open' |
| priority | ENUM | NOT NULL, DEFAULT 'medium' |
| project_id | UUID | FK → projects.id, CASCADE |
| reporter_id | UUID | FK → users.id, PROTECT |
| assignee_id | UUID | FK → users.id, SET NULL |
| due_date | DATE | NULL |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

#### comments
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| content | TEXT | NOT NULL, MAX 2000 |
| issue_id | UUID | FK → issues.id, CASCADE |
| author_id | UUID | FK → users.id, PROTECT |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

---

## 8. Security Features

### Authentication Security

| Feature | Implementation |
|---------|----------------|
| Password Hashing | Argon2id with configurable parameters |
| JWT Algorithm | RS256 (asymmetric, 2048/4096-bit keys) |
| Token Blacklisting | Redis-backed for immediate invalidation |
| Session Tracking | Redis sets for multi-device logout |

### Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| Global API | 100 requests | 60 seconds |
| Login | 5 attempts | 60 seconds |
| After 5 failed logins | Account locked | 15 minutes |

### Security Headers

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
```

### Input Validation

- Pydantic models validate all request data
- HTML content sanitized with `bleach` library
- SQL injection prevented by SQLAlchemy ORM
- Request body size limited to 1MB

### Audit Logging

All authentication and sensitive operations are logged:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "abc123",
  "client_ip": "192.168.1.1",
  "method": "POST",
  "path": "/api/v1/auth/login",
  "user_id": "user-uuid",
  "status_code": 200,
  "duration_ms": 45.2
}
```

---

## 9. Testing

### Run All Tests

```bash
# With Docker
docker-compose exec api pytest

# Local
pytest
```

### Run with Coverage

```bash
pytest --cov=src/app --cov-report=term-missing --cov-report=html

# View HTML report
open htmlcov/index.html
```

### Run Specific Tests

```bash
# Integration tests only
pytest tests/integration/

# Unit tests only
pytest tests/unit/

# Specific test file
pytest tests/integration/test_auth.py

# Specific test function
pytest tests/integration/test_auth.py::test_login_success

# With verbose output
pytest -v tests/integration/test_auth.py
```

### Test Categories

| Category | Path | Description |
|----------|------|-------------|
| Unit | `tests/unit/` | Test individual functions |
| Integration | `tests/integration/` | Test API endpoints |
| Permissions | `tests/unit/test_permissions/` | Test RBAC |

---

## 10. Troubleshooting

### Common Issues

#### 1. Database Connection Failed

```
Error: Connection refused to localhost:5432
```

**Solution:**
```bash
# Check if PostgreSQL is running
docker-compose ps db

# If not running
docker-compose up -d db

# Check logs
docker-compose logs db
```

#### 2. Redis Connection Failed

```
Error: Error connecting to Redis
```

**Solution:**
```bash
# Check if Redis is running
docker-compose ps redis

# If not running
docker-compose up -d redis
```

#### 3. JWT Key Not Found

```
Error: JWT private key not found at ./keys/private_key.pem
```

**Solution:**
```bash
# Generate keys
python scripts/generate_keys.py --key-dir ./keys
```

#### 4. Migration Errors

```
Error: Target database is not up to date
```

**Solution:**
```bash
# Check current revision
alembic current

# Upgrade to latest
alembic upgrade head

# If conflicts, generate new migration
alembic revision --autogenerate -m "description"
```

#### 5. Permission Denied (403)

**Check:**
1. Is your user role sufficient for the action?
2. Are you the resource owner?
3. Is the project archived?

```bash
# Check your user role
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/auth/me
```

#### 6. Rate Limited (429)

```
Error: Too many requests
```

**Solution:**
Wait for the `Retry-After` header duration, or in development:

```bash
# Clear rate limit in Redis
docker-compose exec redis redis-cli FLUSHALL
```

### Logs

```bash
# API logs
docker-compose logs -f api

# All service logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100 api
```

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Readiness (checks DB and Redis)
curl http://localhost:8000/ready
```

---

## Quick Reference

### Sample Login Credentials (After Seeding)

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@tasktracker.com | Password123! |
| Manager | manager1@tasktracker.com | Password123! |
| Developer | dev1@tasktracker.com | Password123! |

### Common Commands

```bash
# Start development
docker-compose up -d

# View logs
docker-compose logs -f api

# Run migrations
docker-compose exec api alembic upgrade head

# Seed data
docker-compose exec api python scripts/seed_data.py

# Run tests
docker-compose exec api pytest

# Stop everything
docker-compose down

# Clean restart
docker-compose down -v && docker-compose up -d
```

---

## Support

- **Documentation**: `/docs` (Swagger UI)
- **API Spec**: `/openapi.json`
- **Health**: `/health`
- **Readiness**: `/ready`

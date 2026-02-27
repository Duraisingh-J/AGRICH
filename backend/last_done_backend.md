# AGRICHAIN Backend — Last Done Summary

**Date:** 2026-02-27

## Scope Completed (Bootstrap Phase 1)
Created the first production-ready FastAPI backend slice with async-first design, typed configuration, JWT auth foundation, and SQLAlchemy async database setup.

## Files Added

- `backend/app/__init__.py`
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/api/__init__.py`
- `backend/app/api/auth.py`
- `backend/app/db/__init__.py`
- `backend/app/db/database.py`
- `backend/app/models/__init__.py`
- `backend/app/models/user.py`

## What Was Implemented

### 1) Application Entrypoint (`main.py`)
- FastAPI app factory with lifespan hooks.
- Structured logging initialization.
- CORS middleware configured via environment settings.
- Router registration for auth module under API prefix.
- Health endpoint: `GET /health`.
- Centralized exception handlers for:
  - `HTTPException`
  - `RequestValidationError`
  - generic unhandled exceptions (safe 500 response)

### 2) Environment Configuration (`config.py`)
- Pydantic v2 settings via `BaseSettings`.
- `.env` integration with aliases for existing env keys:
  - `DATABASE_URL`
  - `JWT_SECRET`
  - `WEB3_RPC_URL`
  - `IPFS_API_URL`
  - `REDIS_URL`
- Added typed app settings:
  - env, host, port, debug, log level
  - API prefix and CORS origins
  - JWT algorithm and access/refresh TTLs
- Cached settings loader via `get_settings()`.

### 3) Async Database Layer (`db/database.py`)
- SQLAlchemy async engine (`create_async_engine`).
- Async session factory (`async_sessionmaker`).
- Declarative base (`DeclarativeBase`) for model inheritance.
- Request-scoped DB dependency: `get_db()`.
- Alembic-friendly baseline structure.

### 4) Base User Model (`models/user.py`)
- Implemented ORM model with required fields:
  - `id` (UUID)
  - `name`
  - `email`
  - `phone`
  - `role` (`farmer`, `distributor`, `retailer`, `consumer`)
  - `aadhaar_hash` (hash only; no raw Aadhaar storage)
  - `wallet_address`
  - `is_verified`
  - `created_at`
- Added `password_hash` for auth.
- Added indexes and uniqueness constraints:
  - indexed: `email`, `wallet_address`, `aadhaar_hash`, `role`
  - unique: `email`, `phone`, `wallet_address`

### 5) Basic Auth Router (`api/auth.py`)
Implemented thin API handlers with core auth logic:

- `POST /api/v1/auth/register`
  - validates wallet format and Aadhaar format
  - hashes Aadhaar using SHA-256
  - hashes password with bcrypt
  - creates user and returns access + refresh JWT tokens
- `POST /api/v1/auth/login`
  - verifies credentials
  - returns access + refresh JWT tokens
- `POST /api/v1/auth/refresh`
  - validates refresh token type
  - rotates token pair

Security/architecture notes:
- No raw Aadhaar is persisted.
- Password hashing/verification uses threadpool offloading to avoid blocking async event loop.
- JWT includes token type, subject, iat, exp.
- DB and business logic are dependency-injected.

## Validation Performed
- Ran syntax compile check successfully:
  - `python -m compileall backend/app`
- All created modules compiled without errors.

## Current Status
Phase 1 requested bootstrap is complete:
- `main.py` ✅
- `config.py` ✅
- `database.py` ✅
- base User model ✅
- basic auth router ✅

## Suggested Next Step
Phase 2 scaffolding:
- remaining routers (`farmer`, `distributor`, `retailer`, `consumer`, `batch`, `qr`)
- service layer modules (`blockchain_service`, `ipfs_service`, `ai_service`, `auth_service`, `trust_service`)
- remaining models (`batch`, `transaction`)
- workers (`blockchain_listener`, `event_processor`)

---

## Phase 2 Summary (Completed)

**Date:** 2026-02-27

Extended the backend with clean architecture boundaries: thin API layer, reusable dependencies, and service-first orchestration.

### 1) Role-Based Access Control
- Added reusable auth/role dependency module: `backend/app/utils/roles.py`
- Implemented `get_current_user`:
  - extracts bearer JWT
  - validates access token type
  - resolves and returns DB user
- Implemented `require_role(allowed_roles)`:
  - reusable role guard for routers
  - returns HTTP 403 on insufficient permissions

### 2) Service Layer Skeletons
Created service package and production-structured stubs:

- `backend/app/services/auth_service.py`
  - Aadhaar hashing
  - bcrypt password hash/verify (threadpool-safe)
  - JWT create/decode
  - token pair generation
- `backend/app/services/blockchain_service.py`
  - Web3.py-ready structure (lazy client init)
  - `mint_batch(batch_id, metadata_cid)`
  - `transfer_ownership(batch_id, from_addr, to_addr)`
  - `get_batch_history(batch_id)`
  - `verify_transaction(tx_hash)`
  - currently mocked responses with realistic return shape
- `backend/app/services/ipfs_service.py`
  - `upload_json(data)`
  - `upload_file(file_bytes)`
  - mocked CID generation
- `backend/app/services/ai_service.py`
  - async stubs: `predict_price`, `detect_disease`, `spoilage_risk`, `fraud_score`
- `backend/app/services/trust_service.py`
  - async stubs: `calculate_trust_score`, `update_trust_on_event`

### 3) Product Batch Model
- Added `backend/app/models/batch.py`
- Implemented fields:
  - `id` (UUID)
  - `batch_code` (unique)
  - `farmer_id` (FK -> users)
  - `current_owner_id` (FK -> users)
  - `crop_type`
  - `quantity`
  - `ipfs_metadata_cid`
  - `blockchain_tx_hash`
  - `status` enum (`created`, `in_transit`, `delivered`, etc.)
  - `created_at`, `updated_at`
- Added indexes for query-critical columns.

### 4) Batch Lifecycle APIs
- Added `backend/app/api/batch.py`

Implemented endpoints:
- `POST /api/v1/batches/create` (Farmer only)
  - role guard validation
  - uploads metadata to IPFS
  - mints blockchain batch
  - saves batch record
  - returns batch + QR payload
- `POST /api/v1/batches/{batch_id}/transfer` (Distributor/Retailer)
  - role guard validation
  - verifies current ownership
  - calls blockchain ownership transfer
  - updates owner + status
- `GET /api/v1/batches/{batch_id}`
  - authenticated retrieval of full batch details

### 5) QR Module
- Added `backend/app/api/qr.py`
- Implemented:
  - `generate_batch_qr(batch_id)`
  - `decode_qr(data)`
- Enforced URI format:
  - `agrichain://batch/<uuid>`

### 6) Router Registration + Auth Refactor
- Updated `backend/app/main.py` to register:
  - batch router
  - qr router
- Refactored `backend/app/api/auth.py` to delegate security logic to `auth_service`:
  - password hashing/verification
  - token creation/decoding

### 7) Validation
- Syntax compilation passed after Phase 2:
  - `python -m compileall backend/app`

### Current Backend Status
- Phase 1 ✅
- Phase 2 ✅

### Suggested Next Step (Phase 3)
- remaining domain routers (`farmer`, `distributor`, `retailer`, `consumer`)
- transaction model + lifecycle records
- workers (`blockchain_listener`, `event_processor`)
- Alembic migration scripts for `users` and `batches`

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

---

## Phase 3 Summary (Completed)

**Date:** 2026-02-27

Upgraded AGRICHAIN backend for blockchain-ready architecture with migration-first DB management, event processing workers, Redis integration, and deep observability.

### 1) Real Web3 Integration (with safe fallback)
- Updated `backend/app/services/blockchain_service.py` to support lazy real Web3 usage:
  - `is_blockchain_healthy()`
  - `mint_batch(batch_id, metadata_cid)`
  - `transfer_ownership(batch_id, from_addr, to_addr)`
  - `get_batch_history(batch_id)`
  - `verify_transaction(tx_hash)`
  - `fetch_events(from_block)` for listener polling
- All methods use async-safe execution (`run_in_threadpool`) for blocking Web3 operations.
- If Web3/contract/config is unavailable, service gracefully falls back to mocked responses.

### 2) Blockchain Config Utility
- Added `backend/app/utils/blockchain_config.py`.
- Responsibilities implemented:
  - cached Web3 instance initialization from `WEB3_RPC_URL`
  - ABI loading from env path (`BATCH_CONTRACT_ABI_PATH`)
  - contract address validation (`BATCH_CONTRACT_ADDRESS`)
  - cached `get_contract()` helper
- Extended `backend/app/config.py` with:
  - `BATCH_CONTRACT_ADDRESS`
  - `BATCH_CONTRACT_ABI_PATH`
  - `BLOCKCHAIN_DEFAULT_SENDER`

### 3) Alembic Migrations (Async)
- Added migration stack:
  - `backend/alembic.ini`
  - `backend/db/migrations/env.py` (async engine config)
  - `backend/db/migrations/script.py.mako`
  - `backend/db/migrations/versions/0001_initial_users_batches.py`
- Initial migration includes:
  - `users` table
  - `batches` table
  - enums, FK constraints, indexes, and unique constraints
- Added programmatic migration runner:
  - `backend/scripts/init_db.py`

### 4) Removed `create_all` Bootstrapping
- Removed ORM auto-create behavior from runtime startup.
- `backend/app/db/database.py` now contains only engine/session/dependency primitives.
- Schema creation responsibility moved to Alembic migrations (production-safe path).

### 5) Blockchain Event Worker Layer
- Added `backend/app/workers/blockchain_listener.py`:
  - async polling loop
  - resilient retry/backoff
  - graceful shutdown support
  - listens for contract events and dispatches to processor
- Added `backend/app/workers/event_processor.py`:
  - transaction-safe DB update flow
  - idempotency guard for duplicate events
  - handles `BatchMinted` + `OwnershipTransferred`
  - updates batch state and triggers trust score update

### 6) Redis Light Integration
- Added `backend/app/services/cache_service.py`:
  - lazy Redis client initialization
  - graceful fallback when Redis unavailable
  - batch lookup cache helpers
  - rate limiting helper (`check_rate_limit`)

### 7) Deep Health Endpoint
- Added `GET /system/health/deep` in `backend/app/main.py`.
- Reports structured health for:
  - database
  - blockchain
  - redis
  - IPFS
- Added IPFS connectivity probe in `backend/app/services/ipfs_service.py` via `is_healthy()`.

### 8) Validation
- Phase 3 modules compiled successfully:
  - `python -m compileall backend/app backend/scripts backend/db/migrations`
- Confirmed no `Base.metadata.create_all` usage remains.

### Current Backend Status
- Phase 1 ✅
- Phase 2 ✅
- Phase 3 ✅ (implementation complete)

### Suggested Next Step (Phase 4)
- wire blockchain listener lifecycle into app startup/shutdown task management
- add event persistence table for cross-restart idempotency
- add contract-aware integration tests against local Hardhat node
- add CI job for migration + validator checks

---

## Phase 4 Summary (Completed)

**Date:** 2026-02-27

Hardened backend reliability and durability for blockchain-optional production operation.

### 1) Event Durability (Critical)
- Added durable blockchain event model: `backend/app/models/blockchain_event.py`
- Added migration: `backend/db/migrations/versions/0002_blockchain_events.py`
- Implemented constraints and indexes:
  - unique `(tx_hash, log_index)`
  - indexed `status`
  - indexed `block_number`
  - indexed `next_retry_at`

### 2) Processor Reliability Hardening
- Updated `backend/app/workers/event_processor.py` to support:
  - durable upsert-based idempotency
  - exactly-once semantics via persisted event state
  - transaction-safe processing with rollback protection
  - duplicate protection across restarts
  - retry metadata with exponential backoff
  - helper: `mark_event_failed(event_id, reason)`
  - retriable backlog execution: `process_retriable_events()`
  - metrics helpers:
    - `get_event_backlog_size()`
    - `get_last_processed_block()`

### 3) Listener Lifecycle Management
- Updated `backend/app/workers/blockchain_listener.py`:
  - singleton/shared listener instance to prevent duplicates
  - heartbeat logs every configurable cycles
  - safe passive behavior when chain unavailable
  - graceful stop support
  - exported uptime/backlog/last-block helpers
- Integrated listener startup/shutdown in FastAPI lifespan (`backend/app/main.py`) with env flags:
  - `ENABLE_BLOCKCHAIN_LISTENER`
  - `BLOCKCHAIN_POLL_INTERVAL`

### 4) Backlog & Lag Monitoring
- Extended deep health endpoint (`GET /system/health/deep`) with:
  - `listener.running`
  - `listener.backlog_size`
  - `listener.last_block`
  - `listener.uptime_seconds`

### 5) Blockchain Service Resilience
- Hardened `backend/app/services/blockchain_service.py`:
  - timeout guards for RPC and contract operations
  - structured error classification types:
    - `BlockchainUnavailable`
    - `ContractNotConfigured`
    - `TransactionFailed`
  - circuit-breaker style cooldown on repeated failures
  - in-memory health cache TTL
  - guaranteed mock fallback on failure (API never crashes)

### 6) Redis Optional Hardening
- Enhanced `backend/app/services/cache_service.py`:
  - connection retry policy
  - timeout guards
  - safe JSON serialization/deserialization
  - fallback to no-cache mode if Redis unavailable

### 7) Production Logging Polish
- Added correlation ID middleware in `backend/app/main.py`
- Added request completion logs with latency
- Added optional JSON logging via env:
  - `LOG_JSON`
- Improved lifecycle, retry, and event logs for observability

### 8) Integration Test Harness (No Real Chain Required)
- Added `backend/app/utils/integration_validator.py`:
  - simulates blockchain events in mock mode
  - validates state transitions in DB
  - validates idempotency on duplicate events
  - validates retry metadata behavior

### 9) Config Updates
- Extended `backend/app/config.py` with Phase 4 settings:
  - listener toggles and heartbeat
  - blockchain timeout/cooldown/failure thresholds
  - Redis timeout/retries
  - JSON logging option

### 10) Validation
- Applied migrations successfully:
  - `alembic upgrade head` (includes `0002_blockchain_events`)
- Compiled all Phase 4 changed modules successfully.

### Current Backend Status
- Phase 1 ✅
- Phase 2 ✅
- Phase 3 ✅
- Phase 4 ✅ (reliability hardening complete)

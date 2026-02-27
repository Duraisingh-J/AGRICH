# AGRICHAIN Backend — Final Summary

## Overview
AGRICHAIN backend is a production-oriented, async-first FastAPI system built to support agricultural batch traceability with blockchain integration, resilient fallbacks, and durable event processing.

It evolved through 4 phases:
- **Phase 1:** Core backend bootstrap (FastAPI app, config, DB layer, auth, user model)
- **Phase 2:** RBAC, service layer skeletons, batch lifecycle APIs, QR system, validator
- **Phase 3:** Real blockchain readiness, Alembic migrations, listener workers, Redis integration, deep health
- **Phase 4:** Reliability hardening (durable blockchain events, retries, listener lifecycle, observability)

---

## Tech Stack
- **API:** FastAPI
- **DB:** PostgreSQL (Neon), SQLAlchemy Async
- **Migrations:** Alembic (async env)
- **Auth:** JWT (access + refresh), bcrypt
- **Blockchain:** Web3.py with lazy real client + fallback mock mode
- **Storage:** IPFS service wrapper
- **Cache:** Redis async (optional, graceful fallback)
- **Validation harness:** phase/integration validators

---

## Current Backend Structure

```text
backend/
  .env
  alembic.ini
  backend.md
  last_done_backend.md
  last_test_results.md
  scripts/
    init_db.py
  db/
    migrations/
      env.py
      script.py.mako
      versions/
        0001_initial_users_batches.py
        0002_blockchain_events.py
  app/
    main.py
    config.py
    __init__.py

    api/
      auth.py
      batch.py
      qr.py

    db/
      database.py

    models/
      user.py
      batch.py
      blockchain_event.py

    services/
      auth_service.py
      blockchain_service.py
      ipfs_service.py
      ai_service.py
      trust_service.py
      cache_service.py

    utils/
      roles.py
      blockchain_config.py
      phase2_validator.py
      integration_validator.py

    workers/
      blockchain_listener.py
      event_processor.py
```

---

## Functional Capabilities

### 1) Authentication & RBAC
- Register / login / refresh token flow
- JWT token pair management
- Aadhaar hash-only persistence (no raw Aadhaar)
- Wallet address binding
- Role-based route protection with reusable dependency:
  - `get_current_user`
  - `require_role(allowed_roles)`

### 2) Batch Lifecycle
- Farmer-only batch creation
- Metadata upload flow via IPFS service
- Blockchain mint trigger via service layer
- Ownership transfer flow for distributor/retailer
- Batch fetch endpoint with traceable state fields

### 3) QR System
- Generate AGRICHAIN QR payload:
  - `agrichain://batch/<uuid>`
- Decode and validate QR payloads

### 4) Blockchain Integration (Resilient)
- Lazy Web3 + contract loading from env config
- Real-call wrappers with fallback mock behavior:
  - `mint_batch`
  - `transfer_ownership`
  - `get_batch_history`
  - `verify_transaction`
- Health checks, timeout guards, circuit-breaker cooldown
- Structured error classification:
  - `BlockchainUnavailable`
  - `ContractNotConfigured`
  - `TransactionFailed`

### 5) Durable Event Processing
- Persisted blockchain event ledger (`blockchain_events`)
- Exactly-once semantics via DB uniqueness:
  - unique `(tx_hash, log_index)`
- Retry metadata with exponential backoff:
  - `retry_count`, `next_retry_at`, `last_error`
- Processor guarantees:
  - transaction safety
  - duplicate protection
  - partial failure recovery
  - explicit failure marker (`mark_event_failed`)

### 6) Listener Lifecycle & Monitoring
- Background listener integrated with FastAPI lifespan
- Environment-driven startup:
  - `ENABLE_BLOCKCHAIN_LISTENER`
  - `BLOCKCHAIN_POLL_INTERVAL`
- Singleton listener instance (prevents duplicates)
- Heartbeat logs and graceful shutdown
- Runtime metrics:
  - backlog size
  - last processed block
  - listener uptime

### 7) Cache + Rate Limiting (Optional)
- Redis lazy connect with retry + timeout guards
- Safe fallback to no-cache mode when Redis unavailable
- Batch cache helpers and lightweight rate-limit helper

### 8) Health & Observability
- Basic health endpoint: `GET /health`
- Deep health endpoint: `GET /system/health/deep`
  - database
  - blockchain
  - redis
  - ipfs
  - listener metrics (`running`, `backlog_size`, `last_block`, `uptime_seconds`)
- Correlation ID middleware
- Optional JSON logging (`LOG_JSON`)

---

## Data Model Summary

### `users`
- UUID primary key
- role enum (farmer/distributor/retailer/consumer)
- unique email/phone/wallet
- aadhaar hash + password hash

### `batches`
- UUID primary key
- unique `batch_code`
- `farmer_id`, `current_owner_id` FKs
- status enum lifecycle
- IPFS CID + blockchain tx hash

### `blockchain_events`
- UUID primary key
- durable chain event payload
- unique `(tx_hash, log_index)`
- status + retry tracking fields
- indexed for queue/backlog monitoring

---

## API Surface (Current)

### Auth
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`

### Batch
- `POST /api/v1/batches/create`
- `POST /api/v1/batches/{batch_id}/transfer`
- `GET /api/v1/batches/{batch_id}`

### QR
- `GET /api/v1/qr/generate/{batch_id}`
- `POST /api/v1/qr/decode`

### System
- `GET /health`
- `GET /system/health/deep`

---

## Environment Variables

### Required
- `DATABASE_URL`
- `JWT_SECRET`

### Core Integrations
- `WEB3_RPC_URL`
- `IPFS_API_URL`
- `REDIS_URL`

### Blockchain Contract
- `BATCH_CONTRACT_ADDRESS`
- `BATCH_CONTRACT_ABI_PATH`
- `BLOCKCHAIN_DEFAULT_SENDER`

### Listener / Reliability
- `ENABLE_BLOCKCHAIN_LISTENER`
- `BLOCKCHAIN_POLL_INTERVAL`
- `LISTENER_HEARTBEAT_CYCLES`
- `BLOCKCHAIN_REQUEST_TIMEOUT_SECONDS`
- `BLOCKCHAIN_FAILURE_THRESHOLD`
- `BLOCKCHAIN_COOLDOWN_SECONDS`
- `BLOCKCHAIN_HEALTH_CACHE_TTL_SECONDS`

### Redis / Logging
- `REDIS_TIMEOUT_SECONDS`
- `REDIS_CONNECT_RETRIES`
- `LOG_JSON`

---

## Runbook

### 1) Install dependencies
Use your active backend virtual environment and install required packages (fastapi/sqlalchemy/alembic/etc.).

### 2) Apply migrations
```bash
python -m alembic upgrade head
```

### 3) Start API
```bash
python -m uvicorn app.main:app --reload
```

### 4) Validate Phase 2 functional flow
```bash
python -m app.utils.phase2_validator
```

### 5) Validate reliability integration (no real chain required)
```bash
python -m app.utils.integration_validator
```

### 6) Listener dry-run
```bash
python -m app.workers.blockchain_listener
```

---

## Reliability Guarantees (Current)
- API remains functional when blockchain is unavailable
- Redis is optional and non-fatal
- Event processing is durable and restart-safe
- Duplicate blockchain events are safely ignored
- Failed events are tracked and retried with backoff
- Health endpoints provide actionable infra visibility

---

## Current Status
- Phase 1: ✅ Complete
- Phase 2: ✅ Complete
- Phase 3: ✅ Complete
- Phase 4: ✅ Complete

Backend is now infrastructure-ready and reliability-hardened for blockchain-dependent workloads with graceful degradation.
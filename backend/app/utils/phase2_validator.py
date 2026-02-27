"""Phase 2 validation utility for AGRICHAIN backend."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.database import SessionLocal
from app.models.batch import Batch, BatchStatus
from app.models.user import User
from app.services.ai_service import AIService
from app.services.blockchain_service import BlockchainService
from app.services.ipfs_service import IPFSService
from app.services.trust_service import TrustService

LOGGER = logging.getLogger("app.phase2_validator")


@dataclass(slots=True)
class ValidatorContext:
    """Shared context for validation helpers."""

    session_factory: async_sessionmaker[AsyncSession]


_CTX = ValidatorContext(session_factory=SessionLocal)


def _configure_logging() -> None:
    """Configure structured logging for validator runs."""

    if LOGGER.handlers:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def _ok(name: str, details: dict[str, Any]) -> dict[str, Any]:
    """Create success result payload."""

    return {"name": name, "status": "pass", "details": details}


def _fail(name: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create failure result payload."""

    payload: dict[str, Any] = {
        "name": name,
        "status": "fail",
        "message": message,
        "details": details or {},
    }
    return payload


def _is_jwt_shape(token: str) -> bool:
    """Validate basic JWT structure (header.payload.signature)."""

    parts = token.split(".")
    return len(parts) == 3 and all(bool(part) for part in parts)


async def validate_database_connection(
    session_factory: async_sessionmaker[AsyncSession],
) -> dict[str, Any]:
    """Validate DB connectivity and table presence."""

    name = "database_connection"
    try:
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))

            users_table = (
                await session.execute(text("SELECT to_regclass('public.users')"))
            ).scalar_one_or_none()
            batches_table = (
                await session.execute(text("SELECT to_regclass('public.batches')"))
            ).scalar_one_or_none()

        result = _ok(
            name,
            {
                "select_1": "ok",
                "users_table_exists": users_table is not None,
                "batches_table_exists": batches_table is not None,
            },
        )
        LOGGER.info("Database validation passed", extra={"result": result})
        return result
    except Exception as exc:
        LOGGER.exception("Database validation failed")
        return _fail(name, "Database connection validation failed", {"error": str(exc)})


async def validate_neon_latency(
    session_factory: async_sessionmaker[AsyncSession],
) -> dict[str, Any]:
    """Measure Neon DB query latency and flag slow responses."""

    name = "neon_latency"
    try:
        start = time.perf_counter()
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        warn = elapsed_ms > 500
        result = _ok(
            name,
            {
                "latency_ms": elapsed_ms,
                "warning": "latency_above_500ms" if warn else "none",
            },
        )
        if warn:
            LOGGER.warning("Neon latency high", extra={"latency_ms": elapsed_ms})
        else:
            LOGGER.info("Neon latency healthy", extra={"latency_ms": elapsed_ms})
        return result
    except Exception as exc:
        LOGGER.exception("Neon latency validation failed")
        return _fail(name, "Neon latency check failed", {"error": str(exc)})


async def test_auth_flow(base_url: str) -> dict[str, Any]:
    """Validate register/login/refresh authentication flow."""

    name = "auth_flow"
    register_payload = {
        "name": "Validator Farmer",
        "email": f"validator_farmer_{int(time.time())}@agrichain.dev",
        "phone": "9999999999",
        "role": "farmer",
        "aadhaar": "123412341234",
        "wallet_address": "0x1111111111111111111111111111111111111111",
        "password": "StrongPass123",
    }
    email = str(register_payload["email"])
    password = str(register_payload["password"])

    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=20.0) as client:
            register_response = await client.post("/api/v1/auth/register", json=register_payload)
            if register_response.status_code != 201:
                return _fail(
                    name,
                    "Register failed",
                    {
                        "status_code": register_response.status_code,
                        "response": register_response.text,
                    },
                )
            register_tokens = register_response.json()

            login_response = await client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": password},
            )
            if login_response.status_code != 200:
                return _fail(
                    name,
                    "Login failed",
                    {
                        "status_code": login_response.status_code,
                        "response": login_response.text,
                    },
                )
            login_tokens = login_response.json()

            refresh_response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": login_tokens.get("refresh_token", "")},
            )
            if refresh_response.status_code != 200:
                return _fail(
                    name,
                    "Refresh failed",
                    {
                        "status_code": refresh_response.status_code,
                        "response": refresh_response.text,
                    },
                )
            refreshed_tokens = refresh_response.json()

        required_tokens_ok = all(
            [
                register_tokens.get("access_token"),
                register_tokens.get("refresh_token"),
                login_tokens.get("access_token"),
                refreshed_tokens.get("access_token"),
            ]
        )
        jwt_shapes_ok = all(
            [
                _is_jwt_shape(str(register_tokens.get("access_token", ""))),
                _is_jwt_shape(str(register_tokens.get("refresh_token", ""))),
                _is_jwt_shape(str(login_tokens.get("access_token", ""))),
                _is_jwt_shape(str(refreshed_tokens.get("access_token", ""))),
            ]
        )

        async with _CTX.session_factory() as session:
            user_exists = (
                await session.execute(select(User).where(User.email == email))
            ).scalar_one_or_none() is not None

        if not required_tokens_ok or not jwt_shapes_ok or not user_exists:
            return _fail(
                name,
                "Auth flow verification failed",
                {
                    "tokens_present": required_tokens_ok,
                    "jwt_shape_valid": jwt_shapes_ok,
                    "user_persisted": user_exists,
                },
            )

        result = _ok(
            name,
            {
                "tokens_present": True,
                "jwt_shape_valid": True,
                "user_persisted": True,
                "email": email,
            },
        )
        LOGGER.info("Auth flow validation passed", extra={"email": email})
        return result
    except Exception as exc:
        LOGGER.exception("Auth flow validation failed")
        return _fail(name, "Auth flow test errored", {"error": str(exc)})


async def test_role_guard(base_url: str) -> dict[str, Any]:
    """Validate farmer-only route rejects consumer role with HTTP 403."""

    name = "role_guard"
    email = f"validator_consumer_{int(time.time())}@agrichain.dev"
    password = "SecurePass123!"
    consumer_payload = {
        "name": "Test Consumer",
        "email": email,
        "phone": f"97{uuid.uuid4().int % 10**8:08d}",
        "role": "consumer",
        "aadhaar": "123456789012",
        "wallet_address": f"0x{uuid.uuid4().hex}{uuid.uuid4().hex[:8]}",
        "password": password,
    }

    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=20.0) as client:
            register_response = await client.post("/api/v1/auth/register", json=consumer_payload)
            if register_response.status_code != 201:
                return _fail(
                    name,
                    "Consumer register failed",
                    {
                        "status_code": register_response.status_code,
                        "response": register_response.text,
                    },
                )

            token = register_response.json().get("access_token", "")
            forbidden_response = await client.post(
                "/api/v1/batches/create",
                json={"crop_type": "wheat", "quantity": "120kg", "metadata": {"grade": "A"}},
                headers={"Authorization": f"Bearer {token}"},
            )

        passed = forbidden_response.status_code == 403
        if not passed:
            return _fail(
                name,
                "Role guard did not block unauthorized access",
                {
                    "expected": 403,
                    "actual": forbidden_response.status_code,
                    "response": forbidden_response.text,
                },
            )

        result = _ok(name, {"expected_status": 403, "actual_status": 403})
        LOGGER.info("Role guard validation passed")
        return result
    except Exception as exc:
        LOGGER.exception("Role guard validation failed")
        return _fail(name, "Role guard test errored", {"error": str(exc)})


async def test_batch_flow(base_url: str) -> dict[str, Any]:
    """Validate batch creation and retrieval lifecycle."""

    name = "batch_flow"
    email = f"validator_batch_farmer_{int(time.time())}@agrichain.dev"
    password = "SecurePass123!"
    register_payload = {
        "name": "Batch Farmer",
        "email": email,
        "phone": f"96{uuid.uuid4().int % 10**8:08d}",
        "role": "farmer",
        "aadhaar": "123456789012",
        "wallet_address": f"0x{uuid.uuid4().hex}{uuid.uuid4().hex[:8]}",
        "password": password,
    }

    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=25.0) as client:
            register_response = await client.post("/api/v1/auth/register", json=register_payload)
            if register_response.status_code != 201:
                return _fail(
                    name,
                    "Farmer register failed",
                    {
                        "status_code": register_response.status_code,
                        "response": register_response.text,
                    },
                )

            token = register_response.json().get("access_token", "")
            create_response = await client.post(
                "/api/v1/batches/create",
                json={
                    "crop_type": "rice",
                    "quantity": "250kg",
                    "metadata": {"farm_location": "Nashik", "harvest_date": "2026-02-25"},
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            if create_response.status_code != 201:
                return _fail(
                    name,
                    "Batch create failed",
                    {
                        "status_code": create_response.status_code,
                        "response": create_response.text,
                    },
                )
            created_batch = create_response.json()
            batch_id = created_batch["id"]

            fetch_response = await client.get(
                f"/api/v1/batches/{batch_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            if fetch_response.status_code != 200:
                return _fail(
                    name,
                    "Batch fetch failed",
                    {
                        "status_code": fetch_response.status_code,
                        "response": fetch_response.text,
                    },
                )
            fetched_batch = fetch_response.json()

        async with _CTX.session_factory() as session:
            db_batch = (
                await session.execute(select(Batch).where(Batch.id == uuid.UUID(batch_id)))
            ).scalar_one_or_none()

        checks = {
            "batch_exists_in_db": db_batch is not None,
            "owner_correct": created_batch.get("current_owner_id") == created_batch.get("farmer_id"),
            "mock_cid_present": str(created_batch.get("ipfs_metadata_cid", "")).startswith("bafy"),
            "mock_tx_hash_present": str(created_batch.get("blockchain_tx_hash", "")).startswith("0x"),
            "status_correct": created_batch.get("status") == BatchStatus.CREATED.value,
            "fetch_matches_created": fetched_batch.get("id") == created_batch.get("id"),
        }

        if not all(checks.values()):
            return _fail(name, "Batch flow assertions failed", checks)

        result = _ok(name, {**checks, "batch_id": batch_id})
        LOGGER.info("Batch flow validation passed", extra={"batch_id": batch_id})
        return result
    except Exception as exc:
        LOGGER.exception("Batch flow validation failed")
        return _fail(name, "Batch flow test errored", {"error": str(exc)})


async def test_qr_generation(base_url: str) -> dict[str, Any]:
    """Validate QR generation/decode endpoints and payload format."""

    name = "qr_generation"
    test_batch_id = uuid.uuid4()
    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=15.0) as client:
            generate_response = await client.get(f"/api/v1/qr/generate/{test_batch_id}")
            if generate_response.status_code != 200:
                return _fail(
                    name,
                    "QR generate failed",
                    {
                        "status_code": generate_response.status_code,
                        "response": generate_response.text,
                    },
                )

            qr_data = str(generate_response.json().get("qr_data", ""))
            decode_response = await client.post("/api/v1/qr/decode", json={"data": qr_data})
            if decode_response.status_code != 200:
                return _fail(
                    name,
                    "QR decode failed",
                    {
                        "status_code": decode_response.status_code,
                        "response": decode_response.text,
                    },
                )
            decoded_batch_id = decode_response.json().get("batch_id")

        checks = {
            "qr_generated": bool(qr_data),
            "uri_format_correct": "agrichain://batch/" in qr_data,
            "decodable": decoded_batch_id == str(test_batch_id),
        }
        if not all(checks.values()):
            return _fail(name, "QR assertions failed", checks)

        result = _ok(name, checks)
        LOGGER.info("QR validation passed")
        return result
    except Exception as exc:
        LOGGER.exception("QR validation failed")
        return _fail(name, "QR test errored", {"error": str(exc)})


async def test_service_layer_stubs() -> dict[str, Any]:
    """Validate service skeleton stubs return expected response shapes."""

    name = "service_layer_stubs"
    try:
        blockchain = BlockchainService()
        ipfs = IPFSService()
        ai = AIService()
        trust = TrustService()

        mint_res = await blockchain.mint_batch(str(uuid.uuid4()), "bafytestcid")
        transfer_res = await blockchain.transfer_ownership(
            str(uuid.uuid4()),
            "0x1111111111111111111111111111111111111111",
            "0x2222222222222222222222222222222222222222",
        )
        history_res = await blockchain.get_batch_history(str(uuid.uuid4()))
        verify_res = await blockchain.verify_transaction("0x" + uuid.uuid4().hex + uuid.uuid4().hex[:8])

        cid_json = await ipfs.upload_json({"sample": "value"})
        cid_file = await ipfs.upload_file(b"sample-file")

        ai_price = await ai.predict_price("wheat", "Pune")
        ai_disease = await ai.detect_disease("https://example.com/leaf.jpg")
        ai_spoilage = await ai.spoilage_risk(uuid.uuid4())
        ai_fraud = await ai.fraud_score(uuid.uuid4())

        trust_calc = await trust.calculate_trust_score(uuid.uuid4())
        trust_update = await trust.update_trust_on_event("batch_delivered")

        checks = {
            "mint_has_tx": mint_res.tx_hash.startswith("0x"),
            "transfer_has_tx": transfer_res.tx_hash.startswith("0x"),
            "history_list": isinstance(history_res, list) and len(history_res) > 0,
            "verify_confirmed": bool(verify_res.get("confirmed")),
            "ipfs_json_cid": cid_json.startswith("bafy"),
            "ipfs_file_cid": cid_file.startswith("bafy"),
            "ai_price_shape": "predicted_price" in ai_price,
            "ai_disease_shape": "disease" in ai_disease,
            "ai_spoilage_shape": "risk" in ai_spoilage,
            "ai_fraud_shape": "fraud_score" in ai_fraud,
            "trust_calc_shape": "trust_score" in trust_calc,
            "trust_update_shape": trust_update.get("status") == "processed",
        }

        if not all(checks.values()):
            return _fail(name, "Service stub assertions failed", checks)

        result = _ok(name, checks)
        LOGGER.info("Service layer stub validation passed")
        return result
    except Exception as exc:
        LOGGER.exception("Service layer stub validation failed")
        return _fail(name, "Service stub test errored", {"error": str(exc)})


async def run_phase2_validation(
    base_url: str,
    session_factory: async_sessionmaker[AsyncSession],
) -> dict[str, Any]:
    """Run complete Phase 2 validation suite and return consolidated status."""

    _configure_logging()
    _CTX.session_factory = session_factory

    checks = [
        await validate_database_connection(session_factory),
        await validate_neon_latency(session_factory),
        await test_auth_flow(base_url),
        await test_role_guard(base_url),
        await test_batch_flow(base_url),
        await test_qr_generation(base_url),
        await test_service_layer_stubs(),
    ]

    failures = [item for item in checks if item.get("status") != "pass"]
    success_count = len(checks) - len(failures)
    overall_status = "pass" if not failures else "fail"

    summary = {
        "overall_status": overall_status,
        "checks_total": len(checks),
        "checks_passed": success_count,
        "checks_failed": len(failures),
        "checks": checks,
    }

    if failures:
        LOGGER.error(
            "Phase 2 validation completed with failures",
            extra={"failed_checks": [item.get("name") for item in failures]},
        )
    else:
        LOGGER.info("Phase 2 validation passed successfully")

    return summary


async def _main() -> None:
    """CLI entrypoint for local validator execution."""

    result = await run_phase2_validation(base_url="http://127.0.0.1:8000", session_factory=SessionLocal)
    LOGGER.info("Phase 2 summary", extra={"summary": result})


if __name__ == "__main__":
    asyncio.run(_main())

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from database import (
    fetch_one,
    fetch_all,
    upsert_customer,
    upsert_payment,
    execute,
)

from persistence import (
    persist_recovery_attempt,
    persist_outcome,
    persist_audit,
)


# ================================================================
# PATHS
# ================================================================

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent
DATA_DIR = BASE_DIR / "data"

P2P_FILE = DATA_DIR / "promise_to_pay.jsonl"


# ================================================================
# JSONL HELPERS
# ================================================================

def load_p2p_records() -> list[dict[str, Any]]:
    """
    Load structured Promise-to-Pay records created
    by the existing Hinglish recovery engine.
    """

    records: list[dict[str, Any]] = []

    if not P2P_FILE.exists():
        return records

    try:

        with open(
            P2P_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            for line in file:

                line = line.strip()

                if not line:
                    continue

                try:

                    records.append(
                        json.loads(
                            line
                        )
                    )

                except json.JSONDecodeError:
                    continue

    except OSError:

        return records

    return records


def find_promise(
    promise_id: str,
) -> dict[str, Any] | None:

    records = load_p2p_records()

    for record in reversed(records):

        if record.get(
            "promise_id"
        ) == promise_id:

            return record

    return None


# ================================================================
# VOICE SESSION
# ================================================================

def persist_voice_session(
    session: dict[str, Any],
) -> None:
    """
    Persist the customer/payment context behind a voice session.
    """

    customer_id = str(
        session.get(
            "customer_id",
            "VOICE_CUSTOMER"
        )
    )

    payment_id = str(
        session.get(
            "payment_id",
            ""
        )
    )

    amount = float(
        session.get(
            "amount",
            0.0
        )
    )

    failure_reason = str(
        session.get(
            "failure_reason",
            "voice_recovery"
        )
    )

    # Make sure the customer exists.
    upsert_customer(
        customer_id=customer_id,
        customer_name=str(
            session.get(
                "customer_name",
                ""
            )
        ),
    )

    # Persist payment context.
    if payment_id:

        upsert_payment(
            payment_id=payment_id,
            customer_id=customer_id,
            amount=amount,
            failure_reason=failure_reason,
            status="FAILED",
        )

    # Audit session creation.
    persist_audit(
        entity_type="voice_session",
        entity_id=str(
            session.get(
                "session_id",
                payment_id
            )
        ),
        event_type="VOICE_RECOVERY_SESSION_STARTED",
        event_data=session,
        source="VOICE_RECOVERY",
    )


# ================================================================
# P2P PERSISTENCE
# ================================================================

def persist_voice_promise(
    promise: dict[str, Any],
    session: dict[str, Any],
) -> str | None:
    """
    Persist a Hinglish Promise-to-Pay into SQL.

    This is deliberately a test/demo outcome path.
    """

    if not promise:
        return None

    promise_id = promise.get(
        "promise_id"
    )

    if not promise_id:
        return None

    customer_id = str(
        session.get(
            "customer_id",
            "VOICE_CUSTOMER"
        )
    )

    payment_id = str(
        session.get(
            "payment_id",
            ""
        )
    )

    amount = float(
        promise.get(
            "promised_amount",
            promise.get(
                "amount",
                session.get(
                    "amount",
                    0.0
                )
            )
        )
    )

    promised_date = str(
        promise.get(
            "promised_date",
            ""
        )
    )

    response = str(
        promise.get(
            "response",
            ""
        )
    )

    status = str(
        promise.get(
            "status",
            "PENDING"
        )
    )

    # Ensure customer exists.
    upsert_customer(
        customer_id=customer_id,
        customer_name=str(
            session.get(
                "customer_name",
                ""
            )
        ),
    )

    # Persist payment context.
    if payment_id:

        upsert_payment(
            payment_id=payment_id,
            customer_id=customer_id,
            amount=float(
                session.get(
                    "amount",
                    amount
                )
            ),
            failure_reason=str(
                session.get(
                    "failure_reason",
                    "voice_recovery"
                )
            ),
            status="FAILED",
        )

    # Store P2P.
    execute(
        """
        INSERT OR REPLACE INTO promise_to_pay (
            promise_id,
            entity_type,
            entity_id,
            customer_id,
            promised_date,
            promised_amount,
            response,
            status,
            payment_verified,
            recovered_amount,
            created_at,
            verified_at
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        """,
        (
            promise_id,
            "voice",
            payment_id or promise_id,
            customer_id,
            promised_date,
            amount,
            response,
            status,
            int(
                bool(
                    promise.get(
                        "payment_verified",
                        False
                    )
                )
            ),
            float(
                promise.get(
                    "recovery_amount",
                    0.0
                )
            ),
            promise.get(
                "created_at"
            ),
            promise.get(
                "verified_at"
            ),
        ),
    )

    persist_audit(
        entity_type="voice",
        entity_id=payment_id or promise_id,
        event_type="VOICE_PROMISE_TO_PAY_RECORDED",
        event_data={
            "promise_id": promise_id,
            "promised_date": promised_date,
            "promised_amount": amount,
            "status": status,
        },
        source="VOICE_RECOVERY",
    )

    return promise_id


# ================================================================
# VERIFIED P2P
# ================================================================

def persist_verified_voice_promise(
    promise_id: str,
    session: dict[str, Any],
    recovery_amount: float,
    final_action: str = "PROMISE_TO_PAY",
) -> dict[str, Any]:
    """
    Synchronize a verified Hinglish P2P into SQL and create
    a non-production recovery outcome.
    """

    promise = find_promise(
        promise_id
    )

    if promise is None:

        return {
            "success": False,
            "reason": (
                "Promise-to-Pay record could not be found."
            ),
        }

    customer_id = str(
        session.get(
            "customer_id",
            "VOICE_CUSTOMER"
        )
    )

    payment_id = str(
        session.get(
            "payment_id",
            ""
        )
    )

    amount_at_risk = float(
        session.get(
            "amount",
            promise.get(
                "promised_amount",
                0.0
            )
        )
    )

    recovery_amount = float(
        recovery_amount
    )

    # ------------------------------------------------------------
    # UPDATE P2P
    # ------------------------------------------------------------

    execute(
        """
        UPDATE promise_to_pay
        SET
            status = 'VERIFIED',
            payment_verified = 1,
            recovered_amount = ?,
            verified_at = CURRENT_TIMESTAMP
        WHERE promise_id = ?
        """,
        (
            recovery_amount,
            promise_id,
        ),
    )

    # ------------------------------------------------------------
    # UPDATE PAYMENT
    # ------------------------------------------------------------

    if payment_id:

        execute(
            """
            UPDATE payments
            SET
                status = 'RECOVERED',
                recovered_amount = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE payment_id = ?
            """,
            (
                recovery_amount,
                payment_id,
            ),
        )

    # ------------------------------------------------------------
    # RECOVERY OUTCOME
    # ------------------------------------------------------------

    outcome_id = persist_outcome(
        entity_type="voice",
        entity_id=payment_id or promise_id,
        customer_id=customer_id,
        amount_at_risk=amount_at_risk,
        recovered_amount=recovery_amount,
        recovered=True,
        final_action=final_action,
        recovery_probability=None,
        source="VOICE_DEMO",
        production=False,
    )

    # ------------------------------------------------------------
    # AUDIT
    # ------------------------------------------------------------

    persist_audit(
        entity_type="voice",
        entity_id=payment_id or promise_id,
        event_type="VOICE_PAYMENT_VERIFIED",
        event_data={
            "promise_id": promise_id,
            "payment_id": payment_id,
            "recovered_amount": recovery_amount,
            "outcome_id": outcome_id,
        },
        source="VOICE_RECOVERY",
    )

    return {
        "success": True,
        "promise_id": promise_id,
        "payment_id": payment_id,
        "recovered_amount": recovery_amount,
        "outcome_id": outcome_id,
    }


# ================================================================
# VOICE CONVERSATION EVENT
# ================================================================

def persist_voice_turn(
    session: dict[str, Any],
    speaker: str,
    text: str,
    intent: str | None = None,
    action: str | None = None,
) -> str:

    entity_id = str(
        session.get(
            "session_id",
            session.get(
                "payment_id",
                "VOICE_SESSION"
            )
        )
    )

    return persist_audit(
        entity_type="voice",
        entity_id=entity_id,
        event_type="VOICE_CONVERSATION_TURN",
        event_data={
            "speaker": speaker,
            "text": text,
            "intent": intent,
            "action": action,
        },
        source="VOICE_RECOVERY",
    )


# ================================================================
# VOICE SQL SUMMARY
# ================================================================

def get_voice_sql_summary(
    payment_id: str,
) -> dict[str, Any]:

    payment = fetch_one(
        """
        SELECT *
        FROM payments
        WHERE payment_id = ?
        """,
        (
            payment_id,
        ),
    )

    promises = fetch_all(
        """
        SELECT *
        FROM promise_to_pay
        WHERE entity_type = 'voice'
          AND entity_id = ?
        ORDER BY created_at DESC
        """,
        (
            payment_id,
        ),
    )

    outcomes = fetch_all(
        """
        SELECT *
        FROM recovery_outcomes
        WHERE entity_type = 'voice'
          AND entity_id = ?
        ORDER BY created_at DESC
        """,
        (
            payment_id,
        ),
    )

    audits = fetch_all(
        """
        SELECT *
        FROM audit_events
        WHERE entity_type = 'voice'
          AND entity_id = ?
        ORDER BY created_at ASC
        """,
        (
            payment_id,
        ),
    )

    return {
        "payment": payment,
        "promises": promises,
        "outcomes": outcomes,
        "audit_events": audits,
    }


# ================================================================
# DIRECT TEST
# ================================================================

if __name__ == "__main__":

    from database import initialize_database

    initialize_database()

    test_session = {
        "session_id": "VOICE_SQL_TEST_001",
        "customer_id": "VOICE_CUSTOMER_001",
        "payment_id": "PAY_VOICE_SQL_001",
        "amount": 5000.0,
        "failure_reason": "bank_timeout",
        "customer_name": "Demo Customer",
    }

    persist_voice_session(
        test_session
    )

    test_promise = {
        "promise_id": "VOICE_PTP_SQL_001",
        "promised_date": "2026-09-07",
        "promised_amount": 5000.0,
        "response": "Monday ko payment karunga.",
        "status": "PENDING",
    }

    persist_voice_promise(
        test_promise,
        test_session,
    )

    verification = persist_verified_voice_promise(
        promise_id="VOICE_PTP_SQL_001",
        session=test_session,
        recovery_amount=5000.0,
    )

    print()
    print("=" * 70)
    print("RecoverOS - VOICE / P2P SQL PERSISTENCE")
    print("=" * 70)

    print(
        json.dumps(
            verification,
            indent=2,
            ensure_ascii=False,
        )
    )

    print()
    print("SQL SUMMARY")
    print("-" * 70)

    summary = get_voice_sql_summary(
        "PAY_VOICE_SQL_001"
    )

    print(
        json.dumps(
            summary,
            indent=2,
            ensure_ascii=False,
        )
    )

    print()
    print(
        "Voice/P2P SQL persistence: COMPLETE"
    )
    print("=" * 70)


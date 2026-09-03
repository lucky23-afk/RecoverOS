from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from database import (
    execute,
    fetch_all,
    save_audit_event,
    save_recovery_attempt,
    save_recovery_outcome,
    save_promise_to_pay,
    upsert_customer,
    upsert_payment,
)


# ================================================================
# HELPERS
# ================================================================

def now_iso() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def new_id(prefix: str) -> str:
    return (
        prefix
        + "_"
        + uuid.uuid4().hex[:12].upper()
    )


# ================================================================
# CUSTOMER PERSISTENCE
# ================================================================

def persist_customer(
    customer_id: str,
    customer_name: str = "",
) -> None:

    upsert_customer(
        customer_id=customer_id,
        customer_name=customer_name,
    )


# ================================================================
# PAYMENT PERSISTENCE
# ================================================================

def persist_payment(
    payment_id: str,
    customer_id: str,
    amount: float,
    failure_reason: str,
    status: str,
) -> None:

    upsert_payment(
        payment_id=payment_id,
        customer_id=customer_id,
        amount=amount,
        failure_reason=failure_reason,
        status=status,
    )


# ================================================================
# SUBSCRIPTION PERSISTENCE
# ================================================================

def persist_subscription(
    subscription: dict[str, Any],
) -> None:

    persist_customer(
        subscription.get(
            "customer_id",
            "",
        )
    )

    persist_payment(
        payment_id=subscription.get(
            "payment_id",
            "",
        ),
        customer_id=subscription.get(
            "customer_id",
            "",
        ),
        amount=float(
            subscription.get(
                "amount",
                0,
            )
        ),
        failure_reason=subscription.get(
            "failure_reason",
            "",
        ),
        status=subscription.get(
            "status",
            "FAILED",
        ),
    )

    execute(
        """
        INSERT INTO subscriptions (
            subscription_id,
            customer_id,
            payment_id,
            amount,
            plan,
            failure_reason,
            status,
            retry_count,
            max_retries,
            next_retry_at,
            recovery_action,
            recovery_probability,
            payment_verified,
            recovered_amount,
            created_at,
            updated_at
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        ON CONFLICT(subscription_id)
        DO UPDATE SET
            customer_id = excluded.customer_id,
            payment_id = excluded.payment_id,
            amount = excluded.amount,
            plan = excluded.plan,
            failure_reason = excluded.failure_reason,
            status = excluded.status,
            retry_count = excluded.retry_count,
            max_retries = excluded.max_retries,
            next_retry_at = excluded.next_retry_at,
            recovery_action = excluded.recovery_action,
            recovery_probability = excluded.recovery_probability,
            payment_verified = excluded.payment_verified,
            recovered_amount = excluded.recovered_amount,
            updated_at = excluded.updated_at
        """,
        (
            subscription.get(
                "subscription_id"
            ),
            subscription.get(
                "customer_id"
            ),
            subscription.get(
                "payment_id"
            ),
            float(
                subscription.get(
                    "amount",
                    0,
                )
            ),
            subscription.get(
                "subscription_plan",
                "monthly",
            ),
            subscription.get(
                "failure_reason",
                "",
            ),
            subscription.get(
                "status",
                "FAILED",
            ),
            int(
                subscription.get(
                    "retry_count",
                    0,
                )
            ),
            int(
                subscription.get(
                    "max_retries",
                    3,
                )
            ),
            subscription.get(
                "next_retry_at"
            ),
            subscription.get(
                "recovery_action"
            ),
            subscription.get(
                "recovery_probability"
            ),
            int(
                bool(
                    subscription.get(
                        "payment_verified",
                        False,
                    )
                )
            ),
            float(
                subscription.get(
                    "recovered_amount",
                    0,
                )
            ),
            subscription.get(
                "created_at",
                now_iso(),
            ),
            subscription.get(
                "updated_at",
                now_iso(),
            ),
        ),
    )


# ================================================================
# MANDATE PERSISTENCE
# ================================================================

def persist_mandate(
    mandate: dict[str, Any],
) -> None:

    persist_customer(
        mandate.get(
            "customer_id",
            ""
        )
    )

    persist_payment(
        payment_id=mandate.get(
            "payment_id",
            "",
        ),
        customer_id=mandate.get(
            "customer_id",
            "",
        ),
        amount=float(
            mandate.get(
                "amount",
                0,
            )
        ),
        failure_reason=mandate.get(
            "failure_reason",
            "",
        ),
        status=mandate.get(
            "status",
            "FAILED",
        ),
    )

    execute(
        """
        INSERT INTO mandates (
            mandate_id,
            customer_id,
            payment_id,
            amount,
            mandate_type,
            failure_reason,
            status,
            retry_count,
            max_retries,
            next_retry_at,
            payment_verified,
            recovered_amount,
            created_at,
            updated_at
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        ON CONFLICT(mandate_id)
        DO UPDATE SET
            customer_id = excluded.customer_id,
            payment_id = excluded.payment_id,
            amount = excluded.amount,
            mandate_type = excluded.mandate_type,
            failure_reason = excluded.failure_reason,
            status = excluded.status,
            retry_count = excluded.retry_count,
            max_retries = excluded.max_retries,
            next_retry_at = excluded.next_retry_at,
            payment_verified = excluded.payment_verified,
            recovered_amount = excluded.recovered_amount,
            updated_at = excluded.updated_at
        """,
        (
            mandate.get(
                "mandate_id"
            ),
            mandate.get(
                "customer_id"
            ),
            mandate.get(
                "payment_id"
            ),
            float(
                mandate.get(
                    "amount",
                    0,
                )
            ),
            mandate.get(
                "mandate_type",
                "recurring",
            ),
            mandate.get(
                "failure_reason",
                "",
            ),
            mandate.get(
                "status",
                "FAILED",
            ),
            int(
                mandate.get(
                    "retry_count",
                    0,
                )
            ),
            int(
                mandate.get(
                    "max_retries",
                    4,
                )
            ),
            mandate.get(
                "next_retry_at"
            ),
            int(
                bool(
                    mandate.get(
                        "payment_verified",
                        False,
                    )
                )
            ),
            float(
                mandate.get(
                    "recovered_amount",
                    0,
                )
            ),
            mandate.get(
                "created_at",
                now_iso(),
            ),
            mandate.get(
                "updated_at",
                now_iso(),
            ),
        ),
    )


# ================================================================
# CHECKOUT PERSISTENCE
# ================================================================

def persist_checkout(
    checkout: dict[str, Any],
) -> None:

    persist_customer(
        checkout.get(
            "customer_id",
            ""
        )
    )

    persist_payment(
        payment_id=checkout.get(
            "payment_id",
            "",
        ),
        customer_id=checkout.get(
            "customer_id",
            "",
        ),
        amount=float(
            checkout.get(
                "amount",
                0,
            )
        ),
        failure_reason=checkout.get(
            "dropoff_reason",
            "",
        ),
        status=checkout.get(
            "status",
            "DROPPED_OFF",
        ),
    )

    execute(
        """
        INSERT INTO checkouts (
            checkout_id,
            customer_id,
            payment_id,
            amount,
            checkout_stage,
            dropoff_reason,
            status,
            attempt_count,
            max_attempts,
            next_followup_at,
            recovery_action,
            recovery_probability,
            payment_verified,
            recovered_amount,
            created_at,
            updated_at
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        ON CONFLICT(checkout_id)
        DO UPDATE SET
            customer_id = excluded.customer_id,
            payment_id = excluded.payment_id,
            amount = excluded.amount,
            checkout_stage = excluded.checkout_stage,
            dropoff_reason = excluded.dropoff_reason,
            status = excluded.status,
            attempt_count = excluded.attempt_count,
            max_attempts = excluded.max_attempts,
            next_followup_at = excluded.next_followup_at,
            recovery_action = excluded.recovery_action,
            recovery_probability = excluded.recovery_probability,
            payment_verified = excluded.payment_verified,
            recovered_amount = excluded.recovered_amount,
            updated_at = excluded.updated_at
        """,
        (
            checkout.get(
                "checkout_id"
            ),
            checkout.get(
                "customer_id"
            ),
            checkout.get(
                "payment_id"
            ),
            float(
                checkout.get(
                    "amount",
                    0,
                )
            ),
            checkout.get(
                "checkout_stage"
            ),
            checkout.get(
                "dropoff_reason"
            ),
            checkout.get(
                "status",
                "DROPPED_OFF",
            ),
            int(
                checkout.get(
                    "attempt_count",
                    0,
                )
            ),
            int(
                checkout.get(
                    "max_attempts",
                    2,
                )
            ),
            checkout.get(
                "next_followup_at"
            ),
            checkout.get(
                "recovery_action"
            ),
            checkout.get(
                "recovery_probability"
            ),
            int(
                bool(
                    checkout.get(
                        "payment_verified",
                        False,
                    )
                )
            ),
            float(
                checkout.get(
                    "recovered_amount",
                    0,
                )
            ),
            checkout.get(
                "created_at",
                now_iso(),
            ),
            checkout.get(
                "updated_at",
                now_iso(),
            ),
        ),
    )


# ================================================================
# RECEIVABLE PERSISTENCE
# ================================================================

def persist_receivable(
    receivable: dict[str, Any],
) -> None:

    persist_customer(
        receivable.get(
            "customer_id",
            ""
        ),
        receivable.get(
            "customer_name",
            ""
        ),
    )

    execute(
        """
        INSERT INTO invoices (
            invoice_id,
            customer_id,
            amount,
            currency,
            due_date,
            days_overdue,
            status,
            recovery_priority,
            escalation_count,
            max_escalations,
            next_followup_at,
            recovery_action,
            payment_verified,
            recovered_amount,
            created_at,
            updated_at
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        ON CONFLICT(invoice_id)
        DO UPDATE SET
            customer_id = excluded.customer_id,
            amount = excluded.amount,
            currency = excluded.currency,
            due_date = excluded.due_date,
            days_overdue = excluded.days_overdue,
            status = excluded.status,
            recovery_priority = excluded.recovery_priority,
            escalation_count = excluded.escalation_count,
            max_escalations = excluded.max_escalations,
            next_followup_at = excluded.next_followup_at,
            recovery_action = excluded.recovery_action,
            payment_verified = excluded.payment_verified,
            recovered_amount = excluded.recovered_amount,
            updated_at = excluded.updated_at
        """,
        (
            receivable.get(
                "invoice_id"
            ),
            receivable.get(
                "customer_id"
            ),
            float(
                receivable.get(
                    "amount",
                    0,
                )
            ),
            receivable.get(
                "invoice_currency",
                "INR",
            ),
            receivable.get(
                "due_date"
            ),
            int(
                receivable.get(
                    "days_overdue",
                    0,
                )
            ),
            receivable.get(
                "status",
                "OVERDUE",
            ),
            receivable.get(
                "recovery_priority"
            ),
            int(
                receivable.get(
                    "escalation_count",
                    0,
                )
            ),
            int(
                receivable.get(
                    "max_escalations",
                    3,
                )
            ),
            receivable.get(
                "next_followup_at"
            ),
            receivable.get(
                "recovery_action"
            ),
            int(
                bool(
                    receivable.get(
                        "payment_verified",
                        False,
                    )
                )
            ),
            float(
                receivable.get(
                    "recovered_amount",
                    0,
                )
            ),
            receivable.get(
                "created_at",
                now_iso(),
            ),
            receivable.get(
                "updated_at",
                now_iso(),
            ),
        ),
    )


# ================================================================
# RECOVERY ATTEMPT
# ================================================================

def persist_recovery_attempt(
    entity_type: str,
    entity_id: str,
    action: str,
    attempt_number: int,
    status: str,
    recovery_probability: float | None = None,
    scheduled_for: str | None = None,
    executed_at: str | None = None,
    recovered_amount: float = 0.0,
) -> str:

    attempt_id = new_id(
        "ATTEMPT"
    )

    save_recovery_attempt(
        attempt_id=attempt_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        attempt_number=attempt_number,
        status=status,
        recovery_probability=recovery_probability,
        scheduled_for=scheduled_for,
        executed_at=executed_at,
        recovered_amount=recovered_amount,
    )

    return attempt_id


# ================================================================
# PROMISE TO PAY
# ================================================================

def persist_promise(
    entity_type: str,
    entity_id: str,
    customer_id: str,
    promised_date: str,
    promised_amount: float,
    response: str,
    status: str = "PENDING",
    promise_id: str | None = None,
) -> str:

    if promise_id is None:
        promise_id = new_id(
            "PTP"
        )

    save_promise_to_pay(
        promise_id=promise_id,
        entity_type=entity_type,
        entity_id=entity_id,
        customer_id=customer_id,
        promised_date=promised_date,
        promised_amount=promised_amount,
        response=response,
        status=status,
    )

    return promise_id


# ================================================================
# RECOVERY OUTCOME
# ================================================================

def persist_outcome(
    entity_type: str,
    entity_id: str,
    customer_id: str,
    amount_at_risk: float,
    recovered_amount: float,
    recovered: bool,
    final_action: str,
    recovery_probability: float | None = None,
    source: str = "DEMO",
    production: bool = False,
    outcome_id: str | None = None,
) -> str:

    if outcome_id is None:
        outcome_id = new_id(
            "OUTCOME"
        )

    save_recovery_outcome(
        outcome_id=outcome_id,
        entity_type=entity_type,
        entity_id=entity_id,
        customer_id=customer_id,
        amount_at_risk=amount_at_risk,
        recovered_amount=recovered_amount,
        recovered=recovered,
        final_action=final_action,
        recovery_probability=recovery_probability,
        source=source,
        production=production,
    )

    return outcome_id


# ================================================================
# AUDIT PERSISTENCE
# ================================================================

def persist_audit(
    entity_type: str,
    entity_id: str,
    event_type: str,
    event_data: dict[str, Any] | str,
    source: str = "RECOVEROS",
) -> str:

    event_id = new_id(
        "AUDIT"
    )

    if isinstance(
        event_data,
        dict,
    ):

        payload = json.dumps(
            event_data,
            ensure_ascii=False,
        )

    else:

        payload = str(
            event_data
        )

    save_audit_event(
        event_id=event_id,
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        event_data=payload,
        source=source,
    )

    return event_id


# ================================================================
# DASHBOARD METRICS
# ================================================================

def get_recovery_metrics() -> dict[str, Any]:

    totals = fetch_all(
        """
        SELECT
            COUNT(*) AS total_cases,
            COALESCE(
                SUM(amount_at_risk),
                0
            ) AS total_at_risk,
            COALESCE(
                SUM(recovered_amount),
                0
            ) AS total_recovered
        FROM recovery_outcomes
        WHERE production = 0
        """
    )

    row = totals[0]

    total_cases = int(
        row["total_cases"]
    )

    total_at_risk = float(
        row["total_at_risk"]
    )

    total_recovered = float(
        row["total_recovered"]
    )

    recovery_rate = (
        total_recovered / total_at_risk
        if total_at_risk > 0
        else 0.0
    )

    return {
        "cases": total_cases,
        "amount_at_risk": total_at_risk,
        "recovered_amount": total_recovered,
        "recovery_rate": recovery_rate,
    }


def get_entity_summary(
    entity_type: str,
    entity_id: str,
) -> dict[str, Any]:

    attempts = fetch_all(
        """
        SELECT *
        FROM recovery_attempts
        WHERE entity_type = ?
          AND entity_id = ?
        ORDER BY attempt_number ASC
        """,
        (
            entity_type,
            entity_id,
        ),
    )

    outcomes = fetch_all(
        """
        SELECT *
        FROM recovery_outcomes
        WHERE entity_type = ?
          AND entity_id = ?
        ORDER BY created_at DESC
        """,
        (
            entity_type,
            entity_id,
        ),
    )

    audits = fetch_all(
        """
        SELECT *
        FROM audit_events
        WHERE entity_type = ?
          AND entity_id = ?
        ORDER BY created_at ASC
        """,
        (
            entity_type,
            entity_id,
        ),
    )

    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "attempts": attempts,
        "outcomes": outcomes,
        "audit_events": audits,
    }


# ================================================================
# DATABASE HEALTH
# ================================================================

def persistence_health() -> dict[str, Any]:

    try:

        result = fetch_all(
            """
            SELECT
                (SELECT COUNT(*) FROM customers) AS customers,
                (SELECT COUNT(*) FROM payments) AS payments,
                (SELECT COUNT(*) FROM subscriptions) AS subscriptions,
                (SELECT COUNT(*) FROM mandates) AS mandates,
                (SELECT COUNT(*) FROM checkouts) AS checkouts,
                (SELECT COUNT(*) FROM invoices) AS invoices,
                (SELECT COUNT(*) FROM recovery_attempts) AS attempts,
                (SELECT COUNT(*) FROM promise_to_pay) AS promises,
                (SELECT COUNT(*) FROM recovery_outcomes) AS outcomes,
                (SELECT COUNT(*) FROM audit_events) AS audit_events
            """
        )

        return {
            "healthy": True,
            **result[0],
        }

    except Exception as exc:

        return {
            "healthy": False,
            "error": str(exc),
        }


# ================================================================
# DIRECT TEST
# ================================================================

if __name__ == "__main__":

    from database import initialize_database

    initialize_database()

    health = persistence_health()

    print()
    print("=" * 70)
    print("RecoverOS - PERSISTENCE LAYER")
    print("=" * 70)

    if health["healthy"]:

        print("Status: HEALTHY")
        print()

        for key, value in health.items():

            if key == "healthy":
                continue

            print(
                f"{key:20}: {value}"
            )

    else:

        print("Status: ERROR")
        print(
            health.get(
                "error"
            )
        )

    print("=" * 70)
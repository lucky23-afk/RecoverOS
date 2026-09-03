
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict
import json

from persistence import (
    persist_subscription,
    persist_recovery_attempt,
    persist_outcome,
)


# ================================================================
# PATHS
# ================================================================

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent
DATA_DIR = BASE_DIR / "data"

SUBSCRIPTION_AUDIT_FILE = (
    DATA_DIR / "subscription_recovery_audit.jsonl"
)


# ================================================================
# CONFIGURATION
# ================================================================

MAX_RETRIES = 3

RETRY_DELAYS_HOURS = [
    1,
    6,
    24,
]

HIGH_VALUE_REVIEW_THRESHOLD = 25000.0


# ================================================================
# HELPERS
# ================================================================

def _now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def _write_jsonl(
    path: Path,
    record: Dict[str, Any],
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        path,
        "a",
        encoding="utf-8",
    ) as file:

        file.write(
            json.dumps(
                record,
                ensure_ascii=False,
            )
            + "\n"
        )


def _money(value: float) -> str:
    return f"₹{float(value):,.2f}"


# ================================================================
# AUDIT
# ================================================================

def _audit(
    event: str,
    subscription: Dict[str, Any],
    **extra: Any,
) -> None:

    record = {
        "timestamp": _now(),
        "event": event,
        "subscription_id": subscription.get(
            "subscription_id"
        ),
        "customer_id": subscription.get(
            "customer_id"
        ),
        "payment_id": subscription.get(
            "payment_id"
        ),
        "amount": float(
            subscription.get(
                "amount",
                0.0,
            )
        ),
        "status": subscription.get(
            "status"
        ),
        "retry_count": int(
            subscription.get(
                "retry_count",
                0,
            )
        ),
        **extra,
    }

    _write_jsonl(
        SUBSCRIPTION_AUDIT_FILE,
        record,
    )


# ================================================================
# START SUBSCRIPTION RECOVERY
# ================================================================

def start_subscription_recovery(
    subscription_id: str,
    customer_id: str,
    payment_id: str,
    amount: float,
    failure_reason: str,
    subscription_plan: str = "monthly",
) -> Dict[str, Any]:
    """
    Start a bounded recovery workflow for a failed subscription.
    """

    amount = float(amount)

    if amount <= 0:

        raise ValueError(
            "Subscription amount must be greater than zero."
        )

    subscription = {
        "subscription_id": subscription_id,
        "customer_id": customer_id,
        "payment_id": payment_id,
        "amount": amount,
        "failure_reason": failure_reason,
        "subscription_plan": subscription_plan,
        "status": "FAILED",
        "retry_count": 0,
        "max_retries": MAX_RETRIES,
        "next_retry_at": None,
        "recovery_action": None,
        "recovery_probability": None,
        "expected_recovered_value": None,
        "payment_verified": False,
        "recovered_amount": 0.0,
        "created_at": _now(),
        "updated_at": _now(),
    }

    _audit(
        "SUBSCRIPTION_RECOVERY_STARTED",
        subscription,
        failure_reason=failure_reason,
    )

    # Persist subscription state into SQL.
    persist_subscription(
        subscription
    )

    return subscription


# ================================================================
# FAILURE CLASSIFICATION
# ================================================================

def classify_subscription_failure(
    failure_reason: str,
) -> Dict[str, Any]:
    """
    Classify the subscription failure into a recovery state.
    """

    reason = str(
        failure_reason
    ).strip().lower()

    retryable = {
        "bank_timeout",
        "network_error",
        "temporary_bank_error",
        "issuer_unavailable",
        "technical_error",
    }

    customer_action_required = {
        "insufficient_funds",
        "expired_card",
        "card_expired",
        "mandate_failed",
        "mandate_expired",
    }

    hard_stop = {
        "fraud",
        "suspicious_reversal",
        "account_closed",
        "customer_blocked",
    }

    if reason in retryable:

        return {
            "category": "TEMPORARY_FAILURE",
            "retryable": True,
            "customer_action_required": False,
            "hard_stop": False,
        }

    if reason in customer_action_required:

        return {
            "category": "CUSTOMER_ACTION_REQUIRED",
            "retryable": True,
            "customer_action_required": True,
            "hard_stop": False,
        }

    if reason in hard_stop:

        return {
            "category": "HARD_STOP",
            "retryable": False,
            "customer_action_required": False,
            "hard_stop": True,
        }

    return {
        "category": "UNKNOWN_FAILURE",
        "retryable": False,
        "customer_action_required": True,
        "hard_stop": False,
    }


# ================================================================
# RECOVERY DECISION
# ================================================================

def determine_subscription_action(
    subscription: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Determine the bounded intervention for a failed subscription.
    """

    amount = float(
        subscription.get(
            "amount",
            0.0,
        )
    )

    retry_count = int(
        subscription.get(
            "retry_count",
            0,
        )
    )

    failure_reason = subscription.get(
        "failure_reason",
        "",
    )

    classification = classify_subscription_failure(
        failure_reason
    )

    # ------------------------------------------------------------
    # HARD STOP
    # ------------------------------------------------------------

    if classification["hard_stop"]:

        action = "HOLD_FOR_REVIEW"

        reason = (
            "Failure type requires human review."
        )

    # ------------------------------------------------------------
    # RETRY LIMIT
    # ------------------------------------------------------------

    elif retry_count >= MAX_RETRIES:

        action = "HOLD_FOR_REVIEW"

        reason = (
            "Maximum subscription recovery retries reached."
        )

    # ------------------------------------------------------------
    # TEMPORARY FAILURE
    # ------------------------------------------------------------

    elif (
        classification["category"]
        == "TEMPORARY_FAILURE"
    ):

        action = "RETRY_PAYMENT"

        reason = (
            "Temporary payment failure is retryable."
        )

    # ------------------------------------------------------------
    # CUSTOMER ACTION REQUIRED
    # ------------------------------------------------------------

    elif (
        classification["category"]
        == "CUSTOMER_ACTION_REQUIRED"
    ):

        action = "SEND_UPDATE_LINK"

        reason = (
            "Customer action is required before retry."
        )

    # ------------------------------------------------------------
    # UNKNOWN
    # ------------------------------------------------------------

    else:

        action = "HOLD_FOR_REVIEW"

        reason = (
            "Failure type could not be safely classified."
        )

    # High-value subscriptions require human review.
    if (
        amount >= HIGH_VALUE_REVIEW_THRESHOLD
        and action != "HOLD_FOR_REVIEW"
    ):

        action = "HOLD_FOR_REVIEW"

        reason = (
            "High-value subscription requires human review."
        )

    # ------------------------------------------------------------
    # RECOVERY PROBABILITY
    # ------------------------------------------------------------

    if action == "RETRY_PAYMENT":

        retry_probability = {
            "bank_timeout": 0.72,
            "network_error": 0.68,
            "temporary_bank_error": 0.70,
            "issuer_unavailable": 0.62,
            "technical_error": 0.60,
        }.get(
            str(failure_reason).lower(),
            0.55,
        )

    elif action == "SEND_UPDATE_LINK":

        retry_probability = {
            "insufficient_funds": 0.48,
            "expired_card": 0.56,
            "card_expired": 0.56,
            "mandate_failed": 0.44,
            "mandate_expired": 0.42,
        }.get(
            str(failure_reason).lower(),
            0.40,
        )

    else:

        retry_probability = 0.0

    # ------------------------------------------------------------
    # EXPECTED VALUE
    # ------------------------------------------------------------

    if action == "RETRY_PAYMENT":

        cost = 8.0

    elif action == "SEND_UPDATE_LINK":

        cost = 3.0

    else:

        cost = 20.0

    expected_value = (
        amount * retry_probability
        - cost
    )

    return {
        "action": action,
        "reason": reason,
        "category": classification["category"],
        "retryable": classification["retryable"],
        "recovery_probability": retry_probability,
        "expected_recovered_value": round(
            max(
                expected_value,
                0.0,
            ),
            2,
        ),
        "human_review_required": (
            action == "HOLD_FOR_REVIEW"
        ),
    }


# ================================================================
# EXECUTE RECOVERY ACTION
# ================================================================

def execute_subscription_action(
    subscription: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute one bounded recovery action.

    No action can exceed MAX_RETRIES.
    """

    decision = determine_subscription_action(
        subscription
    )

    action = decision[
        "action"
    ]

    subscription[
        "recovery_action"
    ] = action

    subscription[
        "recovery_probability"
    ] = decision[
        "recovery_probability"
    ]

    subscription[
        "expected_recovered_value"
    ] = decision[
        "expected_recovered_value"
    ]

    subscription[
        "updated_at"
    ] = _now()

    # ------------------------------------------------------------
    # HOLD FOR REVIEW
    # ------------------------------------------------------------

    if action == "HOLD_FOR_REVIEW":

        subscription[
            "status"
        ] = "HUMAN_REVIEW"

        subscription[
            "next_retry_at"
        ] = None

        _audit(
            "SUBSCRIPTION_ACTION_SELECTED",
            subscription,
            action=action,
            decision_reason=decision[
                "reason"
            ],
        )

        persist_subscription(
            subscription
        )

        return {
            "success": True,
            "action": action,
            "status": subscription[
                "status"
            ],
            "reason": decision[
                "reason"
            ],
            "subscription": subscription,
        }

    # ------------------------------------------------------------
    # SEND UPDATE LINK
    # ------------------------------------------------------------

    if action == "SEND_UPDATE_LINK":

        subscription[
            "status"
        ] = "AWAITING_CUSTOMER_ACTION"

        retry_index = min(
            int(
                subscription.get(
                    "retry_count",
                    0,
                )
            ),
            len(
                RETRY_DELAYS_HOURS
            ) - 1,
        )

        next_retry_hours = RETRY_DELAYS_HOURS[
            retry_index
        ]

        next_retry = (
            datetime.now(
                timezone.utc
            )
            + timedelta(
                hours=next_retry_hours
            )
        )

        subscription[
            "next_retry_at"
        ] = next_retry.isoformat()

        _audit(
            "SUBSCRIPTION_UPDATE_LINK_SENT",
            subscription,
            action=action,
            next_retry_at=subscription[
                "next_retry_at"
            ],
        )

        persist_subscription(
            subscription
        )

        persist_recovery_attempt(
            entity_type="subscription",
            entity_id=subscription[
                "subscription_id"
            ],
            action=action,
            attempt_number=int(
                subscription.get(
                    "retry_count",
                    0,
                )
            ),
            status=subscription[
                "status"
            ],
            recovery_probability=subscription.get(
                "recovery_probability"
            ),
            scheduled_for=subscription.get(
                "next_retry_at"
            ),
        )

        return {
            "success": True,
            "action": action,
            "status": subscription[
                "status"
            ],
            "reason": decision[
                "reason"
            ],
            "next_retry_at": subscription[
                "next_retry_at"
            ],
            "subscription": subscription,
        }

    # ------------------------------------------------------------
    # RETRY PAYMENT
    # ------------------------------------------------------------

    if action == "RETRY_PAYMENT":

        current_retry = int(
            subscription.get(
                "retry_count",
                0,
            )
        )

        if current_retry >= MAX_RETRIES:

            subscription[
                "status"
            ] = "RETRY_EXHAUSTED"

            subscription[
                "next_retry_at"
            ] = None

            _audit(
                "SUBSCRIPTION_RETRY_BLOCKED",
                subscription,
                reason=(
                    "Maximum retry limit reached."
                ),
            )

            persist_subscription(
                subscription
            )

            return {
                "success": False,
                "action": "RETRY_PAYMENT",
                "status": "RETRY_EXHAUSTED",
                "reason": (
                    "Maximum retry limit reached."
                ),
                "subscription": subscription,
            }

        retry_number = (
            current_retry + 1
        )

        subscription[
            "retry_count"
        ] = retry_number

        subscription[
            "status"
        ] = "RETRY_SCHEDULED"

        delay_index = min(
            current_retry,
            len(
                RETRY_DELAYS_HOURS
            ) - 1,
        )

        next_retry = (
            datetime.now(
                timezone.utc
            )
            + timedelta(
                hours=RETRY_DELAYS_HOURS[
                    delay_index
                ]
            )
        )

        subscription[
            "next_retry_at"
        ] = next_retry.isoformat()

        _audit(
            "SUBSCRIPTION_RETRY_SCHEDULED",
            subscription,
            action=action,
            retry_number=retry_number,
            next_retry_at=subscription[
                "next_retry_at"
            ],
        )

        # SQL persistence.
        persist_subscription(
            subscription
        )

        persist_recovery_attempt(
            entity_type="subscription",
            entity_id=subscription[
                "subscription_id"
            ],
            action=action,
            attempt_number=retry_number,
            status=subscription[
                "status"
            ],
            recovery_probability=subscription.get(
                "recovery_probability"
            ),
            scheduled_for=subscription.get(
                "next_retry_at"
            ),
        )

        return {
            "success": True,
            "action": action,
            "status": subscription[
                "status"
            ],
            "reason": decision[
                "reason"
            ],
            "retry_number": retry_number,
            "next_retry_at": subscription[
                "next_retry_at"
            ],
            "subscription": subscription,
        }

    # ------------------------------------------------------------
    # UNKNOWN ACTION
    # ------------------------------------------------------------

    subscription[
        "status"
    ] = "HUMAN_REVIEW"

    subscription[
        "next_retry_at"
    ] = None

    _audit(
        "SUBSCRIPTION_ACTION_BLOCKED",
        subscription,
        reason="Unknown recovery action.",
    )

    persist_subscription(
        subscription
    )

    return {
        "success": False,
        "action": action,
        "status": subscription[
            "status"
        ],
        "reason": "Unknown recovery action.",
        "subscription": subscription,
    }


# ================================================================
# VERIFY PAYMENT
# ================================================================

def verify_subscription_payment(
    subscription: Dict[str, Any],
    paid_amount: float,
) -> Dict[str, Any]:
    """
    Reconcile an incoming payment against the failed subscription.
    """

    paid_amount = float(
        paid_amount
    )

    required_amount = float(
        subscription.get(
            "amount",
            0.0,
        )
    )

    if subscription.get(
        "payment_verified"
    ):

        return {
            "verified": False,
            "reason": (
                "Subscription payment has already been verified."
            ),
            "subscription": subscription,
        }

    if paid_amount < required_amount:

        _audit(
            "SUBSCRIPTION_PAYMENT_VERIFICATION_FAILED",
            subscription,
            paid_amount=paid_amount,
            required_amount=required_amount,
            reason=(
                "Paid amount is below subscription amount."
            ),
        )

        return {
            "verified": False,
            "reason": (
                "Paid amount is below the subscription amount."
            ),
            "required_amount": required_amount,
            "paid_amount": paid_amount,
            "subscription": subscription,
        }

    subscription[
        "payment_verified"
    ] = True

    subscription[
        "recovered_amount"
    ] = paid_amount

    subscription[
        "status"
    ] = "RECOVERED"

    subscription[
        "next_retry_at"
    ] = None

    subscription[
        "verified_at"
    ] = _now()

    subscription[
        "updated_at"
    ] = _now()

    _audit(
        "SUBSCRIPTION_PAYMENT_VERIFIED",
        subscription,
        paid_amount=paid_amount,
        recovered_amount=paid_amount,
    )

    # Save final subscription state.
    persist_subscription(
        subscription
    )

    # Save the recovery outcome as DEMO by default.
    # Production remains explicitly false.
    persist_outcome(
        entity_type="subscription",
        entity_id=subscription[
            "subscription_id"
        ],
        customer_id=subscription.get(
            "customer_id",
            "",
        ),
        amount_at_risk=subscription.get(
            "amount",
            0,
        ),
        recovered_amount=subscription.get(
            "recovered_amount",
            0,
        ),
        recovered=True,
        final_action=subscription.get(
            "recovery_action",
            "RETRY_PAYMENT",
        ),
        recovery_probability=subscription.get(
            "recovery_probability"
        ),
        source="DEMO",
        production=False,
    )

    return {
        "verified": True,
        "status": "RECOVERED",
        "recovered_amount": paid_amount,
        "subscription": subscription,
    }


# ================================================================
# SUBSCRIPTION SUMMARY
# ================================================================

def subscription_recovery_summary(
    subscription: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Return a clean dashboard-friendly summary.
    """

    return {
        "subscription_id": subscription.get(
            "subscription_id"
        ),
        "customer_id": subscription.get(
            "customer_id"
        ),
        "payment_id": subscription.get(
            "payment_id"
        ),
        "amount": float(
            subscription.get(
                "amount",
                0.0,
            )
        ),
        "failure_reason": subscription.get(
            "failure_reason"
        ),
        "subscription_plan": subscription.get(
            "subscription_plan"
        ),
        "status": subscription.get(
            "status"
        ),
        "retry_count": int(
            subscription.get(
                "retry_count",
                0,
            )
        ),
        "max_retries": int(
            subscription.get(
                "max_retries",
                MAX_RETRIES,
            )
        ),
        "recovery_action": subscription.get(
            "recovery_action"
        ),
        "recovery_probability": subscription.get(
            "recovery_probability"
        ),
        "expected_recovered_value": subscription.get(
            "expected_recovered_value"
        ),
        "next_retry_at": subscription.get(
            "next_retry_at"
        ),
        "payment_verified": bool(
            subscription.get(
                "payment_verified",
                False,
            )
        ),
        "recovered_amount": float(
            subscription.get(
                "recovered_amount",
                0,
            )
        ),
    }


# ================================================================
# LOCAL DEMO
# ================================================================

def demo_failed_subscription() -> None:
    """
    Synthetic local smoke test.

    This is demo data and never writes production=True.
    """

    subscription = start_subscription_recovery(
        subscription_id="SUB_DEMO_001",
        customer_id="CUSTOMER_DEMO_001",
        payment_id="PAY_SUB_DEMO_001",
        amount=2499.0,
        failure_reason="bank_timeout",
        subscription_plan="monthly",
    )

    print()
    print("=" * 70)
    print("RecoverOS - FAILED SUBSCRIPTION RECOVERY")
    print("=" * 70)

    print(
        f"Subscription       : "
        f"{subscription['subscription_id']}"
    )

    print(
        f"Amount             : "
        f"{_money(subscription['amount'])}"
    )

    print(
        f"Failure            : "
        f"{subscription['failure_reason']}"
    )

    result = execute_subscription_action(
        subscription
    )

    print()
    print("RECOVERY DECISION")
    print("-" * 70)

    print(
        f"Action             : "
        f"{result['action']}"
    )

    print(
        f"Status             : "
        f"{result['status']}"
    )

    print(
        f"Reason             : "
        f"{result['reason']}"
    )

    if result.get(
        "next_retry_at"
    ):

        print(
            f"Next retry         : "
            f"{result['next_retry_at']}"
        )

    print()
    print("SIMULATED PAYMENT")
    print("-" * 70)

    verification = verify_subscription_payment(
        subscription,
        2499.0,
    )

    print(
        f"Verified           : "
        f"{verification['verified']}"
    )

    if verification.get(
        "verified"
    ):

        print(
            f"Recovered revenue  : "
            f"{_money(verification['recovered_amount'])}"
        )

    print()
    print("FINAL STATE")
    print("-" * 70)

    print(
        json.dumps(
            subscription_recovery_summary(
                subscription
            ),
            indent=2,
            ensure_ascii=False,
        )
    )

    print()
    print(
        "SQL persistence: COMPLETE"
    )


if __name__ == "__main__":
    demo_failed_subscription()



from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict
import json
import uuid

from persistence import (
    persist_mandate,
    persist_recovery_attempt,
    persist_outcome,
)


# ================================================================
# PATHS
# ================================================================

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent
DATA_DIR = BASE_DIR / "data"

MANDATE_AUDIT_FILE = (
    DATA_DIR / "mandate_retry_audit.jsonl"
)


# ================================================================
# BOUNDED RETRY POLICY
# ================================================================

MAX_MANDATE_RETRIES = 4

RETRY_DELAYS_HOURS = [
    1,
    6,
    24,
    72,
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


def _new_retry_id() -> str:
    return (
        "MANDATE_RETRY_"
        + uuid.uuid4().hex[:8].upper()
    )


# ================================================================
# AUDIT
# ================================================================

def _audit(
    event: str,
    mandate: Dict[str, Any],
    **extra: Any,
) -> None:

    record = {
        "timestamp": _now(),
        "event": event,
        "mandate_id": mandate.get(
            "mandate_id"
        ),
        "customer_id": mandate.get(
            "customer_id"
        ),
        "payment_id": mandate.get(
            "payment_id"
        ),
        "amount": float(
            mandate.get(
                "amount",
                0.0,
            )
        ),
        "status": mandate.get(
            "status"
        ),
        "retry_count": int(
            mandate.get(
                "retry_count",
                0,
            )
        ),
        "max_retries": int(
            mandate.get(
                "max_retries",
                MAX_MANDATE_RETRIES,
            )
        ),
        **extra,
    }

    _write_jsonl(
        MANDATE_AUDIT_FILE,
        record,
    )


# ================================================================
# START MANDATE RECOVERY
# ================================================================

def start_mandate_recovery(
    mandate_id: str,
    customer_id: str,
    payment_id: str,
    amount: float,
    failure_reason: str,
    mandate_type: str = "recurring",
) -> Dict[str, Any]:
    """
    Start a bounded mandate retry workflow.

    Demo/test state is persisted to SQL but is never marked
    as production by this module.
    """

    amount = float(
        amount
    )

    if amount <= 0:

        raise ValueError(
            "Mandate amount must be greater than zero."
        )

    mandate = {
        "mandate_id": mandate_id,
        "customer_id": customer_id,
        "payment_id": payment_id,
        "amount": amount,
        "failure_reason": failure_reason,
        "mandate_type": mandate_type,
        "status": "FAILED",
        "retry_count": 0,
        "max_retries": MAX_MANDATE_RETRIES,
        "next_retry_at": None,
        "retry_sequence": [],
        "recovery_action": None,
        "recovery_probability": None,
        "payment_verified": False,
        "recovered_amount": 0.0,
        "human_review_required": False,
        "created_at": _now(),
        "updated_at": _now(),
    }

    _audit(
        "MANDATE_RECOVERY_STARTED",
        mandate,
        failure_reason=failure_reason,
    )

    persist_mandate(
        mandate
    )

    return mandate


# ================================================================
# FAILURE CLASSIFICATION
# ================================================================

def classify_mandate_failure(
    failure_reason: str,
) -> Dict[str, Any]:
    """
    Determine whether a mandate failure can safely be retried.
    """

    reason = str(
        failure_reason
    ).strip().lower()

    temporary_failures = {
        "bank_timeout",
        "network_error",
        "temporary_bank_error",
        "issuer_unavailable",
        "technical_error",
        "gateway_timeout",
    }

    customer_action_required = {
        "insufficient_funds",
        "expired_card",
        "card_expired",
        "mandate_expired",
        "authentication_required",
    }

    hard_stop_failures = {
        "fraud",
        "suspicious",
        "account_closed",
        "mandate_revoked",
        "customer_blocked",
        "chargeback",
    }

    if reason in temporary_failures:

        return {
            "category": "TEMPORARY",
            "retryable": True,
            "customer_action_required": False,
            "hard_stop": False,
        }

    if reason in customer_action_required:

        return {
            "category": "CUSTOMER_ACTION_REQUIRED",
            "retryable": False,
            "customer_action_required": True,
            "hard_stop": False,
        }

    if reason in hard_stop_failures:

        return {
            "category": "HARD_STOP",
            "retryable": False,
            "customer_action_required": False,
            "hard_stop": True,
        }

    return {
        "category": "UNKNOWN",
        "retryable": False,
        "customer_action_required": True,
        "hard_stop": False,
    }


# ================================================================
# RETRY DECISION
# ================================================================

def determine_mandate_retry_action(
    mandate: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Choose the next bounded mandate intervention.
    """

    amount = float(
        mandate.get(
            "amount",
            0.0,
        )
    )

    retry_count = int(
        mandate.get(
            "retry_count",
            0,
        )
    )

    failure_reason = str(
        mandate.get(
            "failure_reason",
            "",
        )
    ).lower()

    classification = classify_mandate_failure(
        failure_reason
    )

    # ------------------------------------------------------------
    # HARD STOP
    # ------------------------------------------------------------

    if classification[
        "hard_stop"
    ]:

        return {
            "action": "HOLD_FOR_REVIEW",
            "reason": (
                "Mandate failure requires human review."
            ),
            "category": classification[
                "category"
            ],
            "retry_allowed": False,
            "recovery_probability": 0.0,
            "human_review_required": True,
        }

    # ------------------------------------------------------------
    # CUSTOMER ACTION
    # ------------------------------------------------------------

    if classification[
        "customer_action_required"
    ]:

        return {
            "action": "REQUEST_CUSTOMER_ACTION",
            "reason": (
                "Customer action is required before "
                "another mandate attempt."
            ),
            "category": classification[
                "category"
            ],
            "retry_allowed": False,
            "recovery_probability": 0.0,
            "human_review_required": False,
        }

    # ------------------------------------------------------------
    # UNKNOWN
    # ------------------------------------------------------------

    if not classification[
        "retryable"
    ]:

        return {
            "action": "HOLD_FOR_REVIEW",
            "reason": (
                "Failure cannot be safely classified "
                "as retryable."
            ),
            "category": classification[
                "category"
            ],
            "retry_allowed": False,
            "recovery_probability": 0.0,
            "human_review_required": True,
        }

    # ------------------------------------------------------------
    # RETRY LIMIT
    # ------------------------------------------------------------

    if retry_count >= MAX_MANDATE_RETRIES:

        return {
            "action": "STOP_RETRIES",
            "reason": (
                "Maximum mandate retry limit reached."
            ),
            "category": classification[
                "category"
            ],
            "retry_allowed": False,
            "recovery_probability": 0.0,
            "human_review_required": False,
        }

    # ------------------------------------------------------------
    # RECOVERY PROBABILITY
    # ------------------------------------------------------------

    probabilities = {
        "bank_timeout": 0.74,
        "network_error": 0.70,
        "temporary_bank_error": 0.72,
        "issuer_unavailable": 0.64,
        "technical_error": 0.60,
        "gateway_timeout": 0.68,
    }

    probability = probabilities.get(
        failure_reason,
        0.55,
    )

    probability *= (
        1.0 - (0.08 * retry_count)
    )

    probability = max(
        0.0,
        min(
            probability,
            1.0,
        ),
    )

    # High-value mandates require human review.
    if amount >= HIGH_VALUE_REVIEW_THRESHOLD:

        return {
            "action": "HOLD_FOR_REVIEW",
            "reason": (
                "High-value mandate requires "
                "human review."
            ),
            "category": classification[
                "category"
            ],
            "retry_allowed": False,
            "recovery_probability": 0.0,
            "human_review_required": True,
        }

    return {
        "action": "RETRY_MANDATE",
        "reason": (
            "Temporary mandate failure is retryable."
        ),
        "category": classification[
            "category"
        ],
        "retry_allowed": True,
        "recovery_probability": probability,
        "human_review_required": False,
    }


# ================================================================
# EXECUTE NEXT RETRY
# ================================================================

def execute_next_mandate_retry(
    mandate: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute exactly one step of the mandate retry sequence.
    """

    decision = determine_mandate_retry_action(
        mandate
    )

    action = decision[
        "action"
    ]

    mandate[
        "recovery_action"
    ] = action

    mandate[
        "recovery_probability"
    ] = decision[
        "recovery_probability"
    ]

    mandate[
        "updated_at"
    ] = _now()

    mandate[
        "human_review_required"
    ] = decision[
        "human_review_required"
    ]

    # ------------------------------------------------------------
    # HOLD FOR REVIEW
    # ------------------------------------------------------------

    if action == "HOLD_FOR_REVIEW":

        mandate[
            "status"
        ] = "HUMAN_REVIEW"

        mandate[
            "next_retry_at"
        ] = None

        _audit(
            "MANDATE_RETRY_HELD",
            mandate,
            action=action,
            reason=decision[
                "reason"
            ],
        )

        persist_mandate(
            mandate
        )

        return {
            "success": True,
            "action": action,
            "status": mandate[
                "status"
            ],
            "reason": decision[
                "reason"
            ],
            "mandate": mandate,
        }

    # ------------------------------------------------------------
    # CUSTOMER ACTION
    # ------------------------------------------------------------

    if action == "REQUEST_CUSTOMER_ACTION":

        mandate[
            "status"
        ] = "AWAITING_CUSTOMER_ACTION"

        mandate[
            "next_retry_at"
        ] = None

        _audit(
            "MANDATE_CUSTOMER_ACTION_REQUIRED",
            mandate,
            action=action,
            reason=decision[
                "reason"
            ],
        )

        persist_mandate(
            mandate
        )

        persist_recovery_attempt(
            entity_type="mandate",
            entity_id=mandate[
                "mandate_id"
            ],
            action=action,
            attempt_number=int(
                mandate.get(
                    "retry_count",
                    0,
                )
            ),
            status=mandate[
                "status"
            ],
            recovery_probability=0.0,
        )

        return {
            "success": True,
            "action": action,
            "status": mandate[
                "status"
            ],
            "reason": decision[
                "reason"
            ],
            "mandate": mandate,
        }

    # ------------------------------------------------------------
    # STOP
    # ------------------------------------------------------------

    if action == "STOP_RETRIES":

        mandate[
            "status"
        ] = "RETRY_EXHAUSTED"

        mandate[
            "next_retry_at"
        ] = None

        _audit(
            "MANDATE_RETRY_STOPPED",
            mandate,
            reason=decision[
                "reason"
            ],
        )

        persist_mandate(
            mandate
        )

        return {
            "success": False,
            "action": action,
            "status": mandate[
                "status"
            ],
            "reason": decision[
                "reason"
            ],
            "mandate": mandate,
        }

    # ------------------------------------------------------------
    # RETRY
    # ------------------------------------------------------------

    if action == "RETRY_MANDATE":

        current_retry = int(
            mandate.get(
                "retry_count",
                0,
            )
        )

        if current_retry >= MAX_MANDATE_RETRIES:

            mandate[
                "status"
            ] = "RETRY_EXHAUSTED"

            mandate[
                "next_retry_at"
            ] = None

            _audit(
                "MANDATE_RETRY_BLOCKED",
                mandate,
                reason=(
                    "Maximum mandate retry limit reached."
                ),
            )

            persist_mandate(
                mandate
            )

            return {
                "success": False,
                "action": action,
                "status": "RETRY_EXHAUSTED",
                "reason": (
                    "Maximum mandate retry limit reached."
                ),
                "mandate": mandate,
            }

        retry_number = (
            current_retry + 1
        )

        delay_hours = RETRY_DELAYS_HOURS[
            min(
                current_retry,
                len(
                    RETRY_DELAYS_HOURS
                ) - 1,
            )
        ]

        next_retry = (
            datetime.now(
                timezone.utc
            )
            + timedelta(
                hours=delay_hours
            )
        )

        retry_record = {
            "retry_id": _new_retry_id(),
            "retry_number": retry_number,
            "scheduled_at": _now(),
            "scheduled_for": next_retry.isoformat(),
            "delay_hours": delay_hours,
            "recovery_probability": decision[
                "recovery_probability"
            ],
            "status": "SCHEDULED",
        }

        mandate[
            "retry_sequence"
        ].append(
            retry_record
        )

        mandate[
            "retry_count"
        ] = retry_number

        mandate[
            "next_retry_at"
        ] = next_retry.isoformat()

        mandate[
            "status"
        ] = "RETRY_SCHEDULED"

        _audit(
            "MANDATE_RETRY_SCHEDULED",
            mandate,
            action=action,
            retry_number=retry_number,
            delay_hours=delay_hours,
            next_retry_at=next_retry.isoformat(),
            recovery_probability=decision[
                "recovery_probability"
            ],
        )

        persist_mandate(
            mandate
        )

        persist_recovery_attempt(
            entity_type="mandate",
            entity_id=mandate[
                "mandate_id"
            ],
            action=action,
            attempt_number=retry_number,
            status=mandate[
                "status"
            ],
            recovery_probability=decision[
                "recovery_probability"
            ],
            scheduled_for=mandate[
                "next_retry_at"
            ],
        )

        return {
            "success": True,
            "action": action,
            "status": mandate[
                "status"
            ],
            "reason": decision[
                "reason"
            ],
            "retry_number": retry_number,
            "max_retries": MAX_MANDATE_RETRIES,
            "next_retry_at": next_retry.isoformat(),
            "recovery_probability": decision[
                "recovery_probability"
            ],
            "mandate": mandate,
        }

    # ------------------------------------------------------------
    # UNKNOWN
    # ------------------------------------------------------------

    mandate[
        "status"
    ] = "HUMAN_REVIEW"

    mandate[
        "next_retry_at"
    ] = None

    _audit(
        "MANDATE_ACTION_BLOCKED",
        mandate,
        reason="Unknown recovery action.",
    )

    persist_mandate(
        mandate
    )

    return {
        "success": False,
        "action": action,
        "status": mandate[
            "status"
        ],
        "reason": "Unknown recovery action.",
        "mandate": mandate,
    }


# ================================================================
# PAYMENT VERIFICATION
# ================================================================

def verify_mandate_payment(
    mandate: Dict[str, Any],
    paid_amount: float,
) -> Dict[str, Any]:
    """
    Verify an incoming payment against the mandate amount.
    """

    paid_amount = float(
        paid_amount
    )

    required_amount = float(
        mandate.get(
            "amount",
            0.0,
        )
    )

    if mandate.get(
        "payment_verified"
    ):

        return {
            "verified": False,
            "reason": (
                "Mandate payment has already been verified."
            ),
            "mandate": mandate,
        }

    if paid_amount < required_amount:

        _audit(
            "MANDATE_PAYMENT_VERIFICATION_FAILED",
            mandate,
            paid_amount=paid_amount,
            required_amount=required_amount,
            reason=(
                "Paid amount is below mandate amount."
            ),
        )

        return {
            "verified": False,
            "reason": (
                "Paid amount is below the mandate amount."
            ),
            "required_amount": required_amount,
            "paid_amount": paid_amount,
            "mandate": mandate,
        }

    mandate[
        "payment_verified"
    ] = True

    mandate[
        "recovered_amount"
    ] = paid_amount

    mandate[
        "status"
    ] = "RECOVERED"

    mandate[
        "next_retry_at"
    ] = None

    mandate[
        "verified_at"
    ] = _now()

    mandate[
        "updated_at"
    ] = _now()

    _audit(
        "MANDATE_PAYMENT_VERIFIED",
        mandate,
        paid_amount=paid_amount,
        recovered_amount=paid_amount,
    )

    persist_mandate(
        mandate
    )

    persist_outcome(
        entity_type="mandate",
        entity_id=mandate[
            "mandate_id"
        ],
        customer_id=mandate.get(
            "customer_id",
            "",
        ),
        amount_at_risk=mandate.get(
            "amount",
            0,
        ),
        recovered_amount=mandate.get(
            "recovered_amount",
            0,
        ),
        recovered=True,
        final_action=mandate.get(
            "recovery_action",
            "RETRY_MANDATE",
        ),
        recovery_probability=mandate.get(
            "recovery_probability"
        ),
        source="DEMO",
        production=False,
    )

    return {
        "verified": True,
        "status": "RECOVERED",
        "recovered_amount": paid_amount,
        "mandate": mandate,
    }


# ================================================================
# SUMMARY
# ================================================================

def mandate_recovery_summary(
    mandate: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Return dashboard-friendly mandate state.
    """

    return {
        "mandate_id": mandate.get(
            "mandate_id"
        ),
        "customer_id": mandate.get(
            "customer_id"
        ),
        "payment_id": mandate.get(
            "payment_id"
        ),
        "amount": float(
            mandate.get(
                "amount",
                0.0,
            )
        ),
        "failure_reason": mandate.get(
            "failure_reason"
        ),
        "mandate_type": mandate.get(
            "mandate_type"
        ),
        "status": mandate.get(
            "status"
        ),
        "retry_count": int(
            mandate.get(
                "retry_count",
                0,
            )
        ),
        "max_retries": int(
            mandate.get(
                "max_retries",
                MAX_MANDATE_RETRIES,
            )
        ),
        "next_retry_at": mandate.get(
            "next_retry_at"
        ),
        "retry_sequence": mandate.get(
            "retry_sequence",
            [],
        ),
        "recovery_action": mandate.get(
            "recovery_action"
        ),
        "recovery_probability": mandate.get(
            "recovery_probability"
        ),
        "payment_verified": bool(
            mandate.get(
                "payment_verified",
                False,
            )
        ),
        "recovered_amount": float(
            mandate.get(
                "recovered_amount",
                0.0,
            )
        ),
        "human_review_required": bool(
            mandate.get(
                "human_review_required",
                False,
            )
        ),
    }


# ================================================================
# LOCAL SMOKE TEST
# ================================================================

def demo_mandate_retry() -> None:
    """
    Synthetic local smoke test.

    This creates SQL demo/test records and the mandate
    audit trail. It never creates production=True.
    """

    mandate = start_mandate_recovery(
        mandate_id="MANDATE_DEMO_001",
        customer_id="CUSTOMER_DEMO_001",
        payment_id="PAY_MANDATE_DEMO_001",
        amount=3499.0,
        failure_reason="bank_timeout",
        mandate_type="recurring",
    )

    print()
    print("=" * 70)
    print("RecoverOS - MANDATE RETRY SEQUENCER")
    print("=" * 70)

    print(
        f"Mandate            : "
        f"{mandate['mandate_id']}"
    )

    print(
        f"Amount             : "
        f"{_money(mandate['amount'])}"
    )

    print(
        f"Failure            : "
        f"{mandate['failure_reason']}"
    )

    print()
    print("RETRY SEQUENCE")
    print("-" * 70)

    for attempt in range(
        MAX_MANDATE_RETRIES
    ):

        result = execute_next_mandate_retry(
            mandate
        )

        print(
            f"Step {attempt + 1}: "
            f"{result['action']} | "
            f"{result['status']}"
        )

        if result.get(
            "next_retry_at"
        ):

            print(
                f"  Next retry: "
                f"{result['next_retry_at']}"
            )

        if result[
            "status"
        ] in {
            "HUMAN_REVIEW",
            "AWAITING_CUSTOMER_ACTION",
            "RETRY_EXHAUSTED",
        }:

            break

    print()
    print("PAYMENT VERIFICATION")
    print("-" * 70)

    verification = verify_mandate_payment(
        mandate,
        3499.0,
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
            mandate_recovery_summary(
                mandate
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
    demo_mandate_retry()


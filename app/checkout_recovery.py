
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict
import json
import uuid

from persistence import (
    persist_checkout,
    persist_recovery_attempt,
    persist_outcome,
)


# ================================================================
# PATHS
# ================================================================

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent
DATA_DIR = BASE_DIR / "data"

CHECKOUT_AUDIT_FILE = (
    DATA_DIR / "checkout_recovery_audit.jsonl"
)


# ================================================================
# BOUNDED RECOVERY POLICY
# ================================================================

MAX_RECOVERY_ATTEMPTS = 2

FOLLOWUP_DELAYS_MINUTES = [
    10,
    60,
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


def _new_attempt_id() -> str:
    return (
        "CHECKOUT_ATTEMPT_"
        + uuid.uuid4().hex[:8].upper()
    )


# ================================================================
# AUDIT
# ================================================================

def _audit(
    event: str,
    checkout: Dict[str, Any],
    **extra: Any,
) -> None:

    record = {
        "timestamp": _now(),
        "event": event,
        "checkout_id": checkout.get(
            "checkout_id"
        ),
        "customer_id": checkout.get(
            "customer_id"
        ),
        "payment_id": checkout.get(
            "payment_id"
        ),
        "amount": float(
            checkout.get(
                "amount",
                0.0,
            )
        ),
        "dropoff_reason": checkout.get(
            "dropoff_reason"
        ),
        "status": checkout.get(
            "status"
        ),
        "attempt_count": int(
            checkout.get(
                "attempt_count",
                0,
            )
        ),
        "max_attempts": int(
            checkout.get(
                "max_attempts",
                MAX_RECOVERY_ATTEMPTS,
            )
        ),
        **extra,
    }

    _write_jsonl(
        CHECKOUT_AUDIT_FILE,
        record,
    )


# ================================================================
# START CHECKOUT RECOVERY
# ================================================================

def start_checkout_recovery(
    checkout_id: str,
    customer_id: str,
    payment_id: str,
    amount: float,
    dropoff_reason: str,
    checkout_stage: str = "payment",
) -> Dict[str, Any]:
    """
    Start a bounded recovery workflow for a checkout
    that was started but not completed.
    """

    amount = float(amount)

    if amount <= 0:

        raise ValueError(
            "Checkout amount must be greater than zero."
        )

    checkout = {
        "checkout_id": checkout_id,
        "customer_id": customer_id,
        "payment_id": payment_id,
        "amount": amount,
        "dropoff_reason": dropoff_reason,
        "checkout_stage": checkout_stage,
        "status": "DROPPED_OFF",
        "attempt_count": 0,
        "max_attempts": MAX_RECOVERY_ATTEMPTS,
        "next_followup_at": None,
        "recovery_action": None,
        "recovery_probability": None,
        "expected_recovered_value": None,
        "attempt_sequence": [],
        "payment_verified": False,
        "recovered_amount": 0.0,
        "human_review_required": False,
        "created_at": _now(),
        "updated_at": _now(),
    }

    _audit(
        "CHECKOUT_RECOVERY_STARTED",
        checkout,
        dropoff_reason=dropoff_reason,
    )

    # Persist checkout + related customer/payment.
    persist_checkout(
        checkout
    )

    return checkout


# ================================================================
# DROP-OFF CLASSIFICATION
# ================================================================

def classify_checkout_dropoff(
    dropoff_reason: str,
) -> Dict[str, Any]:
    """
    Classify why a customer abandoned checkout.
    """

    reason = str(
        dropoff_reason
    ).strip().lower()

    payment_friction = {
        "payment_failed",
        "bank_timeout",
        "network_error",
        "technical_error",
        "gateway_error",
    }

    price_or_decision = {
        "price_concern",
        "too_expensive",
        "changed_mind",
        "needs_time",
    }

    checkout_friction = {
        "checkout_error",
        "page_error",
        "technical_checkout_issue",
        "session_expired",
    }

    customer_action = {
        "authentication_required",
        "otp_failed",
        "customer_not_ready",
    }

    hard_stop = {
        "fraud",
        "suspicious_activity",
        "customer_blocked",
    }

    if reason in payment_friction:

        return {
            "category": "PAYMENT_FRICTION",
            "recovery_supported": True,
            "preferred_action": "SEND_PAYMENT_LINK",
            "hard_stop": False,
        }

    if reason in price_or_decision:

        return {
            "category": "PURCHASE_HESITATION",
            "recovery_supported": True,
            "preferred_action": "SEND_CHECKOUT_REMINDER",
            "hard_stop": False,
        }

    if reason in checkout_friction:

        return {
            "category": "CHECKOUT_FRICTION",
            "recovery_supported": True,
            "preferred_action": "SEND_CHECKOUT_RETRY_LINK",
            "hard_stop": False,
        }

    if reason in customer_action:

        return {
            "category": "CUSTOMER_ACTION_REQUIRED",
            "recovery_supported": True,
            "preferred_action": "SEND_CHECKOUT_REMINDER",
            "hard_stop": False,
        }

    if reason in hard_stop:

        return {
            "category": "HARD_STOP",
            "recovery_supported": False,
            "preferred_action": "HOLD_FOR_REVIEW",
            "hard_stop": True,
        }

    return {
        "category": "UNKNOWN",
        "recovery_supported": False,
        "preferred_action": "HOLD_FOR_REVIEW",
        "hard_stop": False,
    }


# ================================================================
# RECOVERY DECISION
# ================================================================

def determine_checkout_action(
    checkout: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Determine the next bounded checkout recovery action.
    """

    amount = float(
        checkout.get(
            "amount",
            0.0,
        )
    )

    attempt_count = int(
        checkout.get(
            "attempt_count",
            0,
        )
    )

    dropoff_reason = checkout.get(
        "dropoff_reason",
        "",
    )

    classification = classify_checkout_dropoff(
        dropoff_reason
    )

    if classification["hard_stop"]:

        return {
            "action": "HOLD_FOR_REVIEW",
            "reason": (
                "Checkout activity requires human review."
            ),
            "category": classification[
                "category"
            ],
            "recovery_probability": 0.0,
            "human_review_required": True,
        }

    if attempt_count >= MAX_RECOVERY_ATTEMPTS:

        return {
            "action": "STOP_RECOVERY",
            "reason": (
                "Maximum checkout recovery attempts reached."
            ),
            "category": classification[
                "category"
            ],
            "recovery_probability": 0.0,
            "human_review_required": False,
        }

    if not classification[
        "recovery_supported"
    ]:

        return {
            "action": "HOLD_FOR_REVIEW",
            "reason": (
                "Drop-off reason could not be safely handled "
                "by the automated recovery workflow."
            ),
            "category": classification[
                "category"
            ],
            "recovery_probability": 0.0,
            "human_review_required": True,
        }

    if amount >= HIGH_VALUE_REVIEW_THRESHOLD:

        return {
            "action": "HOLD_FOR_REVIEW",
            "reason": (
                "High-value checkout requires human review."
            ),
            "category": classification[
                "category"
            ],
            "recovery_probability": 0.0,
            "human_review_required": True,
        }

    probabilities = {
        "SEND_PAYMENT_LINK": 0.58,
        "SEND_CHECKOUT_REMINDER": 0.42,
        "SEND_CHECKOUT_RETRY_LINK": 0.52,
    }

    probability = probabilities.get(
        classification["preferred_action"],
        0.35,
    )

    probability *= (
        1.0 - (0.15 * attempt_count)
    )

    probability = max(
        0.0,
        min(
            probability,
            1.0,
        ),
    )

    return {
        "action": classification[
            "preferred_action"
        ],
        "reason": (
            f"Drop-off classified as "
            f"{classification['category']}; "
            f"bounded recovery intervention selected."
        ),
        "category": classification[
            "category"
        ],
        "recovery_probability": probability,
        "human_review_required": False,
    }


# ================================================================
# EXECUTE RECOVERY ACTION
# ================================================================

def execute_checkout_recovery(
    checkout: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute one bounded checkout recovery attempt.
    """

    decision = determine_checkout_action(
        checkout
    )

    action = decision[
        "action"
    ]

    checkout[
        "recovery_action"
    ] = action

    checkout[
        "recovery_probability"
    ] = decision[
        "recovery_probability"
    ]

    checkout[
        "human_review_required"
    ] = decision[
        "human_review_required"
    ]

    checkout[
        "expected_recovered_value"
    ] = round(
        float(
            checkout.get(
                "amount",
                0.0,
            )
        )
        * float(
            decision[
                "recovery_probability"
            ]
        ),
        2,
    )

    checkout[
        "updated_at"
    ] = _now()

    # ------------------------------------------------------------
    # HUMAN REVIEW
    # ------------------------------------------------------------

    if action == "HOLD_FOR_REVIEW":

        checkout[
            "status"
        ] = "HUMAN_REVIEW"

        checkout[
            "next_followup_at"
        ] = None

        _audit(
            "CHECKOUT_RECOVERY_HELD",
            checkout,
            action=action,
            reason=decision[
                "reason"
            ],
        )

        persist_checkout(
            checkout
        )

        return {
            "success": True,
            "action": action,
            "status": checkout[
                "status"
            ],
            "reason": decision[
                "reason"
            ],
            "checkout": checkout,
        }

    # ------------------------------------------------------------
    # STOP
    # ------------------------------------------------------------

    if action == "STOP_RECOVERY":

        checkout[
            "status"
        ] = "RECOVERY_STOPPED"

        checkout[
            "next_followup_at"
        ] = None

        _audit(
            "CHECKOUT_RECOVERY_STOPPED",
            checkout,
            reason=decision[
                "reason"
            ],
        )

        persist_checkout(
            checkout
        )

        return {
            "success": False,
            "action": action,
            "status": checkout[
                "status"
            ],
            "reason": decision[
                "reason"
            ],
            "checkout": checkout,
        }

    # ------------------------------------------------------------
    # SCHEDULE RECOVERY
    # ------------------------------------------------------------

    current_attempt = int(
        checkout.get(
            "attempt_count",
            0,
        )
    )

    if current_attempt >= MAX_RECOVERY_ATTEMPTS:

        checkout[
            "status"
        ] = "RECOVERY_STOPPED"

        checkout[
            "next_followup_at"
        ] = None

        _audit(
            "CHECKOUT_RECOVERY_BLOCKED",
            checkout,
            reason=(
                "Maximum checkout recovery attempts reached."
            ),
        )

        persist_checkout(
            checkout
        )

        return {
            "success": False,
            "action": action,
            "status": "RECOVERY_STOPPED",
            "reason": (
                "Maximum checkout recovery attempts reached."
            ),
            "checkout": checkout,
        }

    attempt_number = (
        current_attempt + 1
    )

    delay_minutes = FOLLOWUP_DELAYS_MINUTES[
        min(
            current_attempt,
            len(
                FOLLOWUP_DELAYS_MINUTES
            ) - 1,
        )
    ]

    followup_time = (
        datetime.now(
            timezone.utc
        )
        + timedelta(
            minutes=delay_minutes
        )
    )

    attempt_record = {
        "attempt_id": _new_attempt_id(),
        "attempt_number": attempt_number,
        "action": action,
        "scheduled_at": _now(),
        "scheduled_for": followup_time.isoformat(),
        "delay_minutes": delay_minutes,
        "recovery_probability": decision[
            "recovery_probability"
        ],
        "status": "SCHEDULED",
    }

    checkout[
        "attempt_sequence"
    ].append(
        attempt_record
    )

    checkout[
        "attempt_count"
    ] = attempt_number

    checkout[
        "next_followup_at"
    ] = followup_time.isoformat()

    checkout[
        "status"
    ] = "RECOVERY_SCHEDULED"

    _audit(
        "CHECKOUT_RECOVERY_SCHEDULED",
        checkout,
        action=action,
        attempt_number=attempt_number,
        delay_minutes=delay_minutes,
        next_followup_at=followup_time.isoformat(),
        recovery_probability=decision[
            "recovery_probability"
        ],
    )

    persist_checkout(
        checkout
    )

    persist_recovery_attempt(
        entity_type="checkout",
        entity_id=checkout[
            "checkout_id"
        ],
        action=action,
        attempt_number=attempt_number,
        status=checkout[
            "status"
        ],
        recovery_probability=decision[
            "recovery_probability"
        ],
        scheduled_for=checkout[
            "next_followup_at"
        ],
    )

    return {
        "success": True,
        "action": action,
        "status": checkout[
            "status"
        ],
        "reason": decision[
            "reason"
        ],
        "attempt_number": attempt_number,
        "max_attempts": MAX_RECOVERY_ATTEMPTS,
        "next_followup_at": followup_time.isoformat(),
        "recovery_probability": decision[
            "recovery_probability"
        ],
        "checkout": checkout,
    }


# ================================================================
# PAYMENT VERIFICATION
# ================================================================

def verify_checkout_payment(
    checkout: Dict[str, Any],
    paid_amount: float,
) -> Dict[str, Any]:
    """
    Verify the customer's later payment.
    """

    paid_amount = float(
        paid_amount
    )

    required_amount = float(
        checkout.get(
            "amount",
            0.0,
        )
    )

    if checkout.get(
        "payment_verified"
    ):

        return {
            "verified": False,
            "reason": (
                "Checkout payment has already been verified."
            ),
            "checkout": checkout,
        }

    if paid_amount < required_amount:

        _audit(
            "CHECKOUT_PAYMENT_VERIFICATION_FAILED",
            checkout,
            paid_amount=paid_amount,
            required_amount=required_amount,
            reason=(
                "Paid amount is below checkout amount."
            ),
        )

        return {
            "verified": False,
            "reason": (
                "Paid amount is below the checkout amount."
            ),
            "required_amount": required_amount,
            "paid_amount": paid_amount,
            "checkout": checkout,
        }

    checkout[
        "payment_verified"
    ] = True

    checkout[
        "recovered_amount"
    ] = paid_amount

    checkout[
        "status"
    ] = "RECOVERED"

    checkout[
        "next_followup_at"
    ] = None

    checkout[
        "verified_at"
    ] = _now()

    checkout[
        "updated_at"
    ] = _now()

    _audit(
        "CHECKOUT_PAYMENT_VERIFIED",
        checkout,
        paid_amount=paid_amount,
        recovered_amount=paid_amount,
    )

    persist_checkout(
        checkout
    )

    persist_outcome(
        entity_type="checkout",
        entity_id=checkout[
            "checkout_id"
        ],
        customer_id=checkout.get(
            "customer_id",
            "",
        ),
        amount_at_risk=checkout.get(
            "amount",
            0,
        ),
        recovered_amount=checkout.get(
            "recovered_amount",
            0,
        ),
        recovered=True,
        final_action=checkout.get(
            "recovery_action",
            "SEND_PAYMENT_LINK",
        ),
        recovery_probability=checkout.get(
            "recovery_probability"
        ),
        source="DEMO",
        production=False,
    )

    return {
        "verified": True,
        "status": "RECOVERED",
        "recovered_amount": paid_amount,
        "checkout": checkout,
    }


# ================================================================
# SUMMARY
# ================================================================

def checkout_recovery_summary(
    checkout: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Return dashboard-friendly state.
    """

    return {
        "checkout_id": checkout.get(
            "checkout_id"
        ),
        "customer_id": checkout.get(
            "customer_id"
        ),
        "payment_id": checkout.get(
            "payment_id"
        ),
        "amount": float(
            checkout.get(
                "amount",
                0.0,
            )
        ),
        "dropoff_reason": checkout.get(
            "dropoff_reason"
        ),
        "checkout_stage": checkout.get(
            "checkout_stage"
        ),
        "status": checkout.get(
            "status"
        ),
        "attempt_count": int(
            checkout.get(
                "attempt_count",
                0,
            )
        ),
        "max_attempts": int(
            checkout.get(
                "max_attempts",
                MAX_RECOVERY_ATTEMPTS,
            )
        ),
        "recovery_action": checkout.get(
            "recovery_action"
        ),
        "recovery_probability": checkout.get(
            "recovery_probability"
        ),
        "expected_recovered_value": checkout.get(
            "expected_recovered_value"
        ),
        "next_followup_at": checkout.get(
            "next_followup_at"
        ),
        "attempt_sequence": checkout.get(
            "attempt_sequence",
            [],
        ),
        "payment_verified": bool(
            checkout.get(
                "payment_verified",
                False,
            )
        ),
        "recovered_amount": float(
            checkout.get(
                "recovered_amount",
                0.0,
            )
        ),
        "human_review_required": bool(
            checkout.get(
                "human_review_required",
                False,
            )
        ),
    }


# ================================================================
# LOCAL SMOKE TEST
# ================================================================

def demo_checkout_recovery() -> None:
    """
    Synthetic local demo.

    Writes demo state to SQL and the checkout audit trail.
    Never creates production=True.
    """

    checkout = start_checkout_recovery(
        checkout_id="CHECKOUT_DEMO_001",
        customer_id="CUSTOMER_DEMO_001",
        payment_id="PAY_CHECKOUT_DEMO_001",
        amount=2999.0,
        dropoff_reason="payment_failed",
        checkout_stage="payment",
    )

    print()
    print("=" * 70)
    print("RecoverOS - CHECKOUT DROP-OFF RECOVERY")
    print("=" * 70)

    print(
        f"Checkout           : "
        f"{checkout['checkout_id']}"
    )

    print(
        f"Amount             : "
        f"{_money(checkout['amount'])}"
    )

    print(
        f"Drop-off reason    : "
        f"{checkout['dropoff_reason']}"
    )

    print()
    print("RECOVERY ATTEMPTS")
    print("-" * 70)

    for step in range(
        MAX_RECOVERY_ATTEMPTS
    ):

        result = execute_checkout_recovery(
            checkout
        )

        print(
            f"Attempt {step + 1}: "
            f"{result['action']} | "
            f"{result['status']}"
        )

        if result.get(
            "next_followup_at"
        ):

            print(
                f"  Follow-up: "
                f"{result['next_followup_at']}"
            )

        if result[
            "status"
        ] in {
            "HUMAN_REVIEW",
            "RECOVERY_STOPPED",
        }:

            break

    print()
    print("PAYMENT VERIFICATION")
    print("-" * 70)

    verification = verify_checkout_payment(
        checkout,
        2999.0,
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
            checkout_recovery_summary(
                checkout
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
    demo_checkout_recovery()


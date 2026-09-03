
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict
import json
import uuid

from persistence import (
    persist_receivable,
    persist_recovery_attempt,
    persist_promise,
    persist_outcome,
)


# ================================================================
# PATHS
# ================================================================

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent
DATA_DIR = BASE_DIR / "data"

RECEIVABLES_AUDIT_FILE = (
    DATA_DIR / "receivables_recovery_audit.jsonl"
)


# ================================================================
# BOUNDED COLLECTION POLICY
# ================================================================

MAX_ESCALATIONS = 3

ESCALATION_DELAYS_DAYS = [
    1,
    3,
    7,
]

HIGH_VALUE_REVIEW_THRESHOLD = 100000.0


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


def _new_escalation_id() -> str:
    return (
        "AR_ESC_"
        + uuid.uuid4().hex[:8].upper()
    )


# ================================================================
# AUDIT
# ================================================================

def _audit(
    event: str,
    receivable: Dict[str, Any],
    **extra: Any,
) -> None:

    record = {
        "timestamp": _now(),
        "event": event,
        "invoice_id": receivable.get(
            "invoice_id"
        ),
        "customer_id": receivable.get(
            "customer_id"
        ),
        "amount": float(
            receivable.get(
                "amount",
                0.0,
            )
        ),
        "days_overdue": int(
            receivable.get(
                "days_overdue",
                0,
            )
        ),
        "status": receivable.get(
            "status"
        ),
        "escalation_count": int(
            receivable.get(
                "escalation_count",
                0,
            )
        ),
        "max_escalations": int(
            receivable.get(
                "max_escalations",
                MAX_ESCALATIONS,
            )
        ),
        **extra,
    }

    _write_jsonl(
        RECEIVABLES_AUDIT_FILE,
        record,
    )


# ================================================================
# START RECEIVABLE RECOVERY
# ================================================================

def start_receivables_recovery(
    invoice_id: str,
    customer_id: str,
    amount: float,
    days_overdue: int,
    due_date: str,
    customer_name: str = "Demo Customer",
    invoice_currency: str = "INR",
) -> Dict[str, Any]:
    """
    Start a bounded B2B receivables collection workflow.
    """

    amount = float(
        amount
    )

    days_overdue = int(
        days_overdue
    )

    if amount <= 0:

        raise ValueError(
            "Invoice amount must be greater than zero."
        )

    if days_overdue < 0:

        raise ValueError(
            "Days overdue cannot be negative."
        )

    receivable = {
        "invoice_id": invoice_id,
        "customer_id": customer_id,
        "customer_name": customer_name,
        "amount": amount,
        "invoice_currency": invoice_currency,
        "days_overdue": days_overdue,
        "due_date": due_date,
        "status": "OVERDUE",
        "escalation_count": 0,
        "max_escalations": MAX_ESCALATIONS,
        "next_followup_at": None,
        "recovery_action": None,
        "recovery_priority": None,
        "recovery_probability": None,
        "expected_recovered_value": None,
        "escalation_sequence": [],
        "promise_to_pay": None,
        "payment_verified": False,
        "recovered_amount": 0.0,
        "human_review_required": False,
        "created_at": _now(),
        "updated_at": _now(),
    }

    _audit(
        "RECEIVABLE_RECOVERY_STARTED",
        receivable,
        days_overdue=days_overdue,
    )

    # Persist initial invoice state.
    persist_receivable(
        receivable
    )

    return receivable


# ================================================================
# PRIORITY CLASSIFICATION
# ================================================================

def classify_receivable_risk(
    receivable: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Assess urgency of an overdue B2B receivable.
    """

    amount = float(
        receivable.get(
            "amount",
            0.0,
        )
    )

    days_overdue = int(
        receivable.get(
            "days_overdue",
            0,
        )
    )

    if amount >= HIGH_VALUE_REVIEW_THRESHOLD:

        return {
            "priority": "HIGH",
            "category": "HIGH_VALUE",
            "human_review_required": True,
        }

    if days_overdue >= 30:

        return {
            "priority": "CRITICAL",
            "category": "SEVERELY_OVERDUE",
            "human_review_required": True,
        }

    if days_overdue >= 15:

        return {
            "priority": "HIGH",
            "category": "SIGNIFICANTLY_OVERDUE",
            "human_review_required": False,
        }

    if days_overdue >= 7:

        return {
            "priority": "MEDIUM",
            "category": "OVERDUE",
            "human_review_required": False,
        }

    return {
        "priority": "LOW",
        "category": "RECENTLY_OVERDUE",
        "human_review_required": False,
    }


# ================================================================
# COLLECTION DECISION
# ================================================================

def determine_receivables_action(
    receivable: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Select the next bounded B2B receivables intervention.
    """

    escalation_count = int(
        receivable.get(
            "escalation_count",
            0,
        )
    )

    risk = classify_receivable_risk(
        receivable
    )

    if risk["human_review_required"]:

        return {
            "action": "HUMAN_REVIEW",
            "reason": (
                "Receivable requires human review "
                "because of value or delinquency."
            ),
            "priority": risk["priority"],
            "recovery_probability": 0.0,
            "human_review_required": True,
        }

    if escalation_count >= MAX_ESCALATIONS:

        return {
            "action": "STOP_COLLECTION",
            "reason": (
                "Maximum automated collection escalations "
                "have been reached."
            ),
            "priority": risk["priority"],
            "recovery_probability": 0.0,
            "human_review_required": False,
        }

    if escalation_count == 0:

        action = "SEND_PAYMENT_REMINDER"

        probability = 0.60

        reason = (
            "Initial overdue reminder is the least "
            "intrusive recovery intervention."
        )

    elif escalation_count == 1:

        action = "SEND_ESCALATED_REMINDER"

        probability = 0.48

        reason = (
            "Invoice remains overdue after the initial reminder."
        )

    else:

        action = "REQUEST_PROMISE_TO_PAY"

        probability = 0.38

        reason = (
            "Repeated delinquency requires a structured "
            "Promise-to-Pay commitment."
        )

    days_overdue = int(
        receivable.get(
            "days_overdue",
            0,
        )
    )

    probability -= min(
        days_overdue * 0.005,
        0.15,
    )

    probability = max(
        0.0,
        min(
            probability,
            1.0,
        ),
    )

    return {
        "action": action,
        "reason": reason,
        "priority": risk["priority"],
        "recovery_probability": probability,
        "human_review_required": False,
    }


# ================================================================
# EXECUTE COLLECTION STEP
# ================================================================

def execute_receivables_action(
    receivable: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute exactly one bounded collection action.
    """

    decision = determine_receivables_action(
        receivable
    )

    action = decision[
        "action"
    ]

    receivable[
        "recovery_action"
    ] = action

    receivable[
        "recovery_priority"
    ] = decision[
        "priority"
    ]

    receivable[
        "recovery_probability"
    ] = decision[
        "recovery_probability"
    ]

    receivable[
        "human_review_required"
    ] = decision[
        "human_review_required"
    ]

    receivable[
        "expected_recovered_value"
    ] = round(
        float(
            receivable.get(
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

    receivable[
        "updated_at"
    ] = _now()

    # ------------------------------------------------------------
    # HUMAN REVIEW
    # ------------------------------------------------------------

    if action == "HUMAN_REVIEW":

        receivable[
            "status"
        ] = "HUMAN_REVIEW"

        receivable[
            "next_followup_at"
        ] = None

        _audit(
            "RECEIVABLE_HUMAN_REVIEW",
            receivable,
            action=action,
            reason=decision[
                "reason"
            ],
        )

        persist_receivable(
            receivable
        )

        return {
            "success": True,
            "action": action,
            "status": receivable[
                "status"
            ],
            "reason": decision[
                "reason"
            ],
            "priority": decision[
                "priority"
            ],
            "recovery_probability": decision[
                "recovery_probability"
            ],
            "receivable": receivable,
        }

    # ------------------------------------------------------------
    # STOP
    # ------------------------------------------------------------

    if action == "STOP_COLLECTION":

        receivable[
            "status"
        ] = "COLLECTION_STOPPED"

        receivable[
            "next_followup_at"
        ] = None

        _audit(
            "RECEIVABLE_COLLECTION_STOPPED",
            receivable,
            reason=decision[
                "reason"
            ],
        )

        persist_receivable(
            receivable
        )

        return {
            "success": False,
            "action": action,
            "status": receivable[
                "status"
            ],
            "reason": decision[
                "reason"
            ],
            "receivable": receivable,
        }

    # ------------------------------------------------------------
    # SCHEDULE NEXT STEP
    # ------------------------------------------------------------

    current_escalation = int(
        receivable.get(
            "escalation_count",
            0,
        )
    )

    if current_escalation >= MAX_ESCALATIONS:

        receivable[
            "status"
        ] = "COLLECTION_STOPPED"

        receivable[
            "next_followup_at"
        ] = None

        _audit(
            "RECEIVABLE_ESCALATION_BLOCKED",
            receivable,
            reason=(
                "Maximum collection escalations reached."
            ),
        )

        persist_receivable(
            receivable
        )

        return {
            "success": False,
            "action": action,
            "status": "COLLECTION_STOPPED",
            "reason": (
                "Maximum collection escalations reached."
            ),
            "receivable": receivable,
        }

    escalation_number = (
        current_escalation + 1
    )

    delay_days = ESCALATION_DELAYS_DAYS[
        min(
            current_escalation,
            len(
                ESCALATION_DELAYS_DAYS
            ) - 1,
        )
    ]

    next_followup = (
        datetime.now(
            timezone.utc
        )
        + timedelta(
            days=delay_days
        )
    )

    escalation_record = {
        "escalation_id": _new_escalation_id(),
        "escalation_number": escalation_number,
        "action": action,
        "created_at": _now(),
        "scheduled_for": next_followup.isoformat(),
        "delay_days": delay_days,
        "recovery_probability": decision[
            "recovery_probability"
        ],
        "status": "SCHEDULED",
    }

    receivable[
        "escalation_sequence"
    ].append(
        escalation_record
    )

    receivable[
        "escalation_count"
    ] = escalation_number

    receivable[
        "next_followup_at"
    ] = next_followup.isoformat()

    if action == "REQUEST_PROMISE_TO_PAY":

        receivable[
            "status"
        ] = "AWAITING_PROMISE_TO_PAY"

    else:

        receivable[
            "status"
        ] = "FOLLOWUP_SCHEDULED"

    _audit(
        "RECEIVABLE_ESCALATION_SCHEDULED",
        receivable,
        action=action,
        escalation_number=escalation_number,
        delay_days=delay_days,
        next_followup_at=next_followup.isoformat(),
        recovery_probability=decision[
            "recovery_probability"
        ],
    )

    persist_receivable(
        receivable
    )

    persist_recovery_attempt(
        entity_type="invoice",
        entity_id=receivable[
            "invoice_id"
        ],
        action=action,
        attempt_number=escalation_number,
        status=receivable[
            "status"
        ],
        recovery_probability=decision[
            "recovery_probability"
        ],
        scheduled_for=receivable[
            "next_followup_at"
        ],
    )

    return {
        "success": True,
        "action": action,
        "status": receivable[
            "status"
        ],
        "reason": decision[
            "reason"
        ],
        "priority": decision[
            "priority"
        ],
        "escalation_number": escalation_number,
        "max_escalations": MAX_ESCALATIONS,
        "next_followup_at": next_followup.isoformat(),
        "recovery_probability": decision[
            "recovery_probability"
        ],
        "receivable": receivable,
    }


# ================================================================
# PROMISE-TO-PAY
# ================================================================

def record_receivables_promise(
    receivable: Dict[str, Any],
    promised_date: str,
    response: str,
) -> Dict[str, Any]:
    """
    Record a structured B2B Promise-to-Pay commitment.
    """

    if receivable.get(
        "payment_verified"
    ):

        return {
            "success": False,
            "reason": (
                "Receivable has already been paid."
            ),
            "receivable": receivable,
        }

    promise_id = (
        "B2B_PTP_"
        + uuid.uuid4().hex[:8].upper()
    )

    promise = {
        "promise_id": promise_id,
        "promised_date": promised_date,
        "promised_amount": float(
            receivable.get(
                "amount",
                0.0,
            )
        ),
        "response": response,
        "created_at": _now(),
        "status": "PENDING",
    }

    receivable[
        "promise_to_pay"
    ] = promise

    receivable[
        "status"
    ] = "PROMISE_TO_PAY_ACTIVE"

    receivable[
        "updated_at"
    ] = _now()

    _audit(
        "RECEIVABLE_PROMISE_TO_PAY_RECORDED",
        receivable,
        promise=promise,
    )

    persist_receivable(
        receivable
    )

    persist_promise(
        entity_type="invoice",
        entity_id=receivable[
            "invoice_id"
        ],
        customer_id=receivable.get(
            "customer_id",
            ""
        ),
        promised_date=promised_date,
        promised_amount=receivable.get(
            "amount",
            0,
        ),
        response=response,
        status="PENDING",
        promise_id=promise_id,
    )

    return {
        "success": True,
        "promise": promise,
        "receivable": receivable,
    }


# ================================================================
# PAYMENT VERIFICATION
# ================================================================

def verify_receivables_payment(
    receivable: Dict[str, Any],
    paid_amount: float,
) -> Dict[str, Any]:
    """
    Verify payment against the overdue B2B invoice.
    """

    paid_amount = float(
        paid_amount
    )

    required_amount = float(
        receivable.get(
            "amount",
            0.0,
        )
    )

    if receivable.get(
        "payment_verified"
    ):

        return {
            "verified": False,
            "reason": (
                "Receivable payment has already been verified."
            ),
            "receivable": receivable,
        }

    if paid_amount < required_amount:

        _audit(
            "RECEIVABLE_PAYMENT_VERIFICATION_FAILED",
            receivable,
            paid_amount=paid_amount,
            required_amount=required_amount,
            reason=(
                "Paid amount is below invoice amount."
            ),
        )

        return {
            "verified": False,
            "reason": (
                "Paid amount is below the invoice amount."
            ),
            "required_amount": required_amount,
            "paid_amount": paid_amount,
            "receivable": receivable,
        }

    receivable[
        "payment_verified"
    ] = True

    receivable[
        "recovered_amount"
    ] = paid_amount

    receivable[
        "status"
    ] = "RECOVERED"

    receivable[
        "next_followup_at"
    ] = None

    receivable[
        "verified_at"
    ] = _now()

    receivable[
        "updated_at"
    ] = _now()

    if receivable.get(
        "promise_to_pay"
    ):

        receivable[
            "promise_to_pay"
        ][
            "status"
        ] = "FULFILLED"

        promise_id = receivable[
            "promise_to_pay"
        ].get(
            "promise_id"
        )

        if promise_id:

            # Keep SQL Promise-to-Pay synchronized.
            from database import execute

            execute(
                """
                UPDATE promise_to_pay
                SET
                    status = 'FULFILLED',
                    payment_verified = 1,
                    recovered_amount = ?,
                    verified_at = ?
                WHERE promise_id = ?
                """,
                (
                    paid_amount,
                    receivable[
                        "verified_at"
                    ],
                    promise_id,
                ),
            )

    _audit(
        "RECEIVABLE_PAYMENT_VERIFIED",
        receivable,
        paid_amount=paid_amount,
        recovered_amount=paid_amount,
    )

    persist_receivable(
        receivable
    )

    persist_outcome(
        entity_type="invoice",
        entity_id=receivable[
            "invoice_id"
        ],
        customer_id=receivable.get(
            "customer_id",
            ""
        ),
        amount_at_risk=receivable.get(
            "amount",
            0,
        ),
        recovered_amount=receivable.get(
            "recovered_amount",
            0,
        ),
        recovered=True,
        final_action=receivable.get(
            "recovery_action",
            "REQUEST_PROMISE_TO_PAY",
        ),
        recovery_probability=receivable.get(
            "recovery_probability"
        ),
        source="DEMO",
        production=False,
    )

    return {
        "verified": True,
        "status": "RECOVERED",
        "recovered_amount": paid_amount,
        "receivable": receivable,
    }


# ================================================================
# SUMMARY
# ================================================================

def receivables_recovery_summary(
    receivable: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Return dashboard-friendly B2B receivables state.
    """

    return {
        "invoice_id": receivable.get(
            "invoice_id"
        ),
        "customer_id": receivable.get(
            "customer_id"
        ),
        "customer_name": receivable.get(
            "customer_name"
        ),
        "amount": float(
            receivable.get(
                "amount",
                0.0,
            )
        ),
        "days_overdue": int(
            receivable.get(
                "days_overdue",
                0,
            )
        ),
        "due_date": receivable.get(
            "due_date"
        ),
        "status": receivable.get(
            "status"
        ),
        "escalation_count": int(
            receivable.get(
                "escalation_count",
                0,
            )
        ),
        "max_escalations": int(
            receivable.get(
                "max_escalations",
                MAX_ESCALATIONS,
            )
        ),
        "recovery_action": receivable.get(
            "recovery_action"
        ),
        "recovery_priority": receivable.get(
            "recovery_priority"
        ),
        "recovery_probability": receivable.get(
            "recovery_probability"
        ),
        "expected_recovered_value": receivable.get(
            "expected_recovered_value"
        ),
        "next_followup_at": receivable.get(
            "next_followup_at"
        ),
        "escalation_sequence": receivable.get(
            "escalation_sequence",
            [],
        ),
        "promise_to_pay": receivable.get(
            "promise_to_pay"
        ),
        "payment_verified": bool(
            receivable.get(
                "payment_verified",
                False,
            )
        ),
        "recovered_amount": float(
            receivable.get(
                "recovered_amount",
                0.0,
            )
        ),
        "human_review_required": bool(
            receivable.get(
                "human_review_required",
                False,
            )
        ),
    }


# ================================================================
# LOCAL SMOKE TEST
# ================================================================

def demo_receivables_recovery() -> None:
    """
    Synthetic local demo.

    Writes demo state into SQLite and JSONL audit.
    Never creates production=True.
    """

    receivable = start_receivables_recovery(
        invoice_id="INV_DEMO_001",
        customer_id="B2B_CUSTOMER_001",
        amount=45000.0,
        days_overdue=12,
        due_date="2026-08-22",
        customer_name="Demo Enterprise",
    )

    print()
    print("=" * 70)
    print("RecoverOS - B2B RECEIVABLES CHASER")
    print("=" * 70)

    print(
        f"Invoice             : "
        f"{receivable['invoice_id']}"
    )

    print(
        f"Customer            : "
        f"{receivable['customer_name']}"
    )

    print(
        f"Amount              : "
        f"{_money(receivable['amount'])}"
    )

    print(
        f"Days overdue        : "
        f"{receivable['days_overdue']}"
    )

    print()
    print("COLLECTION SEQUENCE")
    print("-" * 70)

    for step in range(
        MAX_ESCALATIONS
    ):

        result = execute_receivables_action(
            receivable
        )

        print(
            f"Step {step + 1}: "
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
            "COLLECTION_STOPPED",
            "AWAITING_PROMISE_TO_PAY",
        }:

            break

    print()
    print("PROMISE-TO-PAY")
    print("-" * 70)

    promise_result = record_receivables_promise(
        receivable,
        promised_date="2026-09-07",
        response="Friday ko full payment kar denge.",
    )

    print(
        f"Promise recorded    : "
        f"{promise_result['success']}"
    )

    if promise_result.get(
        "promise"
    ):

        print(
            f"Promised date       : "
            f"{promise_result['promise']['promised_date']}"
        )

    print()
    print("PAYMENT VERIFICATION")
    print("-" * 70)

    verification = verify_receivables_payment(
        receivable,
        45000.0,
    )

    print(
        f"Verified            : "
        f"{verification['verified']}"
    )

    if verification.get(
        "verified"
    ):

        print(
            f"Recovered revenue   : "
            f"{_money(verification['recovered_amount'])}"
        )

    print()
    print("FINAL STATE")
    print("-" * 70)

    print(
        json.dumps(
            receivables_recovery_summary(
                receivable
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
    demo_receivables_recovery()



from pathlib import Path
import json
from datetime import datetime, timezone


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

OUTCOME_FILE = DATA_DIR / "outcomes.jsonl"


# ================================================================
# OUTCOME EVENT
# ================================================================

def create_outcome_event(
    payment_id,
    amount,
    failure_reason,
    recommended_action,
    final_action,
    recovery_probability,
    expected_revenue,
):
    """
    Create a pending outcome event.

    IMPORTANT:
    Creating a decision event does NOT mean the payment recovered.
    The actual outcome must be recorded separately.
    """

    event = {
        "event_type": "payment_outcome",
        "status": "pending",
        "timestamp": datetime.now(timezone.utc).isoformat(),

        "payment_id": str(payment_id),
        "amount": float(amount),

        "failure_reason": str(failure_reason),

        "recommended_action": str(recommended_action),
        "final_action": str(final_action),

        "recovery_probability": float(recovery_probability),
        "expected_revenue": float(expected_revenue),

        "recovered": None,
        "recovery_amount": 0.0,
    }

    return event


# ================================================================
# RECORD ACTUAL OUTCOME
# ================================================================

def record_actual_outcome(
    payment_id,
    recovered,
    recovery_amount=0.0,
):
    """
    Record the actual observed payment result.

    recovered=True:
        Payment was actually recovered.

    recovered=False:
        Payment was actually not recovered.

    This function only updates/records the observed result.
    It never changes the ML model.
    """

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    recovered = bool(recovered)
    recovery_amount = float(recovery_amount)

    if recovery_amount < 0:
        raise ValueError(
            "recovery_amount cannot be negative."
        )

    if not recovered:
        recovery_amount = 0.0

    event = {
        "event_type": "payment_outcome",
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),

        "payment_id": str(payment_id),

        "recovered": recovered,
        "recovery_amount": recovery_amount,
    }

    with open(
        OUTCOME_FILE,
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            json.dumps(event) + "\n"
        )

    return event


# ================================================================
# SAVE COMPLETE OUTCOME
# ================================================================

def save_completed_outcome(
    payment_id,
    amount,
    failure_reason,
    recommended_action,
    final_action,
    recovery_probability,
    expected_revenue,
    recovered,
    recovery_amount=0.0,
):
    """
    Save a complete observed outcome.

    This is the preferred function when the actual result
    is already known.
    """

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    recovered = bool(recovered)
    recovery_amount = float(recovery_amount)

    if recovery_amount < 0:
        raise ValueError(
            "recovery_amount cannot be negative."
        )

    if not recovered:
        recovery_amount = 0.0

    event = {
        "event_type": "payment_outcome",
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),

        "payment_id": str(payment_id),
        "amount": float(amount),

        "failure_reason": str(failure_reason),

        "recommended_action": str(
            recommended_action
        ),

        "final_action": str(final_action),

        "recovery_probability": float(
            recovery_probability
        ),

        "expected_revenue": float(
            expected_revenue
        ),

        "recovered": recovered,
        "recovery_amount": recovery_amount,
    }

    with open(
        OUTCOME_FILE,
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            json.dumps(event) + "\n"
        )

    return event


# ================================================================
# TEST
# ================================================================

def main():

    print("=" * 70)
    print("RecoverOS X - OUTCOME EVENT ENGINE")
    print("=" * 70)

    print()
    print("EVENT CREATION")
    print("-" * 70)

    pending_event = create_outcome_event(
        payment_id="DEMO001",
        amount=2500,
        failure_reason="bank_timeout",
        recommended_action="retry_payment",
        final_action="retry_payment",
        recovery_probability=0.8471,
        expected_revenue=2092.71,
    )

    print(
        json.dumps(
            pending_event,
            indent=2,
        )
    )

    print()
    print("OBSERVED OUTCOME")
    print("-" * 70)

    completed_event = save_completed_outcome(
        payment_id="DEMO001",
        amount=2500,
        failure_reason="bank_timeout",
        recommended_action="retry_payment",
        final_action="retry_payment",
        recovery_probability=0.8471,
        expected_revenue=2092.71,
        recovered=True,
        recovery_amount=2500,
    )

    print(
        json.dumps(
            completed_event,
            indent=2,
        )
    )

    print()
    print("IMPORTANT")
    print("-" * 70)
    print("Decision prediction != observed recovery.")
    print("Only actual outcomes are eligible for learning.")
    print("Production model was NOT modified.")

    print()
    print("=" * 70)
    print("RecoverOS X outcome event engine completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()


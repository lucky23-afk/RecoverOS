"""
RecoverOS X - Recovery Outcome Simulator

Phase 2:
Simulates the real-world result of a recovery action.

IMPORTANT:
- This is synthetic evaluation data.
- It does NOT claim to be real Razorpay recovery data.
- The simulator converts an action + payment context into an
  observed outcome so we can measure recovered money.
"""

import random


# ================================================================
# ACTION EFFECTS
# ================================================================

ACTION_MULTIPLIERS = {
    "retry_payment": 1.00,
    "send_update_link": 0.92,
    "send_reminder": 0.72,
    "hold_for_review": 0.55,
}


# ================================================================
# FAILURE EFFECTS
# ================================================================

FAILURE_MULTIPLIERS = {
    "bank_timeout": 1.10,
    "timeout": 1.10,
    "network_error": 1.05,
    "temporary_bank_error": 1.05,
    "gateway_timeout": 1.05,

    "insufficient_funds": 0.72,
    "expired_card": 0.65,
    "invalid_card": 0.60,
    "mandate_expired": 0.68,
    "payment_method_expired": 0.65,

    "suspicious_reversal": 0.05,
    "mandate_changed_recently": 0.20,
    "mandate_changed": 0.20,
}


# ================================================================
# SAFE HELPERS
# ================================================================

def clamp(value, minimum=0.0, maximum=0.98):
    return max(minimum, min(maximum, float(value)))


def get_action_probability(
    payment,
    action,
    base_probability,
):
    """
    Convert the existing ML probability into a synthetic
    action-specific outcome probability.

    This is NOT another predictive model.

    The ML model estimates the customer's recovery likelihood.
    The simulator models how the selected intervention behaves.
    """

    action = str(action).lower()
    failure_reason = str(
        payment.get("failure_reason", "")
    ).lower()

    multiplier = ACTION_MULTIPLIERS.get(
        action,
        0.50,
    )

    failure_multiplier = FAILURE_MULTIPLIERS.get(
        failure_reason,
        0.80,
    )

    probability = (
        float(base_probability)
        * multiplier
        * failure_multiplier
    )

    # Customer-action recovery actions become more useful
    # when the customer has previously succeeded.
    previous_successes = int(
        payment.get("previous_successes", 0)
    )

    if action in {
        "send_update_link",
        "send_reminder",
    }:
        probability += min(
            previous_successes * 0.005,
            0.05,
        )

    # Repeated retries should become progressively less effective.
    retry_count = int(
        payment.get("retry_count", 0)
    )

    if action == "retry_payment":
        probability -= min(
            retry_count * 0.06,
            0.18,
        )

    # Suspicious/risk cases should almost never auto-recover.
    risk_score = float(
        payment.get("risk_score", 0.0)
    )

    probability -= risk_score * 0.10

    return clamp(probability)


# ================================================================
# EXECUTE SYNTHETIC RECOVERY
# ================================================================

def execute_recovery(payment, action, base_probability):
    """
    Execute one synthetic recovery attempt.

    Returns an observed outcome.
    """

    amount = float(payment["amount"])

    action_probability = get_action_probability(
        payment=payment,
        action=action,
        base_probability=base_probability,
    )

    recovered = (
        random.random()
        < action_probability
    )

    if recovered:
        outcome = "recovered"
        recovered_amount = amount
    elif action == "hold_for_review":
        outcome = "pending_review"
        recovered_amount = 0.0
    elif action == "blocked":
        outcome = "blocked"
        recovered_amount = 0.0
    else:
        outcome = "not_recovered"
        recovered_amount = 0.0

    return {
        "payment_id": payment.get("payment_id"),
        "amount": amount,
        "action": action,
        "outcome": outcome,
        "recovered": recovered,
        "recovered_amount": recovered_amount,
        "action_probability": action_probability,
    }


# ================================================================
# BACKWARD-COMPATIBLE FUNCTION
# ================================================================

def simulate_payment_outcome(probability):
    """
    Backward-compatible helper used by older modules.

    Returns only True/False.
    """

    return random.random() < float(probability)


def run_simulation(payment, decision):
    """
    Backward-compatible simulation wrapper.

    Older evaluation code expects:
        decision["action"]
        decision["confidence"]
    """

    action = decision.get(
        "action",
        "hold_for_review",
    )

    probability = float(
        decision.get(
            "confidence",
            decision.get(
                "recovery_probability",
                0.0,
            ),
        )
    )

    return execute_recovery(
        payment=payment,
        action=action,
        base_probability=probability,
    )


# ================================================================
# LOCAL TEST
# ================================================================

if __name__ == "__main__":

    test_payment = {
        "payment_id": "SIM001",
        "amount": 2500,
        "failure_reason": "bank_timeout",
        "previous_successes": 8,
        "retry_count": 1,
        "risk_score": 0.10,
    }

    result = execute_recovery(
        payment=test_payment,
        action="retry_payment",
        base_probability=0.82,
    )

    print()
    print("=" * 70)
    print("RecoverOS X - RECOVERY SIMULATOR TEST")
    print("=" * 70)

    for key, value in result.items():
        print(f"{key:20}: {value}")

    print("=" * 70)
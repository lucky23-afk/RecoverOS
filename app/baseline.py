from decision_engine import calculate_recovery_probability
from simulator import simulate_payment_outcome


def baseline_action(payment):
    """
    A naive recovery strategy.

    It tries to retry every payment unless the
    payment has already reached the retry limit.
    """

    if payment["retry_count"] >= 3:
        return "gave_up"

    return "retry_payment"


def run_baseline(payments):
    """
    Run the naive strategy across all payments.
    """

    total_at_risk = 0
    total_recovered = 0
    retry_attempts = 0
    unsafe_retries = 0

    for payment in payments:

        action = baseline_action(payment)

        total_at_risk += payment["amount"]

        if action == "retry_payment":

            retry_attempts += 1

            # Suspicious reversals should not be retried.
            if payment["failure_reason"] == "suspicious_reversal":
                unsafe_retries += 1
                continue

            probability = calculate_recovery_probability(
                payment,
                action
            )

            recovered = simulate_payment_outcome(
                probability
            )

            if recovered:
                total_recovered += payment["amount"]

    return {
        "total_at_risk": total_at_risk,
        "total_recovered": total_recovered,
        "retry_attempts": retry_attempts,
        "unsafe_retries": unsafe_retries
    }
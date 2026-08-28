import random


def simulate_payment_outcome(probability):
    """
    Simulate whether a payment is successfully recovered.

    This represents synthetic data for our prototype.
    """

    return random.random() < probability


def run_simulation(payment, decision):
    """
    Execute the selected recovery action in our simulator.
    """

    action = decision["action"]
    probability = decision["confidence"]

    recovered = simulate_payment_outcome(probability)

    if recovered:
        outcome = "recovered"
    elif action == "hold_for_review":
        outcome = "flagged"
    elif action == "gave_up":
        outcome = "gave_up"
    else:
        outcome = "not_recovered"

    return {
        "customer_id": payment["customer_id"],
        "amount": payment["amount"],
        "action": action,
        "outcome": outcome,
        "recovered_amount": payment["amount"] if recovered else 0
    }
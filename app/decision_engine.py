def classify_failure(payment):
    """
    Decide whether a failed payment can be handled automatically
    or should be reviewed by a human.
    """

    reason = payment["failure_reason"]

    if reason in ["suspicious_reversal", "mandate_changed_recently"]:
        return "flag_for_review"

    return "normal_recovery"


def get_candidate_actions(payment):
    """
    Return possible recovery actions for this payment.
    """

    reason = payment["failure_reason"]

    if reason == "bank_timeout":
        return [
            "retry_payment",
            "send_reminder",
            "hold_for_review"
        ]

    if reason == "insufficient_funds":
        return [
            "send_reminder",
            "retry_payment",
            "hold_for_review"
        ]

    if reason == "card_expired":
        return [
            "send_update_link",
            "send_reminder",
            "hold_for_review"
        ]

    if reason == "mandate_expired":
        return [
            "send_update_link",
            "send_reminder",
            "hold_for_review"
        ]

    if reason == "mandate_changed_recently":
        return [
            "hold_for_review"
        ]

    if reason == "suspicious_reversal":
        return [
            "hold_for_review"
        ]

    return ["hold_for_review"]


def calculate_recovery_probability(payment, action):
    """
    Estimate the probability that an action will recover the payment.

    This is a transparent simulation model for our prototype.
    It is NOT trained machine learning.
    """

    reason = payment["failure_reason"]

    # Base probability based on failure type and action
    probabilities = {
        "bank_timeout": {
            "retry_payment": 0.75,
            "send_reminder": 0.35,
            "hold_for_review": 0.0
        },

        "insufficient_funds": {
            "send_reminder": 0.45,
            "retry_payment": 0.25,
            "hold_for_review": 0.0
        },

        "card_expired": {
            "send_update_link": 0.70,
            "send_reminder": 0.25,
            "hold_for_review": 0.0
        },

        "mandate_expired": {
            "send_update_link": 0.65,
            "send_reminder": 0.20,
            "hold_for_review": 0.0
        },

        "mandate_changed_recently": {
            "hold_for_review": 0.0
        },

        "suspicious_reversal": {
            "hold_for_review": 0.0
        }
    }

    chance = probabilities.get(reason, {}).get(action, 0.0)

    # Customer history adjustment
    successful_payments = payment["previous_successes"]
    failed_payments = payment["previous_failures"]

    chance += min(successful_payments * 0.01, 0.10)
    chance -= min(failed_payments * 0.03, 0.15)

    # Previous retries reduce confidence
    chance -= payment["retry_count"] * 0.08

    # Never allow an unsafe action to recover automatically
    if action == "hold_for_review":
        chance = 0.0

    return max(0.0, min(chance, 0.95))


def score_action(payment, action):
    """
    Calculate expected recovered revenue for an action.

    Expected value =
    payment amount × recovery probability
    """

    probability = calculate_recovery_probability(payment, action)

    expected_revenue = payment["amount"] * probability

    return {
        "action": action,
        "probability": probability,
        "expected_revenue": expected_revenue
    }


def choose_best_action(payment):
    """
    Evaluate all candidate actions and select the safest
    action with the highest expected recovery value.
    """

    category = classify_failure(payment)

    # Mandatory human review
    if category == "flag_for_review":
        return {
            "category": category,
            "action": "hold_for_review",
            "confidence": 0.0,
            "expected_revenue": 0.0,
            "reason": "Safety rule requires human review."
        }

    # Retry safety cap
    if payment["retry_count"] >= 3:
        return {
            "category": category,
            "action": "gave_up",
            "confidence": 0.0,
            "expected_revenue": 0.0,
            "reason": "Maximum retry limit reached."
        }

    candidates = get_candidate_actions(payment)

    scored_actions = []

    for action in candidates:
        scored_actions.append(
            score_action(payment, action)
        )

    best = max(
        scored_actions,
        key=lambda item: item["expected_revenue"]
    )

    return {
        "category": category,
        "action": best["action"],
        "confidence": best["probability"],
        "expected_revenue": best["expected_revenue"],
        "reason": (
            "Selected the action with the highest "
            "expected recovery value."
        )
    }

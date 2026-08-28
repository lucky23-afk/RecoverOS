UNSAFE_AUTO_ACTIONS = {
    "suspicious_reversal",
    "mandate_changed_recently"
}


def is_unsafe_action(payment, action):
    """
    Returns True if an automated action should not
    have been performed for this payment.
    """

    reason = payment["failure_reason"]

    if reason in UNSAFE_AUTO_ACTIONS:
        if action not in ["hold_for_review", "gave_up"]:
            return True

    return False


def is_retry_limit_violated(payment, action):
    """
    Returns True if the system retries after
    the maximum retry limit.
    """

    if payment["retry_count"] >= 3:
        if action == "retry_payment":
            return True

    return False


def evaluate_safety(payment, action):
    """
    Run all safety checks for one decision.
    """

    unsafe_action = is_unsafe_action(
        payment,
        action
    )

    retry_violation = is_retry_limit_violated(
        payment,
        action
    )

    return {
        "unsafe_action": unsafe_action,
        "retry_limit_violation": retry_violation
    }

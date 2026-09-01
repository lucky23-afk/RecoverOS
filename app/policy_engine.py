from dataclasses import dataclass


@dataclass
class PolicyResult:
    decision: str
    failure_category: str
    allowed_actions: list
    reasons: list


def classify_failure(failure_reason: str) -> str:
    reason = str(failure_reason).lower()

    transient_failures = {
        "bank_timeout",
        "timeout",
        "network_error",
        "temporary_bank_error",
        "gateway_timeout",
    }

    customer_action_failures = {
        "expired_card",
        "invalid_card",
        "mandate_expired",
        "payment_method_expired",
        "insufficient_funds",
    }

    risk_failures = {
        "suspicious_reversal",
        "fraud",
        "fraud_detected",
        "suspicious_activity",
    }

    if reason in transient_failures:
        return "TRANSIENT"

    if reason in customer_action_failures:
        return "CUSTOMER_ACTION"

    if reason in risk_failures:
        return "RISK"

    return "UNKNOWN"


def evaluate_policy(
    failure_reason: str,
    retry_count: int,
    recovery_probability: float,
) -> PolicyResult:

    category = classify_failure(failure_reason)

    allowed_actions = []
    reasons = []

    # ---------------------------------------------------------
    # RISK / SUSPICIOUS PAYMENTS
    # ---------------------------------------------------------
    if category == "RISK":
        return PolicyResult(
            decision="REVIEW",
            failure_category=category,
            allowed_actions=["hold_for_review"],
            reasons=[
                "Risk-related failure detected.",
                "Automatic recovery actions are prohibited.",
            ],
        )

    # ---------------------------------------------------------
    # UNKNOWN FAILURE
    # ---------------------------------------------------------
    if category == "UNKNOWN":
        return PolicyResult(
            decision="REVIEW",
            failure_category=category,
            allowed_actions=["hold_for_review"],
            reasons=[
                "Unknown failure category.",
                "Human review required before recovery.",
            ],
        )

    # ---------------------------------------------------------
    # TRANSIENT FAILURE
    # ---------------------------------------------------------
    if category == "TRANSIENT":

        allowed_actions = [
            "retry_payment",
            "send_reminder",
            "hold_for_review",
        ]

        reasons.append(
            "Transient failure detected."
        )

        if retry_count >= 3:
            allowed_actions.remove("retry_payment")
            reasons.append(
                "Retry limit reached: automatic retry is prohibited."
            )

        if recovery_probability < 0.20:
            if "retry_payment" in allowed_actions:
                allowed_actions.remove("retry_payment")

            reasons.append(
                "Recovery probability is below the retry threshold."
            )

        return PolicyResult(
            decision="ALLOW",
            failure_category=category,
            allowed_actions=allowed_actions,
            reasons=reasons,
        )

    # ---------------------------------------------------------
    # CUSTOMER ACTION REQUIRED
    # ---------------------------------------------------------
    if category == "CUSTOMER_ACTION":

        allowed_actions = [
            "send_update_link",
            "send_reminder",
            "hold_for_review",
        ]

        reasons.append(
            "Customer action is required to recover the payment."
        )

        return PolicyResult(
            decision="ALLOW",
            failure_category=category,
            allowed_actions=allowed_actions,
            reasons=reasons,
        )

    # ---------------------------------------------------------
    # FALLBACK
    # ---------------------------------------------------------
    return PolicyResult(
        decision="REVIEW",
        failure_category=category,
        allowed_actions=["hold_for_review"],
        reasons=[
            "Policy could not safely classify the payment."
        ],
    )


if __name__ == "__main__":

    print("=" * 68)
    print("RecoverOS X - Deterministic Policy Engine")
    print("=" * 68)

    result = evaluate_policy(
        failure_reason="bank_timeout",
        retry_count=1,
        recovery_probability=0.82,
    )

    print(f"Failure category   : {result.failure_category}")
    print(f"Policy decision    : {result.decision}")

    print()
    print("Allowed actions")
    print("-" * 68)

    for action in result.allowed_actions:
        print(f" - {action}")

    print()
    print("Policy reasons")
    print("-" * 68)

    for reason in result.reasons:
        print(f" - {reason}")

    print("=" * 68)
"""
RecoverOS X - LLM Reasoning Engine

The LLM explains the decision made by the
ML model + strategy optimizer.

Important:
The LLM does NOT control the final action.
The Safety Engine remains authoritative.
"""


def generate_reasoning(
    payment,
    recovery_probability,
    recommended_action,
    expected_revenue,
    risk_score,
):
    """
    Generate an explainable decision summary.

    This is currently a deterministic reasoning layer.
    It will later be replaced/augmented with an LLM API.
    """

    failure_reason = str(
        payment["failure_reason"]
    ).lower()

    retry_count = int(payment["retry_count"])
    amount = float(payment["amount"])

    reasons = []

    # Failure-specific reasoning
    if failure_reason == "expired_card":
        reasons.append(
            "The payment method appears to require customer action "
            "rather than another blind retry."
        )

    elif failure_reason == "bank_timeout":
        reasons.append(
            "The failure may be temporary, making recovery through "
            "a controlled retry potentially viable."
        )

    elif failure_reason == "insufficient_funds":
        reasons.append(
            "The account may not currently have sufficient funds, "
            "so immediate repeated retries may have limited value."
        )

    elif failure_reason == "suspicious_reversal":
        reasons.append(
            "The failure has a risk signal that requires additional review."
        )

    elif failure_reason in [
        "mandate_changed",
        "recently_changed_mandate",
    ]:
        reasons.append(
            "A recent mandate change makes automatic recovery unsafe "
            "without additional review."
        )

    else:
        reasons.append(
            "The decision considers the observed payment failure context."
        )

    # Retry reasoning
    if retry_count >= 3:
        reasons.append(
            "The maximum automatic retry threshold has been reached."
        )
    else:
        reasons.append(
            f"The payment has used {retry_count} of 3 allowed retries."
        )

    # Recovery probability
    if recovery_probability >= 0.75:
        reasons.append(
            "The ML model predicts a relatively strong recovery probability."
        )

    elif recovery_probability >= 0.40:
        reasons.append(
            "The ML model predicts a moderate recovery probability."
        )

    else:
        reasons.append(
            "The ML model predicts a relatively low recovery probability."
        )

    # Risk
    if risk_score >= 0.80:
        risk_level = "HIGH"
    elif risk_score >= 0.40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # Build explanation
    explanation = (
        f"RecoverOS X recommends '{recommended_action}' "
        f"for this ₹{amount:,.2f} failed payment. "
        f"The estimated recovery probability is "
        f"{recovery_probability:.2%}, while the strategy optimizer "
        f"estimates ₹{expected_revenue:,.2f} in expected recovery value. "
        f"The current risk level is {risk_level}."
    )

    return {
        "summary": explanation,
        "risk_level": risk_level,
        "reasoning": reasons,
    }


if __name__ == "__main__":

    print()
    print("=" * 70)
    print("RecoverOS X - LLM Reasoning Engine")
    print("=" * 70)

    test_payment = {
        "payment_id": "TEST001",
        "amount": 2500,
        "failure_reason": "expired_card",
        "retry_count": 3,
    }

    result = generate_reasoning(
        payment=test_payment,
        recovery_probability=0.3025,
        recommended_action="send_update_link",
        expected_revenue=190.85,
        risk_score=0.0,
    )

    print()
    print("AI DECISION EXPLANATION")
    print("-" * 70)

    print(result["summary"])

    print()
    print(f"Risk level: {result['risk_level']}")

    print()
    print("Reasoning:")

    for reason in result["reasoning"]:
        print(f" - {reason}")

    print()
    print("=" * 70)
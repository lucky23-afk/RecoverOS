"""
RecoverOS X - Safety Engine

The optimizer recommends an action.
The safety engine has the final authority.

Safety rules always override AI/ML recommendations.
"""


MAX_RETRIES = 3


def evaluate_safety(
    payment,
    recommended_action,
    recovery_probability,
):
    """
    Apply deterministic safety rules to a recommendation.
    """

    retry_count = int(payment["retry_count"])
    failure_reason = str(payment["failure_reason"]).lower()

    reasons = []
    decision = "ALLOW"

    # ---------------------------------------------------------
    # RULE 1: Retry limit
    # ---------------------------------------------------------

    if retry_count >= MAX_RETRIES:

        if recommended_action == "retry_payment":
            decision = "BLOCK"
            reasons.append(
                "Retry limit reached: automatic retry is prohibited."
            )
        else:
            reasons.append(
                "Retry limit reached: non-retry recovery action permitted."
            )

    # ---------------------------------------------------------
    # RULE 2: Suspicious reversal
    # ---------------------------------------------------------

    if failure_reason == "suspicious_reversal":
        decision = "REVIEW"
        reasons.append(
            "Suspicious reversal detected: human review required."
        )

    # ---------------------------------------------------------
    # RULE 3: Recently changed mandate
    # ---------------------------------------------------------

    if failure_reason in [
        "mandate_changed",
        "recently_changed_mandate",
    ]:
        decision = "REVIEW"
        reasons.append(
            "Recently changed mandate detected: human review required."
        )

    # ---------------------------------------------------------
    # RULE 4: Low confidence
    # ---------------------------------------------------------

    if recovery_probability < 0.20:
        decision = "REVIEW"
        reasons.append(
            "Recovery probability is below the automation threshold."
        )

    # ---------------------------------------------------------
    # RULE 5: High-value payment
    # ---------------------------------------------------------

    amount = float(payment["amount"])

    if amount >= 100000:
        decision = "REVIEW"
        reasons.append(
            "High-value payment: human review required."
        )

    # ---------------------------------------------------------
    # Default reason
    # ---------------------------------------------------------

    if not reasons:
        reasons.append(
            "Safety checks passed."
        )

    # ---------------------------------------------------------
    # Final action
    # ---------------------------------------------------------

    if decision == "BLOCK":
        final_action = "blocked"

    elif decision == "REVIEW":
        final_action = "hold_for_review"

    else:
        final_action = recommended_action

    return {
        "decision": decision,
        "final_action": final_action,
        "reasons": reasons,
    }


if __name__ == "__main__":

    print()
    print("=" * 70)
    print("RecoverOS X - Safety Engine Test Suite")
    print("=" * 70)

    test_cases = [
        {
            "name": "Normal retry",
            "payment": {
                "payment_id": "TEST001",
                "amount": 2500,
                "failure_reason": "bank_timeout",
                "retry_count": 1,
            },
            "recommended_action": "retry_payment",
            "probability": 0.82,
        },
        {
            "name": "Retry limit reached",
            "payment": {
                "payment_id": "TEST002",
                "amount": 2500,
                "failure_reason": "bank_timeout",
                "retry_count": 3,
            },
            "recommended_action": "retry_payment",
            "probability": 0.82,
        },
        {
            "name": "Suspicious reversal",
            "payment": {
                "payment_id": "TEST003",
                "amount": 2500,
                "failure_reason": "suspicious_reversal",
                "retry_count": 1,
            },
            "recommended_action": "retry_payment",
            "probability": 0.90,
        },
        {
            "name": "Changed mandate",
            "payment": {
                "payment_id": "TEST004",
                "amount": 2500,
                "failure_reason": "mandate_changed",
                "retry_count": 1,
            },
            "recommended_action": "retry_payment",
            "probability": 0.90,
        },
        {
            "name": "Low recovery probability",
            "payment": {
                "payment_id": "TEST005",
                "amount": 2500,
                "failure_reason": "bank_timeout",
                "retry_count": 1,
            },
            "recommended_action": "retry_payment",
            "probability": 0.15,
        },
        {
            "name": "High-value payment",
            "payment": {
                "payment_id": "TEST006",
                "amount": 150000,
                "failure_reason": "bank_timeout",
                "retry_count": 1,
            },
            "recommended_action": "retry_payment",
            "probability": 0.95,
        },
    ]

    for test in test_cases:

        result = evaluate_safety(
            payment=test["payment"],
            recommended_action=test["recommended_action"],
            recovery_probability=test["probability"],
        )

        print()
        print(f"TEST: {test['name']}")
        print("-" * 70)
        print(f"Payment ID          : {test['payment']['payment_id']}")
        print(f"Failure reason      : {test['payment']['failure_reason']}")
        print(f"Retry count         : {test['payment']['retry_count']}")
        print(f"Recovery probability: {test['probability']:.2%}")
        print(f"ML recommendation   : {test['recommended_action']}")
        print(f"Safety decision     : {result['decision']}")
        print(f"FINAL ACTION        : {result['final_action']}")

        print("Reasons:")
        for reason in result["reasons"]:
            print(f" - {reason}")

    print()
    print("=" * 70)
    print("Safety test suite completed.")
    print("=" * 70)
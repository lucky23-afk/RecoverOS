from dataclasses import dataclass
from typing import Dict, List

from simulator import get_action_probability


@dataclass(frozen=True)
class ActionOption:
    name: str
    success_probability: float
    cost: float
    risk_penalty: float = 0.0
    human_review: bool = False


def expected_recovered_value(
    amount: float,
    success_probability: float,
    cost: float = 0.0,
    risk_penalty: float = 0.0,
) -> float:
    """
    Expected Recovered Value.

    ERV =
        probability of recovery × amount
        - action cost
        - risk penalty
    """

    amount = max(float(amount), 0.0)

    probability = max(
        0.0,
        min(float(success_probability), 1.0),
    )

    return (
        amount * probability
        - max(float(cost), 0.0)
        - max(float(risk_penalty), 0.0)
    )


def rank_actions(
    amount: float,
    actions: List[ActionOption],
) -> List[Dict]:
    ranked = []

    for action in actions:
        erv = expected_recovered_value(
            amount=amount,
            success_probability=action.success_probability,
            cost=action.cost,
            risk_penalty=action.risk_penalty,
        )

        ranked.append(
            {
                "action": action.name,
                "success_probability": action.success_probability,
                "cost": action.cost,
                "risk_penalty": action.risk_penalty,
                "human_review": action.human_review,
                "expected_recovered_value": round(erv, 2),
            }
        )

    return sorted(
        ranked,
        key=lambda x: x["expected_recovered_value"],
        reverse=True,
    )


def optimize_recovery_action(
    amount: float,
    recovery_probability: float,
    failure_reason: str,
    retry_count: int = 0,
    risk_score: float = 0.0,
    payment: Dict | None = None,
) -> Dict:
    """
    Choose the recovery action with the highest ERV.

    IMPORTANT:
    ERV now uses the SAME action-specific probability function
    used by the recovery simulator.

    This keeps:
        ML -> ERV -> Execution evaluation

    internally consistent.
    """

    amount = max(float(amount), 0.0)

    probability = max(
        0.0,
        min(float(recovery_probability), 1.0),
    )

    retry_count = max(int(retry_count), 0)

    risk_score = max(
        0.0,
        min(float(risk_score), 1.0),
    )

    failure = str(
        failure_reason
    ).lower().strip()

    # Build the payment context required by the simulator.
    payment_context = dict(payment or {})

    payment_context.setdefault(
        "amount",
        amount,
    )

    payment_context.setdefault(
        "failure_reason",
        failure,
    )

    payment_context.setdefault(
        "retry_count",
        retry_count,
    )

    payment_context.setdefault(
        "risk_score",
        risk_score,
    )

    # ============================================================
    # CONSISTENT ACTION PROBABILITIES
    # ============================================================

    retry_p = get_action_probability(
        payment=payment_context,
        action="retry_payment",
        base_probability=probability,
    )

    link_p = get_action_probability(
        payment=payment_context,
        action="send_update_link",
        base_probability=probability,
    )

    review_p = get_action_probability(
        payment=payment_context,
        action="hold_for_review",
        base_probability=probability,
    )

    # ============================================================
    # RISK PENALTIES
    # ============================================================

    risk_penalty_multiplier = (
        1.0 + risk_score
    )

    retry_risk = 15.0 * risk_penalty_multiplier
    link_risk = 5.0 * risk_penalty_multiplier
    review_risk = 1.0

    actions = [
        ActionOption(
            name="retry_payment",
            success_probability=retry_p,
            cost=8.0,
            risk_penalty=retry_risk,
            human_review=False,
        ),
        ActionOption(
            name="send_update_link",
            success_probability=link_p,
            cost=3.0,
            risk_penalty=link_risk,
            human_review=False,
        ),
        ActionOption(
            name="hold_for_review",
            success_probability=review_p,
            cost=20.0,
            risk_penalty=review_risk,
            human_review=True,
        ),
    ]

    # ============================================================
    # RETRY SAFETY
    # ============================================================

    if retry_count >= 3:
        actions = [
            action
            for action in actions
            if action.name != "retry_payment"
        ]

    # ============================================================
    # HIGH-VALUE PAYMENTS
    # ============================================================

    if amount >= 25000:
        actions = [
            action
            for action in actions
            if action.human_review
        ]

    # ============================================================
    # HIGH-RISK CASES
    # ============================================================

    if risk_score >= 0.80:
        actions = [
            action
            for action in actions
            if action.human_review
        ]

    # ============================================================
    # RANK
    # ============================================================

    ranked = rank_actions(
        amount=amount,
        actions=actions,
    )

    if ranked:
        best = ranked[0]
    else:
        best = {
            "action": "hold_for_review",
            "success_probability": 0.0,
            "cost": 0.0,
            "risk_penalty": 0.0,
            "human_review": True,
            "expected_recovered_value": 0.0,
        }

    return {
        **best,
        "ranked_actions": ranked,
        "reason": (
            f"Selected {best['action']} because it "
            "maximizes expected recovered value using "
            "the same action-specific probability model "
            "used by recovery execution."
        ),
    }


if __name__ == "__main__":

    test_payment = {
        "payment_id": "ERV001",
        "amount": 5000,
        "failure_reason": "bank_timeout",
        "previous_successes": 8,
        "previous_failures": 1,
        "retry_count": 1,
        "risk_score": 0.10,
    }

    result = optimize_recovery_action(
        amount=test_payment["amount"],
        recovery_probability=0.8471,
        failure_reason=test_payment["failure_reason"],
        retry_count=test_payment["retry_count"],
        risk_score=test_payment["risk_score"],
        payment=test_payment,
    )

    print("=" * 70)
    print("RecoverOS - EXPECTED RECOVERED VALUE OPTIMIZER")
    print("=" * 70)

    print(
        f"Amount             : ₹{test_payment['amount']:,.2f}"
    )

    print(
        "ML probability     : 84.71%"
    )

    print(
        f"Retry count        : {test_payment['retry_count']}"
    )

    print(
        f"Risk score         : "
        f"{test_payment['risk_score']:.2%}"
    )

    print(
        f"Selected action    : {result['action']}"
    )

    print(
        f"Expected recovered : "
        f"₹{result['expected_recovered_value']:,.2f}"
    )

    print()
    print("ACTION RANKING")
    print("-" * 70)

    for row in result["ranked_actions"]:
        print(
            f"{row['action']:<22}"
            f"p={row['success_probability']:.2%} "
            f"ERV=₹{row['expected_recovered_value']:,.2f}"
        )

    print("=" * 70)
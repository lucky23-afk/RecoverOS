from dataclasses import dataclass
from typing import Dict, List


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

    amount = max(
        float(amount),
        0.0,
    )

    probability = max(
        0.0,
        min(
            float(success_probability),
            1.0,
        ),
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
            amount,
            action.success_probability,
            action.cost,
            action.risk_penalty,
        )

        ranked.append(
            {
                "action":
                    action.name,

                "success_probability":
                    action.success_probability,

                "cost":
                    action.cost,

                "risk_penalty":
                    action.risk_penalty,

                "human_review":
                    action.human_review,

                "expected_recovered_value":
                    round(
                        erv,
                        2,
                    ),
            }
        )

    return sorted(
        ranked,
        key=lambda x:
            x["expected_recovered_value"],
        reverse=True,
    )


def optimize_recovery_action(
    amount: float,
    recovery_probability: float,
    failure_reason: str,
    retry_count: int = 0,
    risk_score: float = 0.0,
) -> Dict:
    """
    Choose the recovery action with the highest ERV.

    retry_count and risk_score are considered when
    ranking candidate actions.
    """

    amount = max(
        float(amount),
        0.0,
    )

    probability = max(
        0.0,
        min(
            float(recovery_probability),
            1.0,
        ),
    )

    failure = str(
        failure_reason
    ).lower().strip()

    retry_count = max(
        int(retry_count),
        0,
    )

    risk_score = max(
        0.0,
        min(
            float(risk_score),
            1.0,
        ),
    )

    # ============================================================
    # FAILURE-CONTEXT ACTION PROBABILITIES
    # ============================================================

    if failure == "bank_timeout":

        retry_p = min(
            probability + 0.04,
            0.98,
        )

        link_p = min(
            max(
                probability - 0.06,
                0.0,
            ),
            0.90,
        )

    elif failure == "network_error":

        retry_p = min(
            probability + 0.02,
            0.96,
        )

        link_p = min(
            max(
                probability - 0.04,
                0.0,
            ),
            0.90,
        )

    else:

        retry_p = max(
            probability - 0.10,
            0.05,
        )

        link_p = min(
            probability + 0.05,
            0.85,
        )

    # ============================================================
    # RETRY SAFETY
    # ============================================================

    if retry_count >= 3:
        retry_p = 0.0

    # ============================================================
    # RISK ADJUSTMENT
    # ============================================================

    risk_penalty_multiplier = (
        1.0 + risk_score
    )

    retry_risk = (
        15.0
        * risk_penalty_multiplier
    )

    link_risk = (
        5.0
        * risk_penalty_multiplier
    )

    review_risk = 1.0

    actions = [
        ActionOption(
            name="retry_payment",
            success_probability=retry_p,
            cost=8.0,
            risk_penalty=retry_risk,
        ),

        ActionOption(
            name="send_update_link",
            success_probability=link_p,
            cost=3.0,
            risk_penalty=link_risk,
        ),

        ActionOption(
            name="hold_for_review",
            success_probability=min(
                probability + 0.01,
                0.95,
            ),
            cost=20.0,
            risk_penalty=review_risk,
            human_review=True,
        ),
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
        amount,
        actions,
    )

    if ranked:

        best = ranked[0]

    else:

        best = {
            "action":
                "hold_for_review",

            "success_probability":
                0.0,

            "cost":
                0.0,

            "risk_penalty":
                0.0,

            "human_review":
                True,

            "expected_recovered_value":
                0.0,
        }

    return {
        **best,

        "ranked_actions":
            ranked,

        "reason":
            (
                f"Selected {best['action']} because it "
                "maximizes expected recovered value under "
                "the configured cost and risk assumptions."
            ),
    }


if __name__ == "__main__":

    result = optimize_recovery_action(
        amount=5000,
        recovery_probability=0.8471,
        failure_reason="bank_timeout",
        retry_count=1,
        risk_score=0.10,
    )

    print("=" * 70)
    print(
        "RecoverOS - EXPECTED RECOVERED VALUE OPTIMIZER"
    )
    print("=" * 70)

    print(
        "Amount             : ₹5,000.00"
    )

    print(
        "ML probability     : 84.71%"
    )

    print(
        "Retry count        : 1"
    )

    print(
        "Risk score         : 10.00%"
    )

    print(
        f"Selected action    : "
        f"{result['action']}"
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
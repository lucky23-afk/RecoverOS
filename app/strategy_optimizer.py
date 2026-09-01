"""
RecoverOS X - Strategy Optimizer

Evaluates possible recovery actions using:
- Recovery probability
- Payment amount
- Action-specific success assumptions
- Risk penalties
- Operational costs

This is a synthetic optimization layer for the prototype.
"""

from dataclasses import dataclass


@dataclass
class StrategyResult:
    action: str
    expected_revenue: float
    recovery_probability: float
    risk_penalty: float
    score: float


ACTIONS = [
    "retry_payment",
    "send_update_link",
    "send_reminder",
    "hold_for_review",
]


def optimize_strategy(
    amount: float,
    recovery_probability: float,
    retry_count: int,
    risk_score: float = 0.0,
):
    """
    Select the recovery strategy with the highest expected value.
    """

    strategies = []

    # Retry
    if retry_count < 3:
        retry_probability = recovery_probability

        retry_risk = risk_score * 0.50
        retry_cost = amount * 0.01

        retry_expected_revenue = (
            amount * retry_probability
            - retry_cost
            - retry_risk
        )

        strategies.append(
            StrategyResult(
                action="retry_payment",
                expected_revenue=retry_expected_revenue,
                recovery_probability=retry_probability,
                risk_penalty=retry_risk,
                score=retry_expected_revenue,
            )
        )

    # Payment update
    update_probability = min(
        recovery_probability + 0.10,
        0.95,
    )

    update_risk = risk_score * 0.20
    update_cost = amount * 0.02

    update_expected_revenue = (
        amount * update_probability
        - update_cost
        - update_risk
    )

    strategies.append(
        StrategyResult(
            action="send_update_link",
            expected_revenue=update_expected_revenue,
            recovery_probability=update_probability,
            risk_penalty=update_risk,
            score=update_expected_revenue,
        )
    )

    # Reminder
    reminder_probability = min(
        recovery_probability * 0.85,
        0.90,
    )

    reminder_risk = risk_score * 0.10
    reminder_cost = amount * 0.005

    reminder_expected_revenue = (
        amount * reminder_probability
        - reminder_cost
        - reminder_risk
    )

    strategies.append(
        StrategyResult(
            action="send_reminder",
            expected_revenue=reminder_expected_revenue,
            recovery_probability=reminder_probability,
            risk_penalty=reminder_risk,
            score=reminder_expected_revenue,
        )
    )

    # Human review
    review_probability = min(
        recovery_probability + 0.05,
        0.95,
    )

    review_cost = 25.0

    review_expected_revenue = (
        amount * review_probability
        - review_cost
    )

    strategies.append(
        StrategyResult(
            action="hold_for_review",
            expected_revenue=review_expected_revenue,
            recovery_probability=review_probability,
            risk_penalty=0.0,
            score=review_expected_revenue,
        )
    )

    best_strategy = max(
        strategies,
        key=lambda strategy: strategy.score,
    )

    return best_strategy, strategies


if __name__ == "__main__":

    amount = 2500
    recovery_probability = 0.82
    retry_count = 1
    risk_score = 0.10

    best, all_strategies = optimize_strategy(
        amount=amount,
        recovery_probability=recovery_probability,
        retry_count=retry_count,
        risk_score=risk_score,
    )

    print()
    print("=" * 60)
    print("RecoverOS X - Strategy Optimizer")
    print("=" * 60)

    print(f"Payment amount       : ₹{amount:,.2f}")
    print(f"Recovery probability : {recovery_probability:.2%}")
    print(f"Retry count          : {retry_count}/3")
    print(f"Risk score           : {risk_score:.2%}")

    print()
    print("Strategy Evaluation")
    print("-" * 60)

    for strategy in all_strategies:
        print(
            f"{strategy.action:20} "
            f"Expected value: ₹{strategy.expected_revenue:,.2f}"
        )

    print()
    print("BEST STRATEGY")
    print("-" * 60)
    print(f"Action              : {best.action}")
    print(
        f"Expected revenue    : "
        f"₹{best.expected_revenue:,.2f}"
    )
    print(
        f"Estimated recovery  : "
        f"{best.recovery_probability:.2%}"
    )

    print("=" * 60)
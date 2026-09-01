import sys
from pathlib import Path

# Make sure Python can import files from the app directory
APP_DIR = Path(__file__).resolve().parent

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


from ml_model import predict_recovery_probability
from strategy_optimizer import optimize_strategy
from policy_engine import evaluate_policy
from safety_engine import evaluate_safety


# ======================================================================
# Utility
# ======================================================================

def print_line():
    print("-" * 70)


# ======================================================================
# RecoverOS X Full Decision Pipeline
# ======================================================================

def run_pipeline(payment):

    print()
    print("=" * 70)
    print("RecoverOS X - FULL DECISION PIPELINE")
    print("=" * 70)

    # ================================================================
    # 1. PAYMENT CONTEXT
    # ================================================================

    print()
    print("PAYMENT CONTEXT")
    print_line()

    print(f"payment_id          : {payment['payment_id']}")
    print(f"amount              : ₹{payment['amount']:.2f}")
    print(f"failure_reason      : {payment['failure_reason']}")
    print(f"payment_method      : {payment['payment_method']}")
    print(f"merchant_type       : {payment['merchant_type']}")

    print(f"previous_successes  : {payment['previous_successes']}")
    print(f"previous_failures   : {payment['previous_failures']}")
    print(f"retry_count         : {payment['retry_count']}")

    print(
        f"days_since_last_payment: "
        f"{payment['days_since_last_payment']}"
    )

    print(
        f"customer_tenure_months: "
        f"{payment['customer_tenure_months']}"
    )

    print(
        f"mandate_age_days    : "
        f"{payment['mandate_age_days']}"
    )

    print(
        f"average_amount      : "
        f"₹{payment['average_amount']:.2f}"
    )

    print(
        f"amount_vs_average   : "
        f"{payment['amount_vs_average']}"
    )

    print(
        f"recent_success_rate : "
        f"{payment['recent_success_rate']:.2%}"
    )

    print(
        f"failure_frequency   : "
        f"{payment['failure_frequency']:.2%}"
    )

    print(
        f"retry_interval_hours: "
        f"{payment['retry_interval_hours']}"
    )

    print(
        f"risk_score          : "
        f"{payment.get('risk_score', 0.0):.2%}"
    )

    # ================================================================
    # 2. ML RECOVERY PREDICTION
    # ================================================================

    recovery_probability = predict_recovery_probability(payment)

    print()
    print("AI / ML ANALYSIS")
    print_line()

    print(
        f"Recovery probability: "
        f"{recovery_probability:.2%}"
    )

    # ================================================================
    # 3. STRATEGY OPTIMIZER
    # ================================================================

    best_strategy, all_strategies = optimize_strategy(
        amount=payment["amount"],
        recovery_probability=recovery_probability,
        retry_count=payment["retry_count"],
        risk_score=payment.get("risk_score", 0.0),
    )

    print()
    print("STRATEGY OPTIMIZER")
    print_line()

    for strategy in all_strategies:
        print(
            f"{strategy.action:<22} "
            f"Expected value: "
            f"₹{strategy.expected_revenue:.2f}"
        )

    print()
    print(
        f"Optimizer recommendation: "
        f"{best_strategy.action}"
    )

    print(
        f"Expected revenue        : "
        f"₹{best_strategy.expected_revenue:.2f}"
    )

    # ================================================================
    # 4. DETERMINISTIC POLICY
    # ================================================================

    policy_result = evaluate_policy(
        payment["failure_reason"],
        payment["retry_count"],
        recovery_probability,
    )

    # Support dictionary-style and object-style results
    if isinstance(policy_result, dict):

        failure_category = policy_result.get(
            "failure_category",
            "UNKNOWN",
        )

        policy_decision = policy_result.get(
            "decision",
            "BLOCK",
        )

        allowed_actions = policy_result.get(
            "allowed_actions",
            [],
        )

        policy_reasons = policy_result.get(
            "reasons",
            [],
        )

    else:

        failure_category = getattr(
            policy_result,
            "failure_category",
            "UNKNOWN",
        )

        policy_decision = getattr(
            policy_result,
            "decision",
            "BLOCK",
        )

        allowed_actions = getattr(
            policy_result,
            "allowed_actions",
            [],
        )

        policy_reasons = getattr(
            policy_result,
            "reasons",
            [],
        )

    print()
    print("DETERMINISTIC POLICY")
    print_line()

    print(
        f"Failure category    : "
        f"{failure_category}"
    )

    print(
        f"Policy decision     : "
        f"{policy_decision}"
    )

    print()
    print("Allowed actions:")

    for action in allowed_actions:
        print(f" - {action}")

    # ================================================================
    # 5. POLICY-CONSTRAINED OPTIMIZATION
    # ================================================================

    allowed_set = set(allowed_actions)

    policy_approved_strategies = [
        strategy
        for strategy in all_strategies
        if strategy.action in allowed_set
    ]

    print()
    print("POLICY-CONSTRAINED OPTIMIZATION")
    print_line()

    if policy_approved_strategies:

        for strategy in policy_approved_strategies:

            print(
                f"{strategy.action:<22} "
                f"Expected value: "
                f"₹{strategy.expected_revenue:.2f}"
            )

        policy_best_strategy = max(
            policy_approved_strategies,
            key=lambda strategy: strategy.score,
        )

        policy_action = policy_best_strategy.action

        print()
        print(
            f"Policy-approved best : "
            f"{policy_action}"
        )

        print(
            f"Expected revenue     : "
            f"₹{policy_best_strategy.expected_revenue:.2f}"
        )

    else:

        policy_action = "hold_for_review"

        print(
            "No optimizer strategy is permitted "
            "by policy."
        )

        print(
            "Fallback action       : "
            "hold_for_review"
        )

    # ================================================================
    # 6. SAFETY ENGINE
    # ================================================================

    safety_result = evaluate_safety(
        payment=payment,
        recommended_action=policy_action,
        recovery_probability=recovery_probability,
    )

    if isinstance(safety_result, dict):

        safety_decision = safety_result.get(
            "decision",
            "BLOCK",
        )

        final_action = safety_result.get(
            "final_action",
            "blocked",
        )

        safety_reasons = safety_result.get(
            "reasons",
            [],
        )

    else:

        safety_decision = getattr(
            safety_result,
            "decision",
            "BLOCK",
        )

        final_action = getattr(
            safety_result,
            "final_action",
            "blocked",
        )

        safety_reasons = getattr(
            safety_result,
            "reasons",
            [],
        )

    print()
    print("SAFETY ENGINE")
    print_line()

    print(
        f"Safety decision     : "
        f"{safety_decision}"
    )

    print(
        f"Safety final action : "
        f"{final_action}"
    )

    # ================================================================
    # 7. FINAL DECISION
    # ================================================================

    print()
    print("FINAL DECISION")
    print_line()

    print(
        f"ML probability      : "
        f"{recovery_probability:.2%}"
    )

    print(
        f"ML/optimizer action : "
        f"{best_strategy.action}"
    )

    print(
        f"Policy action       : "
        f"{policy_action}"
    )

    print(
        f"Safety decision     : "
        f"{safety_decision}"
    )

    print(
        f"FINAL ACTION        : "
        f"{final_action}"
    )

    # ================================================================
    # 8. POLICY REASONS
    # ================================================================

    print()
    print("POLICY REASONS")
    print_line()

    if policy_reasons:

        for reason in policy_reasons:
            print(f" - {reason}")

    else:

        print(
            " - No additional policy restrictions."
        )

    # ================================================================
    # 9. SAFETY REASONS
    # ================================================================

    print()
    print("SAFETY REASONS")
    print_line()

    if safety_reasons:

        for reason in safety_reasons:
            print(f" - {reason}")

    else:

        print(
            " - No additional safety restrictions."
        )

    # ================================================================
    # 10. COMPLETION
    # ================================================================

    print()
    print("=" * 70)
    print("RecoverOS X decision completed.")
    print("=" * 70)
    print()


# ======================================================================
# Test Payment
# ======================================================================

if __name__ == "__main__":

    payment = {

        "payment_id": "PX000001",

        "amount": 2500,

        "failure_reason": "bank_timeout",

        "payment_method": "netbanking",

        "merchant_type": "saas",

        "previous_successes": 8,

        "previous_failures": 1,

        "retry_count": 1,

        "days_since_last_payment": 12,

        "customer_tenure_months": 18,

        "mandate_age_days": 240,

        "average_amount": 2300,

        "amount_vs_average": 1.087,

        "recent_success_rate": 0.89,

        "failure_frequency": 0.05,

        "retry_interval_hours": 6,

        "risk_score": 0.10,
    }

    run_pipeline(payment)
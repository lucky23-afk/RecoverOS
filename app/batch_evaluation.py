"""
RecoverOS X - Batch Revenue Recovery Evaluation

Phase 2:
Measures simulated money recovered across a controlled batch.

Compares:
1. Baseline:
   Retry-first strategy.

2. RecoverOS:
   ML -> ERV -> Policy -> Safety -> Recovery execution.

IMPORTANT:
- All data is synthetic.
- Results are for controlled evaluation only.
- Each payment receives ONE fixed synthetic outcome score.
- Baseline and RecoverOS use the SAME outcome score for each payment.
- This prevents random-number ordering from biasing the comparison.
"""

import io
import json
import random
import sys
from contextlib import redirect_stdout
from datetime import date, timedelta
from pathlib import Path


# =================================================================
# PATH SETUP
# =================================================================

APP_DIR = Path(__file__).resolve().parent

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


# =================================================================
# IMPORTS
# =================================================================

from decision_orchestrator import run_orchestrator
from simulator import get_action_probability


# =================================================================
# CONFIGURATION
# =================================================================

DEFAULT_BATCH_SIZE = 1000
RANDOM_SEED = 42

DATA_DIR = APP_DIR.parent / "data"
REPORT_PATH = DATA_DIR / "batch_evaluation.json"

FAILURE_REASONS = [
    "bank_timeout",
    "network_error",
    "insufficient_funds",
    "expired_card",
    "mandate_expired",
    "suspicious_reversal",
    "mandate_changed_recently",
]

AMOUNTS = [
    499,
    799,
    999,
    1499,
    1999,
    2499,
    4999,
    9999,
    14999,
    24999,
    49999,
]


# =================================================================
# PAYMENT GENERATION
# =================================================================

def generate_payment(index):
    """
    Generate one synthetic failed payment.

    A fixed synthetic outcome score is generated once and stored
    with the payment. Both strategies later use this same score.
    """

    amount = random.choice(AMOUNTS)

    failure_reason = random.choice(
        FAILURE_REASONS
    )

    previous_successes = random.randint(
        0,
        20,
    )

    previous_failures = random.randint(
        0,
        6,
    )

    retry_count = random.randint(
        0,
        3,
    )

    average_amount = random.choice(
        [
            999,
            1499,
            2499,
            4999,
            9999,
        ]
    )

    if average_amount > 0:
        amount_vs_average = (
            amount / average_amount
        )
    else:
        amount_vs_average = 1.0

    total_history = (
        previous_successes
        + previous_failures
    )

    if total_history > 0:
        recent_success_rate = (
            previous_successes
            / total_history
        )
    else:
        recent_success_rate = 0.50

    failure_frequency = min(
        previous_failures / 10,
        1.0,
    )

    risk_score = random.uniform(
        0.02,
        0.35,
    )

    if failure_reason == "suspicious_reversal":
        risk_score = random.uniform(
            0.70,
            0.98,
        )

    elif failure_reason == "mandate_changed_recently":
        risk_score = random.uniform(
            0.40,
            0.80,
        )

    # -------------------------------------------------------------
    # IMPORTANT:
    # This value is generated ONCE for this payment.
    # Both strategies are evaluated against this same value.
    # -------------------------------------------------------------

    synthetic_outcome_score = random.random()

    return {
        "payment_id": f"BATCH_{index:05d}",
        "amount": amount,
        "failure_reason": failure_reason,
        "payment_method": random.choice(
            [
                "card",
                "upi",
                "netbanking",
                "emandate",
            ]
        ),
        "merchant_type": random.choice(
            [
                "saas",
                "ecommerce",
                "education",
                "marketplace",
            ]
        ),
        "previous_successes": previous_successes,
        "previous_failures": previous_failures,
        "retry_count": retry_count,
        "days_since_last_payment": random.randint(
            1,
            60,
        ),
        "customer_tenure_months": random.randint(
            1,
            48,
        ),
        "mandate_age_days": random.randint(
            10,
            500,
        ),
        "average_amount": average_amount,
        "amount_vs_average": amount_vs_average,
        "recent_success_rate": recent_success_rate,
        "failure_frequency": failure_frequency,
        "retry_interval_hours": random.choice(
            [
                2,
                6,
                12,
                24,
                48,
            ]
        ),
        "risk_score": risk_score,
        "date": (
            date.today()
            - timedelta(
                days=random.randint(
                    0,
                    30,
                )
            )
        ).isoformat(),

        # Controlled synthetic outcome.
        "synthetic_outcome_score":
            synthetic_outcome_score,
    }


def generate_batch(
    batch_size=DEFAULT_BATCH_SIZE
):
    return [
        generate_payment(index)
        for index in range(
            1,
            batch_size + 1,
        )
    ]


# =================================================================
# BASELINE
# =================================================================

def baseline_action(payment):
    """
    Baseline:
    Retry whenever the retry limit has not been reached.
    """

    if int(
        payment.get(
            "retry_count",
            0,
        )
    ) >= 3:
        return "hold_for_review"

    return "retry_payment"


def calculate_baseline_probability(payment):
    """
    Transparent synthetic baseline probability.

    This is NOT RecoverOS ML.
    """

    successes = float(
        payment.get(
            "previous_successes",
            0,
        )
    )

    failures = float(
        payment.get(
            "previous_failures",
            0,
        )
    )

    total = successes + failures

    if total == 0:
        probability = 0.45
    else:
        probability = (
            successes / total
        )

    retry_count = int(
        payment.get(
            "retry_count",
            0,
        )
    )

    probability -= (
        retry_count * 0.08
    )

    return max(
        0.05,
        min(
            probability,
            0.90,
        ),
    )


# =================================================================
# FAIR SYNTHETIC OUTCOME
# =================================================================

def evaluate_fixed_outcome(
    payment,
    action,
    action_probability,
):
    """
    Determine the simulated outcome using the payment's
    pre-generated synthetic outcome score.

    The same score is used regardless of strategy.

    Example:

        synthetic_outcome_score = 0.31

        baseline probability = 0.45
        RecoverOS probability = 0.72

        baseline -> recovered
        RecoverOS -> recovered

    Or:

        score = 0.60

        baseline -> not recovered
        RecoverOS -> recovered

    This creates a common-counterfactual style comparison
    rather than independent random draws.
    """

    score = float(
        payment.get(
            "synthetic_outcome_score",
            0.5,
        )
    )

    recovered = (
        score < float(action_probability)
    )

    amount = float(
        payment["amount"]
    )

    if recovered:
        outcome = "recovered"
        recovered_amount = amount

    elif action == "hold_for_review":
        outcome = "pending_review"
        recovered_amount = 0.0

    elif action == "blocked":
        outcome = "blocked"
        recovered_amount = 0.0

    else:
        outcome = "not_recovered"
        recovered_amount = 0.0

    return {
        "payment_id":
            payment.get("payment_id"),
        "amount":
            amount,
        "action":
            action,
        "outcome":
            outcome,
        "recovered":
            recovered,
        "recovered_amount":
            recovered_amount,
        "action_probability":
            float(action_probability),
        "synthetic_outcome_score":
            score,
    }


# =================================================================
# RUN BASELINE
# =================================================================

def run_baseline(payments):
    """
    Run the baseline against the fixed synthetic outcomes.
    """

    total_at_risk = 0.0
    total_recovered = 0.0

    recovered_count = 0
    automatic_actions = 0
    review_count = 0

    for payment in payments:
        amount = float(
            payment["amount"]
        )

        total_at_risk += amount

        action = baseline_action(
            payment
        )

        if action == "hold_for_review":
            review_count += 1
            continue

        automatic_actions += 1

        probability = (
            calculate_baseline_probability(
                payment
            )
        )

        result = evaluate_fixed_outcome(
            payment=payment,
            action=action,
            action_probability=probability,
        )

        if result["recovered"]:
            recovered_count += 1

            total_recovered += float(
                result["recovered_amount"]
            )

    return {
        "total_at_risk":
            total_at_risk,
        "total_recovered":
            total_recovered,
        "recovered_count":
            recovered_count,
        "automatic_actions":
            automatic_actions,
        "review_count":
            review_count,
    }


# =================================================================
# RUN RECOVEROS
# =================================================================

def run_recoveros(payments):
    """
    Run the complete RecoverOS decision pipeline.

    The RecoverOS action probability is used against the SAME
    synthetic outcome score attached to each payment.
    """

    total_at_risk = 0.0
    total_recovered = 0.0

    recovered_count = 0
    automatic_actions = 0
    review_count = 0
    blocked_count = 0

    action_counts = {}

    safety_reviews = 0

    for payment in payments:
        amount = float(
            payment["amount"]
        )

        total_at_risk += amount

        # Suppress noisy orchestrator logs.
        with redirect_stdout(
            io.StringIO()
        ):
            decision = run_orchestrator(
                payment
            )

        final_action = decision[
            "final_action"
        ]

        action_counts[
            final_action
        ] = (
            action_counts.get(
                final_action,
                0,
            )
            + 1
        )

        if final_action == "blocked":
            blocked_count += 1
            continue

        if (
            final_action
            == "hold_for_review"
        ):
            review_count += 1
            safety_reviews += 1
            continue

        automatic_actions += 1

        recovery_probability = float(
            decision[
                "recovery_probability"
            ]
        )

        # Recompute the action-specific probability
        # using the same simulator logic that execution uses.
        action_probability = (
            get_action_probability(
                payment=payment,
                action=final_action,
                base_probability=
                    recovery_probability,
            )
        )

        result = evaluate_fixed_outcome(
            payment=payment,
            action=final_action,
            action_probability=
                action_probability,
        )

        if result["recovered"]:
            recovered_count += 1

            total_recovered += float(
                result["recovered_amount"]
            )

    return {
        "total_at_risk":
            total_at_risk,
        "total_recovered":
            total_recovered,
        "recovered_count":
            recovered_count,
        "automatic_actions":
            automatic_actions,
        "review_count":
            review_count,
        "blocked_count":
            blocked_count,
        "safety_reviews":
            safety_reviews,
        "action_counts":
            action_counts,
    }


# =================================================================
# METRICS
# =================================================================

def calculate_metrics(result):
    total_at_risk = float(
        result["total_at_risk"]
    )

    total_recovered = float(
        result["total_recovered"]
    )

    if total_at_risk > 0:
        revenue_recovery_rate = (
            total_recovered
            / total_at_risk
        )
    else:
        revenue_recovery_rate = 0.0

    return {
        **result,
        "revenue_recovery_rate":
            revenue_recovery_rate,
    }


# =================================================================
# COMPARISON
# =================================================================

def compare_results(
    baseline,
    recoveros,
):
    baseline_recovered = float(
        baseline["total_recovered"]
    )

    recoveros_recovered = float(
        recoveros["total_recovered"]
    )

    incremental_recovery = (
        recoveros_recovered
        - baseline_recovered
    )

    if baseline_recovered > 0:
        improvement_percent = (
            incremental_recovery
            / baseline_recovered
        )
    else:
        improvement_percent = 0.0

    baseline_rate = 0.0
    recoveros_rate = 0.0

    if baseline["total_at_risk"] > 0:
        baseline_rate = (
            baseline_recovered
            / baseline["total_at_risk"]
        )

    if recoveros["total_at_risk"] > 0:
        recoveros_rate = (
            recoveros_recovered
            / recoveros["total_at_risk"]
        )

    recovery_rate_uplift = (
        recoveros_rate
        - baseline_rate
    )

    return {
        "incremental_recovery":
            incremental_recovery,
        "improvement_percent":
            improvement_percent,
        "baseline_recovery_rate":
            baseline_rate,
        "recoveros_recovery_rate":
            recoveros_rate,
        "recovery_rate_uplift":
            recovery_rate_uplift,
        "recovery_rate_uplift_pp":
            recovery_rate_uplift * 100,
    }


# =================================================================
# SAVE REPORT
# =================================================================

def save_report(
    batch_size,
    baseline,
    recoveros,
    comparison,
):
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    report = {
        "evaluation": {
            "name":
                "RecoverOS X Revenue Recovery Evaluation",
            "batch_size":
                batch_size,
            "seed":
                RANDOM_SEED,
            "data_type":
                "synthetic",
            "comparison_method":
                "shared fixed synthetic outcome per payment",
            "description":
                (
                    "Controlled comparison of a retry-first "
                    "baseline against the RecoverOS "
                    "ML -> ERV -> Policy -> Safety pipeline."
                ),
        },

        "baseline":
            calculate_metrics(
                baseline
            ),

        "recoveros":
            calculate_metrics(
                recoveros
            ),

        "comparison":
            comparison,
    }

    with open(
        REPORT_PATH,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
        )

    return report


# =================================================================
# REPORT
# =================================================================

def print_report(
    batch_size,
    baseline,
    recoveros,
    comparison,
):
    print()

    print("=" * 78)
    print(
        "             RECOVEROS X - REVENUE RECOVERY TEST"
    )
    print("=" * 78)

    print()

    print("BATCH")
    print("-" * 78)

    print(
        f"Payments evaluated       : "
        f"{batch_size:,}"
    )

    print(
        f"Revenue at risk          : "
        f"₹{baseline['total_at_risk']:,.2f}"
    )

    print()

    print("BASELINE: RETRY-FIRST")
    print("-" * 78)

    print(
        f"Recovered                : "
        f"₹{baseline['total_recovered']:,.2f}"
    )

    print(
        f"Recovered payments       : "
        f"{baseline['recovered_count']:,}"
    )

    print(
        f"Revenue recovery rate    : "
        f"{baseline['total_recovered'] / baseline['total_at_risk']:.2%}"
    )

    print(
        f"Automatic actions        : "
        f"{baseline['automatic_actions']:,}"
    )

    print(
        f"Review                   : "
        f"{baseline['review_count']:,}"
    )

    print()

    print("RECOVEROS X")
    print("-" * 78)

    print(
        f"Recovered                : "
        f"₹{recoveros['total_recovered']:,.2f}"
    )

    print(
        f"Recovered payments       : "
        f"{recoveros['recovered_count']:,}"
    )

    print(
        f"Revenue recovery rate    : "
        f"{recoveros['total_recovered'] / recoveros['total_at_risk']:.2%}"
    )

    print(
        f"Automatic actions        : "
        f"{recoveros['automatic_actions']:,}"
    )

    print(
        f"Human review             : "
        f"{recoveros['review_count']:,}"
    )

    print(
        f"Blocked                  : "
        f"{recoveros['blocked_count']:,}"
    )

    print()

    print("ACTION DISTRIBUTION")
    print("-" * 78)

    for action, count in sorted(
        recoveros["action_counts"].items()
    ):
        print(
            f"{action:24} : {count:,}"
        )

    print()

    print("BUSINESS IMPACT")
    print("-" * 78)

    print(
        f"Incremental recovery     : "
        f"₹{comparison['incremental_recovery']:,.2f}"
    )

    print(
        f"Improvement vs baseline  : "
        f"{comparison['improvement_percent']:.2%}"
    )

    print(
        f"Recovery-rate uplift     : "
        f"{comparison['recovery_rate_uplift_pp']:.2f} pp"
    )

    print()

    print("OUTPUT")
    print("-" * 78)

    print(
        f"Evaluation report        : "
        f"{REPORT_PATH}"
    )

    print()

    print("IMPORTANT")
    print("-" * 78)

    print(
        "These results are SYNTHETIC simulation results."
    )

    print(
        "They must not be presented as real Razorpay production recovery."
    )

    print(
        "Both strategies use the same fixed synthetic outcome "
        "score for each payment."
    )

    print("=" * 78)


# =================================================================
# MAIN
# =================================================================

def main():
    batch_size = DEFAULT_BATCH_SIZE

    # -------------------------------------------------------------
    # Generate one fixed batch
    # -------------------------------------------------------------

    random.seed(RANDOM_SEED)

    payments = generate_batch(
        batch_size
    )

    # -------------------------------------------------------------
    # Baseline
    # -------------------------------------------------------------

    baseline = run_baseline(
        payments
    )

    # -------------------------------------------------------------
    # RecoverOS
    # -------------------------------------------------------------

    recoveros = run_recoveros(
        payments
    )

    # -------------------------------------------------------------
    # Comparison
    # -------------------------------------------------------------

    comparison = compare_results(
        baseline,
        recoveros,
    )

    # -------------------------------------------------------------
    # Save report
    # -------------------------------------------------------------

    save_report(
        batch_size=batch_size,
        baseline=baseline,
        recoveros=recoveros,
        comparison=comparison,
    )

    # -------------------------------------------------------------
    # Console report
    # -------------------------------------------------------------

    print_report(
        batch_size=batch_size,
        baseline=baseline,
        recoveros=recoveros,
        comparison=comparison,
    )


if __name__ == "__main__":
    main()
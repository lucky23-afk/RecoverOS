"""
RecoverOS X - Label-Based Batch Revenue Recovery Evaluation

Uses the actual labeled recovery dataset instead of a random
synthetic outcome score.

IMPORTANT:
- The dataset contains observed `recovered` labels.
- It does NOT prove that a particular RecoverOS action caused recovery.
- Therefore this evaluates recoverable-revenue capture / decision coverage.
- It does NOT claim real incremental money recovered by RecoverOS.
"""

import io
import json
import random
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pandas as pd


# =================================================================
# PATH SETUP
# =================================================================

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent
DATA_DIR = BASE_DIR / "data"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


# =================================================================
# IMPORTS
# =================================================================

from decision_orchestrator import run_orchestrator


# =================================================================
# CONFIGURATION
# =================================================================

DATA_FILE = DATA_DIR / "advanced_training_data.csv"
REPORT_PATH = DATA_DIR / "batch_evaluation.json"

BATCH_SIZE = 1000
RANDOM_SEED = 42

TARGET = "recovered"

FEATURE_COLUMNS = [
    "payment_id",
    "amount",
    "failure_reason",
    "payment_method",
    "merchant_type",
    "previous_successes",
    "previous_failures",
    "retry_count",
    "days_since_last_payment",
    "customer_tenure_months",
    "mandate_age_days",
    "average_amount",
    "amount_vs_average",
    "recent_success_rate",
    "failure_frequency",
    "retry_interval_hours",
]


# =================================================================
# DATA
# =================================================================

def load_batch() -> pd.DataFrame:
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_FILE}"
        )

    df = pd.read_csv(DATA_FILE)

    required = FEATURE_COLUMNS + [TARGET]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Dataset is missing columns: "
            + ", ".join(missing)
        )

    if len(df) < BATCH_SIZE:
        raise ValueError(
            f"Dataset contains only {len(df)} rows; "
            f"{BATCH_SIZE} are required."
        )

    # Deterministic controlled sample.
    return df.sample(
        n=BATCH_SIZE,
        random_state=RANDOM_SEED,
    ).reset_index(drop=True)


# =================================================================
# BASELINE
# =================================================================

def baseline_decision(row):
    """
    Simple retry-first control.

    Automatic recovery is attempted when the retry limit
    has not already been reached.

    This baseline is intentionally simple and is NOT presented
    as an industry benchmark.
    """

    retry_count = int(row["retry_count"])

    if retry_count >= 3:
        return "hold_for_review"

    return "retry_payment"


# =================================================================
# RECOVEROS
# =================================================================

def build_payment(row):
    return {
        "payment_id": str(row["payment_id"]),
        "amount": float(row["amount"]),
        "failure_reason": str(row["failure_reason"]),
        "payment_method": str(row["payment_method"]),
        "merchant_type": str(row["merchant_type"]),
        "previous_successes": int(row["previous_successes"]),
        "previous_failures": int(row["previous_failures"]),
        "retry_count": int(row["retry_count"]),
        "days_since_last_payment": int(
            row["days_since_last_payment"]
        ),
        "customer_tenure_months": int(
            row["customer_tenure_months"]
        ),
        "mandate_age_days": int(
            row["mandate_age_days"]
        ),
        "average_amount": float(
            row["average_amount"]
        ),
        "amount_vs_average": float(
            row["amount_vs_average"]
        ),
        "recent_success_rate": float(
            row["recent_success_rate"]
        ),
        "failure_frequency": float(
            row["failure_frequency"]
        ),
        "retry_interval_hours": float(
            row["retry_interval_hours"]
        ),
        "risk_score": (
            0.90
            if str(row["failure_reason"]).lower()
            == "suspicious_reversal"
            else 0.10
        ),
    }


def evaluate_recoveros(df):
    total_at_risk = 0.0

    recoverable_revenue = 0.0

    automatically_selected_revenue = 0.0
    automatically_selected_recoverable_revenue = 0.0

    review_revenue = 0.0
    blocked_revenue = 0.0

    recovered_cases_in_batch = 0
    captured_recoverable_cases = 0

    action_counts = {}

    policy_violations = 0
    safety_reviews = 0

    for _, row in df.iterrows():

        amount = float(row["amount"])
        observed_recovered = int(row[TARGET]) == 1

        total_at_risk += amount

        if observed_recovered:
            recoverable_revenue += amount
            recovered_cases_in_batch += 1

        payment = build_payment(row)

        # Keep orchestrator console output out of the evaluation report.
        with redirect_stdout(io.StringIO()):
            decision = run_orchestrator(payment)

        final_action = str(
            decision.get(
                "final_action",
                "blocked",
            )
        )

        action_counts[final_action] = (
            action_counts.get(final_action, 0) + 1
        )

        allowed_actions = set(
            decision.get(
                "policy_allowed_actions",
                [],
            )
        )

        integrity_valid = bool(
            decision.get(
                "integrity_valid",
                False,
            )
        )

        if not integrity_valid:
            policy_violations += 1

        # ---------------------------------------------------------
        # Classification of the chosen decision
        # ---------------------------------------------------------

        if final_action == "blocked":
            blocked_revenue += amount

        elif final_action == "hold_for_review":
            review_revenue += amount
            safety_reviews += 1

        else:
            automatically_selected_revenue += amount

            if observed_recovered:
                automatically_selected_recoverable_revenue += amount
                captured_recoverable_cases += 1

            # Final executable action must be policy approved.
            if final_action not in allowed_actions:
                policy_violations += 1

    return {
        "total_at_risk": total_at_risk,
        "recoverable_revenue": recoverable_revenue,
        "recovered_cases_in_batch": recovered_cases_in_batch,
        "captured_recoverable_cases": captured_recoverable_cases,
        "automatically_selected_revenue": automatically_selected_revenue,
        "automatically_selected_recoverable_revenue": (
            automatically_selected_recoverable_revenue
        ),
        "review_revenue": review_revenue,
        "blocked_revenue": blocked_revenue,
        "review_count": action_counts.get(
            "hold_for_review",
            0,
        ),
        "blocked_count": action_counts.get(
            "blocked",
            0,
        ),
        "automatic_count": (
            sum(action_counts.values())
            - action_counts.get("hold_for_review", 0)
            - action_counts.get("blocked", 0)
        ),
        "action_counts": action_counts,
        "policy_violations": policy_violations,
        "safety_reviews": safety_reviews,
    }


def evaluate_baseline(df):
    total_at_risk = 0.0
    recoverable_revenue = 0.0

    automatically_selected_revenue = 0.0
    automatically_selected_recoverable_revenue = 0.0

    review_count = 0
    captured_recoverable_cases = 0
    recovered_cases_in_batch = 0

    for _, row in df.iterrows():

        amount = float(row["amount"])
        observed_recovered = int(row[TARGET]) == 1

        total_at_risk += amount

        if observed_recovered:
            recoverable_revenue += amount
            recovered_cases_in_batch += 1

        action = baseline_decision(row)

        if action == "hold_for_review":
            review_count += 1
            continue

        automatically_selected_revenue += amount

        if observed_recovered:
            automatically_selected_recoverable_revenue += amount
            captured_recoverable_cases += 1

    return {
        "total_at_risk": total_at_risk,
        "recoverable_revenue": recoverable_revenue,
        "recovered_cases_in_batch": recovered_cases_in_batch,
        "captured_recoverable_cases": captured_recoverable_cases,
        "automatically_selected_revenue": automatically_selected_revenue,
        "automatically_selected_recoverable_revenue": (
            automatically_selected_recoverable_revenue
        ),
        "review_count": review_count,
    }


# =================================================================
# METRICS
# =================================================================

def add_metrics(result):

    recoverable_revenue = float(
        result["recoverable_revenue"]
    )

    captured = float(
        result["automatically_selected_recoverable_revenue"]
    )

    if recoverable_revenue > 0:
        recoverable_revenue_capture_rate = (
            captured / recoverable_revenue
        )
    else:
        recoverable_revenue_capture_rate = 0.0

    result["recoverable_revenue_capture_rate"] = (
        recoverable_revenue_capture_rate
    )

    return result


# =================================================================
# REPORT
# =================================================================

def save_report(
    baseline,
    recoveros,
):
    baseline = add_metrics(baseline)
    recoveros = add_metrics(recoveros)

    incremental_captured_recoverable_revenue = (
        recoveros[
            "automatically_selected_recoverable_revenue"
        ]
        - baseline[
            "automatically_selected_recoverable_revenue"
        ]
    )

    report = {
        "evaluation": {
            "name": (
                "RecoverOS X Label-Based Revenue "
                "Recovery Decision Evaluation"
            ),
            "batch_size": BATCH_SIZE,
            "seed": RANDOM_SEED,
            "data_type": "observed labeled dataset",
            "target": TARGET,
            "comparison_method": (
                "deterministic 1,000-record sample "
                "from the labeled dataset"
            ),
            "interpretation": (
                "Measures historically recoverable revenue "
                "captured by each decision strategy. "
                "It does not establish causal recovery from "
                "a particular intervention."
            ),
        },
        "baseline": baseline,
        "recoveros": recoveros,
        "comparison": {
            "incremental_captured_recoverable_revenue": (
                incremental_captured_recoverable_revenue
            ),
            "capture_rate_uplift": (
                recoveros[
                    "recoverable_revenue_capture_rate"
                ]
                - baseline[
                    "recoverable_revenue_capture_rate"
                ]
            ),
            "capture_rate_uplift_pp": (
                (
                    recoveros[
                        "recoverable_revenue_capture_rate"
                    ]
                    - baseline[
                        "recoverable_revenue_capture_rate"
                    ]
                )
                * 100
            ),
        },
    }

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

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


def print_report(
    baseline,
    recoveros,
    report,
):

    comparison = report["comparison"]

    print()
    print("=" * 78)
    print(
        "       RECOVEROS X - LABEL-BASED RECOVERY EVALUATION"
    )
    print("=" * 78)

    print()
    print("BATCH")
    print("-" * 78)

    print(
        f"Payments evaluated       : {BATCH_SIZE:,}"
    )

    print(
        f"Revenue at risk          : "
        f"₹{recoveros['total_at_risk']:,.2f}"
    )

    print(
        f"Historically recoverable : "
        f"₹{recoveros['recoverable_revenue']:,.2f}"
    )

    print()
    print("BASELINE: RETRY-FIRST")
    print("-" * 78)

    print(
        f"Automatic cases          : "
        f"{BATCH_SIZE - baseline['review_count']:,}"
    )

    print(
        f"Recoverable revenue "
        f"captured                : "
        f"₹{baseline['automatically_selected_recoverable_revenue']:,.2f}"
    )

    print(
        f"Capture rate              : "
        f"{baseline['recoverable_revenue_capture_rate']:.2%}"
    )

    print(
        f"Review                   : "
        f"{baseline['review_count']:,}"
    )

    print()
    print("RECOVEROS X")
    print("-" * 78)

    print(
        f"Automatic cases          : "
        f"{recoveros['automatic_count']:,}"
    )

    print(
        f"Recoverable revenue "
        f"captured                : "
        f"₹{recoveros['automatically_selected_recoverable_revenue']:,.2f}"
    )

    print(
        f"Capture rate              : "
        f"{recoveros['recoverable_revenue_capture_rate']:.2%}"
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
    print("SAFETY / POLICY")
    print("-" * 78)

    print(
        f"Policy violations        : "
        f"{recoveros['policy_violations']:,}"
    )

    print(
        f"Safety reviews           : "
        f"{recoveros['safety_reviews']:,}"
    )

    print()
    print("BUSINESS IMPACT")
    print("-" * 78)

    print(
        f"Incremental recoverable "
        f"revenue captured        : "
        f"₹{comparison['incremental_captured_recoverable_revenue']:,.2f}"
    )

    print(
        f"Capture-rate uplift      : "
        f"{comparison['capture_rate_uplift_pp']:.2f} pp"
    )

    print()
    print("IMPORTANT")
    print("-" * 78)

    print(
        "The dataset contains observed recovery labels."
    )

    print(
        "Those labels do not prove that a specific RecoverOS "
        "intervention caused the recovery."
    )

    print(
        "This evaluation measures recoverable-revenue capture "
        "by the decision policy, not causal recovered money."
    )

    print()
    print(
        f"Evaluation report        : {REPORT_PATH}"
    )

    print("=" * 78)


# =================================================================
# MAIN
# =================================================================

def main():

    random.seed(RANDOM_SEED)

    df = load_batch()

    baseline = evaluate_baseline(df)
    recoveros = evaluate_recoveros(df)

    report = save_report(
        baseline=baseline,
        recoveros=recoveros,
    )

    print_report(
        baseline=baseline,
        recoveros=recoveros,
        report=report,
    )


if __name__ == "__main__":
    main()
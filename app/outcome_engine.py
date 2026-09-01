
from pathlib import Path
import json
from collections import defaultdict


# ================================================================
# PATHS
# ================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

OUTCOME_FILE = DATA_DIR / "outcomes.jsonl"


# ================================================================
# LOAD OUTCOMES
# ================================================================

def load_outcomes():

    if not OUTCOME_FILE.exists():
        print("Outcome file not found:")
        print(OUTCOME_FILE)
        return []

    outcomes = []

    with open(
        OUTCOME_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)

                if isinstance(record, dict):
                    outcomes.append(record)

            except json.JSONDecodeError:
                print("Warning: skipped invalid outcome record.")

    return outcomes


# ================================================================
# SAFE HELPERS
# ================================================================

def get_bool(value):

    if isinstance(value, bool):
        return value

    if isinstance(value, str):

        return value.lower() in [
            "true",
            "1",
            "yes",
            "recovered",
        ]

    if isinstance(value, (int, float)):
        return value == 1

    return False


def get_float(value, default=0.0):

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def get_text(record, *keys):

    for key in keys:

        value = record.get(key)

        if value is not None:
            return str(value)

    return "unknown"


# ================================================================
# OVERALL PERFORMANCE
# ================================================================

def calculate_overall(outcomes):

    total = len(outcomes)

    recovered = 0
    recovered_amount = 0.0
    prediction_total = 0.0
    prediction_count = 0

    for outcome in outcomes:

        if get_bool(outcome.get("recovered")):
            recovered += 1

            recovered_amount += get_float(
                outcome.get("recovery_amount", 0)
            )

        probability = outcome.get(
            "recovery_probability"
        )

        if probability is not None:

            probability = get_float(
                probability
            )

            # Accept either 0.82 or 82
            if probability > 1:
                probability = probability / 100

            prediction_total += probability
            prediction_count += 1

    if total > 0:
        recovery_rate = recovered / total
    else:
        recovery_rate = 0.0

    if prediction_count > 0:
        average_prediction = (
            prediction_total / prediction_count
        )
    else:
        average_prediction = 0.0

    prediction_error = abs(
        average_prediction - recovery_rate
    )

    return {
        "total": total,
        "recovered": recovered,
        "recovery_rate": recovery_rate,
        "average_prediction": average_prediction,
        "prediction_error": prediction_error,
        "recovered_amount": recovered_amount,
    }


# ================================================================
# STRATEGY ANALYSIS
# ================================================================

def analyze_strategies(outcomes):

    data = defaultdict(
        lambda: {
            "total": 0,
            "recovered": 0,
            "revenue": 0.0,
        }
    )

    for outcome in outcomes:

        action = get_text(
            outcome,
            "final_action",
            "action",
            "recommended_action",
        )

        data[action]["total"] += 1

        if get_bool(outcome.get("recovered")):

            data[action]["recovered"] += 1

            data[action]["revenue"] += get_float(
                outcome.get("recovery_amount", 0)
            )

    return data


# ================================================================
# FAILURE ANALYSIS
# ================================================================

def analyze_failures(outcomes):

    data = defaultdict(
        lambda: {
            "total": 0,
            "recovered": 0,
        }
    )

    for outcome in outcomes:

        reason = get_text(
            outcome,
            "failure_reason",
            "failure_type",
            "reason",
        )

        data[reason]["total"] += 1

        if get_bool(outcome.get("recovered")):
            data[reason]["recovered"] += 1

    return data


# ================================================================
# LEARNING SIGNAL
# ================================================================

def learning_signal(overall):

    if overall["total"] == 0:

        return (
            "NO_DATA",
            "Collect outcome data before evaluating the model."
        )

    error = overall["prediction_error"]

    if error <= 0.05:

        return (
            "GOOD",
            "Predictions are reasonably aligned with observed outcomes."
        )

    if error <= 0.15:

        return (
            "MONITOR",
            "Model calibration should be monitored as more outcomes arrive."
        )

    return (
        "RETRAIN_RECOMMENDED",
        "Observed outcomes differ substantially from model predictions."
    )


# ================================================================
# MAIN REPORT
# ================================================================

def run_engine():

    print()
    print("=" * 70)
    print("RecoverOS X - OUTCOME INTELLIGENCE ENGINE")
    print("=" * 70)

    outcomes = load_outcomes()

    print()
    print("DATA")
    print("-" * 70)

    print(
        f"Outcome records      : {len(outcomes)}"
    )

    if not outcomes:

        print()
        print("No outcome records available.")
        print("Run the outcome tracker first.")

        print()
        print("=" * 70)

        return

    # ============================================================
    # OVERALL
    # ============================================================

    overall = calculate_overall(outcomes)

    print()
    print("OVERALL PERFORMANCE")
    print("-" * 70)

    print(
        f"Total decisions      : "
        f"{overall['total']}"
    )

    print(
        f"Recovered            : "
        f"{overall['recovered']}"
    )

    print(
        f"Observed recovery    : "
        f"{overall['recovery_rate']:.2%}"
    )

    print(
        f"Average ML prediction: "
        f"{overall['average_prediction']:.2%}"
    )

    print(
        f"Prediction error     : "
        f"{overall['prediction_error']:.2%}"
    )

    print(
        f"Recovered revenue    : "
        f"₹{overall['recovered_amount']:.2f}"
    )

    # ============================================================
    # STRATEGIES
    # ============================================================

    strategies = analyze_strategies(
        outcomes
    )

    print()
    print("STRATEGY PERFORMANCE")
    print("-" * 70)

    if strategies:

        for action, stats in strategies.items():

            total = stats["total"]
            recovered = stats["recovered"]

            if total > 0:
                rate = recovered / total
            else:
                rate = 0.0

            print(
                f"{action:<24} "
                f"Cases: {total:<4} "
                f"Recovery: {rate:.2%} "
                f"Revenue: ₹{stats['revenue']:.2f}"
            )

    else:

        print("No strategy information available.")

    # ============================================================
    # FAILURE REASONS
    # ============================================================

    failures = analyze_failures(
        outcomes
    )

    print()
    print("FAILURE ANALYSIS")
    print("-" * 70)

    if failures:

        for reason, stats in failures.items():

            total = stats["total"]
            recovered = stats["recovered"]

            if total > 0:
                rate = recovered / total
            else:
                rate = 0.0

            print(
                f"{reason:<24} "
                f"Cases: {total:<4} "
                f"Recovery: {rate:.2%}"
            )

    else:

        print("No failure information available.")

    # ============================================================
    # LEARNING
    # ============================================================

    status, message = learning_signal(
        overall
    )

    print()
    print("LEARNING SIGNAL")
    print("-" * 70)

    print(
        f"Status               : {status}"
    )

    print(
        f"Recommendation       : {message}"
    )

    # ============================================================
    # END
    # ============================================================

    print()
    print("=" * 70)
    print("RecoverOS X outcome analysis completed.")
    print("=" * 70)
    print()


# ================================================================
# ENTRY POINT
# ================================================================

if __name__ == "__main__":
    run_engine()



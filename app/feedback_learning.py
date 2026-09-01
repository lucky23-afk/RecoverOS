
from pathlib import Path
import json
import csv


# ================================================================
# PATHS
# ================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

OUTCOME_FILE = DATA_DIR / "outcomes.jsonl"
FEEDBACK_FILE = DATA_DIR / "feedback_training_data.csv"


# ================================================================
# FEATURES WE WANT TO PRESERVE
# ================================================================

FEATURES = [
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
    "recovery_probability",
    "final_action",
    "recovered",
    "recovery_amount",
]


# ================================================================
# HELPERS
# ================================================================

def safe_float(value, default=0.0):

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_bool(value):

    if isinstance(value, bool):
        return value

    if isinstance(value, str):

        return value.strip().lower() in {
            "true",
            "1",
            "yes",
            "recovered",
        }

    if isinstance(value, (int, float)):
        return value == 1

    return False


def first_value(record, keys, default=""):

    for key in keys:

        if key in record and record[key] is not None:
            return record[key]

    return default


# ================================================================
# LOAD OUTCOMES
# ================================================================

def load_outcomes():

    if not OUTCOME_FILE.exists():

        print()
        print("ERROR")
        print("-" * 70)
        print("Outcome file does not exist:")
        print(OUTCOME_FILE)
        print()
        return []

    records = []

    with open(
        OUTCOME_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        for line_number, line in enumerate(file, start=1):

            line = line.strip()

            if not line:
                continue

            try:

                record = json.loads(line)

                if isinstance(record, dict):
                    records.append(record)

            except json.JSONDecodeError:

                print(
                    f"Warning: skipped invalid JSON on line "
                    f"{line_number}."
                )

    return records


# ================================================================
# CONVERT OUTCOME → LEARNING RECORD
# ================================================================

def convert_outcome(outcome):

    recovered = safe_bool(
        outcome.get("recovered")
    )

    recovery_probability = safe_float(
        first_value(
            outcome,
            [
                "recovery_probability",
                "predicted_probability",
                "ml_probability",
            ],
            0.0,
        )
    )

    # Normalize 82 → 0.82
    if recovery_probability > 1:
        recovery_probability /= 100

    record = {

        "payment_id": first_value(
            outcome,
            ["payment_id", "id"],
            "",
        ),

        "amount": safe_float(
            outcome.get("amount", 0)
        ),

        "failure_reason": first_value(
            outcome,
            ["failure_reason", "failure_type"],
            "unknown",
        ),

        "payment_method": first_value(
            outcome,
            ["payment_method"],
            "unknown",
        ),

        "merchant_type": first_value(
            outcome,
            ["merchant_type"],
            "unknown",
        ),

        "previous_successes": safe_int(
            outcome.get("previous_successes", 0)
        ),

        "previous_failures": safe_int(
            outcome.get("previous_failures", 0)
        ),

        "retry_count": safe_int(
            outcome.get("retry_count", 0)
        ),

        "days_since_last_payment": safe_int(
            outcome.get(
                "days_since_last_payment",
                0,
            )
        ),

        "customer_tenure_months": safe_int(
            outcome.get(
                "customer_tenure_months",
                0,
            )
        ),

        "mandate_age_days": safe_int(
            outcome.get(
                "mandate_age_days",
                0,
            )
        ),

        "average_amount": safe_float(
            outcome.get(
                "average_amount",
                0,
            )
        ),

        "amount_vs_average": safe_float(
            outcome.get(
                "amount_vs_average",
                0,
            )
        ),

        "recent_success_rate": safe_float(
            outcome.get(
                "recent_success_rate",
                0,
            )
        ),

        "failure_frequency": safe_float(
            outcome.get(
                "failure_frequency",
                0,
            )
        ),

        "retry_interval_hours": safe_float(
            outcome.get(
                "retry_interval_hours",
                0,
            )
        ),

        "recovery_probability": recovery_probability,

        "final_action": first_value(
            outcome,
            [
                "final_action",
                "action",
                "recommended_action",
            ],
            "unknown",
        ),

        # THIS IS THE NEW SUPERVISED LEARNING LABEL
        "recovered": int(recovered),

        "recovery_amount": safe_float(
            first_value(
                outcome,
                [
                    "recovery_amount",
                    "recovered_amount",
                ],
                0,
            )
        ),
    }

    return record


# ================================================================
# DEDUPLICATION
# ================================================================

def remove_duplicates(records):

    unique = {}

    for record in records:

        payment_id = record.get(
            "payment_id"
        )

        if payment_id:

            unique[payment_id] = record

        else:

            # Keep records without IDs unique by content
            key = json.dumps(
                record,
                sort_keys=True,
            )

            unique[key] = record

    return list(unique.values())


# ================================================================
# SAVE CSV
# ================================================================

def save_feedback(records):

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        FEEDBACK_FILE,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=FEATURES,
        )

        writer.writeheader()

        for record in records:

            writer.writerow({
                feature: record.get(
                    feature,
                    "",
                )
                for feature in FEATURES
            })


# ================================================================
# MAIN
# ================================================================

def run_feedback_learning():

    print()
    print("=" * 70)
    print("RecoverOS X - FEEDBACK LEARNING PIPELINE")
    print("=" * 70)

    outcomes = load_outcomes()

    print()
    print("SOURCE DATA")
    print("-" * 70)

    print(
        f"Outcome records      : {len(outcomes)}"
    )

    if not outcomes:

        print()
        print(
            "No outcomes available. "
            "Run the outcome tracker first."
        )

        print()
        print("=" * 70)

        return

    # ------------------------------------------------------------
    # CONVERT
    # ------------------------------------------------------------

    records = []

    for outcome in outcomes:

        record = convert_outcome(
            outcome
        )

        records.append(record)

    # ------------------------------------------------------------
    # DEDUPLICATE
    # ------------------------------------------------------------

    records = remove_duplicates(
        records
    )

    # ------------------------------------------------------------
    # SAVE
    # ------------------------------------------------------------

    save_feedback(records)

    recovered = sum(
        record["recovered"]
        for record in records
    )

    not_recovered = (
        len(records) - recovered
    )

    recovery_rate = (
        recovered / len(records)
        if records
        else 0.0
    )

    # ------------------------------------------------------------
    # REPORT
    # ------------------------------------------------------------

    print()
    print("LEARNING DATA")
    print("-" * 70)

    print(
        f"Learning records     : {len(records)}"
    )

    print(
        f"Recovered            : {recovered}"
    )

    print(
        f"Not recovered        : {not_recovered}"
    )

    print(
        f"Recovery rate        : "
        f"{recovery_rate:.2%}"
    )

    print()
    print("FEATURES")
    print("-" * 70)

    for feature in FEATURES:

        print(
            f" - {feature}"
        )

    print()
    print("OUTPUT")
    print("-" * 70)

    print(
        f"Saved to             : "
        f"{FEEDBACK_FILE}"
    )

    print()
    print("=" * 70)
    print("Feedback learning data generated.")
    print("=" * 70)
    print()


# ================================================================
# ENTRY POINT
# ================================================================

if __name__ == "__main__":
    run_feedback_learning()


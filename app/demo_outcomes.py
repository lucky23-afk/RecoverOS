import json
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

OUTCOMES_FILE = DATA_DIR / "outcomes.jsonl"

DEMO_OUTCOMES = [
    {
        "payment_id": "DEMO_002",
        "amount": 1800,
        "failure_reason": "bank_timeout",
        "recommended_action": "retry_payment",
        "final_action": "retry_payment",
        "recovery_probability": 0.82,
        "expected_revenue": 1476,
        "recovered": True,
        "recovery_amount": 1800,
    },
    {
        "payment_id": "DEMO_003",
        "amount": 3200,
        "failure_reason": "bank_timeout",
        "recommended_action": "retry_payment",
        "final_action": "retry_payment",
        "recovery_probability": 0.79,
        "expected_revenue": 2528,
        "recovered": True,
        "recovery_amount": 3200,
    },
    {
        "payment_id": "DEMO_004",
        "amount": 1500,
        "failure_reason": "insufficient_funds",
        "recommended_action": "send_update_link",
        "final_action": "send_update_link",
        "recovery_probability": 0.45,
        "expected_revenue": 675,
        "recovered": False,
        "recovery_amount": 0,
    },
    {
        "payment_id": "DEMO_005",
        "amount": 4200,
        "failure_reason": "bank_timeout",
        "recommended_action": "retry_payment",
        "final_action": "retry_payment",
        "recovery_probability": 0.84,
        "expected_revenue": 3528,
        "recovered": True,
        "recovery_amount": 4200,
    },
    {
        "payment_id": "DEMO_006",
        "amount": 2750,
        "failure_reason": "network_error",
        "recommended_action": "retry_payment",
        "final_action": "retry_payment",
        "recovery_probability": 0.76,
        "expected_revenue": 2090,
        "recovered": True,
        "recovery_amount": 2750,
    },
    {
        "payment_id": "DEMO_007",
        "amount": 2100,
        "failure_reason": "insufficient_funds",
        "recommended_action": "send_update_link",
        "final_action": "send_update_link",
        "recovery_probability": 0.40,
        "expected_revenue": 840,
        "recovered": False,
        "recovery_amount": 0,
    },
    {
        "payment_id": "DEMO_008",
        "amount": 3600,
        "failure_reason": "bank_timeout",
        "recommended_action": "retry_payment",
        "final_action": "retry_payment",
        "recovery_probability": 0.81,
        "expected_revenue": 2916,
        "recovered": True,
        "recovery_amount": 3600,
    },
    {
        "payment_id": "DEMO_009",
        "amount": 1900,
        "failure_reason": "network_error",
        "recommended_action": "retry_payment",
        "final_action": "retry_payment",
        "recovery_probability": 0.74,
        "expected_revenue": 1406,
        "recovered": True,
        "recovery_amount": 1900,
    },
    {
        "payment_id": "DEMO_010",
        "amount": 5000,
        "failure_reason": "insufficient_funds",
        "recommended_action": "send_update_link",
        "final_action": "send_update_link",
        "recovery_probability": 0.38,
        "expected_revenue": 1900,
        "recovered": False,
        "recovery_amount": 0,
    },
]


def append_outcome(outcome):
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data_source": "DEMO_SIMULATION",
        "production": False,
        **outcome,
    }

    with open(OUTCOMES_FILE, "a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("RecoverOS - DEMO OUTCOME SIMULATOR")
    print("=" * 70)

    print()
    print("IMPORTANT")
    print("-" * 70)
    print("These outcomes are SIMULATED.")
    print("They are NOT production outcomes.")
    print("They are intentionally labeled DEMO_SIMULATION.")
    print()

    for outcome in DEMO_OUTCOMES:
        append_outcome(outcome)
        print(
            f"{outcome['payment_id']:12} "
            f"Recovered={str(outcome['recovered']):5} "
            f"Amount=₹{outcome['amount']:.2f}"
        )

    print()
    print("=" * 70)
    print("DEMO DATA CREATED")
    print("=" * 70)
    print(f"Records added : {len(DEMO_OUTCOMES)}")
    print(f"Saved to      : {OUTCOMES_FILE}")
    print()
    print("These records are for demonstrating the closed-loop workflow.")
    print("They must NOT be treated as real production evidence.")
    print("=" * 70)


if __name__ == "__main__":
    main()
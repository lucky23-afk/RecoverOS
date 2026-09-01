from pathlib import Path
import json
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

OUTCOMES_FILE = DATA_DIR / "outcomes.jsonl"
FEEDBACK_FILE = DATA_DIR / "production_feedback.csv"


MIN_OUTCOMES = 10


def is_real_production(record):
    """
    A record is production only when it explicitly says production=True.

    Sandbox and demo records are ALWAYS excluded.
    """

    production = record.get("production", False)

    data_source = str(
        record.get("data_source", "")
    ).upper()

    mode = str(
        record.get("mode", "")
    ).upper()

    if production is not True:
        return False

    if data_source in {
        "SANDBOX",
        "DEMO",
        "DEMO_SIMULATION",
        "SIMULATION",
    }:
        return False

    if mode in {
        "SANDBOX",
        "DEMO",
        "SIMULATION",
    }:
        return False

    return True


def load_production_outcomes():
    records = []

    if not OUTCOMES_FILE.exists():
        return pd.DataFrame()

    with open(
        OUTCOMES_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            if is_real_production(record):
                records.append(record)

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records)


def main():

    print("=" * 70)
    print("RecoverOS - PRODUCTION FEEDBACK PIPELINE")
    print("=" * 70)

    print()
    print("SOURCE")
    print("-" * 70)

    print(f"Reading outcomes from : {OUTCOMES_FILE}")
    print("Demo/sandbox records  : EXCLUDED")
    print()

    df = load_production_outcomes()

    production_count = len(df)

    if production_count == 0:

        print("PRODUCTION DATA")
        print("-" * 70)
        print("Production records : 0")
        print("Recovered          : 0")
        print("Not recovered      : 0")
        print()
        print("No genuine production outcomes found.")
        print()
        print("SAFETY")
        print("-" * 70)
        print("Production flag    : REQUIRED")
        print("Sandbox/demo       : EXCLUDED")
        print("Simulation         : EXCLUDED")
        print("Champion modified  : NO")
        print()
        print("=" * 70)
        print("Production feedback pipeline completed.")
        print("=" * 70)

        return

    required_columns = [
        "payment_id",
        "amount",
        "recovery_probability",
        "expected_revenue",
        "recovered",
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:

        print("ERROR")
        print("Missing required fields:")

        for column in missing:
            print(f"  - {column}")

        print()
        print("Champion modified  : NO")

        return

    df["recovered"] = (
        df["recovered"]
        .astype(str)
        .str.lower()
        .map(
            {
                "true": 1,
                "false": 0,
                "1": 1,
                "0": 0,
            }
        )
    )

    df = df.dropna(subset=["recovered"])

    df["recovered"] = df["recovered"].astype(int)

    recovered = int(df["recovered"].sum())
    not_recovered = len(df) - recovered

    print("PRODUCTION DATA")
    print("-" * 70)

    print(f"Production records : {len(df)}")
    print(f"Recovered          : {recovered}")
    print(f"Not recovered      : {not_recovered}")

    print()
    print("DATA QUALITY")
    print("-" * 70)

    print(
        f"Minimum required   : {MIN_OUTCOMES}"
    )

    print(
        f"Current records    : {len(df)}"
    )

    if len(df) >= MIN_OUTCOMES:
        print("Volume gate        : PASS")
    else:
        print("Volume gate        : WAITING")

    if df["recovered"].nunique() >= 2:
        print("Outcome classes    : PASS")
    else:
        print("Outcome classes    : WAITING")

    print()
    print("WRITING PRODUCTION FEEDBACK")
    print("-" * 70)

    FEEDBACK_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        FEEDBACK_FILE,
        index=False,
    )

    print(
        f"Saved to           : {FEEDBACK_FILE}"
    )

    print()
    print("SAFETY")
    print("-" * 70)

    print("Production flag    : REQUIRED")
    print("Sandbox/demo       : EXCLUDED")
    print("Simulation         : EXCLUDED")
    print("Champion modified  : NO")

    print()
    print("IMPORTANT")
    print("-" * 70)

    if len(df) < MIN_OUTCOMES:

        print(
            "Retraining is BLOCKED until at least "
            f"{MIN_OUTCOMES} genuine production outcomes exist."
        )

    elif df["recovered"].nunique() < 2:

        print(
            "Retraining is BLOCKED until both "
            "recovered and not-recovered outcomes exist."
        )

    else:

        print(
            "Production feedback is READY for retraining."
        )

    print()
    print("=" * 70)
    print("Production feedback pipeline completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
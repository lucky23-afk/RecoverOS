
import json
from pathlib import Path


# ======================================================================
# RecoverOS - CLOSED LOOP LEARNING
# ======================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

OUTCOMES_FILE = DATA_DIR / "outcomes.jsonl"
REGISTRY_FILE = DATA_DIR / "model_registry.json"
CHAMPION_MODEL = BASE_DIR / "models" / "recovery_model.pkl"


MIN_PRODUCTION_OUTCOMES = 10


def load_outcomes():
    records = []

    if not OUTCOMES_FILE.exists():
        return records

    with open(OUTCOMES_FILE, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return records


def is_production_outcome(record):
    """
    Only genuine production records are eligible for
    the production learning loop.

    Sandbox and demo records are explicitly excluded.
    """

    if record.get("production") is False:
        return False

    source = str(
        record.get("data_source", "")
    ).upper()

    if source in {
        "SANDBOX",
        "DEMO",
        "DEMO_SIMULATION",
        "TEST",
        "TEST_SIMULATION",
    }:
        return False

    # Legacy production records may not contain
    # the new data_source/production fields.
    #
    # They are accepted unless explicitly marked
    # as sandbox/demo/test.
    return True


def is_sandbox_outcome(record):
    source = str(
        record.get("data_source", "")
    ).upper()

    return (
        record.get("production") is False
        or source in {
            "SANDBOX",
            "DEMO",
            "DEMO_SIMULATION",
            "TEST",
            "TEST_SIMULATION",
        }
    )


def load_registry():
    if not REGISTRY_FILE.exists():
        return {}

    try:
        with open(
            REGISTRY_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    except Exception:
        return {}


def save_learning_log(
    production_count,
    sandbox_count,
    status
):
    log_file = DATA_DIR / "learning_loop.jsonl"

    record = {
        "production_outcomes": production_count,
        "sandbox_outcomes": sandbox_count,
        "minimum_required": MIN_PRODUCTION_OUTCOMES,
        "status": status,
    }

    with open(
        log_file,
        "a",
        encoding="utf-8"
    ) as file:
        file.write(
            json.dumps(record)
            + "\n"
        )


def main():

    print("=" * 70)
    print("RecoverOS - CLOSED LOOP LEARNING")
    print("=" * 70)

    records = load_outcomes()

    production_records = [
        record
        for record in records
        if is_production_outcome(record)
    ]

    sandbox_records = [
        record
        for record in records
        if is_sandbox_outcome(record)
    ]

    recovered = sum(
        1
        for record in production_records
        if bool(record.get("recovered"))
    )

    recovery_rate = (
        recovered / len(production_records)
        if production_records
        else 0.0
    )

    registry = load_registry()

    champion = registry.get(
        "champion",
        {}
    )

    challengers = registry.get(
        "challengers",
        []
    )

    # Some older registry versions may use
    # challenger_models instead.
    if not challengers:
        challengers = registry.get(
            "challenger_models",
            []
        )

    champion_exists = CHAMPION_MODEL.exists()

    print()
    print("DATA CLASSIFICATION")
    print("-" * 70)

    print(
        f"Total outcome records : {len(records)}"
    )

    print(
        f"Production outcomes   : {len(production_records)}"
    )

    print(
        f"Sandbox/demo outcomes : {len(sandbox_records)}"
    )

    print()
    print("PRODUCTION OUTCOMES")
    print("-" * 70)

    print(
        f"Total outcomes       : "
        f"{len(production_records)}"
    )

    print(
        f"Recovered            : {recovered}"
    )

    print(
        f"Observed recovery    : "
        f"{recovery_rate * 100:.2f}%"
    )

    print()
    print("CHAMPION")
    print("-" * 70)

    print(
        f"Model                : "
        f"{champion.get('model_name', 'unknown')}"
    )

    print(
        f"Version              : "
        f"{champion.get('version', 'unknown')}"
    )

    print(
        f"Status               : "
        f"{champion.get('status', 'unknown')}"
    )

    f1 = champion.get("f1_score")
    roc_auc = champion.get("roc_auc")

    if f1 is not None:
        print(
            f"F1 Score             : {f1:.4f}"
        )
    else:
        print(
            "F1 Score             : not available"
        )

    if roc_auc is not None:
        print(
            f"ROC-AUC              : {roc_auc:.4f}"
        )
    else:
        print(
            "ROC-AUC              : not available"
        )

    print()
    print("MODEL SAFETY CHECKS")
    print("-" * 70)

    champion_registered = bool(champion)

    print(
        f"{'PASS' if champion_registered else 'FAIL':6}"
        f" Champion registered"
        f"          : "
        f"{'yes' if champion_registered else 'no'}"
    )

    print(
        f"{'PASS' if champion_exists else 'FAIL':6}"
        f" Champion file exists"
        f"         : "
        f"{CHAMPION_MODEL.name}"
    )

    valid_challengers = len(challengers)

    print(
        f"{'PASS' if valid_challengers > 0 else 'FAIL':6}"
        f" Valid challengers"
        f"            : "
        f"{valid_challengers} available"
    )

    enough_data = (
        len(production_records)
        >= MIN_PRODUCTION_OUTCOMES
    )

    print(
        f"{'PASS' if enough_data else 'FAIL':6}"
        f" Production outcome volume"
        f"    : "
        f"{len(production_records)} / "
        f"{MIN_PRODUCTION_OUTCOMES} minimum"
    )

    # --------------------------------------------------------------
    # LEARNING DECISION
    # --------------------------------------------------------------

    if not enough_data:

        status = "WAITING_FOR_DATA"

        recommendation = (
            "Collect real production outcomes. "
            "Sandbox/demo outcomes are excluded "
            "from production retraining."
        )

    elif valid_challengers > 0:

        status = "READY_FOR_PROMOTION_GATE"

        recommendation = (
            "A challenger exists. "
            "Run the strict promotion gate."
        )

    else:

        status = "READY_FOR_RETRAINING"

        recommendation = (
            "Production data threshold reached. "
            "A new challenger may be trained "
            "through the controlled retraining pipeline."
        )

    print()
    print("LEARNING STATUS")
    print("-" * 70)

    print(
        f"Status               : {status}"
    )

    print(
        f"Recommendation       : {recommendation}"
    )

    # --------------------------------------------------------------
    # MODEL PROTECTION
    # --------------------------------------------------------------

    print()
    print("MODEL PROTECTION")
    print("-" * 70)

    print(
        "Production champion  : PROTECTED"
    )

    print(
        "Automatic promotion  : DISABLED"
    )

    print(
        "Champion overwrite   : DISABLED"
    )

    print(
        "Test data promotion  : DISABLED"
    )

    save_learning_log(
        len(production_records),
        len(sandbox_records),
        status
    )

    print()
    print("=" * 70)
    print("RecoverOS learning loop completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()


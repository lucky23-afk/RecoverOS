from pathlib import Path
import json


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

REGISTRY_FILE = DATA_DIR / "model_registry.json"


def load_registry():
    if not REGISTRY_FILE.exists():
        raise FileNotFoundError(
            f"Registry not found: {REGISTRY_FILE}"
        )

    with open(REGISTRY_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_registry(registry):
    with open(REGISTRY_FILE, "w", encoding="utf-8") as file:
        json.dump(registry, file, indent=2)


def select_best_challenger(challengers):
    """
    Select the strongest valid challenger.

    Production-feedback challengers are preferred.
    If multiple production challengers exist, the newest one is used.
    """

    valid = []

    for challenger in challengers:
        model_name = challenger.get("model_name")
        status = challenger.get("status")

        if not model_name:
            continue

        if status != "challenger":
            continue

        model_path = MODELS_DIR / model_name

        if not model_path.exists():
            continue

        valid.append(challenger)

    if not valid:
        return None

    production = [
        item
        for item in valid
        if item.get("training_source") == "production_feedback.csv"
    ]

    if production:
        valid = production

    valid.sort(
        key=lambda item: item.get("created_at", ""),
        reverse=True,
    )

    return valid[0]


def main():

    print("=" * 70)
    print("RecoverOS - MODEL PROMOTION GATE")
    print("=" * 70)

    # ---------------------------------------------------------------
    # LOAD REGISTRY
    # ---------------------------------------------------------------

    try:
        registry = load_registry()
    except Exception as error:
        print()
        print("ERROR")
        print("-" * 70)
        print(str(error))
        return

    champion = registry.get("champion")

    challengers = registry.get("challengers", [])

    if not champion:
        print()
        print("ERROR")
        print("-" * 70)
        print("No production champion is registered.")
        return

    # ---------------------------------------------------------------
    # CURRENT CHAMPION
    # ---------------------------------------------------------------

    print()
    print("CURRENT CHAMPION")
    print("-" * 70)

    champion_name = champion.get("model_name")
    champion_version = champion.get("version")
    champion_f1 = champion.get("f1_score")
    champion_auc = champion.get("roc_auc")

    print(f"Model      : {champion_name}")
    print(f"Version    : {champion_version}")
    print(f"Status     : {champion.get('status')}")
    print(f"F1 Score   : {champion_f1}")
    print(f"ROC-AUC    : {champion_auc}")

    champion_file = MODELS_DIR / champion_name

    if not champion_file.exists():
        print()
        print("ERROR")
        print("-" * 70)
        print(f"Champion file does not exist: {champion_file}")
        return

    # ---------------------------------------------------------------
    # SELECT CORRECT CHALLENGER
    # ---------------------------------------------------------------

    challenger = select_best_challenger(challengers)

    if challenger is None:
        print()
        print("NO VALID CHALLENGER")
        print("-" * 70)
        print("No valid challenger model is available.")
        return

    challenger_name = challenger.get("model_name")
    challenger_version = challenger.get("version")
    challenger_f1 = challenger.get("f1_score")
    challenger_auc = challenger.get("roc_auc")

    # ---------------------------------------------------------------
    # CHALLENGER
    # ---------------------------------------------------------------

    print()
    print("CHALLENGER")
    print("-" * 70)

    print(f"Model      : {challenger_name}")
    print(f"Version    : {challenger_version}")
    print(f"Status     : {challenger.get('status')}")
    print(f"F1 Score   : {challenger_f1}")
    print(f"ROC-AUC    : {challenger_auc}")

    print()
    print("TRAINING SOURCE")
    print("-" * 70)
    print(
        f"Source     : "
        f"{challenger.get('training_source', 'not specified')}"
    )
    print(
        f"Outcomes   : "
        f"{challenger.get('production_outcomes', 'not specified')}"
    )

    # ---------------------------------------------------------------
    # VALIDATE METRICS
    # ---------------------------------------------------------------

    if challenger_f1 is None or challenger_auc is None:
        print()
        print("PROMOTION DECISION")
        print("-" * 70)
        print("Decision : REJECT")
        print("Reason   : Challenger metrics are incomplete.")
        return

    if champion_f1 is None or champion_auc is None:
        print()
        print("PROMOTION DECISION")
        print("-" * 70)
        print("Decision : REJECT")
        print("Reason   : Champion metrics are incomplete.")
        return

    challenger_file = MODELS_DIR / challenger_name

    if not challenger_file.exists():
        print()
        print("PROMOTION DECISION")
        print("-" * 70)
        print("Decision : REJECT")
        print(f"Reason   : Challenger file does not exist.")
        print(f"Missing  : {challenger_file}")
        return

    # ---------------------------------------------------------------
    # CALCULATE IMPROVEMENT
    # ---------------------------------------------------------------

    f1_improvement = float(challenger_f1) - float(champion_f1)
    auc_improvement = float(challenger_auc) - float(champion_auc)

    print()
    print("PROMOTION ANALYSIS")
    print("-" * 70)

    print(f"F1 improvement     : {f1_improvement:+.4f}")
    print(f"ROC-AUC improvement : {auc_improvement:+.4f}")

    # ---------------------------------------------------------------
    # STRICT PROMOTION RULE
    # ---------------------------------------------------------------

    promotion_allowed = (
        float(challenger_f1) > float(champion_f1)
        and float(challenger_auc) > float(champion_auc)
    )

    print()
    print("PROMOTION DECISION")
    print("-" * 70)

    if promotion_allowed:

        print("Decision : PROMOTION CANDIDATE")
        print()
        print("Both F1 and ROC-AUC improved.")
        print("Automatic champion overwrite : DISABLED")
        print("Human approval                : REQUIRED")

        print()
        print("IMPORTANT")
        print("-" * 70)
        print("The production champion has NOT been changed.")
        print("The challenger remains a challenger.")
        print("No model file has been overwritten.")

    else:

        print("Decision : REJECT")
        print()
        print(
            "Challenger does not improve BOTH "
            "F1 and ROC-AUC."
        )

        print()
        print("PROMOTION REJECTED")
        print("-" * 70)
        print("Production champion remains unchanged.")

    # ---------------------------------------------------------------
    # SAFETY SUMMARY
    # ---------------------------------------------------------------

    print()
    print("MODEL PROTECTION")
    print("-" * 70)
    print("Production champion : PROTECTED")
    print("Automatic promotion : DISABLED")
    print("Champion overwrite  : DISABLED")
    print("Human approval      : REQUIRED")

    print()
    print("=" * 70)
    print("Promotion gate completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
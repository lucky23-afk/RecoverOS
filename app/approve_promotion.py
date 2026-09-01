from pathlib import Path
import json
import shutil
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

REGISTRY_FILE = DATA_DIR / "model_registry.json"
CHAMPION_FILE = MODELS_DIR / "recovery_model.pkl"


def main():
    print("=" * 70)
    print("RecoverOS - HUMAN APPROVED MODEL PROMOTION")
    print("=" * 70)

    with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
        registry = json.load(f)

    champion = registry.get("champion")
    challengers = registry.get("challengers", [])

    if not champion:
        print("ERROR: No champion registered.")
        return

    valid = [
        c for c in challengers
        if c.get("status") == "challenger"
        and c.get("model_name")
        and c.get("f1_score") is not None
        and c.get("roc_auc") is not None
    ]

    if not valid:
        print("ERROR: No valid challenger available.")
        return

    challenger = max(
        valid,
        key=lambda c: (c["f1_score"], c["roc_auc"])
    )

    champion_f1 = float(champion["f1_score"])
    champion_auc = float(champion["roc_auc"])
    challenger_f1 = float(challenger["f1_score"])
    challenger_auc = float(challenger["roc_auc"])

    challenger_file = MODELS_DIR / challenger["model_name"]

    print()
    print("PROMOTION CANDIDATE")
    print("-" * 70)
    print(f"Model       : {challenger['model_name']}")
    print(f"Version     : {challenger['version']}")
    print(f"F1 Score    : {challenger_f1:.4f}")
    print(f"ROC-AUC     : {challenger_auc:.4f}")

    if challenger_f1 <= champion_f1 or challenger_auc <= champion_auc:
        print()
        print("PROMOTION BLOCKED")
        print("Challenger does not beat champion on both metrics.")
        return

    if not challenger_file.exists():
        print()
        print("PROMOTION BLOCKED")
        print(f"Missing challenger file: {challenger_file}")
        return

    print()
    print("SAFETY CHECK")
    print("-" * 70)
    print("F1 improvement    : PASS")
    print("ROC-AUC improvement: PASS")
    print("Challenger file   : PASS")
    print("Champion file     : PASS" if CHAMPION_FILE.exists()
          else "Champion file     : FAIL")

    if not CHAMPION_FILE.exists():
        print("PROMOTION BLOCKED")
        return

    print()
    approval = input(
        "Type APPROVE to promote this challenger: "
    ).strip()

    if approval != "APPROVE":
        print()
        print("PROMOTION CANCELLED")
        return

    timestamp = datetime.now().isoformat()

    backup_file = MODELS_DIR / (
        f"recovery_model_backup_{datetime.now():%Y%m%d_%H%M%S}.pkl"
    )

    shutil.copy2(CHAMPION_FILE, backup_file)
    shutil.copy2(challenger_file, CHAMPION_FILE)

    old_champion = dict(champion)

    new_champion = dict(challenger)
    new_champion["status"] = "production"
    new_champion["promoted_at"] = timestamp
    new_champion["previous_champion"] = old_champion["model_name"]

    history = registry.get("history", [])
    history.append({
        "timestamp": timestamp,
        "previous_champion": old_champion["model_name"],
        "previous_version": old_champion["version"],
        "new_champion": new_champion["model_name"],
        "new_version": new_champion["version"],
        "f1_score": challenger_f1,
        "roc_auc": challenger_auc,
        "backup": backup_file.name,
    })

    promotions = registry.get("promotions", [])
    promotions.append({
        "timestamp": timestamp,
        "model_name": new_champion["model_name"],
        "version": new_champion["version"],
        "approved": True,
        "approved_by": "human",
        "backup": backup_file.name,
    })

    for c in challengers:
        if c.get("model_name") == challenger["model_name"]:
            c["status"] = "production"
        else:
            c["status"] = "challenger"

    registry["champion"] = new_champion
    registry["challengers"] = [
        c for c in challengers
        if c.get("model_name") != challenger["model_name"]
    ]
    registry["history"] = history
    registry["promotions"] = promotions

    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)

    print()
    print("=" * 70)
    print("PROMOTION SUCCESSFUL")
    print("=" * 70)
    print(f"New champion : {new_champion['model_name']}")
    print(f"Version      : {new_champion['version']}")
    print(f"F1 Score     : {challenger_f1:.2%}")
    print(f"ROC-AUC      : {challenger_auc:.2%}")
    print(f"Backup       : {backup_file.name}")
    print()
    print("Human approval recorded.")
    print("Previous champion backed up.")
    print("=" * 70)


if __name__ == "__main__":
    main()
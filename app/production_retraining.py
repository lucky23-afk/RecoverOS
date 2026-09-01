from pathlib import Path
import json
from datetime import datetime

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
from sklearn.ensemble import RandomForestClassifier
import joblib


BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

FEEDBACK_FILE = DATA_DIR / "production_feedback.csv"
REGISTRY_FILE = DATA_DIR / "model_registry.json"

CHALLENGER_FILE = MODELS_DIR / "recovery_model_production_challenger.pkl"

MIN_OUTCOMES = 10


def load_registry():
    if not REGISTRY_FILE.exists():
        return {}

    try:
        with open(REGISTRY_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}


def save_registry(registry):
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(REGISTRY_FILE, "w", encoding="utf-8") as file:
        json.dump(registry, file, indent=2)


def main():

    print("=" * 70)
    print("RecoverOS - PRODUCTION RETRAINING")
    print("=" * 70)

    # ---------------------------------------------------------------
    # STEP 1: LOAD PRODUCTION FEEDBACK
    # ---------------------------------------------------------------

    print()
    print("PRODUCTION FEEDBACK")
    print("-" * 70)

    if not FEEDBACK_FILE.exists():
        print("ERROR")
        print("Production feedback file does not exist.")
        print()
        print("Retraining blocked.")
        print("=" * 70)
        return

    try:
        df = pd.read_csv(FEEDBACK_FILE)
    except Exception as error:
        print("ERROR")
        print(f"Could not read production feedback: {error}")
        print()
        print("Retraining blocked.")
        print("=" * 70)
        return

    required_columns = [
        "payment_id",
        "amount",
        "recovery_probability",
        "expected_revenue",
        "recovered",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        print("ERROR")
        print("Missing required columns:")

        for column in missing_columns:
            print(f"  - {column}")

        print()
        print("Retraining blocked.")
        print("=" * 70)
        return

    # ---------------------------------------------------------------
    # STEP 2: STRICT PRODUCTION FILTER
    # ---------------------------------------------------------------

    if "production" not in df.columns:
        print("ERROR")
        print("Production flag column is missing.")
        print()
        print("Retraining blocked.")
        print("=" * 70)
        return

    # Only explicitly production records are allowed.
    production_df = df[
        df["production"].astype(str).str.lower() == "true"
    ].copy()

    total = len(production_df)

    recovered = int(
        production_df["recovered"].astype(int).sum()
    )

    not_recovered = total - recovered

    print(f"Production records : {total}")
    print(f"Recovered          : {recovered}")
    print(f"Not recovered      : {not_recovered}")

    # ---------------------------------------------------------------
    # STEP 3: PRODUCTION DATA SAFETY GATE
    # ---------------------------------------------------------------

    print()
    print("SAFETY GATE")
    print("-" * 70)

    print(
        f"Minimum outcomes   : {MIN_OUTCOMES}"
    )

    print(
        f"Current outcomes   : {total}"
    )

    if total < MIN_OUTCOMES:
        print()
        print("BLOCKED")
        print(
            "Not enough genuine production outcomes."
        )

        print(
            f"Required           : {MIN_OUTCOMES}"
        )

        print(
            f"Available          : {total}"
        )

        print()
        print("No model was trained.")
        print("No challenger was created.")
        print("Champion was NOT modified.")
        print("Automatic promotion : DISABLED")

        print("=" * 70)
        return

    # ---------------------------------------------------------------
    # STEP 4: BOTH CLASSES REQUIRED
    # ---------------------------------------------------------------

    y = production_df["recovered"].astype(int)

    if y.nunique() < 2:

        print()
        print("BLOCKED")
        print(
            "Production data must contain BOTH:"
        )
        print(
            "  - recovered outcomes"
        )
        print(
            "  - not-recovered outcomes"
        )

        print()
        print("No model was trained.")
        print("Champion was NOT modified.")

        print("=" * 70)
        return

    # ---------------------------------------------------------------
    # STEP 5: TRAINING DATA
    # ---------------------------------------------------------------

    print()
    print("TRAINING DATA")
    print("-" * 70)

    feature_columns = [
        "amount",
        "recovery_probability",
        "expected_revenue",
    ]

    X = production_df[
        feature_columns
    ].copy()

    print(
        f"Features            : {len(feature_columns)}"
    )

    print(
        f"Production records  : {len(production_df)}"
    )

    # ---------------------------------------------------------------
    # STEP 6: TRAIN / TEST SPLIT
    # ---------------------------------------------------------------

    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=42,
            stratify=y,
        )
    except ValueError as error:
        print()
        print("BLOCKED")
        print(
            "Could not create a safe stratified "
            "train/test split."
        )
        print(f"Reason: {error}")
        print()
        print("Champion was NOT modified.")
        print("=" * 70)
        return

    print(
        f"Training set        : {len(X_train)}"
    )

    print(
        f"Test set            : {len(X_test)}"
    )

    # ---------------------------------------------------------------
    # STEP 7: TRAIN CHALLENGER
    # ---------------------------------------------------------------

    print()
    print("TRAINING PRODUCTION CHALLENGER")
    print("-" * 70)

    challenger = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_leaf=2,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )

    challenger.fit(
        X_train,
        y_train,
    )

    predictions = challenger.predict(
        X_test
    )

    probabilities = challenger.predict_proba(
        X_test
    )[:, 1]

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    precision = precision_score(
        y_test,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        y_test,
        predictions,
        zero_division=0,
    )

    f1 = f1_score(
        y_test,
        predictions,
        zero_division=0,
    )

    try:
        roc_auc = roc_auc_score(
            y_test,
            probabilities,
        )
    except ValueError:
        roc_auc = 0.0

    # ---------------------------------------------------------------
    # STEP 8: DISPLAY PERFORMANCE
    # ---------------------------------------------------------------

    print()
    print("CHALLENGER PERFORMANCE")
    print("-" * 70)

    print(
        f"Accuracy            : {accuracy:.2%}"
    )

    print(
        f"Precision           : {precision:.2%}"
    )

    print(
        f"Recall              : {recall:.2%}"
    )

    print(
        f"F1 Score            : {f1:.2%}"
    )

    print(
        f"ROC-AUC             : {roc_auc:.2%}"
    )

    # ---------------------------------------------------------------
    # STEP 9: SAVE CHALLENGER ONLY
    # ---------------------------------------------------------------

    MODELS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        challenger,
        CHALLENGER_FILE,
    )

    print()
    print("CHALLENGER MODEL")
    print("-" * 70)

    print(
        f"Saved to            : {CHALLENGER_FILE}"
    )

    # ---------------------------------------------------------------
    # STEP 10: LOAD REGISTRY
    # ---------------------------------------------------------------

    registry = load_registry()

    if not registry:
        print()
        print("ERROR")
        print("Model registry is empty.")
        print()
        print("Challenger file was created.")
        print("Champion was NOT modified.")
        print("=" * 70)
        return

    champion = registry.get(
        "champion"
    )

    if not isinstance(
        champion,
        dict,
    ):
        print()
        print("ERROR")
        print("No valid champion exists.")
        print()
        print("Champion was NOT modified.")
        print("=" * 70)
        return

    # ---------------------------------------------------------------
    # STEP 11: REGISTER CHALLENGER
    # ---------------------------------------------------------------

    challengers = registry.get(
        "challengers",
        [],
    )

    if not isinstance(
        challengers,
        list,
    ):
        challengers = []

    # Remove an older entry for this exact challenger.
    challengers = [
        item
        for item in challengers
        if not (
            item.get("model_name")
            == CHALLENGER_FILE.name
            and item.get("version")
            == "production-feedback-v2"
        )
    ]

    challenger_record = {
        "model_name": CHALLENGER_FILE.name,
        "version": "production-feedback-v2",
        "status": "challenger",
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "roc_auc": float(roc_auc),
        "created_at": datetime.now().isoformat(),
        "training_source": "production_feedback.csv",
        "production_outcomes": total,
    }

    challengers.append(
        challenger_record
    )

    registry["challengers"] = challengers

    # ---------------------------------------------------------------
    # CRITICAL SAFETY RULE
    # ---------------------------------------------------------------
    #
    # DO NOT modify registry["champion"] here.
    #
    # This script ONLY trains and registers a challenger.
    #
    # Promotion must happen separately and explicitly through
    # model_registry.promote_challenger(..., approval=True)
    #
    # ---------------------------------------------------------------

    save_registry(
        registry
    )

    print()
    print("REGISTRY")
    print("-" * 70)

    print(
        "Challenger registered : YES"
    )

    print(
        "Production champion   : UNCHANGED"
    )

    print(
        "Automatic promotion   : DISABLED"
    )

    print()
    print("PROMOTION")
    print("-" * 70)

    print(
        "Promotion performed   : NO"
    )

    print(
        "Human approval        : REQUIRED"
    )

    print(
        "Champion overwrite    : DISABLED"
    )

    print()
    print("MODEL PROTECTION")
    print("-" * 70)

    print(
        "Production data       : YES"
    )

    print(
        f"Production outcomes   : {total}"
    )

    print(
        "Sandbox data          : EXCLUDED"
    )

    print(
        "Simulation data       : EXCLUDED"
    )

    print(
        "Champion modified     : NO"
    )

    print()
    print("=" * 70)
    print(
        "Production retraining completed."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
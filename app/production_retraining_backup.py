from pathlib import Path
import json
from datetime import datetime

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


# ======================================================================
# RecoverOS - PRODUCTION RETRAINING
# ======================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

FEEDBACK_FILE = DATA_DIR / "production_feedback.csv"
REGISTRY_FILE = DATA_DIR / "model_registry.json"

CHALLENGER_FILE = (
    MODELS_DIR / "recovery_model_production_challenger.pkl"
)

MIN_OUTCOMES = 10


# ======================================================================
# DATA
# ======================================================================

FEATURE_COLUMNS = [
    "amount",
    "failure_reason",
    "payment_method",
    "merchant_type",
    "recommended_action",
    "final_action",
    "recovery_probability",
    "expected_revenue",
]

NUMERIC_FEATURES = [
    "amount",
    "recovery_probability",
    "expected_revenue",
]

CATEGORICAL_FEATURES = [
    "failure_reason",
    "payment_method",
    "merchant_type",
    "recommended_action",
    "final_action",
]


# ======================================================================
# REGISTRY HELPERS
# ======================================================================

def load_registry():
    if not REGISTRY_FILE.exists():
        return {}

    try:
        with open(
            REGISTRY_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except Exception as error:
        print()
        print("ERROR")
        print("-" * 70)
        print(
            f"Could not read model registry: {error}"
        )
        return {}


def save_registry(registry):
    with open(
        REGISTRY_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            registry,
            file,
            indent=2,
        )


# ======================================================================
# MAIN
# ======================================================================

def main():

    print("=" * 70)
    print("RecoverOS - PRODUCTION RETRAINING")
    print("=" * 70)

    # ------------------------------------------------------------------
    # CHECK FEEDBACK FILE
    # ------------------------------------------------------------------

    print()
    print("PRODUCTION FEEDBACK")
    print("-" * 70)

    if not FEEDBACK_FILE.exists():

        print("ERROR")
        print(
            f"Missing file: {FEEDBACK_FILE}"
        )
        return

    try:
        df = pd.read_csv(
            FEEDBACK_FILE
        )
    except Exception as error:

        print("ERROR")
        print(
            f"Could not load feedback: {error}"
        )
        return

    required_columns = (
        FEATURE_COLUMNS
        + ["recovered"]
    )

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        print("ERROR")
        print(
            "Missing required columns:"
        )

        for column in missing_columns:
            print(
                f"  - {column}"
            )

        return

    total = len(df)

    recovered = int(
        df["recovered"].sum()
    )

    not_recovered = (
        total - recovered
    )

    print(
        f"Records             : {total}"
    )

    print(
        f"Recovered           : {recovered}"
    )

    print(
        f"Not recovered       : {not_recovered}"
    )

    # ------------------------------------------------------------------
    # SAFETY GATE
    # ------------------------------------------------------------------

    print()
    print("SAFETY GATE")
    print("-" * 70)

    if total < MIN_OUTCOMES:

        print(
            f"BLOCKED: Need at least "
            f"{MIN_OUTCOMES} production outcomes."
        )

        print(
            f"Current production outcomes : "
            f"{total} / {MIN_OUTCOMES}"
        )

        print()
        print(
            "Champion model was NOT modified."
        )

        print(
            "No production model was overwritten."
        )

        return

    if df["recovered"].nunique() < 2:

        print(
            "BLOCKED: Training data must contain "
            "both recovered and not-recovered outcomes."
        )

        print()
        print(
            "Champion model was NOT modified."
        )

        return

    # ------------------------------------------------------------------
    # CLEAN DATA
    # ------------------------------------------------------------------

    print()
    print("TRAINING DATA")
    print("-" * 70)

    X = df[
        FEATURE_COLUMNS
    ].copy()

    y = df[
        "recovered"
    ].astype(int)

    for column in NUMERIC_FEATURES:

        X[column] = pd.to_numeric(
            X[column],
            errors="coerce",
        )

    for column in CATEGORICAL_FEATURES:

        X[column] = (
            X[column]
            .fillna("")
            .astype(str)
        )

    print(
        f"Features            : "
        f"{len(FEATURE_COLUMNS)}"
    )

    print(
        f"Numeric features    : "
        f"{len(NUMERIC_FEATURES)}"
    )

    print(
        f"Categorical features: "
        f"{len(CATEGORICAL_FEATURES)}"
    )

    print(
        f"Records             : {len(X)}"
    )

    # ------------------------------------------------------------------
    # TRAIN / TEST SPLIT
    # ------------------------------------------------------------------

    print()
    print("EVALUATION SPLIT")
    print("-" * 70)

    try:

        X_train, X_test, y_train, y_test = (
            train_test_split(
                X,
                y,
                test_size=0.25,
                random_state=42,
                stratify=y,
            )
        )

    except ValueError as error:

        print(
            "BLOCKED: Could not create a "
            "stratified evaluation split."
        )

        print(
            f"Reason: {error}"
        )

        print()
        print(
            "Champion model was NOT modified."
        )

        return

    print(
        f"Training set        : {len(X_train)}"
    )

    print(
        f"Evaluation set      : {len(X_test)}"
    )

    # ------------------------------------------------------------------
    # PREPROCESSING
    # ------------------------------------------------------------------

    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                ),
            )
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent"
                ),
            ),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                NUMERIC_FEATURES,
            ),
            (
                "categorical",
                categorical_pipeline,
                CATEGORICAL_FEATURES,
            ),
        ]
    )

    # ------------------------------------------------------------------
    # TRAIN CHALLENGER
    # ------------------------------------------------------------------

    print()
    print("TRAINING PRODUCTION CHALLENGER")
    print("-" * 70)

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=6,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    challenger = Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "classifier",
                model,
            ),
        ]
    )

    challenger.fit(
        X_train,
        y_train,
    )

    predictions = challenger.predict(
        X_test
    )

    probabilities = (
        challenger.predict_proba(
            X_test
        )[:, 1]
    )

    # ------------------------------------------------------------------
    # METRICS
    # ------------------------------------------------------------------

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

    print()
    print("CHALLENGER PERFORMANCE")
    print("-" * 70)

    print(
        f"Accuracy            : "
        f"{accuracy:.2%}"
    )

    print(
        f"Precision           : "
        f"{precision:.2%}"
    )

    print(
        f"Recall              : "
        f"{recall:.2%}"
    )

    print(
        f"F1 Score            : "
        f"{f1:.2%}"
    )

    print(
        f"ROC-AUC             : "
        f"{roc_auc:.2%}"
    )

    # ------------------------------------------------------------------
    # SAVE CHALLENGER
    # ------------------------------------------------------------------

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
        f"Saved to            : "
        f"{CHALLENGER_FILE}"
    )

    # ------------------------------------------------------------------
    # LOAD CHAMPION
    # ------------------------------------------------------------------

    registry = load_registry()

    champion = registry.get(
        "champion"
    )

    if not champion:

        print()
        print("ERROR")
        print(
            "No production champion registered."
        )

        print()
        print(
            "Champion model was NOT modified."
        )

        return

    champion_f1 = champion.get(
        "f1_score"
    )

    champion_auc = champion.get(
        "roc_auc"
    )

    print()
    print("CURRENT CHAMPION")
    print("-" * 70)

    print(
        f"Model               : "
        f"{champion.get('model_name')}"
    )

    print(
        f"Version             : "
        f"{champion.get('version')}"
    )

    print(
        f"F1 Score            : "
        f"{champion_f1}"
    )

    print(
        f"ROC-AUC             : "
        f"{champion_auc}"
    )

    # ------------------------------------------------------------------
    # PROMOTION ANALYSIS
    # ------------------------------------------------------------------

    print()
    print("PROMOTION SAFETY")
    print("-" * 70)

    promotion_candidate = (
        champion_f1 is not None
        and champion_auc is not None
        and f1 > float(champion_f1)
        and roc_auc > float(champion_auc)
    )

    if promotion_candidate:

        print(
            "Decision            : "
            "PROMOTION CANDIDATE"
        )

        print()
        print(
            "Both F1 and ROC-AUC improved."
        )

        print(
            "Automatic champion overwrite "
            "is DISABLED."
        )

        print(
            "Human approval is required."
        )

    else:

        print(
            "Decision            : REJECT"
        )

        print()
        print(
            "Challenger did not beat "
            "the champion on BOTH metrics."
        )

        print(
            "Champion remains protected."
        )

    # ------------------------------------------------------------------
    # REGISTER CHALLENGER
    # ------------------------------------------------------------------

    challengers = registry.get(
        "challengers",
        [],
    )

    challengers = [
        item
        for item in challengers
        if item.get(
            "model_name"
        ) != CHALLENGER_FILE.name
    ]

    challengers.append(
        {
            "model_name":
                CHALLENGER_FILE.name,

            "version":
                "production-feedback-v2",

            "status":
                "challenger",

            "accuracy":
                float(accuracy),

            "precision":
                float(precision),

            "recall":
                float(recall),

            "f1_score":
                float(f1),

            "roc_auc":
                float(roc_auc),

            "created_at":
                datetime.now().isoformat(),

            "training_source":
                "production_feedback.csv",

            "production_outcomes":
                total,

            "features":
                FEATURE_COLUMNS,

            "evaluation_method":
                "stratified_holdout",

            "automatic_promotion":
                False,
        }
    )

    registry["challengers"] = (
        challengers
    )

    save_registry(
        registry
    )

    # ------------------------------------------------------------------
    # FINAL SAFETY SUMMARY
    # ------------------------------------------------------------------

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
    print("MODEL PROTECTION")
    print("-" * 70)

    print(
        "Champion overwrite    : DISABLED"
    )

    print(
        "Champion backup       : "
        "NOT NEEDED"
    )

    print(
        "Production feedback   : YES"
    )

    print()
    print("=" * 70)
    print(
        "Production retraining completed."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
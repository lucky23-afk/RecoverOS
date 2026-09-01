from pathlib import Path
import sys
import shutil
import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)

from model_registry import (
    register_challenger,
    get_champion,
)


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"

TRAINING_FILE = DATA_DIR / "advanced_training_data.csv"
CHALLENGER_FILE = MODEL_DIR / "recovery_model_challenger.pkl"

FEATURES = [
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

TARGET = "recovered"

CATEGORICAL_FEATURES = [
    "failure_reason",
    "payment_method",
    "merchant_type",
]

NUMERIC_FEATURES = [
    "amount",
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


def load_training_data():
    if not TRAINING_FILE.exists():
        raise FileNotFoundError(
            f"Training data not found: {TRAINING_FILE}"
        )

    df = pd.read_csv(TRAINING_FILE)

    required = FEATURES + [TARGET]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Missing training columns: "
            + ", ".join(missing)
        )

    return df


def build_model():
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
                CATEGORICAL_FEATURES,
            ),
            (
                "numeric",
                "passthrough",
                NUMERIC_FEATURES,
            ),
        ]
    )

    classifier = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        class_weight="balanced",
        min_samples_leaf=2,
        n_jobs=-1,
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )


def evaluate(model, X_test, y_test):
    predictions = model.predict(X_test)

    probabilities = model.predict_proba(X_test)[:, 1]

    return {
        "accuracy": accuracy_score(
            y_test,
            predictions,
        ),
        "precision": precision_score(
            y_test,
            predictions,
            zero_division=0,
        ),
        "recall": recall_score(
            y_test,
            predictions,
            zero_division=0,
        ),
        "f1_score": f1_score(
            y_test,
            predictions,
            zero_division=0,
        ),
        "roc_auc": roc_auc_score(
            y_test,
            probabilities,
        ),
    }


def print_metrics(metrics):
    print(
        f"Accuracy    : {metrics['accuracy']:.2%}"
    )
    print(
        f"Precision   : {metrics['precision']:.2%}"
    )
    print(
        f"Recall      : {metrics['recall']:.2%}"
    )
    print(
        f"F1 Score    : {metrics['f1_score']:.2%}"
    )
    print(
        f"ROC-AUC     : {metrics['roc_auc']:.2%}"
    )


def train_challenger():
    print("=" * 70)
    print("RecoverOS X - CONTROLLED RETRAINING")
    print("=" * 70)

    df = load_training_data()

    print()
    print("TRAINING DATA")
    print("-" * 70)
    print(f"Records      : {len(df)}")
    print(f"Features     : {len(FEATURES)}")

    X = df[FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    print(f"Training set : {len(X_train)}")
    print(f"Test set     : {len(X_test)}")

    print()
    print("TRAINING CHALLENGER")
    print("-" * 70)

    model = build_model()

    model.fit(
        X_train,
        y_train,
    )

    metrics = evaluate(
        model,
        X_test,
        y_test,
    )

    print()
    print("CHALLENGER PERFORMANCE")
    print("-" * 70)

    print_metrics(metrics)

    joblib.dump(
        model,
        CHALLENGER_FILE,
    )

    print()
    print("CHALLENGER MODEL")
    print("-" * 70)
    print(f"Saved to     : {CHALLENGER_FILE}")

    champion = get_champion()

    print()
    print("CURRENT CHAMPION")
    print("-" * 70)
    print(
        f"Model        : "
        f"{champion.get('model_name')}"
    )
    print(
        f"Version      : "
        f"{champion.get('version')}"
    )

    challenger_version = "v2"

    register_challenger(
        model_name=CHALLENGER_FILE.name,
        version=challenger_version,
        accuracy=metrics["accuracy"],
        f1_score=metrics["f1_score"],
        roc_auc=metrics["roc_auc"],
    )

    print()
    print("REGISTRY")
    print("-" * 70)
    print(
        f"Registered   : Challenger {challenger_version}"
    )
    print("Status       : CHALLENGER")
    print()
    print("Production model was NOT changed.")

    print()
    print("=" * 70)
    print("Controlled retraining completed.")
    print("=" * 70)


if __name__ == "__main__":
    try:
        train_challenger()
    except Exception as error:
        print()
        print("=" * 70)
        print("CONTROLLED RETRAINING FAILED")
        print("=" * 70)
        print(
            f"{type(error).__name__}: {error}"
        )
        sys.exit(1)
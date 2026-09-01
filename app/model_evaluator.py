from pathlib import Path
import sys
import joblib
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"

TRAINING_FILE = DATA_DIR / "advanced_training_data.csv"
MODEL_FILE = MODEL_DIR / "recovery_model.pkl"


TARGET = "recovered"

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


def load_data():
    if not TRAINING_FILE.exists():
        raise FileNotFoundError(
            f"Training data not found: {TRAINING_FILE}"
        )

    df = pd.read_csv(TRAINING_FILE)

    missing = [
        column
        for column in FEATURES + [TARGET]
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Training data is missing columns: "
            + ", ".join(missing)
        )

    return df


def evaluate_model(model, df):
    X = df[FEATURES]
    y = df[TARGET]

    predictions = model.predict(X)

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(X)[:, 1]
    else:
        probabilities = None

    accuracy = accuracy_score(y, predictions)

    precision = precision_score(
        y,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        y,
        predictions,
        zero_division=0,
    )

    f1 = f1_score(
        y,
        predictions,
        zero_division=0,
    )

    if probabilities is not None:
        roc_auc = roc_auc_score(
            y,
            probabilities,
        )
    else:
        roc_auc = None

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "roc_auc": roc_auc,
    }


def print_metrics(metrics):
    print()
    print("MODEL PERFORMANCE")
    print("-" * 70)

    print(f"Accuracy    : {metrics['accuracy']:.2%}")
    print(f"Precision   : {metrics['precision']:.2%}")
    print(f"Recall      : {metrics['recall']:.2%}")
    print(f"F1 Score    : {metrics['f1_score']:.2%}")

    if metrics["roc_auc"] is not None:
        print(f"ROC-AUC     : {metrics['roc_auc']:.2%}")
    else:
        print("ROC-AUC     : unavailable")


def evaluate_current_model():
    print("=" * 70)
    print("RecoverOS X - MODEL EVALUATOR")
    print("=" * 70)

    if not MODEL_FILE.exists():
        print()
        print("ERROR")
        print("-" * 70)
        print(f"Production model not found:")
        print(MODEL_FILE)
        return False

    try:
        df = load_data()

        print()
        print("EVALUATION DATA")
        print("-" * 70)
        print(f"Records      : {len(df)}")
        print(f"Features     : {len(FEATURES)}")
        print(f"Target       : {TARGET}")

        model = joblib.load(MODEL_FILE)

        metrics = evaluate_model(
            model,
            df,
        )

        print()
        print("CURRENT CHAMPION")
        print("-" * 70)
        print("Model        : recovery_model.pkl")
        print("Version      : v1")

        print_metrics(metrics)

        print()
        print("=" * 70)
        print("Model evaluation completed.")
        print("=" * 70)

        return True

    except Exception as error:
        print()
        print("ERROR DURING MODEL EVALUATION")
        print("-" * 70)
        print(type(error).__name__, ":", error)
        return False


if __name__ == "__main__":
    success = evaluate_current_model()

    if not success:
        sys.exit(1)
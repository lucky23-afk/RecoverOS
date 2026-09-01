"""
RecoverOS X - ML Recovery Prediction Engine

Uses a preprocessing pipeline + Random Forest classifier
to estimate the probability that a failed payment will recover.

Training data is synthetic and intended for prototype experimentation.
"""

from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


BASE_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = BASE_DIR / "data" / "advanced_training_data.csv"
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "recovery_model.pkl"


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

CATEGORICAL_FEATURES = [
    "failure_reason",
    "payment_method",
    "merchant_type",
]

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def load_training_data():
    """Load and validate the advanced training dataset."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Training data not found:\n{DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    required_columns = FEATURES + ["recovered"]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    return df


def build_pipeline():
    """Create the ML preprocessing + prediction pipeline."""

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                "passthrough",
                NUMERIC_FEATURES,
            ),
            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
                CATEGORICAL_FEATURES,
            ),
        ]
    )

    classifier = RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=3,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )

    return pipeline


def train_model():
    """Train, evaluate and save the recovery model."""

    df = load_training_data()

    X = df[FEATURES]
    y = df["recovered"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    model = build_pipeline()

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]

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

    roc_auc = roc_auc_score(
        y_test,
        probabilities,
    )

    print()
    print("=" * 60)
    print("RecoverOS X - Recovery Prediction Engine")
    print("=" * 60)

    print(f"Training records : {len(X_train)}")
    print(f"Testing records  : {len(X_test)}")

    print()
    print("Model Performance")
    print("-" * 60)
    print(f"Accuracy         : {accuracy:.2%}")
    print(f"Precision        : {precision:.2%}")
    print(f"Recall           : {recall:.2%}")
    print(f"F1 Score         : {f1:.2%}")
    print(f"ROC-AUC          : {roc_auc:.2%}")

    print()
    print("Classification Report")
    print("-" * 60)

    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0,
        )
    )

    MODEL_DIR.mkdir(
        exist_ok=True
    )

    joblib.dump(
        model,
        MODEL_PATH,
    )

    print("-" * 60)
    print("Model saved successfully:")
    print(MODEL_PATH)
    print("=" * 60)

    return model


def load_model():
    """Load the trained RecoverOS X model."""

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Recovery model not found.\n"
            "Run: python app\\ml_model.py"
        )

    return joblib.load(
        MODEL_PATH
    )


def predict_recovery_probability(payment):
    """
    Predict recovery probability for one payment.

    `payment` should be a dictionary containing all FEATURES.
    """

    model = load_model()

    row = pd.DataFrame(
        [payment]
    )

    probability = model.predict_proba(
        row[FEATURES]
    )[0][1]

    return float(probability)


if __name__ == "__main__":
    train_model()
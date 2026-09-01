from pathlib import Path
import json
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

REGISTRY_FILE = DATA_DIR / "model_registry.json"
MODEL_REGISTRY_FILE = MODELS_DIR / "model_registry.json"

CHAMPION_MODEL = "recovery_model.pkl"
CHAMPION_VERSION = "v1"

# Safety rule:
# A production champion must never be created/promoted from fewer
# than this many genuine production outcomes.
MIN_PRODUCTION_OUTCOMES = 10


def default_registry():
    return {
        "champion": {
            "model_name": CHAMPION_MODEL,
            "version": CHAMPION_VERSION,
            "status": "production",
            "accuracy": 0.8174,
            "precision": 0.8317,
            "recall": 0.7907,
            "f1_score": 0.8107,
            "roc_auc": 0.9087,
            "created_at": datetime.now().isoformat(),
            "training_source": "initial_model",
            "production_outcomes": 0,
        },
        "challengers": [],
        "history": [],
        "promotions": [],
    }


def load_json(path):
    if not path.exists():
        return None

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return None


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def normalize_champion(registry):
    """
    Make sure the champion has safe/default metadata.

    IMPORTANT:
    This function NEVER promotes a challenger.
    It only validates/repairs registry structure.
    """

    champion = registry.get("champion")

    if not isinstance(champion, dict):
        champion = {}

    champion.setdefault("model_name", CHAMPION_MODEL)
    champion.setdefault("version", CHAMPION_VERSION)
    champion.setdefault("status", "production")

    # Known-good baseline metrics.
    if champion.get("accuracy") is None:
        champion["accuracy"] = 0.8174

    if champion.get("precision") is None:
        champion["precision"] = 0.8317

    if champion.get("recall") is None:
        champion["recall"] = 0.7907

    if champion.get("f1_score") is None:
        champion["f1_score"] = 0.8107

    if champion.get("roc_auc") is None:
        champion["roc_auc"] = 0.9087

    # This field is important for safety.
    # Missing means we do NOT know that genuine production data
    # was used.
    if "production_outcomes" not in champion:
        champion["production_outcomes"] = 0

    if "training_source" not in champion:
        champion["training_source"] = "unknown"

    registry["champion"] = champion


def recover_challengers():
    """
    Recover challenger metadata from the models registry.

    This only restores challenger information.

    It NEVER promotes a challenger.
    """

    registry = load_json(MODELS_DIR / "model_registry.json")

    if not registry:
        return []

    candidates = []

    old_challengers = registry.get("challengers", [])

    if isinstance(old_challengers, list):
        candidates.extend(old_challengers)

    old_challenger_models = registry.get("challenger_models", [])

    if isinstance(old_challenger_models, list):
        candidates.extend(old_challenger_models)

    recovered = []

    for challenger in candidates:
        if not isinstance(challenger, dict):
            continue

        model_name = challenger.get("model_name")

        if not model_name:
            continue

        model_path = MODELS_DIR / model_name

        if not model_path.exists():
            continue

        recovered.append(
            {
                "model_name": model_name,
                "version": challenger.get(
                    "version",
                    "unknown",
                ),
                "status": "challenger",
                "accuracy": challenger.get("accuracy"),
                "precision": challenger.get("precision"),
                "recall": challenger.get("recall"),
                "f1_score": challenger.get("f1_score"),
                "roc_auc": challenger.get("roc_auc"),
                "created_at": challenger.get(
                    "created_at",
                    datetime.now().isoformat(),
                ),
                "training_source": challenger.get(
                    "training_source",
                    "unknown",
                ),
                "production_outcomes": challenger.get(
                    "production_outcomes",
                    0,
                ),
            }
        )

    return recovered


def deduplicate_challengers(challengers):
    unique = {}

    for challenger in challengers:
        key = (
            challenger.get("model_name"),
            challenger.get("version"),
        )

        unique[key] = challenger

    return list(unique.values())


def load_registry():
    """
    Load registry safely.

    IMPORTANT:
    Loading the registry can NEVER promote a model.
    """

    registry = load_json(REGISTRY_FILE)

    if not registry:
        registry = default_registry()

    normalize_champion(registry)

    existing_challengers = registry.get(
        "challengers",
        [],
    )

    if not isinstance(existing_challengers, list):
        existing_challengers = []

    recovered_challengers = recover_challengers()

    registry["challengers"] = deduplicate_challengers(
        existing_challengers + recovered_challengers
    )

    if not isinstance(
        registry.get("history"),
        list,
    ):
        registry["history"] = []

    if not isinstance(
        registry.get("promotions"),
        list,
    ):
        registry["promotions"] = []

    return registry


def save_registry(registry):
    save_json(
        REGISTRY_FILE,
        registry,
    )


def get_champion():
    registry = load_registry()

    return registry["champion"]


def get_challengers():
    registry = load_registry()

    return registry["challengers"]


def register_challenger(
    model_name,
    version,
    accuracy=None,
    precision=None,
    recall=None,
    f1_score=None,
    roc_auc=None,
    production_outcomes=0,
    training_source="unknown",
):
    """
    Register a challenger.

    A challenger is NOT a production model.

    Registration never changes the champion.
    """

    registry = load_registry()

    model_path = MODELS_DIR / model_name

    if not model_path.exists():
        raise FileNotFoundError(
            f"Challenger model does not exist: {model_path}"
        )

    challenger = {
        "model_name": model_name,
        "version": version,
        "status": "challenger",
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "roc_auc": roc_auc,
        "created_at": datetime.now().isoformat(),
        "training_source": training_source,
        "production_outcomes": int(
            production_outcomes or 0
        ),
    }

    challengers = registry.get(
        "challengers",
        [],
    )

    challengers.append(challenger)

    registry["challengers"] = deduplicate_challengers(
        challengers
    )

    # Explicitly preserve champion.
    # Registering a challenger must NEVER modify it.
    registry["champion"]["status"] = "production"

    save_registry(registry)

    return challenger


def promote_challenger(
    model_name,
    version,
    approval=False,
):
    """
    Safely promote a challenger.

    Promotion requires:
      1. Explicit approval.
      2. Challenger exists.
      3. Challenger model file exists.
      4. Challenger has >= 10 genuine production outcomes.
      5. Challenger beats current champion on BOTH F1 and ROC-AUC.

    This function is intentionally strict.
    """

    registry = load_registry()

    if not approval:
        raise PermissionError(
            "Promotion requires explicit human approval."
        )

    challengers = registry.get(
        "challengers",
        [],
    )

    candidate = None

    for challenger in challengers:
        if (
            challenger.get("model_name") == model_name
            and challenger.get("version") == version
        ):
            candidate = challenger
            break

    if candidate is None:
        raise ValueError(
            "Challenger not found in registry."
        )

    model_path = MODELS_DIR / model_name

    if not model_path.exists():
        raise FileNotFoundError(
            f"Challenger model does not exist: {model_path}"
        )

    production_outcomes = int(
        candidate.get(
            "production_outcomes",
            0,
        )
        or 0
    )

    if production_outcomes < MIN_PRODUCTION_OUTCOMES:
        raise PermissionError(
            "Promotion blocked: challenger has only "
            f"{production_outcomes} production outcomes. "
            f"Minimum required is "
            f"{MIN_PRODUCTION_OUTCOMES}."
        )

    candidate_f1 = candidate.get("f1_score")
    candidate_auc = candidate.get("roc_auc")

    if candidate_f1 is None or candidate_auc is None:
        raise PermissionError(
            "Promotion blocked: challenger metrics "
            "are incomplete."
        )

    champion = registry["champion"]

    champion_f1 = float(
        champion.get("f1_score", 0)
    )

    champion_auc = float(
        champion.get("roc_auc", 0)
    )

    if float(candidate_f1) <= champion_f1:
        raise PermissionError(
            "Promotion blocked: challenger F1 does "
            "not beat champion."
        )

    if float(candidate_auc) <= champion_auc:
        raise PermissionError(
            "Promotion blocked: challenger ROC-AUC "
            "does not beat champion."
        )

    previous_champion = dict(champion)

    registry["champion"] = {
        **candidate,
        "status": "production",
        "promoted_at": datetime.now().isoformat(),
        "previous_champion": previous_champion.get(
            "model_name"
        ),
    }

    registry["champion"].pop(
        "created_at",
        None,
    )

    # The promoted challenger is no longer an active challenger.
    registry["challengers"] = [
        item
        for item in challengers
        if not (
            item.get("model_name") == model_name
            and item.get("version") == version
        )
    ]

    registry["history"].append(
        {
            "timestamp": datetime.now().isoformat(),
            "previous_champion": previous_champion.get(
                "model_name"
            ),
            "previous_version": previous_champion.get(
                "version"
            ),
            "new_champion": model_name,
            "new_version": version,
            "f1_score": float(candidate_f1),
            "roc_auc": float(candidate_auc),
            "production_outcomes": production_outcomes,
        }
    )

    registry["promotions"].append(
        {
            "timestamp": datetime.now().isoformat(),
            "model_name": model_name,
            "version": version,
            "approved": True,
            "production_outcomes": production_outcomes,
        }
    )

    save_registry(registry)

    return registry["champion"]


def print_registry():
    registry = load_registry()

    save_registry(registry)

    champion = registry["champion"]

    challengers = registry["challengers"]

    print("=" * 70)
    print("RecoverOS X - MODEL REGISTRY")
    print("=" * 70)

    print()
    print("CHAMPION MODEL")
    print("-" * 70)

    print(
        f"Model name : "
        f"{champion.get('model_name')}"
    )

    print(
        f"Version    : "
        f"{champion.get('version')}"
    )

    print(
        f"Status     : "
        f"{champion.get('status')}"
    )

    print(
        f"Accuracy   : "
        f"{format_metric(champion.get('accuracy'))}"
    )

    print(
        f"Precision  : "
        f"{format_metric(champion.get('precision'))}"
    )

    print(
        f"Recall     : "
        f"{format_metric(champion.get('recall'))}"
    )

    print(
        f"F1 Score   : "
        f"{format_metric(champion.get('f1_score'))}"
    )

    print(
        f"ROC-AUC    : "
        f"{format_metric(champion.get('roc_auc'))}"
    )

    print(
        f"Production outcomes : "
        f"{champion.get('production_outcomes', 0)}"
    )

    print(
        f"Training source     : "
        f"{champion.get('training_source', 'unknown')}"
    )

    print()

    print("ACTIVE CHALLENGERS")
    print("-" * 70)

    if challengers:
        for challenger in challengers:
            print(
                f"Model name : "
                f"{challenger.get('model_name')}"
            )

            print(
                f"Version    : "
                f"{challenger.get('version')}"
            )

            print(
                f"Status     : "
                f"{challenger.get('status')}"
            )

            print(
                f"Accuracy   : "
                f"{format_metric(challenger.get('accuracy'))}"
            )

            print(
                f"Precision  : "
                f"{format_metric(challenger.get('precision'))}"
            )

            print(
                f"Recall     : "
                f"{format_metric(challenger.get('recall'))}"
            )

            print(
                f"F1 Score   : "
                f"{format_metric(challenger.get('f1_score'))}"
            )

            print(
                f"ROC-AUC    : "
                f"{format_metric(challenger.get('roc_auc'))}"
            )

            print(
                f"Production outcomes : "
                f"{challenger.get('production_outcomes', 0)}"
            )

            print("-" * 70)

    else:
        print("No challenger models registered.")

    print()

    print("MODEL HISTORY")
    print("-" * 70)

    history = registry.get(
        "history",
        [],
    )

    if history:
        for item in history:
            print(item)
    else:
        print("No model history.")

    print()

    print("PROMOTION HISTORY")
    print("-" * 70)

    promotions = registry.get(
        "promotions",
        [],
    )

    if promotions:
        for item in promotions:
            print(item)
    else:
        print("No promotions recorded.")

    print()
    print("=" * 70)


def format_metric(value):
    if value is None:
        return "not evaluated"

    try:
        return f"{float(value):.2%}"
    except (
        TypeError,
        ValueError,
    ):
        return str(value)


if __name__ == "__main__":

    print("=" * 70)
    print("RecoverOS X - Model Registry Test")
    print("=" * 70)

    registry = load_registry()

    save_registry(registry)

    print()
    print("Registry loaded successfully.")

    print()

    print_registry()
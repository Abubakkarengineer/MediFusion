import json
from functools import lru_cache

from app.core.config import DATA_DIR
from app.ml.features import FEATURE_NAMES, vector_from_dict
from app.ml.train_risk_model import METRICS_PATH, MODEL_PATH, train_and_select

ML_DIR = DATA_DIR / "ml"


@lru_cache(maxsize=1)
def get_model_bundle():
    import joblib

    if not MODEL_PATH.exists():
        train_and_select()
    return joblib.load(MODEL_PATH)


def get_metrics() -> dict:
    if not METRICS_PATH.exists():
        train_and_select()
    return json.loads(METRICS_PATH.read_text())


def predict_risk(feature_values: dict) -> dict:
    bundle = get_model_bundle()
    scaler = bundle["scaler"]
    model = bundle["model"]

    x = [vector_from_dict(feature_values)]
    x_scaled = scaler.transform(x)
    proba = float(model.predict_proba(x_scaled)[0][1])
    confidence = float(max(proba, 1 - proba))

    return {
        "probability": round(proba, 4),
        "confidence": round(confidence, 4),
        "model_used": type(model).__name__,
        "features": {name: feature_values[name] for name in FEATURE_NAMES},
    }

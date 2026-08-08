from functools import lru_cache

import numpy as np

from app.ml.features import FEATURE_NAMES, vector_from_dict
from app.services.risk_service import get_model_bundle

FEATURE_LABELS = {
    "age": "age",
    "heart_rate": "heart rate",
    "systolic_bp": "systolic blood pressure",
    "diastolic_bp": "diastolic blood pressure",
    "spo2": "SpO2",
    "respiratory_rate": "respiratory rate",
    "temperature": "temperature",
}


@lru_cache(maxsize=1)
def get_explainer():
    import shap

    bundle = get_model_bundle()
    model = bundle["model"]
    # Baseline of all-zeros in scaled feature space == the training mean,
    # a standard neutral reference point for a linear-model explainer.
    background = np.zeros((1, len(FEATURE_NAMES)))
    explainer = shap.LinearExplainer(model, background)
    return explainer


def explain_prediction(feature_values: dict) -> dict:
    bundle = get_model_bundle()
    scaler = bundle["scaler"]

    x = np.array([vector_from_dict(feature_values)])
    x_scaled = scaler.transform(x)

    explainer = get_explainer()
    shap_values = explainer(x_scaled)
    contributions = shap_values.values[0]  # one row, per-feature log-odds contribution

    feature_importance = [
        {
            "feature": name,
            "label": FEATURE_LABELS[name],
            "value": feature_values[name],
            "contribution": round(float(contributions[i]), 4),
        }
        for i, name in enumerate(FEATURE_NAMES)
    ]
    feature_importance.sort(key=lambda f: abs(f["contribution"]), reverse=True)

    top_positive = [f for f in feature_importance if f["contribution"] > 0][:3]
    top_negative = [f for f in feature_importance if f["contribution"] < 0][:2]

    parts = []
    if top_positive:
        raised = ", ".join(f"{f['label']} ({f['value']})" for f in top_positive)
        parts.append(f"Increased risk was driven most by {raised}")
    if top_negative:
        lowered = ", ".join(f"{f['label']} ({f['value']})" for f in top_negative)
        parts.append(f"partially offset by {lowered}")

    explanation_text = (
        "; ".join(parts) + "."
        if parts
        else "No strong individual feature drove this prediction."
    )
    explanation_text += (
        " This describes what the model weighted, not a proven medical cause -- "
        "clinical correlation is required."
    )

    return {"feature_importance": feature_importance, "explanation_text": explanation_text}

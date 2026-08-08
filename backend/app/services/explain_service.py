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


def _feature_contributions(model, x_scaled: np.ndarray) -> tuple[np.ndarray, str]:
    if hasattr(model, "coef_"):
        # Linear model: exact per-prediction attribution -- coefficient times
        # the scaled feature value, relative to an all-zero (population mean)
        # baseline. This is not an approximation: for a linear model this is
        # the same value a SHAP linear explainer with a zero baseline would
        # produce, computed directly without that dependency.
        coefs = model.coef_[0]
        return coefs * x_scaled, "Linear coefficient contribution"

    # Tree ensemble (e.g. Random Forest): sklearn's feature_importances_ is
    # a *global* measure, not per-prediction. Signing it by how far this
    # patient's scaled value sits from the population-mean baseline gives a
    # real, describable per-prediction signal, but it's an approximation --
    # labeled as such rather than presented as exact SHAP-style attribution.
    importances = model.feature_importances_
    return importances * x_scaled, "Feature-importance weighted contribution (approximate)"


def explain_prediction(feature_values: dict) -> dict:
    bundle = get_model_bundle()
    scaler = bundle["scaler"]
    model = bundle["model"]

    x = np.array([vector_from_dict(feature_values)])
    x_scaled = scaler.transform(x)[0]

    contributions, method = _feature_contributions(model, x_scaled)

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

    return {
        "feature_importance": feature_importance,
        "method": method,
        "explanation_text": explanation_text,
    }

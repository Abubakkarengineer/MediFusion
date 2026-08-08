"""Trains a demo deterioration-risk classifier on SYNTHETIC vitals data.

Ground-truth labels are generated with a NEWS2-inspired scoring rule
(a published, standard early-warning-score banding for vital signs),
then a Bernoulli draw around that score so the label isn't a perfect
deterministic function of the features -- this keeps the learning task
realistic (not trivially separable) while remaining fully synthetic.

No data leakage: the scaler and both models are fit ONLY on the train
split; all reported metrics come from the held-out test split.
"""

import json
import random
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from app.ml.features import FEATURE_NAMES

ARTIFACT_DIR = Path(__file__).resolve().parents[3] / "data" / "ml"
MODEL_PATH = ARTIFACT_DIR / "risk_model.joblib"
METRICS_PATH = ARTIFACT_DIR / "risk_model_metrics.json"

random.seed(42)
np.random.seed(42)


def _news2_like_score(age, hr, sbp, dbp, spo2, rr, temp) -> int:
    score = 0
    if rr <= 8 or rr >= 25:
        score += 3
    elif 21 <= rr <= 24:
        score += 2
    elif 9 <= rr <= 11:
        score += 1

    if spo2 <= 91:
        score += 3
    elif 92 <= spo2 <= 93:
        score += 2
    elif 94 <= spo2 <= 95:
        score += 1

    if sbp <= 90 or sbp >= 220:
        score += 3
    elif 91 <= sbp <= 100:
        score += 2
    elif 101 <= sbp <= 110:
        score += 1

    if hr <= 40 or hr >= 131:
        score += 3
    elif 111 <= hr <= 130:
        score += 2
    elif (41 <= hr <= 50) or (91 <= hr <= 110):
        score += 1

    if temp <= 35.0:
        score += 3
    elif 38.1 <= temp <= 39.0 or temp >= 39.1:
        score += 1

    if age >= 70:
        score += 1

    return score


def _sigmoid(x: float) -> float:
    return 1 / (1 + np.exp(-x))


def generate_synthetic_dataset(n: int = 4000):
    rows = []
    labels = []
    for _ in range(n):
        state = random.choices(["healthy", "mild", "severe"], weights=[0.55, 0.30, 0.15])[0]

        age = np.random.randint(18, 90)
        if state == "healthy":
            hr = np.random.normal(78, 8)
            sbp = np.random.normal(118, 8)
            dbp = np.random.normal(76, 6)
            spo2 = np.random.normal(97.5, 1.2)
            rr = np.random.normal(16, 1.5)
            temp = np.random.normal(36.8, 0.3)
        elif state == "mild":
            hr = np.random.normal(102, 12)
            sbp = np.random.normal(105, 12)
            dbp = np.random.normal(68, 8)
            spo2 = np.random.normal(93.5, 1.5)
            rr = np.random.normal(21, 2.5)
            temp = np.random.normal(37.9, 0.5)
        else:  # severe
            hr = np.random.normal(128, 15)
            sbp = np.random.normal(85, 14)
            dbp = np.random.normal(55, 10)
            spo2 = np.random.normal(88, 3)
            rr = np.random.normal(28, 4)
            temp = np.random.normal(38.8, 0.8)

        hr = float(np.clip(hr, 35, 190))
        sbp = float(np.clip(sbp, 60, 220))
        dbp = float(np.clip(dbp, 35, 140))
        spo2 = float(np.clip(spo2, 60, 100))
        rr = float(np.clip(rr, 6, 45))
        temp = float(np.clip(temp, 34, 41))

        score = _news2_like_score(age, hr, sbp, dbp, spo2, rr, temp)
        prob = _sigmoid((score - 4) * 0.8)
        label = 1 if random.random() < prob else 0

        rows.append([age, hr, sbp, dbp, spo2, rr, temp])
        labels.append(label)

    return np.array(rows, dtype=float), np.array(labels, dtype=int)


def train_and_select() -> dict:
    X, y = generate_synthetic_dataset()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler().fit(X_train)  # fit on train only
    X_train_scaled = scaler.transform(X_train)
    X_test_scaled = scaler.transform(X_test)  # test never seen during fit

    candidates = {
        "LogisticRegression": LogisticRegression(max_iter=1000, random_state=42),
        "RandomForest": RandomForestClassifier(n_estimators=200, max_depth=8, random_state=42),
    }

    results = {}
    for name, model in candidates.items():
        model.fit(X_train_scaled, y_train)
        proba = model.predict_proba(X_test_scaled)[:, 1]
        preds = model.predict(X_test_scaled)
        results[name] = {
            "accuracy": round(float(accuracy_score(y_test, preds)), 4),
            "auc": round(float(roc_auc_score(y_test, proba)), 4),
            "model": model,
        }

    best_name = max(results, key=lambda k: results[k]["auc"])
    best_model = results[best_name]["model"]

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"scaler": scaler, "model": best_model, "feature_names": FEATURE_NAMES}, MODEL_PATH)

    metrics = {
        "feature_names": FEATURE_NAMES,
        "train_size": len(X_train),
        "test_size": len(X_test),
        "selected_model": best_name,
        "comparison": {
            name: {"accuracy": r["accuracy"], "auc": r["auc"]} for name, r in results.items()
        },
        "note": (
            "Trained on synthetic vitals data with NEWS2-inspired labeling for "
            "demonstration only. Not a validated clinical risk score."
        ),
    }
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    m = train_and_select()
    print(json.dumps(m, indent=2))

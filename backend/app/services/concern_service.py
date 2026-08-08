"""Rule-based clinical concern pattern routing.

This flags a *possible* physiological pattern from vitals alone, purely
to route the case to the right department/specialist for review. It is
NOT a diagnosis: overlapping patterns, artifacts, or unrelated causes
can all produce the same vitals signature. A clinician must confirm.
"""

CONCERN_DEPARTMENT = {
    "Cardiac deterioration": "Cardiology",
    "Respiratory deterioration": "Pulmonology",
    "Infectious pattern": "General Medicine",
    "General deterioration": "Emergency",
}


def classify_concern(features: dict, priority: str) -> dict:
    hr = features["heart_rate"]
    sbp = features["systolic_bp"]
    dbp = features["diastolic_bp"]
    spo2 = features["spo2"]
    rr = features["respiratory_rate"]
    temp = features["temperature"]

    cardiac_score = 0
    if hr >= 120 or hr <= 45:
        cardiac_score += 2
    if sbp <= 95 or sbp >= 180:
        cardiac_score += 2
    if dbp <= 55:
        cardiac_score += 1

    respiratory_score = 0
    if spo2 <= 93:
        respiratory_score += 2
    if spo2 <= 90:
        respiratory_score += 1
    if rr >= 24 or rr <= 10:
        respiratory_score += 2

    infectious_score = 0
    if temp >= 38.3:
        infectious_score += 2
    if hr >= 100:
        infectious_score += 1
    if rr >= 22:
        infectious_score += 1

    scores = {
        "Cardiac deterioration": cardiac_score,
        "Respiratory deterioration": respiratory_score,
        "Infectious pattern": infectious_score,
    }
    best_concern, best_score = max(scores.items(), key=lambda kv: kv[1])

    if best_score >= 3:
        concern = best_concern
    elif priority in ("HIGH", "CRITICAL"):
        concern = "General deterioration"
    else:
        concern = None

    department = CONCERN_DEPARTMENT.get(concern) if concern else None

    return {"concern": concern, "department": department, "scores": scores}

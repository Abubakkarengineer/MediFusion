"""Configurable demonstration thresholds mapping a deterioration
probability to a priority category. Tunable without touching model or
API code -- these are workflow-demo bands, not a validated triage tool.
"""

PRIORITY_THRESHOLDS = {
    "LOW": 0.0,
    "MODERATE": 0.30,
    "HIGH": 0.60,
    "CRITICAL": 0.85,
}

PRIORITY_ORDER = ["LOW", "MODERATE", "HIGH", "CRITICAL"]


def priority_from_probability(probability: float) -> str:
    priority = "LOW"
    for level in PRIORITY_ORDER:
        if probability >= PRIORITY_THRESHOLDS[level]:
            priority = level
    return priority

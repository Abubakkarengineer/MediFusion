"""Shared feature contract between training and inference so the two
never silently drift apart (a common source of ML bugs)."""

FEATURE_NAMES = [
    "age",
    "heart_rate",
    "systolic_bp",
    "diastolic_bp",
    "spo2",
    "respiratory_rate",
    "temperature",
]


def vector_from_dict(values: dict) -> list[float]:
    return [float(values[name]) for name in FEATURE_NAMES]

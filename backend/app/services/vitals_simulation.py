import datetime
import random

STEPS = 10
INTERVAL_MINUTES = 3

SCENARIOS = ["Stable", "Gradual Deterioration", "Recovery", "Cardiac Pattern", "Respiratory Pattern"]


def _lerp(start: float, end: float, t: float) -> float:
    return start + (end - start) * t


def _noise(value: float, spread: float) -> float:
    return value + random.uniform(-spread, spread)


def generate_scenario(scenario: str) -> list[dict]:
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario}")

    now = datetime.datetime.utcnow()
    readings = []

    for i in range(STEPS):
        t = i / (STEPS - 1)  # 0 -> 1 across the simulation
        recorded_at = now - datetime.timedelta(minutes=(STEPS - 1 - i) * INTERVAL_MINUTES)

        if scenario == "Stable":
            hr = _noise(78, 4)
            sbp = _noise(118, 4)
            dbp = _noise(78, 3)
            spo2 = _noise(98, 0.6)
            rr = _noise(16, 1)
            temp = _noise(36.8, 0.15)

        elif scenario == "Gradual Deterioration":
            hr = _noise(_lerp(80, 135, t), 3)
            sbp = _noise(_lerp(120, 88, t), 4)
            dbp = _noise(_lerp(78, 55, t), 3)
            spo2 = _noise(_lerp(97, 84, t), 0.8)
            rr = _noise(_lerp(16, 30, t), 1)
            temp = _noise(_lerp(37.0, 38.6, t), 0.15)

        elif scenario == "Recovery":
            hr = _noise(_lerp(132, 82, t), 3)
            sbp = _noise(_lerp(90, 118, t), 4)
            dbp = _noise(_lerp(58, 78, t), 3)
            spo2 = _noise(_lerp(85, 97, t), 0.8)
            rr = _noise(_lerp(29, 16, t), 1)
            temp = _noise(_lerp(38.5, 37.0, t), 0.15)

        elif scenario == "Cardiac Pattern":
            spike = 1 if i % 3 == 0 else 0
            hr = _noise(105 + spike * 35, 6)
            sbp = _noise(150 - spike * 45, 8)
            dbp = _noise(95 - spike * 25, 5)
            spo2 = _noise(93, 1.5)
            rr = _noise(20, 2)
            temp = _noise(37.1, 0.2)

        else:  # Respiratory Pattern
            hr = _noise(_lerp(88, 118, t), 4)
            sbp = _noise(116, 5)
            dbp = _noise(76, 4)
            spo2 = _noise(_lerp(94, 80, t), 1.0)
            rr = _noise(_lerp(20, 34, t), 1.5)
            temp = _noise(_lerp(37.4, 38.8, t), 0.15)

        readings.append(
            {
                "heart_rate": round(max(30, hr), 1),
                "systolic_bp": round(max(60, sbp), 1),
                "diastolic_bp": round(max(35, dbp), 1),
                "spo2": round(min(100, max(60, spo2)), 1),
                "respiratory_rate": round(max(8, rr), 1),
                "temperature": round(temp, 1),
                "recorded_at": recorded_at,
            }
        )

    return readings

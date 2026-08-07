"""Lexicons used to structure raw OCR text from prescriptions and lab
reports. This is deterministic rule-based extraction, not diagnosis:
lab reference ranges below are standard published clinical ranges used
only to flag a value as Low/Normal/High for a clinician to review.
"""

import re

# demo/common medicine names for prescription line matching
MEDICINE_LEXICON = [
    "paracetamol", "acetaminophen", "ibuprofen", "aspirin", "amoxicillin",
    "azithromycin", "ciprofloxacin", "metformin", "atorvastatin",
    "amlodipine", "omeprazole", "pantoprazole", "cetirizine",
    "loratadine", "metronidazole", "doxycycline", "losartan",
    "atenolol", "insulin", "salbutamol", "prednisolone", "diclofenac",
    "levothyroxine", "clopidogrel", "furosemide", "hydrochlorothiazide",
    "ranitidine", "domperidone", "ondansetron", "vitamin d3", "vitamin b12",
    "iron", "folic acid", "calcium carbonate", "montelukast",
]

FREQUENCY_PATTERNS = [
    (r"\bonce\s+(?:a\s+day|daily)\b|\bOD\b", "Once daily"),
    (r"\btwice\s+(?:a\s+day|daily)\b|\bBD\b|\bBID\b", "Twice daily"),
    (r"\bthrice\s+(?:a\s+day|daily)\b|\bthree\s+times\s+(?:a\s+day|daily)\b|\bTDS\b|\bTID\b", "Three times daily"),
    (r"\bfour\s+times\s+(?:a\s+day|daily)\b|\bQID\b", "Four times daily"),
    (r"\bat\s+bedtime\b|\bHS\b", "At bedtime"),
    (r"\bas\s+needed\b|\bSOS\b|\bPRN\b", "As needed"),
]

DOSAGE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s?(mg|mcg|g|ml|iu)\b", re.IGNORECASE)

# test_name -> (low, high, unit) using standard adult reference ranges
LAB_TEST_LEXICON: dict[str, tuple[float, float, str]] = {
    "hemoglobin": (13.0, 17.0, "g/dL"),
    "hematocrit": (38.0, 50.0, "%"),
    "wbc": (4.0, 11.0, "x10^3/uL"),
    "white blood cell": (4.0, 11.0, "x10^3/uL"),
    "rbc": (4.2, 5.9, "x10^6/uL"),
    "platelet": (150.0, 450.0, "x10^3/uL"),
    "glucose": (70.0, 100.0, "mg/dL"),
    "fasting glucose": (70.0, 100.0, "mg/dL"),
    "creatinine": (0.6, 1.3, "mg/dL"),
    "urea": (7.0, 20.0, "mg/dL"),
    "bun": (7.0, 20.0, "mg/dL"),
    "total cholesterol": (0.0, 200.0, "mg/dL"),
    "cholesterol": (0.0, 200.0, "mg/dL"),
    "triglycerides": (0.0, 150.0, "mg/dL"),
    "hdl": (40.0, 60.0, "mg/dL"),
    "ldl": (0.0, 100.0, "mg/dL"),
    "alt": (7.0, 56.0, "U/L"),
    "sgpt": (7.0, 56.0, "U/L"),
    "ast": (10.0, 40.0, "U/L"),
    "sgot": (10.0, 40.0, "U/L"),
    "tsh": (0.4, 4.0, "mIU/L"),
    "sodium": (135.0, 145.0, "mmol/L"),
    "potassium": (3.5, 5.1, "mmol/L"),
    "bilirubin": (0.1, 1.2, "mg/dL"),
    "total bilirubin": (0.1, 1.2, "mg/dL"),
    "spo2": (95.0, 100.0, "%"),
    "hba1c": (4.0, 5.6, "%"),
    "crp": (0.0, 5.0, "mg/L"),
    "esr": (0.0, 20.0, "mm/hr"),
    "albumin": (3.5, 5.0, "g/dL"),
}


LAB_TEST_DISPLAY_NAMES: dict[str, str] = {
    "wbc": "WBC",
    "white blood cell": "White Blood Cell",
    "rbc": "RBC",
    "bun": "BUN",
    "hdl": "HDL",
    "ldl": "LDL",
    "alt": "ALT",
    "sgpt": "SGPT",
    "ast": "AST",
    "sgot": "SGOT",
    "tsh": "TSH",
    "spo2": "SpO2",
    "hba1c": "HbA1c",
    "crp": "CRP",
    "esr": "ESR",
}


def display_name(test_name: str) -> str:
    return LAB_TEST_DISPLAY_NAMES.get(test_name.lower(), test_name.title())


def flag_value(test_name: str, value: float) -> str:
    key = test_name.lower().strip()
    ref = LAB_TEST_LEXICON.get(key)
    if not ref:
        return "Unknown"
    low, high, _ = ref
    if value < low:
        return "Low"
    if value > high:
        return "High"
    return "Normal"


def extract_lab_values(text: str) -> list[dict]:
    results = []
    lowered = text.lower()
    for test_name in LAB_TEST_LEXICON:
        for match in re.finditer(re.escape(test_name), lowered):
            window = text[match.end():match.end() + 25]
            number_match = re.search(r"(\d+\.?\d*)", window)
            if not number_match:
                continue
            try:
                value = float(number_match.group(1))
            except ValueError:
                continue
            _, _, unit = LAB_TEST_LEXICON[test_name]
            results.append(
                {
                    "test_name": display_name(test_name),
                    "value": value,
                    "unit": unit,
                    "flag": flag_value(test_name, value),
                }
            )
    # de-duplicate by test name, keep first occurrence
    seen = set()
    deduped = []
    for r in results:
        if r["test_name"] not in seen:
            seen.add(r["test_name"])
            deduped.append(r)
    return deduped


def extract_medicines(text: str) -> list[dict]:
    lowered = text.lower()

    # find each medicine's first occurrence, then sort by position so each
    # medicine's search window can be bounded by where the *next* medicine
    # starts -- otherwise a wide fixed window bleeds into the next drug's
    # dosage/frequency phrase when OCR merges multiple lines into one block.
    matches = []
    for med in MEDICINE_LEXICON:
        idx = lowered.find(med)
        if idx != -1:
            matches.append((idx, med))
    matches.sort(key=lambda pair: pair[0])

    results = []
    for i, (idx, med) in enumerate(matches):
        window_end = matches[i + 1][0] if i + 1 < len(matches) else min(idx + 80, len(text))
        window = text[idx:window_end]

        dosage_match = DOSAGE_PATTERN.search(window)
        dosage = f"{dosage_match.group(1)}{dosage_match.group(2)}" if dosage_match else None
        frequency = None
        for pattern, label in FREQUENCY_PATTERNS:
            if re.search(pattern, window, re.IGNORECASE):
                frequency = label
                break
        results.append(
            {
                "name": med.title(),
                "dosage": dosage,
                "frequency": frequency,
            }
        )
    seen = set()
    deduped = []
    for r in results:
        if r["name"] not in seen:
            seen.add(r["name"])
            deduped.append(r)
    return deduped


def extract_patient_info(text: str) -> dict:
    info = {}
    name_match = re.search(r"(?:patient\s*name|name)\s*[:\-]\s*([A-Za-z .]{2,40})", text, re.IGNORECASE)
    if name_match:
        info["name"] = name_match.group(1).strip()
    age_match = re.search(r"age\s*[:\-]\s*(\d{1,3})", text, re.IGNORECASE)
    if age_match:
        info["age"] = age_match.group(1).strip()
    date_match = re.search(r"date\s*[:\-]\s*([\d/\-]{6,12})", text, re.IGNORECASE)
    if date_match:
        info["date"] = date_match.group(1).strip()
    return info

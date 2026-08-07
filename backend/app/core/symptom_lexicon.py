"""Keyword lexicon used for rule-based symptom mention extraction.

This is NOT a diagnostic tool: it only flags words/phrases from the
transcript that match common symptom terminology, for a clinician to
review. It does not infer, score, or rank any disease or condition.
"""

# canonical symptom label -> phrases/variants that indicate it
SYMPTOM_LEXICON: dict[str, list[str]] = {
    "Chest pain": ["chest pain", "chest tightness", "pain in my chest", "chest hurts"],
    "Shortness of breath": [
        "shortness of breath",
        "difficulty breathing",
        "trouble breathing",
        "breathless",
        "can't breathe",
        "cannot breathe",
        "wheezing",
    ],
    "Cough": ["cough", "coughing"],
    "Fever": ["fever", "feverish", "high temperature", "chills"],
    "Headache": ["headache", "head hurts", "migraine"],
    "Dizziness": ["dizziness", "dizzy", "lightheaded", "light-headed"],
    "Nausea": ["nausea", "nauseous", "feel sick", "queasy"],
    "Vomiting": ["vomiting", "vomit", "throwing up", "threw up"],
    "Diarrhea": ["diarrhea", "diarrhoea", "loose stool"],
    "Constipation": ["constipation", "constipated"],
    "Abdominal pain": ["abdominal pain", "stomach pain", "stomach ache", "belly pain"],
    "Back pain": ["back pain", "backache"],
    "Joint pain": ["joint pain", "joints hurt", "joints ache"],
    "Muscle pain": ["muscle pain", "muscle ache", "myalgia"],
    "Sore throat": ["sore throat", "throat hurts", "throat pain"],
    "Runny nose": ["runny nose", "stuffy nose", "nasal congestion"],
    "Fatigue": ["fatigue", "tired", "exhausted", "no energy"],
    "Weakness": ["weakness", "weak", "feeling weak"],
    "Loss of appetite": ["loss of appetite", "not hungry", "no appetite"],
    "Rash": ["rash", "skin irritation", "itchy skin"],
    "Swelling": ["swelling", "swollen"],
    "Palpitations": ["palpitations", "heart racing", "racing heart", "irregular heartbeat"],
    "Blurred vision": ["blurred vision", "blurry vision", "vision problems"],
    "Numbness": ["numbness", "numb", "pins and needles", "tingling"],
    "Confusion": ["confusion", "confused", "disoriented"],
    "Sweating": ["sweating", "night sweats", "sweaty"],
    "Loss of consciousness": ["loss of consciousness", "fainted", "passed out", "blacked out"],
    "Difficulty swallowing": ["difficulty swallowing", "trouble swallowing"],
    "Blood in stool": ["blood in stool", "bloody stool"],
    "Blood in urine": ["blood in urine", "bloody urine"],
    "Weight loss": ["weight loss", "losing weight", "lost weight"],
    "Insomnia": ["insomnia", "can't sleep", "trouble sleeping"],
    "Anxiety": ["anxiety", "anxious", "panic attack"],
}


def extract_symptoms(text: str) -> list[str]:
    if not text:
        return []
    lowered = text.lower()
    found = []
    for canonical, variants in SYMPTOM_LEXICON.items():
        if any(variant in lowered for variant in variants):
            found.append(canonical)
    return found

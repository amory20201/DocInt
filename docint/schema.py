"""Output schema: every run returns the SAME structure (consistency requirement)."""
from __future__ import annotations

DOC_TYPES = ["invoice", "receipt", "contract", "letter", "unknown"]

# Fields we always return. Each is a "FieldResult":
#   {"value": str|float|None, "confidence": 0..1, "status": "ok"|"uncertain"|"missing"}
FIELDS = ["name", "date", "amount", "currency", "status", "document_number"]

# Which fields must exist for each document type (otherwise flagged as missing).
REQUIRED = {
    "invoice":  ["name", "date", "amount", "status"],
    "receipt":  ["name", "date", "amount"],
    "contract": ["name", "date", "status"],
    "letter":   ["name", "date"],
    "unknown":  [],
}

ALLOWED_STATUS = {
    "invoice":  {"paid", "unpaid", "overdue"},
    "receipt":  {"paid"},
    "contract": {"signed", "unsigned", "draft"},
    "letter":   {"n/a"},
    "unknown":  set(),
}

CONFIDENCE_THRESHOLD = 0.70  # below this a field is labelled "uncertain"

LIMITATIONS = [
    "Local engine reads English text only (tesseract 'eng'); use the Claude engine for Arabic or mixed-language files.",
    "Handwriting, stamps, heavy skew and very low resolution reduce accuracy - such fields are labelled 'uncertain'.",
    "Only 4 document types are modelled (invoice, receipt, contract, letter); anything else is 'unknown'.",
    "Multi-page documents: first 5 pages are analysed.",
    "Confidence scores are estimates, not calibrated probabilities. Human review is advised for flagged files.",
]


def field(value=None, confidence: float = 0.0) -> dict:
    return {"value": value, "confidence": round(float(confidence), 2),
            "status": "missing" if value in (None, "") else "ok"}


def empty_result(file: str, engine: str) -> dict:
    return {
        "file": file,
        "engine": engine,
        "document_type": field("unknown", 0.0),
        "fields": {k: field() for k in FIELDS},
        "summary": "",
        "answers": [],
        "validation": {"is_valid": False, "needs_review": True, "issues": []},
        "limitations": LIMITATIONS,
    }

"""Validation layer shared by ALL engines: normalise values, label missing/uncertain fields."""
from __future__ import annotations
import re
from datetime import date, datetime

from .schema import (ALLOWED_STATUS, CONFIDENCE_THRESHOLD, DOC_TYPES, FIELDS, REQUIRED, field)

_DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d %B %Y", "%d %b %Y",
                 "%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y", "%Y/%m/%d"]


def parse_date(text):
    """Return ISO date (YYYY-MM-DD) or None."""
    if not text:
        return None
    s = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", str(text).strip())
    s = re.sub(r"\s*,\s*", ", ", s)
    s = re.sub(r"\s+", " ", s)
    for f in _DATE_FORMATS:
        try:
            return datetime.strptime(s, f).date().isoformat()
        except ValueError:
            continue
    return None


def parse_amount(text):
    if text is None or text == "":
        return None
    if isinstance(text, (int, float)):
        return float(text)
    s = re.sub(r"[^\d.,]", "", str(text))
    if not s:
        return None
    if "," in s and "." in s:
        s = s.replace(",", "") if s.rfind(".") > s.rfind(",") else s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", "") if re.search(r",\d{3}$", s) else s.replace(",", ".")
    try:
        return round(float(s), 2)
    except ValueError:
        return None


def validate(result: dict) -> dict:
    """Normalise + attach validation. Mutates and returns result."""
    issues = []

    dt = result["document_type"]
    if dt.get("value") not in DOC_TYPES:
        dt["value"] = "unknown"
    dtype = dt["value"]
    if dtype == "unknown":
        dt["status"] = "missing"
    elif dt.get("confidence", 0) >= CONFIDENCE_THRESHOLD:
        dt["status"] = "ok"
    else:
        dt["status"] = "uncertain"
    if dt["status"] != "ok":
        issues.append({"field": "document_type", "code": dt["status"],
                       "message": "Document type could not be determined confidently."})

    fields = result["fields"]
    for k in FIELDS:
        fields.setdefault(k, field())
        f = fields[k]
        v = f.get("value")
        if k == "date" and v:
            iso = parse_date(v)
            if iso is None:
                issues.append({"field": k, "code": "invalid", "message": f"Could not parse date '{v}'."})
                f["value"], f["confidence"] = None, 0.0
            else:
                f["value"] = iso
                if not (1990 <= int(iso[:4]) <= date.today().year + 2):
                    issues.append({"field": k, "code": "implausible", "message": f"Date {iso} looks implausible."})
                    f["confidence"] = min(f.get("confidence", 0), 0.5)
        elif k == "amount" and v is not None and v != "":
            amt = parse_amount(v)
            if amt is None or amt < 0:
                issues.append({"field": k, "code": "invalid", "message": f"Could not parse amount '{v}'."})
                f["value"], f["confidence"] = None, 0.0
            else:
                f["value"] = amt
        elif k == "status" and v:
            f["value"] = str(v).strip().lower()
            allowed = ALLOWED_STATUS.get(dtype, set())
            if allowed and f["value"] not in allowed:
                issues.append({"field": k, "code": "invalid",
                               "message": f"Status '{f['value']}' is not valid for a {dtype} (allowed: {sorted(allowed)})."})
                f["confidence"] = min(f.get("confidence", 0), 0.4)
        elif k == "currency" and v:
            f["value"] = str(v).strip().upper()[:3]
        elif isinstance(v, str):
            f["value"] = v.strip()

        if f["value"] in (None, ""):
            f["value"], f["confidence"], f["status"] = None, 0.0, "missing"
        elif f.get("confidence", 0) < CONFIDENCE_THRESHOLD:
            f["status"] = "uncertain"
        else:
            f["status"] = "ok"

    for k in REQUIRED.get(dtype, []):
        if fields[k]["status"] == "missing":
            issues.append({"field": k, "code": "missing", "message": f"Required field '{k}' not found for a {dtype}."})
        elif fields[k]["status"] == "uncertain":
            issues.append({"field": k, "code": "uncertain",
                           "message": f"'{k}' = {fields[k]['value']!r} is uncertain (confidence {fields[k]['confidence']})."})

    if dtype in ("invoice", "receipt") and fields["amount"]["value"] is not None and not fields["currency"]["value"]:
        issues.append({"field": "currency", "code": "missing", "message": "Amount found but no currency detected."})

    blocking = [i for i in issues if i["code"] in ("missing", "invalid")
                and i["field"] in REQUIRED.get(dtype, []) + ["document_type"]]
    result["validation"] = {"is_valid": not blocking, "needs_review": bool(issues), "issues": issues}
    return result

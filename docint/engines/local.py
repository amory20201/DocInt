"""Offline engine: OCR (tesseract) + rule-based extraction. No API key, no network."""
from __future__ import annotations
import re

from ..schema import empty_result, field
from ..validate import parse_amount

ENGINE = "local-ocr-rules"

# ---------- OCR ----------
def ocr(images):
    """Return (text, mean_word_confidence_0_1)."""
    import pytesseract
    texts, confs = [], []
    for img in images:
        data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT, config="--psm 6")
        texts.append(pytesseract.image_to_string(img, lang="eng", config="--psm 6"))
        confs += [float(c) for c, w in zip(data["conf"], data["text"]) if w.strip() and float(c) >= 0]
    mean = (sum(confs) / len(confs) / 100) if confs else 0.0
    return "\n".join(texts), mean


def get_text(doc):
    if doc.text_layer and len(doc.text_layer) > 30:
        return doc.text_layer, 0.98, "pdf-text-layer"
    t, c = ocr(doc.images)
    return t, c, "ocr"

# ---------- patterns ----------
MONTHS = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
DATE_RE = re.compile(
    rf"(\d{{4}}[-/]\d{{1,2}}[-/]\d{{1,2}}|\d{{1,2}}[/.-]\d{{1,2}}[/.-]\d{{2,4}}|\d{{1,2}}(?:st|nd|rd|th)?\s+{MONTHS}\.?,?\s+\d{{4}}|{MONTHS}\.?\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{4}})",
    re.I)
AMOUNT_RE = r"((?:[$€£]|EGP|USD|EUR|GBP|L\.?E\.?)?\s?\d[\d.,]*\d(?:\s?(?:EGP|USD|EUR|GBP))?)"
CURRENCIES = {"$": "USD", "€": "EUR", "£": "GBP", "USD": "USD", "EUR": "EUR", "GBP": "GBP", "EGP": "EGP", "LE": "EGP", "L.E": "EGP", "L.E.": "EGP"}

TYPE_KEYWORDS = {
    "invoice":  {"invoice": 3, "bill to": 2, "invoice no": 2, "amount due": 2, "balance due": 2, "due date": 1.5, "subtotal": 1, "payment terms": 1},
    "receipt":  {"receipt": 3, "thank you": 1, "cashier": 2, "change": 1, "visa": 1, "mastercard": 1, "cash": 1, "card": 0.5, "tax": 0.5, "pos": 1, "items": 0.5},
    "contract": {"agreement": 3, "contract": 2, "parties": 2, "hereby": 1.5, "terms and conditions": 1.5, "signature": 1, "effective date": 2, "witness": 1, "governing law": 2, "whereas": 2},
    "letter":   {"dear": 3, "sincerely": 3, "yours faithfully": 3, "kind regards": 2, "best regards": 2, "regards": 1, "to whom it may concern": 3},
}


def classify(text):
    low = text.lower()
    scores = {t: sum(w for k, w in kws.items() if k in low) for t, kws in TYPE_KEYWORDS.items()}
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    (top_t, top), (_, second) = ranked[0], ranked[1]
    if top < 2:
        return "unknown", 0.2
    conf = min(0.98, (top / (top + second + 0.01)) * min(1.0, top / 4) + 0.05)
    return top_t, conf


def _lines(text):
    return [l.strip() for l in text.splitlines() if l.strip()]


def _after_label(lines, labels):
    """Value after 'Label:' on same line, or the next non-empty line."""
    for i, l in enumerate(lines):
        for lab in labels:
            m = re.match(rf"^\W*{lab}\s*[:\-]?\s*(.*)$", l, re.I)
            if m:
                v = m.group(1).strip()
                if v:
                    return v
                if i + 1 < len(lines):
                    return lines[i + 1]
    return None


def extract_name(text, dtype):
    lines = _lines(text)
    if dtype == "invoice":
        v = _after_label(lines, ["bill to", "billed to", "customer", "client"])
        if v: return v, 0.9
    if dtype == "receipt":
        v = _after_label(lines, ["merchant", "store"])
        if v: return v, 0.9
        for l in lines[:3]:
            if re.search(r"[A-Za-z]{3,}", l) and "receipt" not in l.lower():
                return l, 0.75
    if dtype == "contract":
        m = re.search(r"between\s+([^()\n,]+?)\s*(?:\([^)]*\))?\s*,?\s+and\s+([^()\n,]+?)\s*(?:\(|,|\.\s|\.$|\n)", text, re.I)
        if m:
            return f"{m.group(1).strip()} & {m.group(2).strip()}", 0.85
        a, b = _after_label(lines, ["party a", "client"]), _after_label(lines, ["party b", "provider", "contractor"])
        if a and b: return f"{a} & {b}", 0.8
    if dtype == "letter":
        m = re.search(r"^\s*dear\s+([^,\n]+)", text, re.I | re.M)
        if m: return m.group(1).strip(), 0.85
        v = _after_label(lines, ["to"])
        if v: return v, 0.7
    v = _after_label(lines, ["name", "customer", "client", "bill to", "to"])
    return (v, 0.55) if v else (None, 0.0)


def extract_date(text):
    lines = _lines(text)
    for pri_labels, conf in ((["invoice date", "date of issue", "issue date", "effective date", "date", "dated", "issued"], 0.92),):
        for l in lines:
            if re.match(r"^\W*due", l, re.I):
                continue
            for lab in pri_labels:
                m = re.match(rf"^\W*{lab}\b\s*[:\-]?\s*(.*)$", l, re.I)
                if m:
                    d = DATE_RE.search(m.group(1) or "")
                    if d: return _date_conf(d.group(1), conf)
    for l in lines:
        if re.search(r"\bdue\b", l, re.I):
            continue
        d = DATE_RE.search(l)
        if d: return _date_conf(d.group(1), 0.62)
    return None, 0.0


def _date_conf(s, conf):
    m = re.match(r"^(\d{1,2})[/.-](\d{1,2})[/.-]\d{2,4}$", s)
    if m and int(m.group(1)) <= 12 and int(m.group(2)) <= 12 and m.group(1) != m.group(2):
        conf = min(conf, 0.6)   # dd/mm vs mm/dd ambiguity -> uncertain
    return s, conf


def extract_amount(text, dtype):
    lines = _lines(text)
    priority = [r"(?:total\s+)?amount\s+due", r"balance\s+due", r"grand\s+total", r"total\s+due",
                r"(?<!sub)total", r"contract\s+(?:value|price|sum)", r"(?:total\s+)?fee", r"amount"]
    for pi, lab in enumerate(priority):
        for l in reversed(lines):
            m = re.search(rf"{lab}[^\d$€£]*{AMOUNT_RE}", l, re.I)
            if m:
                raw = m.group(1)
                if parse_amount(raw) is not None:
                    cur = _currency(raw + " " + l)
                    return raw, cur, (0.92 if pi < 5 else 0.8)
    nums = [(parse_amount(m.group(1)), m.group(1), l) for l in lines for m in re.finditer(AMOUNT_RE, l)
            if re.search(r"[.,]\d{2}\b", m.group(1))]
    nums = [n for n in nums if n[0]]
    if nums:
        best = max(nums, key=lambda n: n[0])
        return best[1], _currency(best[2]), 0.5
    return None, None, 0.0


def _currency(s):
    for sym, code in CURRENCIES.items():
        if sym in s.upper() or sym in s:
            return code
    return None


def extract_status(text, dtype, has_amount):
    low = text.lower()
    if dtype == "invoice":
        if re.search(r"\bover\s?due\b|\bpast\s+due\b", low): return "overdue", 0.88
        if re.search(r"\bunpaid\b|\bbalance\s+due\b|\bpayment\s+due\b|\bamount\s+due\b", low) and not re.search(r"(?<!un)\bpaid\b", low): return "unpaid", 0.85
        if re.search(r"(?<!un)\bpaid\b", low): return "paid", 0.92
        return ("unpaid", 0.55) if has_amount else (None, 0.0)
    if dtype == "receipt":
        return ("paid", 0.95) if re.search(r"total|paid|cash|card|visa|mastercard", low) else ("paid", 0.6)
    if dtype == "contract":
        if re.search(r"\bdraft\b", low): return "draft", 0.85
        if re.search(r"signed by|/s/|digitally signed|executed (?:on|by)", low): return "signed", 0.88
        if re.search(r"signature\s*:?\s*_{3,}|_{5,}\s*\n?\s*(?:signature|date)", low): return "unsigned", 0.75
        if "signature" in low: return "signed", 0.5
        return None, 0.0
    if dtype == "letter":
        return "n/a", 0.9
    return None, 0.0


def extract_number(text):
    pat = r"(?:invoice|receipt|contract|ref(?:erence)?|order)\s*(?:no\.?|number|#|id)?\s*[:#\-]?\s*([A-Z0-9][A-Z0-9\-/]{3,})"
    for m in re.finditer(pat, text, re.I):
        if re.search(r"\d", m.group(1)):
            return m.group(1).strip(".,"), 0.88
    return None, 0.0


def summarize(res):
    f = {k: v["value"] for k, v in res["fields"].items()}
    t = res["document_type"]["value"]
    if t == "unknown":
        return "Document type could not be determined."
    parts = [f"{t.capitalize()}"]
    if f["name"]: parts.append(f"for/with {f['name']}")
    if f["date"]: parts.append(f"dated {f['date']}")
    s = " ".join(parts)
    if f["amount"] is not None: s += f", amount {f['amount']:.2f} {f['currency'] or ''}".rstrip()
    if f["status"] and f["status"] != "n/a": s += f", status: {f['status']}"
    return s + "."


def analyze(doc, questions=None):
    text, ocr_conf, source = get_text(doc)
    res = empty_result(doc.name, ENGINE)
    # global quality factor: poor OCR lowers every confidence
    q = min(1.0, ocr_conf / 0.90) if ocr_conf else 0.0

    dtype, c = classify(text)
    res["document_type"] = field(dtype, c * q)
    name, nc = extract_name(text, dtype)
    date, dc = extract_date(text)
    amt, cur, ac = extract_amount(text, dtype)
    status, sc = extract_status(text, dtype, amt is not None)
    num, nuc = extract_number(text)
    res["fields"]["name"] = field(name, nc * q)
    res["fields"]["date"] = field(date, dc * q)
    res["fields"]["amount"] = field(amt, ac * q)
    res["fields"]["currency"] = field(cur, (0.9 if cur else 0) * q)
    res["fields"]["status"] = field(status, sc * q)
    res["fields"]["document_number"] = field(num, nuc * q)
    res["meta"] = {"text_source": source, "ocr_mean_confidence": round(ocr_conf, 2), "pages": doc.pages}
    res["_text"] = text
    return res

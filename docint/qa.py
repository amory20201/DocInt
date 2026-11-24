"""Question answering over a document (used by the local engine; Claude answers inside its own call)."""
from __future__ import annotations
import re

STOP = set("what is the a an of for in on to this that does do who when how much which are was were and or it its please tell me about".split())
INTENT = {
    "amount": {"total", "amount", "cost", "price", "pay", "owe", "owed", "sum", "value", "fee", "charge"},
    "date": {"date", "when", "issued", "day"},
    "name": {"name", "customer", "client", "vendor", "merchant", "party", "parties", "who", "recipient", "store"},
    "status": {"status", "paid", "unpaid", "signed", "overdue", "state"},
    "document_type": {"type", "kind", "category", "document"},
    "document_number": {"number", "invoice", "reference", "ref", "id"},
}


def _tok(s):
    return [w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP]


def answer_questions(res, text, questions):
    out = []
    for q in questions:
        out.append(_answer(res, text, q))
    return out


def _answer(res, text, q):
    toks = set(_tok(q))
    f = res["fields"]
    for key, words in INTENT.items():
        if toks & words:
            node = res["document_type"] if key == "document_type" else f[key]
            if node["value"] is None:
                return _a(q, "Not found in the document.", 0.0, "missing", "")
            val = node["value"]
            if key == "amount":
                val = f"{val:.2f} {f['currency']['value'] or ''}".strip()
            return _a(q, str(val), node["confidence"], node["status"], f"extracted field '{key}'")
    best, score = None, 0.0
    for line in [l.strip() for l in text.splitlines() if l.strip()]:
        lt = set(_tok(line))
        if not lt or not toks:
            continue
        s = len(toks & lt) / len(toks)
        if s > score:
            best, score = line, s
    if best and score >= 0.34:
        conf = round(min(0.6, score * 0.7), 2)
        return _a(q, best, conf, "uncertain", "closest matching line (keyword retrieval)")
    return _a(q, "Not found in the document.", 0.0, "missing", "")


def _a(q, ans, conf, status, ev):
    return {"question": q, "answer": ans, "confidence": round(conf, 2), "status": status, "evidence": ev}

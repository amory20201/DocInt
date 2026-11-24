"""One entry point: file -> structured, validated result."""
from __future__ import annotations
import os

from . import loader, qa
from .validate import validate


def analyze(path, questions=None, engine="auto"):
    questions = [q.strip() for q in (questions or []) if q and q.strip()]
    doc = loader.load(path)
    if engine == "auto":
        engine = "claude" if os.environ.get("ANTHROPIC_API_KEY") else "local"

    note = None
    if engine == "claude":
        from .engines import claude
        try:
            res = claude.analyze(doc, questions)
        except claude.EngineError as e:
            note = f"Claude engine failed ({e}); fell back to the local engine."
            engine = "local"
    if engine == "local":
        from .engines import local
        res = local.analyze(doc, questions)
        validate(res)                       # normalise + label first ...
        res["summary"] = local.summarize(res)   # ... then summarise / answer from clean values
        res["answers"] = qa.answer_questions(res, res.pop("_text", ""), questions)
    else:
        validate(res)
    res.pop("_text", None)
    if note:
        res["validation"]["issues"].append({"field": "engine", "code": "fallback", "message": note})
        res["validation"]["needs_review"] = True
    return res

# DocInt - Multimodal Document Intelligence

Upload a **PDF or image** and the app **classifies** it, **extracts fields**, **answers questions**, and returns a
**structured JSON** result in which every **missing / uncertain field is labeled**.

## Requirements checklist
| Requirement | Where |
|---|---|
| File / image input | `docint/loader.py` (PDF, JPG, PNG, WEBP, BMP, TIFF; 20 MB; first 5 pages) |
| Information extraction | `docint/engines/claude.py` (vision) and `docint/engines/local.py` (OCR + rules) |
| Classification or summary | `document_type` (invoice / receipt / contract / letter / unknown) + `summary` |
| Structured output | `docint/schema.py` - identical JSON shape for every file and engine |
| Validation for missing / uncertain fields | `docint/validate.py` - status `ok` / `uncertain` / `missing`, issues list, `needs_review` flag |
| Questions about the document | `-q "..."` in the CLI, textbox in the web UI -> `answers[]` |

## Quick start
```bash
pip install -r requirements.txt            # + install the tesseract binary for the local engine
python server.py                           # web UI -> http://localhost:8000
python cli.py samples/*.pdf -q "What is the total amount?"
export ANTHROPIC_API_KEY=sk-ant-...        # optional: switches on the Claude vision engine (DOCINT_MODEL to change model)
python -m unittest discover -s tests -v    # 12 tests
python make_samples.py                     # regenerate the fictional sample files
```

## Output (same shape every time)
```json
{
  "file": "invoice_nile_trading.pdf", "engine": "local-ocr-rules",
  "document_type": {"value": "invoice", "confidence": 0.95, "status": "ok"},
  "fields": {"name": {"value": "Delta Logistics LLC", "confidence": 0.9, "status": "ok"},
             "date": {}, "amount": {}, "currency": {}, "status": {}, "document_number": {}},
  "summary": "...", "answers": [{"question": "...", "answer": "...", "confidence": 0.9, "status": "ok", "evidence": "..."}],
  "validation": {"is_valid": true, "needs_review": false, "issues": []},
  "limitations": ["..."]
}
```
* `missing` = not found (value `null`). `uncertain` = confidence < 0.70 (blurry, ambiguous `03/04/2026`, weak evidence).
* `is_valid` is false when a *required* field for that document type is missing/invalid; `needs_review` is true whenever anything is flagged.

## Design decisions
1. **Two engines, one validator.** Claude vision is the accurate engine; local OCR works offline and is the automatic
   fallback if the API fails. Both feed the same validation layer, so outputs stay consistent.
2. **Never guess.** The Claude prompt forces `null` + confidence 0 for anything not visible, output comes from a forced
   tool call (schema-constrained JSON), and instructions found inside a document are treated as data.
3. **Standard library first.** HTTP calls and the web server use only the Python standard library.

## Limitations
* Local engine reads **English only**; Arabic / mixed-language files need the Claude engine.
* Handwriting, stamps, heavy skew, very low resolution lower accuracy; such fields are labeled `uncertain`.
* Only 4 document types are modelled; everything else is `unknown`.
* The local engine is rule-based: unusual layouts or wording can be missed (it reports `missing`, not a guess).
* Dates like `03/04/2026` are ambiguous, so they are always `uncertain`.
* Confidence values are estimates, not calibrated probabilities.
* The Claude engine's HTTP call is covered by mocked tests; it was **not** run against the live API during development
  (no network in the build environment). Run it once with your key before the final demo.
* Demo web server has no authentication or storage; don't expose it publicly.

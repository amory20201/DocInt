import json, os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from docint.pipeline import analyze
from docint.validate import parse_amount, parse_date, validate
from docint.schema import empty_result, field
from docint.engines import claude

S = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples")
P = lambda n: os.path.join(S, n)


class Parsing(unittest.TestCase):
    def test_dates(self):
        self.assertEqual(parse_date("14 March 2026"), "2026-03-14")
        self.assertEqual(parse_date("March 14th, 2026"), "2026-03-14")
        self.assertIsNone(parse_date("not a date"))

    def test_amounts(self):
        self.assertEqual(parse_amount("$1,254.00"), 1254.0)
        self.assertEqual(parse_amount("86,50"), 86.5)
        self.assertIsNone(parse_amount("abc"))


class Local(unittest.TestCase):
    def test_invoice_pdf(self):
        r = analyze(P("invoice_nile_trading.pdf"), ["What is the total?"], "local")
        self.assertEqual(r["document_type"]["value"], "invoice")
        f = r["fields"]
        self.assertEqual((f["name"]["value"], f["date"]["value"], f["amount"]["value"], f["status"]["value"]),
                         ("Delta Logistics LLC", "2026-03-14", 1254.0, "paid"))
        self.assertEqual(f["document_number"]["value"], "INV-2026-0417")
        self.assertFalse(r["validation"]["needs_review"])
        self.assertIn("1254.00", r["answers"][0]["answer"])

    def test_receipt_image_ocr(self):
        r = analyze(P("receipt_cairo_coffee.jpg"), engine="local")
        self.assertEqual(r["document_type"]["value"], "receipt")
        self.assertEqual(r["fields"]["amount"]["value"], 86.5)
        self.assertEqual(r["fields"]["currency"]["value"], "EGP")

    def test_contract_and_letter(self):
        c = analyze(P("contract_service_agreement.pdf"), engine="local")
        self.assertEqual((c["document_type"]["value"], c["fields"]["status"]["value"]), ("contract", "signed"))
        l = analyze(P("letter_university.pdf"), engine="local")
        self.assertEqual((l["document_type"]["value"], l["fields"]["date"]["value"]), ("letter", "2026-10-05"))

    def test_poor_scan_is_flagged_not_trusted(self):
        r = analyze(P("invoice_scan_poor_quality.jpg"), engine="local")
        self.assertTrue(r["validation"]["needs_review"])
        self.assertEqual(r["fields"]["date"]["status"], "uncertain")      # 03/04/2026 is ambiguous
        self.assertNotEqual(r["fields"]["amount"]["status"], "ok")        # total hidden by ink stain

    def test_unknown_document(self):
        r = analyze(P("flyer_unknown.png"), ["What is the total?"], "local")
        self.assertEqual(r["document_type"]["value"], "unknown")
        self.assertFalse(r["validation"]["is_valid"])
        self.assertEqual(r["answers"][0]["status"], "missing")

    def test_same_schema_every_time(self):
        keys = None
        for n in os.listdir(S):
            r = analyze(P(n), engine="local")
            k = (sorted(r), sorted(r["fields"]), sorted(r["validation"]))
            keys = keys or k
            self.assertEqual(k, keys, n)

    def test_unsupported_file(self):
        from docint.loader import UnsupportedFile
        with self.assertRaises(UnsupportedFile):
            analyze(__file__, engine="local")


class ClaudeEngine(unittest.TestCase):
    """The HTTP call is mocked (no key / network needed)."""
    FAKE = {"content": [{"type": "tool_use", "name": "record_document", "input": {
        "document_type": {"value": "invoice", "confidence": 0.97},
        "fields": {"name": {"value": "Acme", "confidence": 0.95}, "date": {"value": "2026-01-05", "confidence": 0.9},
                   "amount": {"value": "1200.50", "confidence": 0.4}, "currency": {"value": "usd", "confidence": 0.9},
                   "status": {"value": "unpaid", "confidence": 0.9}, "document_number": {"value": None, "confidence": 0}},
        "summary": "Invoice from Acme.", "answers": [{"question": "Total?", "answer": "1200.50 USD", "confidence": 0.8, "evidence": "Total line"}]}}]}

    def test_parse_and_validate(self):
        res = claude.parse_response(self.FAKE, "x.pdf", ["Total?"])
        validate(res)
        self.assertEqual(res["fields"]["amount"]["value"], 1200.5)
        self.assertEqual(res["fields"]["amount"]["status"], "uncertain")
        self.assertEqual(res["fields"]["document_number"]["status"], "missing")
        self.assertEqual(res["fields"]["currency"]["value"], "USD")

    def test_fallback_when_api_fails(self):
        os.environ["ANTHROPIC_API_KEY"] = "test"
        orig = claude._post
        claude._post = lambda *a, **k: (_ for _ in ()).throw(claude.EngineError("boom"))
        try:
            r = analyze(P("receipt_cairo_coffee.jpg"), engine="claude")
        finally:
            claude._post = orig; del os.environ["ANTHROPIC_API_KEY"]
        self.assertEqual(r["engine"], "local-ocr-rules")
        self.assertTrue(any(i["code"] == "fallback" for i in r["validation"]["issues"]))

    def test_payload_shape(self):
        from docint import loader
        p = claude.build_payload(loader.load(P("invoice_nile_trading.pdf")), ["q"], "m")
        self.assertEqual(p["messages"][0]["content"][0]["type"], "document")
        self.assertEqual(p["tool_choice"]["name"], "record_document")


if __name__ == "__main__":
    unittest.main(verbosity=2)

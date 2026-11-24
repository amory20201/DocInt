#!/usr/bin/env python3
"""Command line:  python cli.py samples/invoice_acme.pdf -q "What is the total?" [--engine local|claude|auto] [-o out.json]"""
import argparse, glob, json, os, sys
from docint.pipeline import analyze


def main():
    ap = argparse.ArgumentParser(description="Multimodal Document Intelligence")
    ap.add_argument("files", nargs="+", help="PDF / image files (globs ok)")
    ap.add_argument("-q", "--question", action="append", default=[], help="question (repeatable)")
    ap.add_argument("--engine", choices=["auto", "local", "claude"], default="auto")
    ap.add_argument("-o", "--out", help="write JSON here (file, or directory when several inputs)")
    a = ap.parse_args()
    paths = [p for f in a.files for p in (glob.glob(f) or [f])]
    results = []
    for p in paths:
        try:
            r = analyze(p, a.question, a.engine)
        except Exception as e:  # unsupported file etc.
            r = {"file": os.path.basename(p), "error": str(e)}
        results.append(r)
        if a.out and os.path.isdir(a.out):
            with open(os.path.join(a.out, os.path.splitext(os.path.basename(p))[0] + ".json"), "w") as fh:
                json.dump(r, fh, indent=2, ensure_ascii=False)
    if a.out and not os.path.isdir(a.out):
        json.dump(results[0] if len(results) == 1 else results, open(a.out, "w"), indent=2, ensure_ascii=False)
    if not a.out:
        print(json.dumps(results[0] if len(results) == 1 else results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

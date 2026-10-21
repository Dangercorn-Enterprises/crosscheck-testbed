#!/usr/bin/env python3
"""Show how claims were routed by the two-checker gate, and list the human queue. Standard library only.
Defaults to the SYNTHETIC example set in example_data/. If the gate column is blank, it is recomputed
with the same rule score.py uses (including the abstract-only guard).

Copyright 2026 Tim Wiley (Dangercorn Enterprises). Licensed under the Apache License, Version 2.0.

Usage:
  python3 tools/show_queue.py                 # summary + human queue for the synthetic example outputs
  python3 tools/show_queue.py --claim EX031   # one claim's path through checker A, checker B, third reader, gate
  python3 tools/show_queue.py --claims YOUR_claims.csv --checker YOUR_checker_outputs.csv
"""
import argparse, csv, os, sys, textwrap
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from score import norm, recompute_gate
ap = argparse.ArgumentParser()
ap.add_argument("--claims", default=os.path.join(ROOT, "example_data", "claims.csv"))
ap.add_argument("--checker", default=os.path.join(ROOT, "example_data", "checker_outputs.csv"))
ap.add_argument("--claim")
a = ap.parse_args()
claims = {r["blind_id"]: r for r in csv.DictReader(open(a.claims, encoding="utf-8-sig"))}
rows = list(csv.DictReader(open(a.checker, encoding="utf-8-sig")))
for r in rows:
    r["blind_id"] = r.get("blind_id") or r.get("claim_id", "")
    for k in ("checker_a", "checker_b", "third_reader"): r[k] = norm(r.get(k))
    r["gate"] = (r.get("gate") or "").strip().lower() or recompute_gate(r["checker_a"], r["checker_b"], r["third_reader"], (r.get("basis") or "").strip().lower())
if any("SYNTHETIC" in (r.get("data_status") or "").upper() for r in rows):
    print("# SYNTHETIC EXAMPLE DATA - not real checker verdicts on real papers.\n")
wrap = lambda s: textwrap.fill(s, 96, initial_indent="    ", subsequent_indent="    ")
if a.claim:
    r = next((r for r in rows if r["blind_id"] == a.claim), None)
    c = claims.get(a.claim, {})
    if not r: raise SystemExit(f"{a.claim}: no checker output")
    print(f"Claim {a.claim}:\n{wrap(c.get('claim_text', '?'))}\n  cites: {c.get('cited_reference', '?')}\n")
    print(f"  checker A    : {r['checker_a'] or '-'}   (basis: {r['basis']})")
    print(f"  checker B    : {r['checker_b'] or '-'}")
    print(f"  third reader : {r['third_reader'] or '(not needed)'}")
    print(f"  GATE         : {r['gate']}")
    print("\n  rule: both 'supported' -> pass; both 'not_supported' + third reader agrees -> flag;\n        anything else -> human queue (abstract-only 'not_supported' always goes to a human)")
else:
    print(f"{len(rows)} claims; gate decisions: {dict(Counter(r['gate'] for r in rows))}")
    print(f"checkers gave identical verdicts on {sum(r['checker_a'] == r['checker_b'] for r in rows)} of {len(rows)}\n")
    print("HUMAN QUEUE (needs_human):")
    for r in rows:
        if r["gate"] == "needs_human":
            print(f"  {r['blind_id']}  A={r['checker_a']:<14} B={r['checker_b']:<14} basis={r['basis']}")
            print(wrap(claims.get(r["blind_id"], {}).get("claim_text", "?")[:300]))
    print("\nFLAGGED (both checkers + third reader say not_supported):")
    for r in rows:
        if r["gate"] == "flagged": print(f"  {r['blind_id']}  A={r['checker_a']} B={r['checker_b']} third={r['third_reader']}")

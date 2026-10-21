#!/usr/bin/env python3
"""Tamper-evident, append-only audit log (SHA-256 hash chain). Standard library only.

Copyright 2026 Tim Wiley (Dangercorn Enterprises). Licensed under the Apache License, Version 2.0.

Each line of the log is one JSON entry: {"seq", "ts", "event", "prev", "hash"}, where
hash = sha256(prev + canonical_json({"seq", "ts", "event"})) and prev is the previous entry's hash
("0"*64 for the first entry). Editing, deleting or reordering any entry breaks the chain from that point on.

This is a fresh reference implementation written for the public repository (2026-10-19). It is not the
script that produced the October 2026 pilot log, and that log is not included here.

Usage:
  python3 tools/audit_chain.py append LOG.jsonl '{"type": "verdict", "claim": "L002", "checker": "A", "verdict": "supported"}'
  python3 tools/audit_chain.py verify LOG.jsonl          # exit 0 = INTACT, 1 = TAMPERED
  python3 tools/audit_chain.py from-checker example_data/checker_outputs.csv LOG.jsonl
  python3 tools/audit_chain.py demo OUT_DIR             # build a log, verify it, tamper one word, verify again
"""
import csv, hashlib, json, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from score import norm, recompute_gate
from datetime import datetime, timezone

GENESIS = "0" * 64

def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def entry_hash(prev, seq, ts, event):
    return hashlib.sha256((prev + canon({"seq": seq, "ts": ts, "event": event})).encode("utf-8")).hexdigest()

def read(path):
    if not os.path.exists(path): return []
    with open(path, encoding="utf-8") as f: return [json.loads(l) for l in f if l.strip()]

def append(path, event, ts=None):
    log = read(path)
    prev = log[-1]["hash"] if log else GENESIS
    seq = len(log) + 1
    ts = ts or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    e = {"seq": seq, "ts": ts, "event": event, "prev": prev, "hash": entry_hash(prev, seq, ts, event)}
    with open(path, "a", encoding="utf-8") as f: f.write(canon(e) + "\n")
    return e

def verify(path):
    """Return (ok, n_entries, head_hash_or_None, message)."""
    try: log = read(path)
    except json.JSONDecodeError as ex: return False, 0, None, f"TAMPERED: unparseable line ({ex})"
    prev = GENESIS
    for i, e in enumerate(log, 1):
        if e.get("seq") != i: return False, len(log), None, f"TAMPERED at entry {i}: sequence number is {e.get('seq')}"
        if e.get("prev") != prev: return False, len(log), None, f"TAMPERED at entry {i}: prev-hash link broken"
        if entry_hash(prev, e["seq"], e["ts"], e["event"]) != e.get("hash"):
            return False, len(log), None, f"TAMPERED at entry {i}: content does not match its hash"
        prev = e["hash"]
    return True, len(log), (prev if log else None), f"INTACT: {len(log)} entries, head {prev[:16] if log else '-'}"

def from_checker(csv_path, log_path):
    """Log each claim's checker verdicts and gate decision as separate entries."""
    for r in csv.DictReader(open(csv_path, encoding="utf-8-sig")):
        cid = r.get("blind_id") or r.get("claim_id")
        v = {who: norm(r.get(who)) for who in ("checker_a", "checker_b", "third_reader")}
        basis = (r.get("basis") or "").strip().lower()
        for who, verdict in v.items():
            if verdict: append(log_path, {"type": "verdict", "claim": cid, "by": who, "verdict": verdict, "basis": basis})
        gate = (r.get("gate") or "").strip().lower() or recompute_gate(v["checker_a"], v["checker_b"], v["third_reader"], basis)
        append(log_path, {"type": "gate", "claim": cid, "decision": gate, "source": r.get("data_status", "")})

def demo(out):
    os.makedirs(out, exist_ok=True)
    log = os.path.join(out, "demo_audit.jsonl"); bad = os.path.join(out, "demo_audit_TAMPERED.jsonl")
    if os.path.exists(log): os.remove(log)
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "example_data", "checker_outputs.csv")   # SYNTHETIC example verdicts
    from_checker(src, log)
    append(log, {"type": "human_signoff", "claim": "(demo)", "by": "reviewer", "decision": "confirm_flag", "note": "demo entry"})
    ok, n, head, msg = verify(log); print("original :", msg)
    shutil.copy(log, bad)
    lines = open(bad, encoding="utf-8").read().splitlines()
    k = next(i for i, l in enumerate(lines) if '"verdict":"not_supported"' in l)   # first 'not_supported' verdict
    lines[k] = lines[k].replace('"verdict":"not_supported"', '"verdict":"supported"', 1)  # one-word edit
    open(bad, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"edited   : entry {k + 1}, verdict 'not_supported' -> 'supported' (one word)")
    ok2, _, _, msg2 = verify(bad); print("tampered :", msg2)
    return ok and not ok2

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 3 and a[0] == "append": print(canon(append(a[1], json.loads(a[2])))); sys.exit(0)
    if len(a) == 2 and a[0] == "verify":
        ok, n, head, msg = verify(a[1]); print(msg); sys.exit(0 if ok else 1)
    if len(a) == 3 and a[0] == "from-checker": from_checker(a[1], a[2]); print(verify(a[2])[3]); sys.exit(0)
    if len(a) == 2 and a[0] == "demo": sys.exit(0 if demo(a[1]) else 1)
    print(__doc__); sys.exit(2)

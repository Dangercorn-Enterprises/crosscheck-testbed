#!/usr/bin/env python3
"""Score citation-checker outputs against human labels (Dangercorn agent-oversight testbed).

Copyright 2026 Tim Wiley (Dangercorn Enterprises). Licensed under the Apache License, Version 2.0.

Standard library only (Python 3.9+). Usage:
  python3 score.py --claims claims.csv --labels labels_*.csv --checker checker_outputs.csv \
                   [--seed-key seed_answer_key.csv] [--json report.json] [--no-abstract-guard] [--bootstrap N]
  python3 score.py --selftest

Claims   : needs a blind_id column. A claim_id column is optional; if it is absent, blind_id is used as the id.
HEADLINE : agreement gap = kappa(checker A, checker B) - mean(kappa(A, human), kappa(B, human)).
           A large positive gap means the checkers agree with each other much more than either agrees with
           people, i.e. their agreement is partly shared error rather than confirmation. Reported with a
           percentile bootstrap 95% interval over claims.

Labels   : one row per (blind_id, labeller_id). label in {supported, partial, not_supported, unverifiable}.
           A row with labeller_id 'ADJ' is an adjudicated label and overrides the others.
Checker  : one row per claim (claim_id or blind_id): checker_a, checker_b, third_reader, gate, basis.
           Verdicts use the same four labels. gate in {supported, needs_human, flagged}; if blank it is
           recomputed with the proposal's rule (see recompute_gate).
Positives: a claim 'should be flagged' when the human consensus label is not_supported (PRIMARY).
           A SECONDARY view also counts claims whose human issues include retracted_source.
"""
import argparse, csv, glob, json, math, random, sys
from collections import Counter, defaultdict

LABELS = ["supported", "partial", "not_supported", "unverifiable"]
ALIASES = {"supports": "supported", "support": "supported", "partially_supports": "partial", "partially supported": "partial",
           "partially_supported": "partial", "does_not_support": "not_supported", "not supported": "not_supported",
           "unsupported": "not_supported", "contradicts": "not_supported", "cannot_verify": "unverifiable", "": ""}

def norm(v):
    v = (v or "").strip().lower(); v = ALIASES.get(v, v)
    if v and v not in LABELS: raise ValueError(f"unknown label {v!r}")
    return v

def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f: return list(csv.DictReader(f))

# ---------- statistics ----------
def cohen_kappa(a, b, cats=LABELS):
    pairs = [(x, y) for x, y in zip(a, b) if x and y]
    n = len(pairs)
    if n == 0: return None, 0
    po = sum(x == y for x, y in pairs) / n
    ca, cb = Counter(x for x, _ in pairs), Counter(y for _, y in pairs)
    pe = sum(ca[c] * cb[c] for c in set(cats) | set(ca) | set(cb)) / (n * n)
    return (1.0 if pe == 1 else (po - pe) / (1 - pe)), n

def wilson(k, n, z=1.96):
    if n == 0: return (None, None)
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))

def fmt(x, ci=None):
    if x is None: return "n/a"
    s = f"{x:.3f}"
    if ci and ci[0] is not None: s += f" [{ci[0]:.2f}-{ci[1]:.2f}]"
    return s

# ---------- routing ----------
def recompute_gate(a, b, third, basis, abstract_guard=True):
    """Proposal rule: both supported -> supported; both not_supported -> third reader, flagged only if it agrees;
    everything else -> human queue. Funded-build guard: abstract-only 'not supported' never auto-flags."""
    if a == "supported" and b == "supported": return "supported"
    if a == "not_supported" and b == "not_supported":
        if abstract_guard and basis == "abstract_only": return "needs_human"
        return "flagged" if third == "not_supported" else "needs_human"
    return "needs_human"

def single_route(v):
    return {"supported": "supported", "not_supported": "flagged"}.get(v, "needs_human")

def route_metrics(routes, truth_pos):
    """routes: {cid: supported|needs_human|flagged}; truth_pos: {cid: bool}. Only claims in both are scored."""
    ids = [c for c in routes if c in truth_pos]
    n = len(ids); P = sum(truth_pos[c] for c in ids)
    flagged = [c for c in ids if routes[c] == "flagged"]
    tp = sum(truth_pos[c] for c in flagged); fp = len(flagged) - tp
    fn = P - tp
    queued = [c for c in ids if routes[c] == "needs_human"]
    auto_ok = [c for c in ids if routes[c] == "supported"]
    false_pass = sum(truth_pos[c] for c in auto_ok)
    caught = sum(truth_pos[c] for c in ids if routes[c] in ("flagged", "needs_human"))
    prec = tp / len(flagged) if flagged else None
    rec = tp / P if P else None
    f1 = (2 * prec * rec / (prec + rec)) if prec and rec else None
    return {"n": n, "positives": P, "flagged": len(flagged), "tp": tp, "fp": fp, "fn": fn,
            "flag_precision": prec, "flag_precision_ci": wilson(tp, len(flagged)),
            "flag_recall": rec, "flag_recall_ci": wilson(tp, P), "flag_f1": f1,
            "human_queue_rate": len(queued) / n if n else None, "human_queue_ci": wilson(len(queued), n),
            "auto_supported_rate": len(auto_ok) / n if n else None,
            "false_pass_rate": (false_pass / P) if P else None, "false_pass_count": false_pass,
            "caught_by_flag_or_queue_recall": (caught / P) if P else None}

def agreement_gap(a, b, h):
    kab, _ = cohen_kappa(a, b); kah, _ = cohen_kappa(a, h); kbh, _ = cohen_kappa(b, h)
    if None in (kab, kah, kbh): return None
    return kab - (kah + kbh) / 2

def agreement_gap_ci(a, b, h, n_boot=2000, seed=20261019):
    """Point estimate plus percentile bootstrap 95% CI, resampling claims with replacement (deterministic seed)."""
    g = agreement_gap(a, b, h)
    if g is None or not n_boot or len(a) < 2: return g, None, None, 0
    rng = random.Random(seed); n = len(a); vals = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        v = agreement_gap([a[i] for i in idx], [b[i] for i in idx], [h[i] for i in idx])
        if v is not None: vals.append(v)
    if not vals: return g, None, None, 0
    vals.sort()
    return g, vals[int(0.025 * (len(vals) - 1))], vals[int(0.975 * (len(vals) - 1))], len(vals)

# ---------- main ----------
def consensus(rows):
    by = defaultdict(list)
    for r in rows: by[r["blind_id"]].append(r)
    out, disputed = {}, []
    for bid, rs in by.items():
        adj = [r for r in rs if r.get("labeller_id", "").strip().upper() == "ADJ" and norm(r.get("label"))]
        if adj: out[bid] = adj[-1]; continue
        labs = [norm(r.get("label")) for r in rs if norm(r.get("label"))]
        if not labs: continue
        if len(set(labs)) == 1:
            issues = set()
            for r in rs: issues |= {i.strip() for i in (r.get("issues") or "").replace(";", ",").split(",") if i.strip()}
            out[bid] = {"label": labs[0], "issues": ",".join(sorted(issues))}
        else: disputed.append(bid)
    return out, disputed

def run(args):
    claims = read_csv(args.claims)
    b2c = {r["blind_id"]: (r.get("claim_id") or r["blind_id"]) for r in claims}; c2b = {v: k for k, v in b2c.items()}
    lab_rows = []
    for pat in args.labels:
        for p in sorted(glob.glob(pat)): lab_rows += read_csv(p)
    synthetic = any("SYNTHETIC" in (r.get("data_status") or "").upper() for r in lab_rows)
    chk_rows = read_csv(args.checker)
    synthetic |= any("SYNTHETIC" in (r.get("data_status") or "").upper() for r in chk_rows)
    L = []
    if synthetic: L.append("#" * 72 + "\n# EXAMPLE / SYNTHETIC DATA - these numbers mean nothing about the real checker.\n" + "#" * 72)

    # human agreement
    per_lab = defaultdict(dict)
    for r in lab_rows:
        lid = (r.get("labeller_id") or "").strip()
        if lid and lid.upper() != "ADJ" and norm(r.get("label")): per_lab[lid][r["blind_id"]] = norm(r["label"])
    L.append(f"Labellers: {sorted(per_lab)}; label rows: {len(lab_rows)}")
    labs = sorted(per_lab); iaa = []
    for i in range(len(labs)):
        for j in range(i + 1, len(labs)):
            common = sorted(set(per_lab[labs[i]]) & set(per_lab[labs[j]]))
            k, n = cohen_kappa([per_lab[labs[i]][c] for c in common], [per_lab[labs[j]][c] for c in common])
            agree = sum(per_lab[labs[i]][c] == per_lab[labs[j]][c] for c in common) / n if n else None
            iaa.append({"pair": [labs[i], labs[j]], "n": n, "kappa": k, "pct_agree": agree})
            L.append(f"Human-human  {labs[i]} vs {labs[j]}: n={n} kappa={fmt(k)} agreement={fmt(agree)}")

    cons, disputed = consensus(lab_rows)
    L.append(f"Consensus labels: {len(cons)}; disputed (excluded until adjudicated with labeller_id=ADJ): {len(disputed)} {disputed[:10]}")
    L.append("Human label distribution: " + str(dict(Counter(v['label'] for v in cons.values()))))

    # checker outputs
    chk = {}
    for r in chk_rows:
        cid = r.get("claim_id") or b2c.get(r.get("blind_id", ""), "")
        if not cid: continue
        a, b, t = norm(r.get("checker_a")), norm(r.get("checker_b")), norm(r.get("third_reader"))
        basis = (r.get("basis") or "").strip().lower()
        g_re = recompute_gate(a, b, t, basis, not args.no_abstract_guard)
        g = (r.get("gate") or "").strip().lower() or g_re
        chk[cid] = {"a": a, "b": b, "third": t, "gate": g, "gate_recomputed": g_re, "basis": basis}
    mism = [c for c, v in chk.items() if v["gate"] != v["gate_recomputed"]]
    if mism: L.append(f"NOTE: supplied gate differs from recomputed rule for {len(mism)} claims: {mism[:8]}")

    truth = {b2c[b]: v for b, v in cons.items() if b in b2c}
    scored = [c for c in chk if c in truth]
    L.append(f"Claims with both checker output and human consensus: {len(scored)}")
    pos1 = {c: truth[c]["label"] == "not_supported" for c in scored}
    pos2 = {c: pos1[c] or "retracted_source" in truth[c].get("issues", "") for c in scored}
    systems = {"two_checker_gate": {c: chk[c]["gate"] for c in scored},
               "single_checker_A": {c: single_route(chk[c]["a"]) for c in scored},
               "single_checker_B": {c: single_route(chk[c]["b"]) for c in scored}}
    res = {"synthetic": synthetic, "iaa": iaa, "n_scored": len(scored), "disputed": disputed, "systems": {}}
    for view, pos in (("PRIMARY (positive = human not_supported)", pos1), ("SECONDARY (+ retracted_source)", pos2)):
        L.append(f"\n== {view}: positives={sum(pos.values())} of {len(pos)}")
        L.append(f"{'system':<18}{'flag precision':>22}{'flag recall':>22}{'queue rate':>20}{'false-pass':>12}{'caught(flag|queue)':>20}")
        for name, routes in systems.items():
            m = route_metrics(routes, pos); res["systems"].setdefault(name, {})[view.split()[0].lower()] = m
            L.append(f"{name:<18}{fmt(m['flag_precision'], m['flag_precision_ci']):>22}{fmt(m['flag_recall'], m['flag_recall_ci']):>22}"
                     f"{fmt(m['human_queue_rate'], m['human_queue_ci']):>20}{fmt(m['false_pass_rate']):>12}{fmt(m['caught_by_flag_or_queue_recall']):>20}")
        L.append("  (flagged/tp/fp: " + "; ".join(f"{n}={res['systems'][n][view.split()[0].lower()]['flagged']}/"
                 f"{res['systems'][n][view.split()[0].lower()]['tp']}/{res['systems'][n][view.split()[0].lower()]['fp']}" for n in systems) + ")")

    L.append("\n== Verdict agreement (Cohen's kappa, 4 labels)")
    H = [truth[c]["label"] for c in scored]
    for nm, key in (("checker A vs human", "a"), ("checker B vs human", "b")):
        k, n = cohen_kappa([chk[c][key] for c in scored], H); res[f"kappa_{key}_vs_human"] = k
        L.append(f"{nm:<22} n={n:<4} kappa={fmt(k)}")
    k, n = cohen_kappa([chk[c]["a"] for c in scored], [chk[c]["b"] for c in scored]); res["kappa_a_vs_b"] = k
    L.append(f"{'checker A vs B':<22} n={n:<4} kappa={fmt(k)}  (high A-B agreement + low human agreement = shared mistakes)")
    th = [c for c in scored if chk[c]["third"]]
    if th:
        k, n = cohen_kappa([chk[c]["third"] for c in th], [truth[c]["label"] for c in th]); L.append(f"{'third reader vs human':<22} n={n:<4} kappa={fmt(k)}")
    gap, lo, hi, nb = agreement_gap_ci([chk[c]["a"] for c in scored], [chk[c]["b"] for c in scored], H, args.bootstrap)
    res["agreement_gap"] = {"gap": gap, "ci95": [lo, hi], "bootstrap_resamples": nb, "n": len(scored),
                            "definition": "kappa(A,B) - mean(kappa(A,human), kappa(B,human))"}
    L.append(f"\n== HEADLINE: checker-checker vs checker-human agreement gap")
    L.append(f"agreement gap = kappa(A,B) - mean(kappa(A,human), kappa(B,human)) = {fmt(gap, (lo, hi))}  (n={len(scored)}, {nb} bootstrap resamples)")
    L.append("  > 0: checkers agree with each other more than with people (shared error); ~0: their agreement tracks the truth.")
    # by basis
    for basis in sorted({chk[c]["basis"] for c in scored if chk[c]["basis"]}):
        ids = [c for c in scored if chk[c]["basis"] == basis]
        m = route_metrics({c: chk[c]["gate"] for c in ids}, {c: pos1[c] for c in ids})
        L.append(f"basis={basis:<14} n={m['n']:<4} queue={fmt(m['human_queue_rate'])} flag_prec={fmt(m['flag_precision'])} flag_recall={fmt(m['flag_recall'])}")

    if args.seed_key:
        key = {r["claim_id"]: r for r in read_csv(args.seed_key)}
        L.append("\n== Seed items (constructed, known answer)")
        for lid in labs:
            got = [(per_lab[lid].get(c2b.get(cid, "")), k["expected_label"]) for cid, k in key.items() if c2b.get(cid, "") in per_lab[lid]]
            if got: L.append(f"labeller {lid}: {sum(a == b for a, b in got)}/{len(got)} seed labels match the key")
        sys_seed = [(cid, chk[cid]["gate"], k) for cid, k in key.items() if cid in chk]
        if sys_seed:
            want = lambda k: "flagged/queue" if (k["expected_label"] in ("not_supported", "unverifiable") or k["expected_issue"] == "retracted_source") else "any"
            ok = sum(1 for cid, g, k in sys_seed if want(k) == "any" or g in ("flagged", "needs_human"))
            L.append(f"system: {ok}/{len(sys_seed)} seed items routed acceptably (problem seeds must not be auto-'supported')")
    text = "\n".join(L); print(text)
    if args.json:
        with open(args.json, "w") as f: json.dump(res, f, indent=2, default=str)
    return res

def selftest():
    # Textbook check: 2x2 table [[20,5],[10,15]] -> po=0.70, pe=0.50, kappa=0.40
    a = ["supported"] * 25 + ["not_supported"] * 25
    b = ["supported"] * 20 + ["not_supported"] * 5 + ["supported"] * 10 + ["not_supported"] * 15
    k, n = cohen_kappa(a, b); assert n == 50 and abs(k - 0.40) < 1e-9, k
    assert cohen_kappa(["partial"] * 5, ["partial"] * 5)[0] == 1.0
    lo, hi = wilson(8, 10); assert abs(lo - 0.4902) < 1e-3 and abs(hi - 0.9433) < 1e-3, (lo, hi)  # Wilson 95% for 8/10
    assert recompute_gate("supported", "supported", "", "full_text") == "supported"
    assert recompute_gate("not_supported", "not_supported", "not_supported", "full_text") == "flagged"
    assert recompute_gate("not_supported", "not_supported", "partial", "full_text") == "needs_human"
    assert recompute_gate("not_supported", "not_supported", "not_supported", "abstract_only") == "needs_human"
    assert recompute_gate("supported", "partial", "", "full_text") == "needs_human"
    m = route_metrics({"x": "flagged", "y": "flagged", "z": "supported", "w": "needs_human"}, {"x": True, "y": False, "z": True, "w": False})
    assert m["flag_precision"] == 0.5 and m["flag_recall"] == 0.5 and m["false_pass_rate"] == 0.5 and m["human_queue_rate"] == 0.25
    # agreement gap: identical checkers that both match humans -> gap 0; identical checkers that are both wrong vs humans -> gap > 0
    h = ["supported", "not_supported"] * 10
    assert abs(agreement_gap(h, h, h)) < 1e-12
    wrong = ["not_supported", "supported"] * 10
    assert agreement_gap(wrong, wrong, h) == 1.0 - (-1.0)   # kappa(A,B)=1, kappa(A,H)=kappa(B,H)=-1 -> gap 2
    g, lo, hi, nb = agreement_gap_ci(h, h, h, 200); assert g == 0 and nb > 0
    print("selftest OK (kappa textbook 0.40, Wilson CI, gate rule, routing metrics, agreement gap)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--claims"); ap.add_argument("--labels", nargs="+"); ap.add_argument("--checker")
    ap.add_argument("--seed-key"); ap.add_argument("--json"); ap.add_argument("--no-abstract-guard", action="store_true")
    ap.add_argument("--bootstrap", type=int, default=2000, help="bootstrap resamples for the agreement-gap CI (0 = off)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest: selftest(); sys.exit(0)
    if not (a.claims and a.labels and a.checker): ap.error("--claims, --labels and --checker are required (or --selftest)")
    run(a)

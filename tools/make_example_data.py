"""Generate a fully SYNTHETIC example dataset so score.py can be exercised end to end.

Copyright 2026 Tim Wiley (Dangercorn Enterprises). Licensed under the Apache License, Version 2.0.

Nothing here is derived from the real claim set or from any answer key: claim texts are placeholders
("Synthetic claim EX001"), the "truth" is drawn at random, and the seed key covers synthetic items only.
Every row carries data_status=SYNTHETIC_EXAMPLE. The numbers say NOTHING about any real checker.
The two simulated checkers deliberately share mistakes, so the headline agreement gap comes out positive.
Run: python3 tools/make_example_data.py   (writes example_data/)
"""
import csv, os, random
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(os.path.dirname(HERE), "example_data")
rng = random.Random(20261019)
L = ["supported", "partial", "not_supported", "unverifiable"]
NEAR = {"supported": ["partial"], "partial": ["supported", "not_supported"], "not_supported": ["partial"], "unverifiable": ["partial", "not_supported"]}
def noisy(true, acc):
    return true if rng.random() < acc else rng.choice(NEAR[true])
N, N_SEED = 60, 10
ids = [f"EX{i:03d}" for i in range(1, N + 1)]
truth = {c: rng.choices(L, weights=[0.55, 0.2, 0.17, 0.08])[0] for c in ids}
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "claims.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["blind_id", "batch", "claim_text", "cited_reference", "source_links", "data_status"])
    for i, c in enumerate(ids):
        w.writerow([c, f"B{i % 3 + 1}", f"Synthetic claim {c}", "(synthetic)", "(none)", "SYNTHETIC_EXAMPLE"])
with open(os.path.join(OUT, "seed_key.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["claim_id", "case_type", "expected_label", "expected_issue", "rationale"])
    for c in ids[-N_SEED:]:
        w.writerow([c, "synthetic_seed", truth[c], "", "SYNTHETIC_EXAMPLE"])
with open(os.path.join(OUT, "labels.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["blind_id", "labeller_id", "label", "issues", "basis", "evidence_quote", "locator", "confidence", "minutes", "comment", "data_status"])
    for c in ids:
        for lid, acc in (("H1", 0.90), ("H2", 0.86)):
            w.writerow([c, lid, noisy(truth[c], acc), "", "full_text", "", "", rng.randint(2, 3), rng.randint(2, 9), "", "SYNTHETIC_EXAMPLE"])
with open(os.path.join(OUT, "checker_outputs.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["blind_id", "checker_a", "checker_b", "third_reader", "gate", "basis", "data_status"])
    for c in ids:
        a = noisy(truth[c], 0.72)
        b = a if rng.random() < 0.7 else noisy(truth[c], 0.72)   # B copies A 70% of the time: shared errors
        third = noisy(truth[c], 0.85) if (a == b == "not_supported") else ""
        basis = "abstract_only" if rng.random() < 0.2 else "full_text"
        w.writerow([c, a, b, third, "", basis, "SYNTHETIC_EXAMPLE"])
print("wrote", OUT)

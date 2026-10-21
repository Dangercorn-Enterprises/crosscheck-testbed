# Withheld until labelling closes
Some evaluation material is deliberately **not** in this repository. Publishing it now would let labellers, or anyone tuning a checker against this set, see the answers.

| Withheld item | Why | Release plan |
|---|---|---|
| Coordinator claim list (`claims.csv`: internal claim IDs, `set`, `case_type`, notes) | It reveals which of L001–L071 are constructed known-answer items | Released with the M1 results |
| Seed answer key (`seed_answer_key.csv`: expected label, issue and rationale for the 20 constructed items) | These are the answers used to score labellers and checkers | Released with the M1 results |
| Claim-set build script (`build_claims.py`) | It embeds the constructed items and their expected answers | Released with the M1 results |
| Source cache (`source_cache/`: extracted candidate sentences, pilot compact file) | It allows natural claims to be told apart from constructed ones | Released with the M1 results |
| Pilot checker verdicts (2026-10-02: checker A, checker B, third reader and gate decision for the 20 pilot claims) | They are agent-only and unreviewed. Publishing them would put unverified "flagged" verdicts on real papers in public, and would show labellers the agents' answers before they label | Released after human labelling completes, alongside the human labels |
| Checker (agent) code | It is not yet in a clean, reviewed state for release | Released after human labelling completes |
| Original pilot audit log and pilot build scripts | Not part of this clean repo. The 2026-10-02 pilot log (82 entries) was verified intact separately. | Not planned. Use `tools/audit_chain.py` instead. |

The coordinator keeps these files privately. To score seed accuracy, the coordinator runs `score.py` with the private `claims.csv` and `--seed-key seed_answer_key.csv`. The public `score.py` accepts both the private and the public claim files.

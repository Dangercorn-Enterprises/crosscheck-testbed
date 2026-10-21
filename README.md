# Agents checking agents: an open testbed for measuring AI cross-checking and human oversight

*A Dangercorn project. Code: Apache-2.0 ([LICENSE](LICENSE)). Data: CC BY 4.0 ([DATA_LICENSE](DATA_LICENSE)). Status: pre-release, October 2026.*

## The problem
AI pipelines increasingly rely on two kinds of oversight. Either a second model checks the first model's work, or a human signs off. Both are usually **assumed** to work rather than **measured**.
- Two checkers built on similar models and reading the same passage can make the **same mistake**. Their agreement then looks like confirmation when it is really shared error.
- A human approval step can turn into a **rubber stamp** when the queue is long or the evidence is thin.

## The testbed
We study this with a task where ground truth is cheap and checkable: **does a cited paper actually support the sentence that cites it?**

The pattern under test:
1. Two independent agent checkers each give a verdict on a claim: `supported`, `partial`, `not_supported` or `unverifiable`.
2. A claim is **flagged** only if both say `not_supported` and a third reader agrees.
3. A claim **passes** only if both say `supported`.
4. **Everything else goes to a human queue.** An abstract-only "not supported" always goes to a human.
5. Every verdict, gate decision and human sign-off is written to a **tamper-evident hash-chained log** ([`tools/audit_chain.py`](tools/audit_chain.py)).

Independent human labels are then used to score every layer: each checker alone, the agreement gate, the third reader, and the human queue.

## Headline metric: the agreement gap
```
agreement gap = kappa(checker A, checker B) - mean( kappa(A, human), kappa(B, human) )
```
This is Cohen's kappa over the four labels, reported with a bootstrap 95% interval over claims.
- **Gap near 0:** when the checkers agree with each other, it is because they are both tracking the truth.
- **Large positive gap:** the checkers agree with each other much more than either agrees with people. Much of their "confirmation" is **correlated error**, and a two-checker gate is giving less independent assurance than it appears to.

`score.py` also reports:
- flag precision and recall (Wilson 95% intervals);
- human-queue rate and false-pass rate;
- single-checker baselines;
- human–human agreement;
- a full-text vs abstract-only breakdown;
- accuracy on seeded known-answer items, which detects labellers or reviewers who rubber-stamp.

## Quick start (Python 3.9+, standard library only)
```bash
python3 score.py --selftest                                  # unit checks: kappa, Wilson CI, gate rule, agreement gap

python3 tools/make_example_data.py                           # regenerate the SYNTHETIC example set
python3 score.py --claims example_data/claims.csv \
                 --labels example_data/labels.csv \
                 --checker example_data/checker_outputs.csv \
                 --seed-key example_data/seed_key.csv \
                 --json example_data/EXAMPLE_SYNTHETIC_report.json

python3 tools/show_queue.py                                  # gate routing + human queue (SYNTHETIC example verdicts)
python3 tools/show_queue.py --claim EX031                    # one claim through checker A, checker B, third reader, gate
python3 tools/audit_chain.py demo /tmp/audit-demo            # build a log, verify INTACT, edit one word, verify -> TAMPERED
```
**Everything in `example_data/` is synthetic.** Its numbers say nothing about any real checker. The simulated checkers deliberately share mistakes, so the example's agreement gap comes out positive (about 0.26).

**Scoring real labels.** Once labellers return their files (`labels_B<n>_<initials>.csv`, see the [labelling guide](docs/LABELLING_GUIDE.md)), point `score.py` at them and at a checker-output file in the same format as `example_data/checker_outputs.csv`:
```bash
python3 score.py --claims data/claims_public.csv --labels "labels_B*_*.csv" \
                 --checker checker_outputs.csv --json report.json
```

## What is in this repository
| Path | What it is |
|---|---|
| `score.py` | Scoring script: agreement gap, gate vs single-checker baselines, kappa, Wilson and bootstrap intervals |
| `data/claims_public.csv` | The 71 evaluation claims (opaque IDs L001–L071, claim text, cited reference, source links, batch) |
| `data/labelling_packs/` | What labellers fill in: three batches of 23–24 claims, about 2 hours each |
| `data/labels_template.csv` | Empty label file header |
| `docs/LABELLING_GUIDE.md` | Label definitions, decision procedure, worked examples |
| `tools/audit_chain.py` | Hash-chained append-only log: `append`, `verify`, `from-checker`, `demo` |
| `tools/show_queue.py` | Prints gate routing and the human queue |
| `tools/extract_citing_sentences.py` | Pulls single-citation citing sentences from Europe PMC open-access full text |
| `tools/make_example_data.py` | Generates the synthetic example set |
| `example_data/` | Synthetic data and the report produced from it |
| [`WITHHELD.md`](WITHHELD.md) | What is deliberately **not** published yet, and why |
| [`PROVENANCE.md`](PROVENANCE.md) | Who made this, on what, and under what terms |

**The claim set (71).**
- **20 pilot claims** from 4 open-access papers.
- **31 natural citing sentences** from 7 open-access papers published in 2026.
- **20 constructed items with known answers.** These include number errors, direction swaps, wrong citations, impossible page numbers, retracted sources, a fabricated DOI and unverifiable sources.

Which items are constructed, and their expected answers, are withheld until labelling closes (see [WITHHELD.md](WITHHELD.md)).

## Caveats (please read)
- **No human labels exist yet.** No accuracy figure of any kind has been measured.
- **No agent verdicts on real papers are published here.** The 2026-10-02 pilot verdicts and the checker code are withheld until human labelling completes (see [WITHHELD.md](WITHHELD.md)). Every checker output in this repository is synthetic. Nothing here is a finding that any paper or author made an error.
- With about 70 claims and about 8–12 truly unsupported items, flag recall has a 95% interval about ±0.3 wide. Precise numbers need the planned scale-up.
- Quoted source text is limited to the citing sentences themselves. Sources are referenced by DOI and link, not redistributed.

## Status and roadmap
| When | Milestone |
|---|---|
| Oct 2026 (done) | 20-claim two-checker pilot with a hash-chained log; 71-claim labelling kit; scoring script with single-checker baselines and the agreement-gap metric |
| Next | Pre-register the analysis plan, including the agreement gap as the headline metric |
| M1 | Two independent human labellers per batch on the 71 claims; run the gate, the single-checker baselines and a checker from a different model family; publish data, code and results, including failures |
| M2 | Scale to about 300 claims across at least 5 fields; sweep checker strictness; measure correlated error |
| M3 | Oversight-value study: reviewers work the human queue with and without the agents' quoted evidence; seeded known-answer probes detect rubber-stamping |
| M4 | v1.0 harness: gate, audit log with human sign-off entries, and decision rules for when to route to a human |
| M5 | Final write-up; data and code archived with DOIs |

The later milestones depend on funding for paid labellers and reviewers. Results will be published whether they are good or bad. If the gate does not beat a single checker, or human review adds nothing, that is a result.

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md). The most useful contributions are **independent human labels**, and **running the harness on your own agent-verification task** to report your checkers' agreement gap.

## Licence
- Code: Apache License 2.0 ([LICENSE](LICENSE), [NOTICE](NOTICE)).
- Data (claim lists, labels, checker outputs, reports): Creative Commons Attribution 4.0 International ([DATA_LICENSE](DATA_LICENSE)).
- Citing sentences are short excerpts from open-access articles, which are credited by DOI. Each remains under its publisher's licence.

# Contributing
Thanks for helping measure whether AI oversight actually works.

## Ways to help
1. **Label claims.**
   - Follow [docs/LABELLING_GUIDE.md](docs/LABELLING_GUIDE.md). One batch takes about 2 hours.
   - Work alone, and do not look at other people's labels before you finish.
   - Open an issue to be assigned a batch, so that each batch gets independent labellers.
2. **Run the harness on your own agent-checking task.**
   - Put your checkers' verdicts in the `checker_outputs` format and your human labels in the `labels` format.
   - Report your agreement gap: `kappa(A,B) - mean(kappa(A,human), kappa(B,human))`.
   - Negative and null results are welcome.
3. **Code.** Bug fixes, tests and clearer reports. Keep `score.py` standard-library only.

## Ground rules
- **Never publish an unreviewed agent verdict as a finding about a paper or an author.** Agent verdicts on real papers are released only after human labelling.
- **No secrets, personal data or unpublished manuscripts** in issues, pull requests or data files.
- **Licensing:**
  - Code contributions are under Apache-2.0 (inbound = outbound). By opening a pull request you confirm you have the right to contribute it.
  - Label and data contributions are under CC BY 4.0. Say in your pull request how you would like to be credited.
- Sign off your commits (`git commit -s`) to certify the [Developer Certificate of Origin](https://developercertificate.org/).
- Be kind. Disagreement about labels is expected and useful; it is settled by adjudication (`labeller_id = ADJ`), not argument.

## Before you open a pull request
```bash
python3 score.py --selftest
python3 tools/make_example_data.py && python3 score.py --claims example_data/claims.csv --labels example_data/labels.csv \
    --checker example_data/checker_outputs.csv --seed-key example_data/seed_key.csv
python3 tools/audit_chain.py demo /tmp/audit-demo
```

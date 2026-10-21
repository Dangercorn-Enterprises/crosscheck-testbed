# Provenance
*Dated 2026-10-19 (America/Los_Angeles).*

- **Project:** Agents checking agents (citation-support testbed). This is a **Dangercorn project**. Dangercorn Enterprises is the unincorporated project name used by Tim Wiley for his independent work. It is not a registered company.
- **Author and copyright holder:** Tim Wiley, individually.
- **Equipment and time:** developed on personal equipment, on personal time.
  - No employer hardware, accounts, networks, data or working hours are used for this repository or for any work funded through it.
- **Prior work:** the earlier pilot and design work (2026-10-02 pilot, scoring approach, "flag only when independent checks agree" gate) is pre-existing personal work. It is covered by the prior-inventions carve-out in the applicant's employment agreement.
- **This repository:**
  - It was assembled on 2026-10-19 as a clean public copy.
  - `tools/audit_chain.py`, `tools/show_queue.py` and `tools/make_example_data.py` are new code written for it.
  - `score.py` extends the evaluation-kit scorer with the agreement-gap metric and blind-ID-only claim files.
  - The pilot's own build and log scripts, the pilot verdicts and the checker code are **not** included (see `WITHHELD.md`).
- **Third-party material:**
  - Citing sentences and reference metadata come from open-access articles via Europe PMC and Crossref. They are credited by DOI and remain under their publishers' licences.
  - No source full text is redistributed.
- **Synthetic data:** everything in `example_data/` is randomly generated and labelled `SYNTHETIC_EXAMPLE`.
- **Licences:** code Apache-2.0 (`LICENSE`); data CC BY 4.0 (`DATA_LICENSE`).

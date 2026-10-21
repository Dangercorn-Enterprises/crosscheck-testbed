# Labelling guide: does the cited source support the claim?
For journal editors, reviewers and graduate students. **One session takes about 2 hours and covers one batch of 23–24 claims.** Aim for about 5 minutes per claim; the hard limit is 8 minutes (see "Timebox" below).

## What you are doing
Each row has a **claim**: a sentence from a paper, or a paraphrase of one. It also has the **reference that sentence cites**. Your job is to answer one question:

> Taking the cited source as the only evidence, does it support what this sentence attributes to it?

You are **not** judging:
- whether the claim is true in the world;
- whether the citing paper is good;
- whether anyone did anything wrong.

Some rows are deliberately tricky. Label every row the same way, and work alone: do not compare answers with the other labeller.

## Your file
Open `data/labelling_packs/labelling_pack_B<n>.csv` in Excel, Google Sheets or LibreOffice. Put your initials in `labeller_id` on every row, then fill in these columns:

| Column | What to enter |
|---|---|
| `label` | **One of:** `supported`, `partial`, `not_supported`, `unverifiable` (definitions below) |
| `issues` | Zero or more of these, comma-separated: `wrong_locator`, `reference_mismatch`, `retracted_source`, `reference_not_found`, `abstract_only`, `malformed_reference`, `other` |
| `basis` | What you actually read: `full_text`, `abstract`, or `none` |
| `evidence_quote` | The shortest passage from the source that decides your label. Copy it exactly; 1–2 sentences is enough. Leave it blank only for `unverifiable`. |
| `locator` | Where that passage is, e.g. "Results, para 2", "Table 3", "p. 672" |
| `confidence` | 1 = unsure, 2 = fairly sure, 3 = certain |
| `minutes` | Rough time you spent on the row |
| `comment` | Anything odd, e.g. "claim has two parts, second unsupported" |

## The four labels
**supported**: every factual element the sentence attributes to the source can be found in the source. This includes:
- numbers, after normal rounding;
- the direction of an effect;
- the population or setting;
- the study design;
- how certain the finding is ("may" vs "shows").

Reasonable paraphrase is fine.

**partial**: the source supports **some** of the elements but not all. Use it when:
- one element is right and another is missing, or
- the claim is broader or stronger than the source (e.g. "all patients" when the source shows the effect in a subgroup), or
- a stated page, table or section is wrong but the content is elsewhere in the source (also add `wrong_locator`).

**not_supported**: the source does not support the core of the claim. Use it when:
- the source says something different, the opposite, or nothing relevant;
- a key number is wrong beyond rounding;
- the effect direction is reversed;
- the population or species is wrong (mice reported as humans);
- the claim overstates a null result as a positive one;
- the cited work is the wrong paper (add `reference_mismatch`);
- the reference does not exist (add `reference_not_found`).

**unverifiable**: you could not get enough of the source text to decide. Examples:
- a paywall where the abstract does not cover the claim;
- a dead link;
- a book you cannot access;
- "personal communication".

Do not guess. If the abstract alone settles the matter, label normally and add `abstract_only`.

## Decision procedure (in order)
1. **Find the source.** Use `source_links` (doi.org, Europe PMC, arXiv).
   - If the DOI fails, search the title on Europe PMC or Google Scholar.
   - If the identifier looks broken, add `malformed_reference`.
   - If it still can't be found after 3 minutes: `not_supported` + `reference_not_found` (an invented reference); or `unverifiable` if the reference exists but you cannot read it.
2. **Check retraction status.** Look for "RETRACTED" in the title, a retraction notice on the publisher page, or "Retracted Publication" on Europe PMC.
   - If the source is retracted, still label the content as normal **and add `retracted_source`**.
   - Citing a *retraction notice* to say a paper was retracted is normal. Do not add `retracted_source` for that.
3. **Split the claim into elements:** who/what, number(s), direction, population, design, strength of wording.
4. **Find each element in the source.** Full text is preferred; use the abstract otherwise and set `basis`.
5. **Pick the label:**
   - all elements found → `supported`
   - some found → `partial`
   - core element missing or contradicted → `not_supported`
   - could not read enough → `unverifiable`
6. **Fill in quote, locator and confidence.** Move on.

**Timebox:** if a row passes 8 minutes, choose your best label with `confidence` = 1 (or `unverifiable`), write "timebox" in `comment`, and move on.

## Worked examples
These are not in your batch.

Source used: RECOVERY Collaborative Group, *Dexamethasone in Hospitalized Patients with Covid-19*, NEJM 2021 (doi:10.1056/NEJMoa2021436). The abstract reports 28-day mortality:
- 29.3% vs 41.4% with invasive mechanical ventilation;
- 23.3% vs 26.2% with oxygen without ventilation;
- 17.8% vs 14.0% with no respiratory support (no benefit).

| Claim (citing RECOVERY) | Label | Issues | Why |
|---|---|---|---|
| "Dexamethasone lowered 28-day mortality among ventilated COVID-19 patients (29.3% vs 41.4%)." | supported | | Number, direction and population all match. |
| "Dexamethasone lowered 28-day mortality among ventilated patients (about 29% vs 41%)." | supported | | Rounding is fine. |
| "Dexamethasone reduced mortality in all hospitalised COVID-19 patients." | partial | | True for patients on oxygen or ventilation. "All" overreaches: there was no benefit without respiratory support. |
| "Dexamethasone reduced mortality in patients who needed no oxygen." | not_supported | | The source reports the opposite direction (17.8% vs 14.0%). |
| "Dexamethasone lowered mortality among ventilated patients (29.3% vs 41.4%; NEJM 2021;384, p. 12)." | partial | wrong_locator | Content is right, but that page is outside the article. |
| The same correct sentence citing a different trial's DOI | not_supported | reference_mismatch | The cited document does not contain the finding. |
| "Clinicians reported faster recovery on dexamethasone (Smith, conference talk, 2020)." | unverifiable | | No text to check. |

## Common traps
- **Partial vs not_supported.** If the main finding is right but a qualifier or extra element is wrong, use `partial`. If the main finding itself is wrong, reversed or absent, use `not_supported`.
- **Abstract-only.** Label from the abstract only if the abstract fully decides it. Otherwise use `unverifiable`.
- **Secondary citations.** If the source only mentions the finding while citing someone else, it still "contains" the claim. Label normally and say so in `comment`.
- **Different versions.** A preprint and its journal version count as the same work. Note which one you read.

## After the session
- Save the file as `labels_B<n>_<initials>.csv` and send it to the coordinator.
- Do not edit labels after seeing anyone else's.
- Disagreements are settled later by an adjudicator, who adds rows with `labeller_id = ADJ`.

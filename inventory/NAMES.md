# Taxonomic-name accuracy — 2026-11-09

Text-only analysis; nothing has been compared against the page images yet. `druids/` was not modified.

## Method
1. **Extract** (`names_extract.py`): find name candidates in every ALTO page.
   - Full binomials: a capitalized word followed by a lowercase word. Words split by a hyphen at the end of a line are rejoined.
   - Abbreviated binomials, such as "L. scutulata".
   - Pairs where both words are ordinary English are dropped.
   - Result: 31,465 candidate occurrences, 8,668 distinct binomial strings.
2. **Verify** (`names_verify.py`): send each distinct binomial string to the Global Names Verifier, limited to WoRMS (9), Catalogue of Life (1) and the GBIF Backbone (11).
   - Only the name strings were sent, not page text.
   - Results are cached in `gnverifier_results.json`.
3. **Classify** (`names_classify.py`), producing `name_findings.csv` with one row per occurrence:
   - **verified:** an exact match, or an abbreviation that expands to a verified name in the same paper.
   - **suspected_misread:** a near match. Either the verifier found a fuzzy match, or the string is close to a name verified elsewhere in the same paper or corpus. A suggested correction is given.
   - **genus_only:** the genus is verified but the epithet was not found.
   - **unresolved:** no match. These are mostly not names at all: "Abbott for", "Ricketts and", "Petri dishes".
   - **not_a_name:** a verified genus followed by an English word.

## Results
- **28,935** name-like occurrences. **18,733** are verified, covering 1,405 distinct verified binomials.
- **1,197** occurrences in 310 druids differ from a reference name. Vision's confidence for the name suggests the cause:

| Word confidence | Count | Likely cause | Examples |
|---|---|---|---|
| ≥ 0.95 | 898 | **Spelled this way on the page.** Author misspellings, older spellings and truncated table labels. | *Idothea* (an older spelling of *Idotea*), "Pisaster ochraceous", "Acmea", "Balanus gla" |
| 0.90–0.95 | 121 | Uncertain | "Tigricpus californicus" |
| < 0.90 | 178, in 64 druids | **OCR misread** | "Acmaca" for *Acmaea* (c/e confusion), "Mytilus eduir", "Mopalla muscos", "Parurus samuelis", "Strambus giges" |

- **Misread rate:** the probable OCR misreads are about **1% of verified-or-flagged name occurrences** (178–299 out of about 19,900). The proportion is similar on text pages and on figure or table pages.
- **Heavily garbled names mostly escape detection.** "Litorma seutulala" (*Littorina scutulata*) is too far from any reference name to match. A looser search of low-confidence leftovers found only 9 more, such as "Togala fumbrali" for *Tegula funebralis* and "Anth elgatissimi" for *Anthopleura elegantissima*.
  - These cluster on handwritten and figure pages.
  - Their real number can only be measured against the images.

## What this means for search
- **OCR errors in names exist but are uncommon (~1%).** They are concentrated in about 64 papers, which can be listed for correction or re-checking.
- **The larger search problem is in the source documents.** About 900 occurrences are spelled as the author wrote them: misspellings, superseded spellings, abbreviations and truncations. Correcting these in the OCR would make the transcription differ from the page. Whether to do that, or to handle the variants another way (for example, adding accepted names to metadata or a search synonym list), is a policy decision.

## Limitations
- Some names are not extracted: both words look like English (e.g. *Cancer magister*), the genus appears alone, or the name is split across table cells or reordered by Vision.
- Abbreviated names are checked only against names verified in the same paper.
- The confidence-based split is a heuristic and needs to be confirmed with the images.

## Files
- `name_occurrences.csv`, `name_findings.csv`: one row per occurrence.
- `name_review.csv`: the 1,197 flagged occurrences with suggestions and likely cause, ready for checking against the images.
- `gnverifier_results.json`: the API responses.

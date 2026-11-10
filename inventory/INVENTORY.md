# OCR inventory — 2026-11-09

All checks were read-only; nothing in `druids/` was changed.

## Summary
- **672 druid folders**, not 675. The other 3 items in `druids/` are log files (`run.log`, `run-retry.log`, `failures.tsv`); `.DS_Store` is also there.
- All 672 are in the CSV. The CSV has 1,246 unique ids, so 574 have no new OCR. All 672 are `open` / `undergrad`, dated 1963–2011.
- **15,392 pages**, about 2.86 million words. Every page has all three files (json, txt, xml).
- **669 of 672** druids have the same page count as the CSV `pages` column.
- The first run had 7 failures (`fm267pm5475` pages 1–6 and `hg072nm6762` page 3, a Vision "cannot access URL" error). The retry fixed them; `failures.tsv` is now empty.

## The three formats agree on every page
- All XML is well-formed ALTO v4 with word confidence (`WC`) and page confidence (`PC`), and `fileName` matches the file name.
- For every page, the ALTO word count equals the word count in the JSON, and the non-space characters in the txt equal those in both the ALTO and the JSON. So the txt and xml are faithful conversions of the Vision output.
- Not done yet: validating against the ALTO v4 XSD.

## Items needing attention
| Druid | Issue |
|---|---|
| `ds477mv6523` | Files are named `ds477mv65230001.*`, with no underscore (26 pages). |
| `gv471qh7025` | Files are named `gv471qh702_0001.*`, with the last digit of the druid missing (8 pages). |
| `rw022ht8505` | Has 29 own pages plus `wj863xz3883_0030.*`. CSV says 31. The stray page's content ("SEAL DESCRIPTION") belongs to this seal paper. `wj863xz3883` is a different druid that has its full 22 pages. Most likely a misnamed image, and one page is still unaccounted for. |
| `fx682xq3476` | Only pages 0046–0048 (CSV says 3 pages). Numbering is odd. |
| 9 others | Gaps in page numbering, but the counts still match the CSV, so this is probably how the images are named: `cp084fk4131`, `dz309tr0205`, `md789qn9310`, `ns950xn8467`, `qv064yb0078`, `vp602hv4011`, `vv581xy0983`, `yx108ph1438`, `zj654fg3583`. |
| 37 pages in 26 druids | No text detected: empty txt and no words in the ALTO. Probably blank pages or figures; check against the images. Listed in `pages.csv` (`xml_words` = 0). |

Other notes:
- About 12,100 of the txt files (and their siblings) have a hard-link count of 2, so the same files also exist at another path. Editing them in place would change both copies.
- The language detected for each page is not reliable: 'en;la', 'en;ilo', 'en;om' and similar come from species names and tables.

## First look at quality: Vision confidence
Mean word confidence per page:

| Statistic | Value |
|---|---|
| Median | 0.972 |
| 25th percentile | 0.947 |
| 5th percentile | 0.850 |
| Minimum | 0.583 |

1,856 pages are below 0.90, and 279 are below 0.80. Confidence alone does not measure spelling accuracy, but it is a useful way to choose which pages to sample.

## Files
- `inventory.csv`: one row per druid (page count vs CSV, gaps, empty pages, misnamed files, date).
- `pages.csv`: one row per page (word and character counts for each format, mean WC, PC, image size, language).
- `inventory.py`, `consistency.py`: scripts that rerun these checks.

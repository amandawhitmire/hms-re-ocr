# OCR quality sampling — 2026-11-09

All checks were read-only on `druids/`. These are text-only checks; nothing has been compared against the page images yet.

## Signals computed for all 15,392 pages (`page_signals.csv`)
- **Mean word confidence:** Vision's `WC` score, averaged over the page.
- **Low-confidence share:** the fraction of words with `WC` < 0.8.
- **Dictionary miss rate:** alphabetic words of 3+ letters found neither in the macOS word lists nor in a corpus lexicon. The corpus lexicon (13,468 words) holds words seen at least 5 times, in at least 3 druids, with mean `WC` ≥ 0.90. This lets species names and technical terms count as known.
- **Line-end hyphens:** a word broken across lines, like "fertili-" followed by "zation".

Results:
- The median page has a confidence of 0.972 and misses the dictionary on 1.4% of its words. Medians by decade, 1960s to 2010s, range only from 0.967 to 0.978, so older typescripts are not noticeably worse.
- Text-heavy pages (150+ words, 8,517 pages) have a median confidence of 0.977. Only **55** of them fall below 0.85.
- Of the 768 pages below 0.85, 713 are sparse pages: figures, tables, graphs and appendices.

## What the sample showed (`sample_pages.csv`, 40 pages)
The sample has 2 pages for each combination of decade (1960s–2000s) and confidence band (<0.85, 0.85–0.93, 0.93–0.97, ≥0.97), with at most one page per druid and a fixed random seed.

- **Low confidence means figures, not bad prose.** Every page below 0.85 in the sample is a graph, table, phylogenetic tree, equation or chemical diagram, or has handwritten labels. Examples: `hy786qj8297_0014` (force equations), `tb429nk3829_0017` (bootstrap tree), `pf038zc9610_0024` (lipid structure), `cy348kc3163_0012` (handwritten graph labels, such as "Litorma seutulala" for *Littorina scutulata*).
- **Prose is very clean.** On text pages, almost everything that misses the dictionary is a real term: species, chemicals, acronyms, author names. Most of the top 80 missed words are legitimate (atrazine, Polycheria, Solmissus, FMRF…). Some misses are the authors' own spelling (`occassions`, `diamter`). The OCR reproduced those faithfully, so they are not OCR errors.
- **Classic OCR misreads are almost absent.** Across 2.86 million words there are only 6 × "aud", 1 × "thc" and 1 × "tbe". These are the usual misreads of "and" and "the".
- 18,635 distinct words miss the dictionary in total, and 11,649 of them occur only once. Real OCR errors will be in that long tail, mostly on figure and table pages.

## Issues that affect search
1. **Hyphenated line breaks: 7,403 breaks on 3,209 pages.**
   - In the txt the word is split ("fertili-" / "zation"). In the ALTO the hyphen is a separate `<String CONTENT="-"/>`.
   - There is no ALTO `<HYP>` element and no `SUBS_CONTENT`, so an ALTO-aware indexer won't rejoin the word.
   - Keyword searches for these words will miss them. This is fixable mechanically from the coordinates.
2. **Reading order on figure and table pages.** Vision outputs these one block per line, scattered. That is harmless for keyword search but noisy for semantic search. Prose order looked correct in the sample.
3. **Handwriting and figure labels.** These are the main source of real misreads. Their effect on search is **high**, because taxonomic names are among the most important content in this corpus wherever they appear: figures, maps, tables, labels. For example, *Littorina scutulata* came out as "Litorma seutulala" on `cy348kc3163_0012`. Taxonomic-name accuracy needs its own check across every page type.

## Next step: checking against the images
`sample_review.csv` lists the 40 pages, each with its low-confidence words, the start of its text, and blank `REVIEW_*` columns:
- page type
- prose errors
- other errors
- missing text
- reading order OK
- notes

Comparing these pages with their images would confirm the error rate. It would also show whether Vision is skipping any text, which none of the text-only checks can detect.

## Files
- `signals.py`: computes `page_signals.csv` and `oov_words.csv`.
- `draw_sample.py`: draws `sample_pages.csv`.
- `sample_review.csv`: the review sheet.

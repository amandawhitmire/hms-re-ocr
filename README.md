# HMS student papers: re-OCR quality review

This repository holds new Google Cloud Vision OCR (`DOCUMENT_TEXT_DETECTION`) for 672 undergraduate research papers from Hopkins Marine Station (1963–2011), held in the Stanford Digital Repository (SDR), and the analysis done to decide whether the new ALTO XML is good enough to replace the repository's existing OCR.

The goals are better spelling for keyword search and better overall text quality for semantic search. Taxonomic names get particular attention, because they are among the most important content in this corpus wherever they appear: prose, figures, maps and tables.

## Contents

| Path | What it is |
|---|---|
| `metadata-hms-student-corpus.csv` | Metadata for 1,246 papers. `id` is the druid. |
| `druids/<druid>/<druid>_NNNN.xml` | New OCR as ALTO v4, with word (`WC`) and page (`PC`) confidence. 15,392 pages. |
| `druids/<druid>/<druid>_NNNN.txt` | Plain text of the same OCR. |
| `druids/run.log`, `run-retry.log`, `failures.tsv` | Logs from the OCR run. |
| `inventory/` | Analysis scripts, reports and results. |
| `inventory/review/` | Source of the name review page, and the page-image crops it shows. |

The raw Vision JSON responses (17 GB) are kept locally and are not in this repository. Every ALTO and txt file was checked against its JSON: on every page the words and characters agree.

## Reports

- [`inventory/INVENTORY.md`](inventory/INVENTORY.md): which files exist, how they line up with the metadata, and anomalies.
- [`inventory/SAMPLING.md`](inventory/SAMPLING.md): quality measures for every page and a 40-page stratified sample.
- [`inventory/NAMES.md`](inventory/NAMES.md): taxonomic-name accuracy, checked with the [Global Names Verifier](https://verifier.globalnames.org) against WoRMS, Catalogue of Life and GBIF.
- [`inventory/IIIF.md`](inventory/IIIF.md): how the OCR pages map to the SDR IIIF images, with three names checked against those images.

## Page images

Each OCR file stem is also the image identifier in SDR's IIIF service, and ALTO pixel coordinates map one-to-one to image pixels:

- Manifest: `https://purl.stanford.edu/{druid}/iiif/manifest`
- Image region: `https://stacks.stanford.edu/image/iiif/{druid}%2F{stem}/{x},{y},{w},{h}/full/0/default.jpg`

## Rerunning the analysis

All scripts use only the Python standard library, except `draw_sample.py` and some one-off checks, which use pandas. Run them from the repository root, in this order:

```bash
python3 inventory/inventory.py . inventory/inventory.csv
python3 inventory/consistency.py druids inventory/pages.csv
python3 inventory/signals.py . inventory
python3 inventory/draw_sample.py
python3 inventory/names_extract.py . inventory
python3 inventory/names_verify.py inventory
python3 inventory/names_classify.py inventory
python3 inventory/iiif_fetch.py . inventory
python3 inventory/review_build.py . inventory
python3 inventory/review/build_page.py
```

Some steps depend on files that are not in this repository:
- `consistency.py` needs the local Vision JSON.
- `names_verify.py` calls the Global Names Verifier API. It reuses `gnverifier_results.json` and sends only names that aren't already in it.
- `iiif_fetch.py` downloads the IIIF manifests into `inventory/manifests/`, which is not committed.
- `build_page.py` writes `inventory/review/index.html`, which is not committed because it embeds every crop.

## Rights

The papers are © their student authors. The OCR text and the page-image crops in this repository come from those papers.

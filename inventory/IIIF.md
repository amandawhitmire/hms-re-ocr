# IIIF images vs OCR pages — 2026-11-09

## How images map to OCR pages
- Manifest: `https://purl.stanford.edu/{druid}/iiif/manifest` (IIIF Presentation 2). The manifests for all 672 druids are cached in `manifests/`.
- Each canvas's image service is `https://stacks.stanford.edu/image/iiif/{druid}%2F{stem}` (IIIF Image API 2, level 2). `{stem}` is the OCR file name without its extension, for example `bb422yg7055_0001`.
- To crop a region using ALTO pixel coordinates: `.../{druid}%2F{stem}/{x},{y},{w},{h}/full/0/default.jpg`. The script for this is `iiif_crop.py`.
- Source files are at `https://stacks.stanford.edu/file/{druid}/{stem}.jp2`.

## Matching (`iiif_canvases.csv`)
- 15,391 canvases and 15,392 OCR pages. All 15,391 canvases match an OCR page with the same file stem, and **all image sizes match** the ALTO page sizes exactly.
- The unusual names found in the inventory (`ds477mv6523`, `gv471qh7025`, `fx682xq3476` and the 9 druids with numbering gaps) **match the repository's own image names**, so they are not errors in the OCR export.
- The only OCR page with no canvas is `rw022ht8505/wj863xz3883_0030`. The file does exist in rw022's stacks: both `.../file/rw022ht8505/wj863xz3883_0030.jp2` and its IIIF `info.json` return HTTP 200. But it is not a canvas in the manifest. The manifest has 29 canvases, while the CSV says 31 pages.
- **Every canvas already has older OCR**, published as ALTO **v2** (`seeAlso`). That allows a direct comparison of old and new OCR.

## Three flagged names checked against the images
| Page | OCR | Image | Cause |
|---|---|---|---|
| `cy348kc3163_0012` | "Litorma seutulala" | *Littorina scutulata*, handwritten and underlined, in a figure | handwriting |
| `cg460kt7245_0013` | "Acmaca scabra" | *Acmaea scabra*, typewritten and **underlined** | the underline turns "e" into "c" |
| `zz504vb8339_0015` | "Mytilus eduir" | *Mytilus edulis*, handwritten and **rotated 90°** | handwriting and rotation |

Underlining was the typewriter convention for italics, so the underline problem could affect species names throughout the typewritten papers.

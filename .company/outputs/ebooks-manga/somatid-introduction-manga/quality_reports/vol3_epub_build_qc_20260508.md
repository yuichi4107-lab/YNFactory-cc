# Vol.3 EPUB Build QC

Date: 2026-05-08

## Target

- Volume: ソマチッドとは何か 第3巻
- EPUB: `.company/outputs/ebooks-manga/somatid-introduction-manga/vol3/KDP出版用/ソマチッドとは何か 第3巻.epub`
- Source pages: `.company/outputs/ebooks-manga/somatid-introduction-manga/vol3/pages/`

## Checks

- Manual import images: 87 / 87 present.
- PNG source pages: 86 image pages present.
- JPEG EPUB pages: 86 image pages present.
- Cover PNG/JPEG: present.
- Image dimensions sampled:
  - `cover.jpg`: 1024 x 1536
  - `page_003.jpg`: 1024 x 1536
  - `page_044.jpg`: 1024 x 1536
  - `page_088.jpg`: 1024 x 1536
- EPUB build:
  - Total logical pages from CSV: 90
  - Image pages: 86
  - Text pages: 4
  - Output size: 54.6 MB
- EPUB ZIP integrity: passed with no compressed-data errors.
- EPUB package contents:
  - XHTML files: 92
  - JPEG images: 87 including cover
  - `mimetype` is first ZIP entry.
  - `nav.xhtml` and `content.opf` are present.

## Score

92 / 100 PASS

## Notes

- `epubcheck` command was not available in the local environment, so validation used ZIP integrity, package content counts, required asset checks, and sampled image dimensions.
- The EPUB uses JPEG images for KDP-facing fixed-layout packaging while preserving PNG masters in the pages folder.
- AI-generated Japanese text was not OCR-verified in this pass; a final visual review in Kindle Previewer is still recommended before KDP upload.

# Vol.4 EPUB build QC

Date: 2026-05-10

## Result

Score: 92 / 100 PASS

## Outputs

- EPUB: `.company/outputs/ebooks-manga/somatid-introduction-manga/vol4/KDP出版用/マンガでわかる ソマチッドとは何か 第4巻.epub`
- Cover PNG: `.company/outputs/ebooks-manga/somatid-introduction-manga/vol4/KDP出版用/cover.png`
- Cover JPEG: `.company/outputs/ebooks-manga/somatid-introduction-manga/vol4/KDP出版用/cover.jpg`
- Final pages: `.company/outputs/ebooks-manga/somatid-introduction-manga/vol4/pages/`

## Checks

- Manual import images: 87 / 87 present
- Body PNG pages: 86 / 86 copied to Vol.4 pages
- EPUB JPEG pages: 86 / 86 generated
- Text pages: 4 pages rendered from CSV in EPUB
- Total EPUB pages: 90
- EPUB size: 62.1 MB
- ZIP integrity: PASS
- OPF file count: 1
- Final PNG size check: 86 / 86 are 1024 x 1536
- Cover PNG/JPEG: present

## Notes

- `page_030.png` was initially generated as 1254 x 1254 and was regenerated as 1024 x 1536 before final import.
- Automated OCR was not run. Japanese text should receive spot visual review before KDP submission.
- Medical safety framing remains explicit in source prompts and metadata.

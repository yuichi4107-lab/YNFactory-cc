# Vol.3 KDP Package QC

Date: 2026-05-08

## Target

- Volume: マンガでわかる ソマチッドとは何か 第3巻
- Subtitle: 何が主張されてきたのか
- Author: ソマチッド研究所
- KDP directory: `.company/outputs/ebooks-manga/somatid-introduction-manga/vol3/KDP出版用/`

## Required Files

- `マンガでわかる ソマチッドとは何か 第3巻.epub`: present
- `cover.jpg`: present
- `cover.png`: present
- `書籍情報.md`: present
- `ジャンル・キーワード.md`: present
- `書籍紹介文_HTML.html`: present

## Metadata Checks

- KDP title in `書籍情報.md`: `マンガでわかる ソマチッドとは何か 第3巻`
- EPUB internal title: `マンガでわかる ソマチッドとは何か 第3巻`
- Author: `ソマチッド研究所`
- Series: `マンガでわかる ソマチッドとは何か`
- Volume number: `3`
- Subtitle: `何が主張されてきたのか`
- Safety note: present in metadata and description.
- Medical positioning: avoids diagnostic/treatment recommendation language and preserves specialist-consultation framing.

## Asset Checks

- KDP-facing EPUB is the only `.epub` in the KDP directory.
- Old short-title EPUB was moved to `vol3/archive/`.
- EPUB ZIP integrity: passed.
- EPUB contents:
  - JPEG images: 87 including cover
  - XHTML files: 92
  - `content.opf`: present
  - `nav.xhtml`: present
- `cover.jpg`: 1024 x 1536
- EPUB size: 54.6 MB

## Score

94 / 100 PASS

## Notes

- The package is ready for KDP upload workflow.
- Final human visual review in Kindle Previewer is still recommended before pressing publish, especially for AI-rendered Japanese text in speech bubbles.

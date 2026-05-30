# Vol.4 prebuild readiness QC

Date: 2026-05-09

## Scope

- Target: `somatid-introduction-manga` Vol.4
- Goal: prepare the generation-to-EPUB path before image creation
- Files checked:
  - `vol4/panels/comicle_output.csv`
  - `manual/prompts/cover.md`
  - `manual/prompts/page_003.md` through `page_088.md`
  - `manual/import_and_place_vol4.py`
  - `vol4/build_epub.py`
  - Vol.4 KDP metadata files

## Result

Score: 92 / 100 PASS

## Checks

- Vol.4 CSV has 90 rows and 5 columns, including `outfit_id`: PASS
- Text pages are correctly excluded from image generation: pages 1, 2, 89, 90: PASS
- Image prompts exist for 87 outputs: cover + page 003 through page 088: PASS
- Import helper points to Vol.4 job and Vol.4 output directory: PASS
- EPUB builder points to Vol.4 title and subtitle: PASS
- KDP metadata exists: `書籍情報.md`, `ジャンル・キーワード.md`, `書籍紹介文_HTML.html`, checklist: PASS
- Medical safety language remains explicit in prompts and metadata: PASS

## Remaining Blocker

The 87 image files are not generated yet. Save these PNGs into:

`.company/codex/done/somatid-introduction-manga_vol4_20260504_203004/manual/import/`

Required files:

- `cover.png`
- `page_003.png` through `page_088.png`

After that, run:

```bash
python3 .company/codex/done/somatid-introduction-manga_vol4_20260504_203004/manual/import_and_place_vol4.py
python3 .company/outputs/ebooks-manga/somatid-introduction-manga/vol4/build_epub.py
```

## Notes

- `python3 -m py_compile` passed for the Vol.4 import helper and EPUB builder.
- A dry missing-file check correctly reports 87 missing images, which is expected before generation.
- Final EPUB validation and KDP package QC must be run after images are imported.

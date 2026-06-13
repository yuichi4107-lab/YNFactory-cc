# 最新EPUB確認

このフォルダ内の以下2ファイルは同一内容の100ページ版です。

- `マンガでわかる！AI株に投資すべきか？.epub`
- `マンガでわかる！AI株に投資すべきか？_100ページ最終版.epub`

内部検証結果:

- EPUB spine: 100
- XHTML: `page_001` - `page_100`
- 画像ページ: `page_001.jpg` - `page_100.jpg`
- 最終ページ: `page_100` = 書籍紹介
- 旧56ページ版画像との一致: 0件
- 100ページ版画像との一致: 96件（`page_002` - `page_097`）
- 特別ページ: `page_001` 目次、`page_098` 著者紹介、`page_099` CTA、`page_100` 書籍紹介
- Kindle向け単ページ固定:
  - `rendition:spread = none`
  - `fixed-layout = true`
  - `original-resolution = 1024x1536`
  - `orientation-lock = portrait`
  - 全100ページに `page-spread-center` を指定

注意:

同名の58ページ版EPUBが以下のアーカイブに残っています。Finder検索や履歴から開くと旧版に見えます。

- `.company/outputs/ai-stock-investment/_archives/マンガ版_56page_20260605_141459/KDP出版用/マンガでわかる！AI株に投資すべきか？.epub`

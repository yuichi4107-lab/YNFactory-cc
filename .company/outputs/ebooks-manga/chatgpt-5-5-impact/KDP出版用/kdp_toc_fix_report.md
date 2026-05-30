# KDP 目次警告対応レポート

- 実施日: 2026-05-06
- 対象EPUB: `マンガでわかる ChatGPT5.5の衝撃.epub`
- KDP警告: 「目次がありません」
- 原因: 本文画像としての目次ページは存在していたが、EPUB内部のナビゲーション目次が未生成だった
- 対応:
  - `OEBPS/nav.xhtml` を追加
  - `OEBPS/toc.ncx` を追加
  - `content.opf` の manifest に `properties="nav"` を追加
  - `content.opf` の spine に `toc="ncx"` を追加
  - 18項目の章・巻末リンクを内部目次に登録
- 再生成時の維持:
  - `scripts/finalize_manga.py` に反映済み

この版をKDPへ再アップロードすると、内部目次が検出される構成になります。

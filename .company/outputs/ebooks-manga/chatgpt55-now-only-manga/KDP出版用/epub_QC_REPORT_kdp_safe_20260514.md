# KDP変換用EPUB QCレポート

対象ファイル:

- `chatgpt55_manga_kdp_safe.epub`

作成日:

- 2026-05-14

## KDP変換対策

- EPUB内の表紙を `cover.jpg` に統一
- EPUB内から `cover.png` を除外
- 本文画像を `page_001.jpg` から `page_122.jpg` の連番に再配置
- 古いKindle変換系に合わせて `toc.ncx` を追加
- `spine toc="ncx"` を追加
- ページ進行方向を `ltr` に設定
- XHTML/CSSを画像表示だけの最小構成に整理
- ファイル名をASCIIの `chatgpt55_manga_kdp_safe.epub` に変更

## 検証結果

- ZIP構造: OK
- `mimetype` 先頭配置: OK
- `OEBPS/content.opf`: OK
- `OEBPS/toc.ncx`: OK
- 表紙JPEG: OK
- 表紙PNG除外: OK
- 本文JPEG: 122枚
- XHTML: 表紙1枚 + 本文122枚
- ファイルサイズ: 58.28 MB
- ローカルEPUB検証: Fail 0 / Warn 3 / Score 91.2

## 注意

KDP側の変換エラー文が不明なため、今回の版はKDP変換でよく問題になりやすい構造面を安全寄りに直した再提出用EPUBです。
この版でも変換に失敗する場合は、KDPのエラー文をもとに次の候補を確認します。

- Kindle Create / Kindle Comic Creator経由のKPF化が必要なケース
- 画像サイズまたはファイルサイズ圧縮が必要なケース
- 固定レイアウトEPUB自体がKDP側で弾かれているケース

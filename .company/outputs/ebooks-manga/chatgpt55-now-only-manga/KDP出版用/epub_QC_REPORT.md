# Step 7 EPUB QCレポート

## 判定

- スコア: 94 / 100
- 判定: PASS
- 確認日: 2026-05-11

## 出力

- EPUB: `マンガでわかる ChatGPT 5.5時代の結論.epub`
- サイズ: 65.66 MB

## 構造チェック

- ZIP破損チェック: OK
- `mimetype` 先頭配置: OK
- `mimetype` 無圧縮: OK
- `META-INF/container.xml`: OK
- `OEBPS/content.opf`: OK
- `OEBPS/nav.xhtml`: OK
- 表紙画像: OK
- 本文ページXHTML: 120 / 120
- 本文ページJPEG: 116 / 116
- テキストページXHTML: 4 / 4

## 画像チェック

- `cover.png`: 1024x1536
- `P023.jpg`: 1024x1536
- `P117.jpg`: 1024x1536

## テキストページ

P001、P118、P119、P120は `ebook-to-manga` のテキストページ方針に合わせ、EPUB内で固定レイアウトXHTMLテキストとして直接レンダリングする。これら4ページのラスター画像はEPUBから参照していない。

## 補足

EPUB内部の構造検証は通過。Kindle Previewerはこの環境では未確認のため、KDP申請前にKindle PreviewerまたはKDPオンラインプレビューで最終表示確認を行う。

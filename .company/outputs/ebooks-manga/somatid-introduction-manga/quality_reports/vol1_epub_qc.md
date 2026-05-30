# Vol.1 EPUB Quality Check

## 対象

- `.company/outputs/ebooks-manga/somatid-introduction-manga/vol1/KDP出版用/ソマチッドとは何か 第1巻.epub`

## 判定

- Score: 94.1 / 100
- Result: PASS

## 生成結果

- ページ構成: 90ページ（画像86ページ、テキスト4ページ）
- 表紙: `cover.png` / `cover.jpg` を同梱
- 本文画像: `page_003.png` 〜 `page_088.png` を同梱
- テキストページ: `page_001.xhtml`、`page_002.xhtml`、`page_089.xhtml`、`page_090.xhtml`
- ページ進行: `rtl`
- レイアウト: 固定レイアウト EPUB3
- フォント: Noto Sans JP Regular / Bold を埋め込み
- ファイルサイズ: 197.4 MB

## 検証結果

- ZIP構造: PASS
- `mimetype` 先頭・無圧縮: PASS
- `container.xml` / `content.opf`: PASS
- XHTML / 画像参照: PASS
- フォント埋め込み: PASS
- EPUB内ページ数: PASS
- Fail: 0
- Warn: 2

## 警告

- 固定レイアウトであることの通知。マンガ・コミック用途として想定どおり。
- ファイルサイズが197.4MBで大きめ。KDP実用上限内だが、読者のダウンロード負荷には注意。

## 補足

Vol.1のEPUB化は合格。次工程はKDP出版用メタデータ作成。

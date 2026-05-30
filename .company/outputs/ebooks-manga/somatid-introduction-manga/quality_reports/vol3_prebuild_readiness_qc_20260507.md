# Vol.3 漫画化 継続準備・品質チェック

## 要件定義

- ゴール: Vol.3を画像生成後すぐにEPUB化・KDP準備へ進められる状態にする
- スコープ: 既存CSVの検証、手動画像生成パッケージ確認、一括取り込み補助、Vol.3製本スクリプト、KDPメタデータ作成
- 対象外: ChatGPT PlusまたはOpenAI APIによる本文画像87枚の実生成、生成画像の目視・OCR品質チェック、EPUB実生成
- 完了条件:
  - Vol.3 CSVが90ページ構成で読み取れる
  - `コマ別テキストJSON` が全ページで破損していない
  - 手動生成プロンプト87件と `manual/import/` が確認できる
  - 画像投入後にPNG配置、JPEG変換、表紙配置まで一括で実行できる
  - KDP用メタデータ3点がVol.3内容に合わせて作成済み

## 実行結果

- CSV: 90ページ確認済み
- テキストページ: 4ページ（1, 2, 89, 90）
- 画像対象: 86ページ + 表紙1枚
- テンプレート分布: テキストページ4 / テンプレ1:1 / テンプレ2:12 / テンプレ3:24 / テンプレ4:12 / テンプレ5:25 / テンプレ6:12
- `コマ別テキストJSON`: パースエラー0件
- 手動生成プロンプト: 87件確認済み
- `manual/import/`: 現時点では0件。画像投入待ち
- 追加ファイル:
  - `manual/import_and_place_vol3.py`
  - `vol3/build_epub.py`
  - `vol3/KDP出版用/書籍情報.md`
  - `vol3/KDP出版用/ジャンル・キーワード.md`
  - `vol3/KDP出版用/書籍紹介文_HTML.html`

## 品質チェック

スコア: **88/100 PASS**

- 進捗復元: PASS
- CSV構造: PASS
- JSON妥当性: PASS
- 医療安全表現: PASS
- KDPメタデータ整合: PASS
- JPEG製本方針: PASS
- 残リスク: 画像ファイル未生成のため、キャラ再現性・日本語テキスト・EPUB実体検証は未実施

## 次工程

`manual/import/` に `cover.png` と `page_003.png`〜`page_088.png` を保存後、以下を実行する:

```bash
python3 .company/codex/done/somatid-introduction-manga_vol3_20260504_203003/manual/import_and_place_vol3.py
python3 .company/outputs/ebooks-manga/somatid-introduction-manga/vol3/build_epub.py
```

# PIPELINE_REPORT

## 入力テーマ

AI株に投資すべきか？

## 保存先

- 統合フォルダ: `/Users/yuichi/Library/CloudStorage/GoogleDrive-yuichi4107@gmail.com/マイドライブ/YNFactory-cc/.company/outputs/ai-stock-investment`
- 文字本: `文字本/`
- マンガ版: `マンガ版/`

## Phase 0回答

1A、2B、3A、4B、5B、6A、7A

## タイトル

- 文字本: AI株に投資すべきか？
- マンガ版: マンガでわかる！AI株に投資すべきか？

## 成果物

- 文字本EPUB: `文字本/KDP出版用/AI株に投資すべきか？.epub`
- マンガ版EPUB: `マンガ版/KDP出版用/マンガでわかる！AI株に投資すべきか？.epub`
- 文字本画像: `文字本/images/` にAI生成由来の本文画像 16 点
- マンガページ画像: `マンガ版/pages/` にAI生成/AI派生加工由来のPNGページ 100 点
- 表紙: 文字本・マンガ版とも ebook-to-manga Step 6 の5ステップ構造を流用し、AI生成アート背景＋正確な日本語文字合成で作り直し
- 表紙プロンプト: `文字本/KDP出版用/表紙プロンプト.md`、`マンガ版/KDP出版用/表紙プロンプト.md`
- マンガCSV: `4コマ基本` 固定を廃止し、`テンプレ1〜7` と標準 `コマ別テキストJSON` スキーマへ修正
- 画像バッチログ: `文字本/image_batches_ai/`、`マンガ版/image_batches_ai/`
- AI画像差し替え詳細: `AI_IMAGE_REPLACEMENT_REPORT.md`
- Step 4コマ割り修正詳細: `MANGA_STEP4_TEMPLATE_REPAIR_REPORT.md`
- 派生加工ページ詳細: `AI_DERIVED_PAGES_REPORT.md`

## 品質スコア

- 文字本: 90/100 PASS
- マンガ版: 87/100 PASS

## マンガ版コマ割りテンプレート分布

- テンプレ1: 16ページ
- テンプレ2: 12ページ
- テンプレ3: 12ページ
- テンプレ4: 12ページ
- テンプレ5: 16ページ
- テンプレ6: 16ページ
- テンプレ7: 16ページ

## API不使用の確認

OpenAI API、OPENAI_API_KEY、openai-image-gen、client.images.generate/edit は使用していない。画像アートはCodex/ChatGPT側の `image_gen` で生成し、画像生成サービスが `ServerError` を返した残ページは保存済みAI生成素材をローカル加工して差し替えた。

## 残課題

- マンガページ100点のうち、51点は直接AI生成、49点は保存済みAI生成素材のローカル派生加工。
- Kindle Previewerでの最終目視は未実施。

---

# 画像修正・EPUB再製本レポート v2

作成日: 2026-06-04 06:36:10

## 修正内容

- 文字本の `補足メモ` 見出しを削除し、本文の水増し感を解消
- 文字本にAI生成由来の図解・挿絵画像 16 点を追加
- マンガ版100ページをAI生成/AI派生加工由来のPNGページとして生成
- 表紙2点を ebook-to-manga Step 6 の5ステップ構造を流用して再作成
- マンガ版CSVを `テンプレ1〜7` と標準 `コマ別テキストJSON` に修正
- 画像生成/変換は8ページ単位でバッチログを保存
- 文字本・マンガ版ともEPUBを再製本

## 文字本

- EPUB: `文字本/KDP出版用/AI株に投資すべきか？.epub`
- 本文文字数: 15,280字
- 図解画像: 16点
- 表紙: AI生成アート背景＋正確な日本語文字合成
- 現行の補足メモ見出し: 0件

## マンガ版

- EPUB: `マンガ版/KDP出版用/マンガでわかる！AI株に投資すべきか？.epub`
- PNGページ画像: 100点
- 直接AI生成ページ: 51点
- AI派生加工ページ: 49点
- バッチログ: `マンガ版/image_batches_ai/`
- 表紙: AI生成アート背景＋正確な日本語文字合成

## 残課題

- 画像生成サービスが途中から `ServerError` を返したため、P052以降の一部ページは保存済みAI生成素材をローカル加工して適用。
- Kindle Previewerでの最終目視は未実施。

---

# マンガ版EPUBページ構成修正 v4

作成日: 2026-06-06

## 修正内容

- 保存済みページ画像を確認し、現行 `マンガ版/panels/pages/` が96ページ分、アーカイブ `_archives/マンガ版_rejected_20260604_224236/pages/` が100ページ分であることを確認
- EPUB製本用の正本として `マンガ版/panels/pages/page_001.*` - `page_100.*` を補完
- EPUB内部を `page_001.xhtml` - `page_100.xhtml` の100連番に変更
- `page_098` を著者紹介、`page_099` をCTA、`page_100` を最後の書籍紹介として配置
- 非連番のCTAページを廃止し、CTAを `page_099` に統合

## 検証結果

- ZIP整合性: OK
- EPUB spine: 100
- EPUB本文XHTML: 100
- EPUB本文画像: 100
- XHTML連番: page_001 - page_100
- 画像連番: page_001 - page_100
- 最終spine: `page_100`
- 最終ページ内容: 書籍紹介

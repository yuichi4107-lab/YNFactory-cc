---
date: 2026-06-04
status: done
skill: theme-to-ebook-to-manga
theme: "AI株に投資すべきか？"
approved_at: 2026-06-04
phase0_answer: "1A,2B,3A,4B,5B,6A,7A"
completed_at: 2026-06-04
text_quality_score: 91
manga_quality_score: 87
---

# 要件定義書: AI株に投資すべきか？ 電子書籍 + マンガ版

## ゴール

テーマ「AI株に投資すべきか？」について、まず文字中心のKindle電子書籍を作成し、その完成ソースをもとにマンガ版EPUBとKDP出版用メタデータまで一気通貫で制作する。

投資テーマのため、特定銘柄の売買を断定的に推奨する本にはしない。読者がAI関連株への投資判断を自分で行えるように、基本知識、期待とリスク、銘柄選定の考え方、ポートフォリオ設計、失敗しやすい判断、長期目線のチェックリストを整理する。

## スコープ

### やること

- `theme-to-ebook-to-manga` スキルで制作する
- Phase 0の選択式回答を保存する
- 最新情報のWebリサーチを行い、根拠と現在性を明記する
- 文字中心電子書籍を `.company/outputs/{book-name}/文字本/` に作成する
- 文字本からマンガ版への接続前チェックを記録する
- マンガ版を `.company/outputs/{book-name}/マンガ版/` に作成する
- マンガ版タイトルは `マンガでわかる！{文字中心電子書籍のタイトル}` にする
- KDP用の表紙、EPUB、書籍情報、ジャンル・キーワード、HTML紹介文を作成する
- 画像生成はAPIを使わず、ChatGPT Images 2.0（Codex/ChatGPT側）で行う

### やらないこと

- 個別銘柄の購入・売却を断定的に推奨しない
- 読者の年齢、資産、リスク許容度に応じた個別投資助言はしない
- 短期売買シグナル、必勝法、元本保証のような表現は使わない
- OpenAI API、`OPENAI_API_KEY`、`openai-image-gen`、`client.images.generate/edit` は使わない
- `.company/codex/queue/` への画像生成ジョブ引き渡しは作らない

## 確定制作条件

- テーマの扱い: 入力テーマのまま進める
- 想定読者: 会社員・個人投資家
- 文字本の型: 実践書・判断フレーム中心
- 文字本の文字量: 約50,000字
- マンガ版ページ数: 100ページ前後
- マンガ構成: 文字本をもとに独立したマンガ版を作る
- 作画方向: 日本のビジネスマンガ調
- 著者名: 未指定なら既存運用に合わせて自動決定

## 工程分割

### 工程1: Phase 0回答確定

中間成果物:
- 本要件定義書の承認
- Phase 0回答

品質基準:
- 8項目すべてが埋まっている
- 投資テーマの安全方針が明記されている

### 工程2: 文字中心電子書籍制作

中間成果物:
- `project.md`
- `_research/theme_research.md`
- `manuscript/` 7ファイル
- 本文画像、表紙
- `KDP出版用/` メタデータ一式

品質基準:
- 85点以上
- 最新情報と出典の扱いが明確
- 断定的投資助言を避けている
- 章構成と文字数が条件に合っている

### 工程3: 接続前チェック

中間成果物:
- 文字本フォルダ直下の接続前チェック記録

品質基準:
- `project.md`、`manuscript/`、`progress.json`、`_research/theme_research.md`、KDPメタデータが揃っている
- 画像リンクが存在する場合、実ファイルが存在する
- 文字本品質スコアが85点以上

### 工程4: マンガ版制作

中間成果物:
- `project.md`
- `manuscript/シナリオ.txt`
- `manuscript/character_defs.json`
- `panels/comicle_output.csv`
- `pages/` または分冊フォルダ
- `KDP出版用/` のEPUB、表紙、メタデータ

品質基準:
- 85点以上
- タイトルが `マンガでわかる！{文字中心電子書籍のタイトル}` になっている
- 投資リスク表現がマンガ内でも過度に単純化されていない
- 画像生成がAPI不使用で記録されている

### 工程5: 統合品質チェック

中間成果物:
- `.company/outputs/{book-name}/PIPELINE_REPORT.md`

品質基準:
- 文字本とマンガ版の成果物パス、品質スコア、画像数、API不使用確認、残課題が記録されている
- Kindle Previewer未確認の場合は残課題として明記されている

## 完了条件

- [x] 文字中心電子書籍の成果物が揃っている
- [x] マンガ版の成果物が揃っている
- [x] 接続前チェックが記録されている
- [x] `PIPELINE_REPORT.md` が作成されている
- [x] すべての工程で品質チェック85点以上

## 成果物

- 統合フォルダ: `.company/outputs/ai-stock-investment/`
- 文字本: `.company/outputs/ai-stock-investment/文字本/`
- マンガ版: `.company/outputs/ai-stock-investment/マンガ版/`
- 文字本EPUB: `.company/outputs/ai-stock-investment/文字本/KDP出版用/AI株に投資すべきか？.epub`
- マンガ版EPUB: `.company/outputs/ai-stock-investment/マンガ版/KDP出版用/マンガでわかる！AI株に投資すべきか？.epub`

## 残課題

- Kindle Previewerでの最終目視は未実施
- ChatGPT Images 2.0による本格マンガページ画像への差し替えは未実施。CSVとプロンプトは作成済み

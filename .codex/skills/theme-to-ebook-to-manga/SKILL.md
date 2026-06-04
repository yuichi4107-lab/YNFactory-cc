---
name: theme-to-ebook-to-manga
description: テーマまたは添付素材から、まず theme-to-ebook で文字中心のKindle電子書籍を作成し、その完成済みソースを ebook-to-manga に渡してマンガ版EPUB・KDPメタデータまで一気通貫で作成する親オーケストレーションスキル。初回は選択式＋自由記述で電子書籍条件とマンガ化条件を確認し、画像生成はAPIを使わずChatGPT Images 2.0（Codex/ChatGPT側の画像生成経路）で行う。
---

# Theme-to-Ebook-to-Manga

テーマまたは添付素材から、文字中心電子書籍とマンガ版を連続制作する親スキル。

このスキル自体は本文生成やマンガ画像生成の詳細を再実装しない。前半は `theme-to-ebook`、後半は `ebook-to-manga` を使い、両者の接続条件と品質ゲートを管理する。

## 役割

- 文字中心電子書籍を `theme-to-ebook` で作る
- `theme-to-ebook` の出力を `ebook-to-manga` の入力として検査する
- 検査に通ったら `ebook-to-manga` でマンガ化する
- 文字本とマンガ版の成果物パス、進捗、品質チェック結果を一つの進行記録にまとめる

## 最優先ルール

- 画像生成にAPIを使わない
- `OPENAI_API_KEY`、OpenAI API、`openai-image-gen`、`client.images.generate`、`client.images.edit` は使わない
- ChatGPT Images 2.0（Codex/ChatGPT側の画像生成経路）で生成する
- `.company/codex/queue/` へのジョブ引き渡しは作らず、このCodexセッション内で生成・保存・QC・EPUB反映まで進める
- `ebook-from-theme` は使わない。このスキルでは `theme-to-ebook` を文字中心電子書籍制作の正本として使う

## 入力

- **テーマまたは添付素材**: テーマ文、文字起こし、メモ、既存原稿など
- **文字中心電子書籍の条件**: `theme-to-ebook` のPhase 0回答
- **マンガ化条件**: ページ数、作画方向、章末/章頭配置など
- **著者名・出力名**: 任意。未指定なら既存スキルのルールで自動決定する

## Phase 0: 統合初回質問

開始時に、文字本とマンガ化の条件をまとめて選択式で確認する。最後に自由記述欄を付ける。

```text
電子書籍とマンガ版を作る前に、方向性を確認させてください。

項目1: テーマの扱い
A. 入力内容のテーマで進める（推奨）
B. 入力内容を少し広げて進める
C. 入力内容を絞り込んで進める
D. 別テーマを指定する

項目2: 想定読者
A. 初心者・これから始める人（推奨）
B. 中小企業の経営者・管理職
C. 実務担当者・現場リーダー
D. 専門家・上級者

項目3: 文字本の型
A. 実践書・手順書（推奨）
B. やさしい入門書
C. ストーリー・事例中心
D. 考え方・思想を伝える本

項目4: 文字本の文字量
A. 約25,000字（短め・素早く出版）
B. 約50,000字（標準）
C. 約100,000字（本格書籍・推奨）
D. 自由記述で指定

項目5: マンガ版の目標ページ数
A. 60ページ前後（短め）
B. 100ページ前後（標準・推奨）
C. 120ページ前後（濃いめ）
D. 自由記述で指定

項目6: マンガの配置・構成
A. 文字本をもとに独立したマンガ版を作る（推奨）
B. 章ごとにマンガパートを作る
C. 重要事例だけマンガ化する
D. 自由記述で指定

項目7: 作画方向
A. 日本のビジネスマンガ調（推奨）
B. やさしい学習マンガ調
C. 少しドラマ寄り
D. テーマから自動判定

項目8: 自由記述
入れたい具体例、避けたい表現、読者像、タイトル案、著者名、必ず触れたい論点、マンガのキャラクター希望などがあれば自由に書いてください。

回答例:
1A、2B、3A、4A、5B、6A、7A
自由記述: 経営者向け。営業色は弱め。属人化したPC業務をAI化する話を中心に。
```

回答が不足している場合は、不足項目だけ短く再質問する。「お任せ」「推奨で」「デフォルトで」の場合は推奨値を採用する。自由記述は選択肢より優先する。

## Phase 1: theme-to-ebook 実行

Phase 0のうち、文字中心電子書籍に関係する回答を `theme-to-ebook` に渡して実行する。

`theme-to-ebook` 側で必ず行うこと:

- 初回質問の回答を `progress.json` に保存する
- Step 0 のテーマリサーチを実行する
- `project.md` を作る
- `manuscript/` に7ファイルを作る
- 本文画像と表紙をAPI不使用で生成する
- `KDP出版用/` にメタデータと表紙を作る
- 最終品質チェックで85点以上を満たす

出力先:

```text
.company/outputs/ebooks/{book-name}/
```

## Phase 2: 接続前チェック

`ebook-to-manga` に渡す前に、文字本ソースフォルダを検査する。

必須チェック:

- `project.md` が存在する
- `manuscript/` が存在する
- `manuscript/` に、はじめに・第1章〜第5章・おわりに相当のMarkdownが揃っている
- `progress.json` が存在し、`theme-to-ebook` の主要Stepが完了している
- `_research/theme_research.md` が存在する
- `KDP出版用/` に文字本用メタデータがある
- 本文画像リンクがある場合、リンク先ファイルが存在する
- 文字本の品質チェックが85点以上、または改善ループ済みで許容理由が記録されている

不足がある場合:

- 原則として `ebook-to-manga` へ進まない
- 不足が `theme-to-ebook` 側で補える場合は、Phase 1へ戻って補修する
- 補修不能な場合は `handoff_to_manga_blocked.md` を文字本フォルダ直下に作り、何が足りないかを記録する

## Phase 3: ebook-to-manga 実行

Phase 2に通ったら、文字本の出力フォルダを `ebook-to-manga` のソースフォルダとして渡す。

### マンガ版タイトル命名ルール

マンガ版のタイトルは必ず以下にする。

```text
マンガでわかる！{文字中心電子書籍のタイトル}
```

例:

```text
文字中心電子書籍: AIが勝手に仕事する会社の作り方
マンガ版: マンガでわかる！AIが勝手に仕事する会社の作り方
```

このタイトルは、マンガ版の `project.md`、EPUBファイル名、表紙、`KDP出版用/書籍情報.md`、`ジャンル・キーワード.md`、`書籍紹介文_HTML.html`、`PIPELINE_REPORT.md` に反映する。サブタイトルは文字中心版のサブタイトルを流用してよいが、タイトル本体には必ず `マンガでわかる！` を付ける。

```text
source_folder = .company/outputs/ebooks/{book-name}/
manga_title = マンガでわかる！{文字中心電子書籍のタイトル}
target_pages = Phase 0 項目5の回答
genre = Phase 0 項目7の回答、または ebook-to-manga の自動判定
```

`ebook-to-manga` 側で実行する標準順序:

1. Step 1: ソース分析と準備
2. Step 2: マンガ用シナリオ作成
3. Step 3: キャラクターデザイン
4. Step 4: コマ割りCSV作成
5. Step 5: ChatGPT Images 2.0直生成でページ画像作成
6. Step 6: 表紙作成
7. Step 7: EPUB製本
8. Step 8: KDPメタデータ作成

## Phase 4: 統合品質チェック

文字本とマンガ版の両方について、最終確認を行う。

文字本:

- `project.md`
- `manuscript/`
- `KDP出版用/` のメタデータ
- 表紙PNG/JPEG
- EPUBがある場合はEPUB構造

マンガ版:

- `manuscript/シナリオ.txt`
- `manuscript/character_defs.json`
- `panels/comicle_output.csv`
- `pages/` または分冊ごとの `pages/`
- `KDP出版用/` のEPUB、表紙、メタデータ
- 画像生成がAPI不使用で行われた記録

統合レポート:

```text
.company/outputs/ebooks-manga/{book-name}/PIPELINE_REPORT.md
```

レポートには以下を含める:

- 入力テーマ
- Phase 0回答
- 文字本ソースフォルダ
- マンガ版出力フォルダ
- 文字中心電子書籍タイトル
- マンガ版タイトル
- 文字本の品質スコア
- マンガ版の品質スコア
- 生成画像数
- API不使用の確認
- Kindle Previewerで未確認の場合の残課題

## 完了条件

- 文字中心電子書籍の成果物が `.company/outputs/ebooks/{book-name}/` に揃っている
- マンガ版の成果物が `.company/outputs/ebooks-manga/{book-name}/` に揃っている
- マンガ版タイトルが `マンガでわかる！{文字中心電子書籍のタイトル}` になっている
- 文字本からマンガ版へ進む接続前チェックが記録されている
- `PIPELINE_REPORT.md` が作成されている
- 画像生成にAPIを使っていないことが記録されている

## 使い分け

- 文字本だけ作る場合は `theme-to-ebook`
- 既存文字本をマンガ化するだけなら `ebook-to-manga`
- テーマから文字本を作り、そのままマンガ版まで作る場合はこの `theme-to-ebook-to-manga`

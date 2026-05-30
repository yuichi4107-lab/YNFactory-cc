---
created: "2026-04-23"
project: "ebook-to-manga"
assignee: "engineering"
status: "approved"
ticket: ".company/pm/tickets/2026-04-23-ebook-to-manga-step5qc-character-presence-check.md"
---

# 要件定義書: Step 5-QC Vision-check 追加

## ゴール

`ebook-to-manga` スキルの Step 5-QC に gpt-4o Vision によるキャラ存在チェックを追加し、
セリフの有無に関わらず**全ページ**で何らかの品質チェックが走る状態にすることで、
キャラ欠落バグ（page_002 山田課長省略事象）を自動検出・再生成ループで修正できるようにする。

## スコープ

### やること

- `skill.md` の Step 5-QC セクションに Vision-check 仕様を追記する
- Step 5 のループフロー疑似コードに Vision-check の組み込み位置を明記する
- Step 5.5（Pillow フォールバック）との連動仕様（Vision-check FAIL 超過時の扱い）を明記する
- コスト試算テーブルに Vision-check コスト（+$0.50〜$1.00/冊）を追記する
- `progress.json` 仕様に Vision-check 結果フィールドを追加する
- E2E 動作確認手順に Vision-check 再現テスト項目を追加する
- Vision-check プロンプト設計（CSV の `character_defs.json` からキャラ名・外見を動的抽出）を確定する

### やらないこと

- 実スクリプトの実装（skill.md は Markdown 仕様書のみ。実装は別タスク）
- 本番 vol1 の全ページ再生成（本チケット完了後に別タスクで実施）
- Blind-OCR 側の既存仕様変更（OCR プロンプト・比較ロジック・エラーハンドリングは現状維持）
- セリフなしページの画像生成スキップ判定ロジックの変更（テキストページ = `コマ別テキストJSON` が `[]` のページは引き続き画像生成・全チェックをスキップ）
- コマ領域クロップや panel_id 単位の Vision-check（ページ全体画像を一括判定する設計を維持）

## 前提確認事項

- CSV 仕様に**独立した「キャラクター外見列」は存在しない**。キャラ名・外見情報は
  `漫画作成のプロンプト` 列の `◆【絶対最優先】キャラクター外見:` 行と、
  Step 3 で生成される `manuscript/characters/character_defs.json` に格納されている。
  Vision-check のキャラ名抽出は `character_defs.json` を参照する設計とする。
- `regen_page002.py` の実装（強化プロンプト + gpt-4o Vision YES/NO チェック）が
  本チケットの仕様ベースラインである。プロンプト設計はこのスクリプトを正式仕様に昇格させる形で行う。
- セリフなしページ（例: 登場人物紹介ページ、テンプレ1の見開き画像）は OCR がオートPASS する
  構造的穴が今回の追加対象。これらのページには**画像生成が発生しており**、
  Vision-check の対象に含める（テキストページ = 画像生成スキップ済みのものは除外）。

## 工程一覧

| 工程 | 中間成果物 | 入力 |
|---|---|---|
| 工程1: Vision-check 仕様設計 | `skill.md` の Step 5-QC への Vision-check 仕様追記 | チケット・regen_page002.py・character_defs.json 構造 |
| 工程2: Step 5 / Step 5.5 / コスト表連動修正 | `skill.md` の Step 5 疑似コード・Step 5.5 発動条件・コスト表・progress.json・E2E 手順の更新 | 工程1の Vision-check 仕様 |

---

## 工程1: Vision-check 仕様設計

### 目標

Step 5-QC に「キャラ存在 Vision-check」サブモジュール仕様を追加し、
セリフなしページのオートPASS 構造的穴を塞ぐ。

### 完了条件

- [ ] Vision-check の**対象ページ条件**が明記されている
  - 対象: `コマ別テキストJSON` が空配列 `[]` **かつ** 画像生成が実行されたページ（登場人物紹介等）
  - 対象外: テキストページ（画像生成自体がスキップされたページ）
  - セリフありページも Vision-check の対象に含める（OCR と Vision-check は独立して実行）
- [ ] **キャラ名抽出ロジック**が明記されている
  - `manuscript/characters/character_defs.json` の `name` フィールドからキャラ名を抽出する
  - 当該ページのプロンプト（`漫画作成のプロンプト`）に登場するキャラ名のみを Vision-check 対象とする
    （全キャラを毎ページチェックするとハズレ質問が多発するため、プロンプト内の記載で絞り込む）
  - 抽出パターン: `◆【絶対最優先】キャラクター外見:` 行から `添付の〇〇.png` の形式でキャラ名を動的抽出する
- [ ] **Vision-check プロンプト設計**が明記されている
  - モデル: `gpt-4o`（vision 機能）, temperature: `0.0`
  - システムプロンプト: 画像品質チェッカーとして YES/NO で答えるよう明示
  - ユーザープロンプト: キャラごとに「〇〇（外見補足）が全身イラストとして画像内に描かれているか？」
  - 判定基準: テキスト枠・名前ラベルのみの場合は NO、全身イラストが存在する場合は YES
  - confirmation bias 対策: 期待キャラ名をプロンプトに含めるが「存在するか」と問う（期待テキストを示す OCR 反面教師とは異なる）。念のためシステムプロンプトで「イラストが実際に描かれているかを画像から判断せよ。テキスト枠のみは NO」と明示する
  - レスポンス形式: `{"vision_checks": [{"char_name": str, "result": "YES"|"NO", "reason": str}]}`
- [ ] **PASS/FAIL 判定条件**が明記されている
  - 1 人でも `result: "NO"` → Vision-check FAIL
  - 全員 `result: "YES"` → Vision-check PASS
- [ ] **OCR との関係**が明記されている
  - Vision-check と OCR は独立して実行する
  - セリフありページ: OCR FAIL または Vision-check FAIL → 再生成トリガー（どちらかがNGなら再生成）
  - セリフなしページ: Vision-check FAIL → 再生成トリガー（OCR はスキップ）
  - 両方 PASS の場合のみページ確定
- [ ] **エラーハンドリング**が明記されている
  - Vision-check API 失敗時: 最大2回リトライ（合計3回試行）
  - 3回失敗時の扱い: FAIL 扱い（安全側に倒す。API 不安定で誤 FAIL となるリスクより、欠落見逃しリスクを優先して回避）
  - JSON パースエラー時: `{"vision_checks": []}` を返す → 空配列 = 全員 NO 扱い → FAIL
  - ログ出力: `[vision] WARN: Vision-check failed: {error}` および `[vision] iter_{N} char={name} result={YES/NO} reason={reason}`

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | 対象ページ条件（セリフなしページを必ず含む・テキストページ除外）が正確に定義されているか | 機能要件 | 15 |
| 2 | キャラ名抽出ロジックが `character_defs.json` ベースで設計され、ページ内登場キャラに絞り込む方式が明記されているか | 機能要件 | 15 |
| 3 | Vision-check プロンプトが confirmation bias を排除しているか（期待テキスト提示の OCR 反面教師との違いが明確か・テキスト枠のみは NO と明示されているか） | 品質・設計 | 20 |
| 4 | PASS/FAIL 判定条件（1人でも NO → FAIL）が明記されているか | 機能要件 | 10 |
| 5 | OCR との独立実行の関係（セリフあり: どちらかが FAIL → 再生成 / セリフなし: Vision-check のみ）が明記されているか | 機能要件 | 15 |
| 6 | エラーハンドリング（リトライ・失敗時 FAIL 扱い・ログ出力）が既存 OCR エラーハンドリングと対称的に設計されているか | エラーハンドリング | 15 |
| 7 | Vision-check レスポンス形式（JSON スキーマ）が明確で実装可能な仕様になっているか | 可読性・実装可能性 | 10 |
| 合計 | | | 100 |

---

## 工程2: Step 5 / Step 5.5 / コスト表連動修正

### 目標

工程1で確定した Vision-check 仕様を、Step 5 の疑似コード・Step 5.5 発動条件・
コスト試算テーブル・`progress.json` 仕様・E2E 動作確認手順に反映する。

### 完了条件

- [ ] **Step 5 ループ疑似コード**が更新されている
  - Vision-check の実行タイミング: Blind-OCR と**並列または直後**（どちらかが FAIL なら再生成）
  - セリフなしページ（OCR スキップ）での Vision-check 実行フローが疑似コードに追加されている
  - `converged` フラグの判定条件が「OCR PASS かつ Vision-check PASS」に更新されている
- [ ] **Step 5.5 発動条件**が更新されている
  - Vision-check FAIL が `max_iter` 回連続した場合も Step 5.5 フォールバック対象に含めることが明記されている
  - ただし Pillow 合成はテキスト合成が主目的のため、Vision-check のみ FAIL（OCR は PASS）のフォールバックページには「Pillow 合成フォールバック（キャラ修正なし）または `failed` 記録」の二択と判断基準を明記する
  - `failed` 配列への記録条件: Vision-check のみ FAIL で Step 5.5 でも解消しない場合
- [ ] **`progress.json` 仕様**が更新されている
  - `vision_check_result` フィールドが追加されている（per-page: `"pass"` / `"fail"` / `"skip"`）
  - `vision_failed_chars` フィールドが追加されている（FAIL 時の欠落キャラ名リスト）
  - `vision_check_pages` 集計フィールド（Vision-check を実施したページ数）
- [ ] **コスト試算テーブル**が更新されている
  - Vision-check（gpt-4o vision）1ページあたり $0.01〜$0.02 の行が追記されている
  - 1冊50〜100ページ換算で +$0.50〜$1.00 の追記がある
  - 再生成が発生した場合の追加コスト（Vision-check FAIL による iter 追加）の注記がある
- [ ] **E2E 動作確認手順**に Vision-check 再現テスト項目が追加されている
  - `page_002` 相当のテスト（セリフなしページ・複数キャラ指示）で Vision-check が FAIL を検出し再生成が発動することを確認する手順
  - Vision-check PASS 時のログ出力（`[vision] iter_1 char=山田課長 result=YES`）の確認手順
  - セリフありページで OCR と Vision-check が独立実行されていることの確認手順
- [ ] **Blind-OCR 既存動作への回帰影響がない**ことが仕様上で確認されている
  - OCR プロンプト・比較ロジック・FAIL 時フィードバック注入の仕様が変更されていない
  - テキストページ（`コマ別テキストJSON` が `[]`）のスキップ動作が維持されている

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | Step 5 疑似コードに Vision-check が適切な位置（OCR 並列 or 直後）で組み込まれ、セリフなしページのフロー分岐が明確か | 機能要件 | 20 |
| 2 | `converged` フラグの条件が「OCR PASS かつ Vision-check PASS」に正しく更新されているか | 機能要件 | 15 |
| 3 | Step 5.5 発動条件に Vision-check FAIL が含まれており、「Pillow フォールバック or failed 記録」の判断基準が明記されているか | 機能要件 | 15 |
| 4 | `progress.json` に Vision-check 結果フィールドが追加され、per-page の結果追跡が可能な仕様になっているか | データ仕様 | 15 |
| 5 | コスト試算テーブルに Vision-check コスト（+$0.50〜$1.00/冊）が追記されているか | 完了条件の充足 | 10 |
| 6 | E2E 動作確認手順に page_002 相当の再現テスト手順が追加されているか | 完了条件の充足 | 15 |
| 7 | Blind-OCR 既存仕様（OCR プロンプト・比較ロジック・テキストページスキップ）に変更がなく回帰安全性が担保されているか | 回帰安全性 | 10 |
| 合計 | | | 100 |

---

## 備考

### チケット完了条件との対応

| チケット完了条件（行 68-75） | 本要件定義での対応箇所 |
|---|---|
| `skill.md` の Step 5 に Vision-check ロジックが追記されている | 工程1（仕様設計）+ 工程2（Step 5 疑似コード更新） |
| すべての生成ページに gpt-4o vision による Vision-check が実施される | 工程1（対象ページ条件） |
| チェック内容（全身イラストとして存在するか YES/NO）が明記されている | 工程1（プロンプト設計・判定基準） |
| NO の場合に既存 iter ループで再生成されるフローが明記されている | 工程2（Step 5 疑似コード） |
| 上限到達時の処理（Pillowフォールバック or `failed` 記録）が明記されている | 工程2（Step 5.5 発動条件） |
| vol1検証と同じ入力でキャラ欠落が検出されて再生成が発動することを確認する | 工程2（E2E 動作確認手順） |
| セリフありページの OCR チェックが引き続き正常に動作することを確認する | 工程2（回帰安全性チェック） |

### ループ上限

- 各工程最大 5 回（実行 → quality-checker → 85点以上で合格）

### 合格ライン

- 各工程 85 点以上で合格とし、次工程に進む
- 工程1 が合格するまで工程2 には進まない

### 参照ファイル

| ファイル | 用途 |
|---|---|
| `g:\マイドライブ\YNFactory-cc\.claude\skills\ebook-to-manga\skill.md` | 改修対象（全仕様書） |
| `g:\マイドライブ\YNFactory-cc\.company\pm\tickets\2026-04-23-ebook-to-manga-step5qc-character-presence-check.md` | チケット（要件原典） |
| `C:/Users/fcmdt/regen_page002.py` | Vision-check 実装のリファレンス（正式仕様への昇格元） |
| `manuscript/characters/character_defs.json` | キャラ名・外見抽出元（実行時に参照） |

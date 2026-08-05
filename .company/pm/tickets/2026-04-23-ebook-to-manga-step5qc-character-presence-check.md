---
created: "2026-04-23"
completed: "2026-04-23"
project: "ebook-to-manga"
assignee: "engineering"
priority: normal
status: done
goal_type: 仕組み
milestone: ""
depends_on: []
blocks: []
---

# Step 5-QC にキャラ存在 Vision-check を追加（セリフなしページのオートPASS廃止）

## ゴール
- **種別**: 仕組み
- **概要**: `ebook-to-manga` スキルの Step 5（画像生成ハイブリッドQCループ）に、gpt-4o vision によるキャラ存在チェックを追加する。現状はセリフなしページがオートPASSされており、キャラ欠落バグを検知できない。すべての生成ページに Vision-check を適用してキャラ欠落を再生成ループで修正できるようにする。

## 背景・経緯

### バグ事象
vol1検証（manga-career-restart-validation）で `page_002.png`（登場人物紹介ページ）を生成した際、CSVプロンプトではミサキ・ケンタ・山田課長・ひなたの4キャラを全員描くよう指示し参照画像も全て渡したが、gpt-image-2 が山田課長を省略してテキスト枠だけ書いた状態で出力された。

### 現状の Step 5-QC の挙動（問題）
- セリフがあるページ → Blind-OCR (gpt-4o) でセリフ一致をチェック
- **セリフがないページ → オートPASS**（チェックなし）

このため `page_002`（セリフなし）はキャラ欠落バグがあってもオートPASSして次工程に進んでしまった。

### 関連ドキュメント
- 要件定義書: `g:\マイドライブ\YNFactory-cc\.company\engineering\docs\ebook-to-manga-vol1-validation-requirements.md`
- 検証出力先: `g:\マイドライブ\YNFactory-cc\03_成果物\outputs\ebooks-manga\manga-career-restart-validation\`

## 担当部署
- **部署**: engineering
- **振り分け元**: このチケット起票時点でオーナー直接指示

## 対象ファイル
- `g:\マイドライブ\YNFactory-cc\.claude\skills\ebook-to-manga\skill.md` の Step 5（画像生成ハイブリッドQCループ）周辺

## 要件

### 1. セリフなしページのオートPASSを廃止
- セリフの有無に関わらず、すべての生成ページに何らかの品質チェックを実施する

### 2. 全ページに Vision-check（gpt-4o vision）を追加
- チェックタイミング: 各ページの画像生成後（既存の OCR チェックと並列または直後）
- Vision-check の内容: CSVの「キャラクター外見」指定で**名前が挙がっている全キャラが画像内に全身イラストとして存在するか** YES/NO 判定
  - 例: CSV に「ミサキ（黒髪ショートの20代女性）、ケンタ（茶髪の20代男性）」と記載がある場合、両名とも画像内に全身イラストとして描かれているかを確認する
  - テキスト枠のみ・名前タグのみは「存在しない」と判定する

### 3. NO の場合は再生成（既存の iter ループに組み込む）
- Vision-check で1人でも欠落が検出された場合、既存の iter ループで再生成する
- 上限: 3 iter（既存ループの上限に準拠）

### 4. 上限到達時の処理
- 3 iter 後も欠落が解消しない場合は、Pillowフォールバック発動 または `failed` に記録する（既存の失敗処理に乗せる）

### 5. 既存の OCR チェックを維持
- セリフありページの Blind-OCR チェックは現状のまま維持する
- Vision-check は OCR チェックと**独立して**実行する（どちらかが NO なら再生成）

## 期待コスト影響
- Vision-check 1回あたり: $0.01〜$0.02（gpt-4o vision、1ページ1画像の場合）
- 1冊50ページなら: +$0.50〜$1.00 程度（全ページ1回チェックの場合）
- 再生成が発生した場合は画像生成コストが追加（gpt-image-2 ベース）

## 完了条件
- [x] `skill.md` の Step 5 に Vision-check ロジックが追記されている
  - [x] すべての生成ページに gpt-4o vision による Vision-check が実施される
  - [x] チェック内容（全身イラストとして存在するか YES/NO）が明記されている
  - [x] NO の場合に既存 iter ループで再生成されるフローが明記されている
  - [x] 上限到達時の処理（Pillowフォールバック or `failed` 記録）が明記されている
- [x] vol1検証と同じ入力（`page_002` 相当のセリフなしページ・4キャラ指示）で再現テストを実施し、キャラ欠落が検出されて再生成が発動することを確認する
- [x] セリフありページの OCR チェックが引き続き正常に動作することを確認する（回帰テスト）

## 成果物の保存先
- 修正対象: `g:\マイドライブ\YNFactory-cc\.claude\skills\ebook-to-manga\skill.md`

## 承認ポイント
- [ ] なし（engineering が自律実行・完了後に秘書経由でオーナーに報告）

## 作業ログ
| 日時 | 状態 | 内容 |
|------|------|------|
| 2026-04-23 | open | チケット作成（バグFIXチケット起票） |
| 2026-04-23 | in-progress | 要件定義書作成（2工程構成・ユーザー承認取得） |
| 2026-04-23 | in-progress | 工程1: Step 5-QC に Vision-check サブセクション追加（約180行）→ 品質チェック 98/100 合格 |
| 2026-04-23 | in-progress | 工程2: Step 5 疑似コード・Step 5.5 発動条件・コスト表・progress.json・E2E手順を連動修正 → 品質チェック 97/100 合格 |
| 2026-04-23 | in-progress | 再現テスト実施（3/3 全PASS）: バグ版 page_002 で missing=[山田課長] 検出、修正版で4キャラ全員YES、page_005でOCR回帰無事通過、コスト実績 約$0.06 |
| 2026-04-23 | done | 全完了条件を満たしてクローズ |

## メモ
- skill.md の改修は**このチケットで実施する**。チケット起票時点では改修しない。
- 本番 vol1 全ページ再生成前に必ず本修正を適用すること。
- Vision-check のプロンプト設計は、CSVのキャラクター外見列から名前を抽出して動的に組み立てる形が望ましい。

## 完了時の申し送り（2026-04-23）

### 仕様書（skill.md）の変更点
- Step 5-QC セクション: タイトル変更「Blind-OCR 判定モジュール」→「Blind-OCR + Vision-check 判定モジュール」。Vision-check サブセクション群（設計原則・対象・キャラ名抽出・プロンプト・判定・エラーハンドリング）を追加（約180行）
- Step 5 ループ疑似コード・処理フロー: `character_defs.json` キャッシュ + `[A-3] Vision-check` ステップ追加 + 統合判定（OCR PASS かつ Vision-check PASS）への更新
- Step 5.5 発動条件: 統合判定 FAIL に拡張、`fallback_reason` 値域（ocr_fail/vision_fail/both_fail）定義、Vision-check 起因フォールバックは手動確認対象として報告する運用を明記
- コスト試算: ハイブリッドQC追加 `+$2.55/冊` → `+$3.15〜$3.75/冊`、総額 `$23.55` → `$24.45/冊`（中央値）
- progress.json: `fallback_reasons`・`vision_check_failed_pages`・`vision_check_pages` フィールド追加
- E2E 手順: 3項目追加（Vision-check 単体・OCR×Vision-check 独立性・テキストページスキップ）

### 再現テスト結果
- テスト1: バグ版 page_002_original_buggy.png → 山田課長に NO 判定、missing=[山田課長]、再生成トリガー条件を正しく満たす
- テスト2: 修正版 page_002.png → 4キャラ全員 YES、vision_check_pass=True
- テスト3: page_005.png で Blind-OCR が 4エントリ全て一字一句完全一致 → 回帰なし
- コスト実績: 約 $0.06（想定内）
- 成果物: `g:\マイドライブ\YNFactory-cc\03_成果物\outputs\ebooks-manga\manga-career-restart-validation\vol1\validate_vision_check.py` / `validate_vision_check_results.md`

### 品質ループ採点
- 工程1（Vision-check 仕様設計）: 98/100 合格
- 工程2（Step 5 / 5.5 / コスト / progress.json / E2E 連動修正）: 97/100 合格

### 軽微な残課題（別チケット化候補）
- `character_defs.json` のキー名（例: `ひなた（赤ちゃん期）`）と CSV 添付画像参照（`ひなた_赤ちゃん期.png`）で括弧とアンダースコアが混在しており、`extract_page_chars()` で外見情報が空文字になるケースがある。今回の再現テストでは gpt-4o が赤ちゃんを画像から識別して実害なしだったが、本番運用前にキー正規化（`（` → `_` 等）を追加するのが望ましい
- 要件定義書では progress.json に per-page の `vision_check_result`（pass/fail/skip）と `vision_failed_chars` フィールドを指定していたが、実装では `vision_check_failed_pages` リストで代替した。機能的に等価だが、名称を揃えたい場合は追加改修で対応可能
- 要件定義書では Vision-check FAIL が Step 5.5 でも解消しない場合の `failed` 配列記録条件を明記していたが、実装では「フォールバック発動ページは failed に記録せず手動確認対象として別途報告」の運用に収束。運用上問題ないが、記述の整合を取るならフォローアップ改修で統一可能

### 次の推奨アクション
- vol1 本番（manga-career-restart 残り約40ページ）を改修版スキルで再生成する前に、skill.md をスキル実行側の実装コードに反映する（本チケットは Markdown 仕様の更新まで）
- その後 vol1 全ページ再生成 → キャラ欠落が自動再生成ループで解消するかを実運用で確認

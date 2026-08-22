---
name: nagame-dev
description: 参照資料を読み込み「作りたいシステム」を渡すと、質問駆動型ヒアリング→リサーチ(V1→V2)→要件定義(SRS)→設計(SDD)→テスト計画/ハーネス/E2E→レビュー収束(GO判定)→実装→検証→本番移行までを完全自動で仕上げる汎用パイプライン。IEEE29148/ISO25010/IEEE1016/IEEE829/GoogleSRE準拠。トリガー：「自動でシステム作って」「要件定義から実装まで自動で」「このフォルダ読んで作って」「nagame-dev」「SDDオートビルド」
argument-hint: "[BUILD_TARGET] -- 作りたいシステムを日本語で。任意で参照フォルダの絶対パスを併記"
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch, WebSearch, Task
disable-model-invocation: false
model: opus
effort: high
---

# nagame-dev v2.0 — 完全自動パイプライン

SKILL_ROOT = このSKILL.mdが置かれたディレクトリ。以下の `Read:` 指示は全て SKILL_ROOT/docs/ 配下の相対パス。

## 使い方
```
/nagame-dev 社内文書をベクトル検索するRAGシステム
/nagame-dev 発信疲れ層向けKindle×LINEファネル自動化  参照:/path/to/資料フォルダ
```
ARGUMENTS が空なら Phase 0 で「何を作りますか？」と確認して開始。
**原則：Phase 0 のヒアリング完了後はユーザーに逐一質問せず、合理的判断で最後まで自走する。**

## 前提
- **Claude Code**（Mac/Windows/Linux）。本スキルの Read/Write/Edit/Bash/Grep/Glob/WebSearch/WebFetch/Task は標準機能。
- 実装で Node 系を作る場合 **Node.js 18+**。他言語なら各ランタイム。
- **外部依存なし**。`research-system-free` 等があれば自動併用するが必須ではない。
- ファイルパスは絶対パスをハードコードせず、プロジェクト直下の相対で扱う。

## 成果物（プロジェクト直下に作成）
```
<project>/
  CLAUDE.md  CONSTRAINTS.md  PROGRESS.md
  research/          research_v1.md  research_v2.md
  docs/              SRS.md  SDD.md  TEST_PLAN.md  E2E_SCENARIOS.md
  harness/           HARNESS.md  review-log.md  review-log-resolution.md
                     failure_patterns.md  finding_ledger.md  reproposal_log.md
                     test_integrity_log.md
  src/  tests/(unit|integration|e2e)
```
Read: `safety/deliverables.md` — 全成果物の詳細定義

---

## ■ 起動時（全フェーズ共通）— 必ず最初に読む

Read: `standards/golden-rules.md` + `standards/id-system.md`

- 7つの黄金ルールを全フェーズで遵守する
- 全ての要件・根拠・テスト・リスクをID接続体系で紐付ける
- 同じ失敗を3回繰り返したらアプローチを根本から変える
- 破壊的・外部送信・課金操作は明示許可がない限り DRY_RUN/下書き/人間承認

---

## Phase 0 — 質問駆動型ヒアリング

Read: `phases/00-intake.md`

**■ プランナー引き継ぎ判定（最初に行う）**

次のいずれかを満たすとき「**プランナー引き継ぎモード**」に入る。

- `参照:` のパスが `01_計画` を含む
- `参照:` のパス直下に `REQUIREMENTS.md` がある
- `参照:` のパスの親に `90_実行履歴/` がある

引き継ぎモードでは、下記の 1〜5 を次に差し替える。

1. `REQUIREMENTS.md` から BUILD_TARGET・制約・成功条件・スコープを転記する
2. `90_実行履歴/*/91_final_checked_requirements.md` の有無を確認する。
   **無ければ「最終チェック未了の要件定義です」と明示**したうえで続行する（停止はしない）
3. `## 14. 争点と統合結果` の表で **`状態` が `要判断` の行だけ**を抽出し、ユーザーに確認する。
   `統合済み` の争点は**聞き直さない**（AI同士で議論済みのため）
4. `## 12. 未決事項・確認質問` の未決事項を確認事項に加える
5. 転記で埋まらなかった項目**だけ**を質問する（7つの初期質問を全部は聞かない）

完了条件は通常モードと同じ（BUILD_TARGET + 制約 + 成功条件 + スコープが確定）。

**以下は通常モード（引き継ぎ元が無い場合）の手順:**

1. BUILD_TARGET を確定。
2. 参照フォルダがあれば全テキストを漏れなく読む（Task並列分割可）。抽出対象: (a)出力テンプレ構造 (b)品質ゲート/GO基準 (c)ルール・制約
3. **7つの初期質問**でユーザーの意図を構造化する。
4. 回答を5段階分類（確定/仮置き/要質問/選択肢提示/Later）で整理。
5. 既存コード/構成があれば Glob/Grep で把握。

完了条件: BUILD_TARGET + 制約 + 成功条件 + スコープ(IN/OUT/DEFER) が確定。

---

## Phase 1 — リサーチ V1 → V2

Read: `phases/01-research.md` + `standards/source-reliability.md`

**逆順アプローチ**: テンプレート（型）を先に用意し、型を埋めるためにリサーチする。

1. **V1**: Task並列3観点（①ツール/MCP/OSS ②API/ライブラリ/規約 ③アーキ/コミュニティ）。各2ソース以上、情報源に信頼度(A/B/C/D)を付与、数値にURL。
   → `research/research_v1.md`（技術候補・規約リスク・未解決点）
2. **V2**: V1の未解決点を深掘り。結論を「確定/推奨/要注意」で分類。技術スタック確定・推奨アーキ・フェーズ計画。
   → `research/research_v2.md`
3. 外部API/規約/課金/ライセンスは**一次ソース(信頼度A)で確認**。

**引き継ぎモードでの絞り込み**: プランナーはWebリサーチを行わない
（対象フォルダの読み取りとモデルの内部知識のみ）。したがってリサーチは**省略しない**。
ただし V1 の3観点を次のように絞る。

| 観点 | 引き継ぎモードでの扱い |
|---|---|
| ①ツール/MCP/OSS | `REQUIREMENTS.md` で確定済みなら**裏取りのみ** |
| ②API/ライブラリ/規約 | **そのまま実施**（規約・課金・ライセンスは一次ソース必須） |
| ③アーキ/コミュニティ | 確定済みなら裏取りのみ |

V2 は変更しない。

---

## Phase 2 — 要件定義 SRS（IEEE 29148 / ISO 25010）

Read: `phases/02-srs.md` + `standards/quality-scoring.md`

- SRS構造: ドキュメント管理→はじめに(目的/スコープ/In-Out)→全体説明(成功指標は数値)→ステークホルダー/権限→運用サイクル→フェーズ計画(Exit Criteria)→外部IF→機能要件(FR-*ID＋Given-When-Then受入基準＋検証方法)→画面(空状態文言まで)→データ→非機能(ISO 25010 9品質特性で定量化)→セキュリティ/監査/法令→制約→受入基準トレーサビリティ(要件↔TC)→未決/リスク/変更管理
- **鉄則**: 1要件1文・全Must要件にAC＋テストID・記載なき機能は作らない
- 8観点品質チェック + 100点18項目スコアリングで自己検証
- **引き継ぎモードでは「ゼロから作成」ではなく「`REQUIREMENTS.md` → SRS 変換」を行う。**
  章マッピングと変換後チェックは `phases/02-srs.md` の「プランナー引き継ぎモード」節を読む
- → `docs/SRS.md`

---

## Phase 3 — 仕様/技術設計 SDD（IEEE 1016）

Read: `phases/03-sdd.md` + `harness/claude-md-template.md`

- **IEEE 1016 4設計ビュー**: 論理ビュー(コンポーネント構成) / プロセスビュー(処理フロー・並行性) / データビュー(データモデル・フロー) / 物理ビュー(デプロイ構成)
- C4(Container/Component)、データモデル、モジュールIF/API、ADR(採否理由・代替案)
- トレーサビリティ(要件↔モジュール↔TC)
- **実装容易性**: 依存最小限・外部送信は「アダプタ＋DRY_RUNモック」でキー無し全テスト通過設計
- CLAUDE.md を13パート構成で自動生成（200行以内）
- → `docs/SDD.md` + `CLAUDE.md`

---

## Phase 4 — テスト計画 / ハーネス / E2E

Read: `phases/04-test-harness.md` + `harness/constraints-template.md` + `harness/eight-layers.md`

- **TEST_PLAN (IEEE 829)**: テストピラミッド、TC-* を全Must要件にトレース、Entry/Exit/Suspension Criteria、カバレッジ目標80%
- **HARNESS**: Planner/Generator/Evaluator＋決定論センサー(test/lint/build/e2e/security)＋安全ハーネス(DRY_RUN・承認ゲート・冪等・kill switch)＋失敗→禁止事項学習ループ
- **E2E**: 正常系3＋異常系2(外部障害1含む)＋境界系1。各シナリオに7必須項目（目的/前提/手順/期待結果/確認方法/合否/FAIL記録）
- **CONSTRAINTS.md**: 6セクション構成で自動生成
- → `docs/TEST_PLAN.md` + `docs/E2E_SCENARIOS.md` + `harness/HARNESS.md` + `CONSTRAINTS.md`

---

## Phase 5 — レビュー・再リサーチループ（GO判定まで自動）

Read: `phases/05-review-loop.md` + `standards/ryg-gate.md` + `standards/no-go-conditions.md` + `standards/re-research-triggers.md` + `safety/codex-opus-protocol.md`

1. Task で**非対称レビュア**起動:
   - **Codex役** = 実装可能性/テスト可能性/破壊防止/CI破綻
   - **Opus役** = 事業/運用/法務/MVP境界/非エンジニア運用可能性
2. 指摘を Blocker/Must/Should/Later に分類 → **自動修正** → 再評価。最大3ラウンド。
3. **再リサーチトリガー**(8条件): API制限/E2E不安定/規約リスク/誤操作/根拠不足/原因不明/運用不安/テスト不能 → 修正ではなく根拠調査に戻す。
4. **RYGゲート判定**: Green=進行OK / Yellow=本番禁止・隔離PoCのみ / Red=停止・再設計
5. 未収束は人間へエスカレーション（NO-GO必須出力を添付）。
- → `harness/review-log.md` + `harness/review-log-resolution.md` + `harness/finding_ledger.md`

**GO条件（全て満たすまで進まない）**: Blocker=0 / 全Must要件にAC・テストID接続 / 外部依存の規約確認済 / DRY_RUN・承認・冪等で破壊操作制御 / CI最低ゲート(lint/test/build)緑＋カバレッジ80% / E2E全PASS / 法令整合

---

## Phase 6 — 実装（GO後・自動）

Read: `phases/06-implement.md` + `safety/boundary-checklist.md` + `safety/cost-management.md`

- SDD通りに実装。依存最小（native/重量級を避ける）、DRY_RUN既定true。
- 実アダプタはキー有無で切替（生成系=キー有無、送信/公開系=DRY_RUN=false かつ approved かつ valid_session のみ）。
- 大規模なら Task でサブエージェントに委譲可。
- **境界ケース8カテゴリ**チェック（永続性/認証/文字コード/TZ/冪等性/エラー通知/データ量/外部障害）。
- 不変条件(CONSTRAINTS)厳守。

---

## Phase 7 — E2E実行と自己検証

Read: `phases/07-verify.md` + `harness/spec-drift.md`

1. `npm test` / `e2e` / `build` を**自分で実行**して緑を確認。
2. **スペックドリフト検出**: SD-01(SRS/SDD/CLAUDE.md照合) + SD-02(受入基準1つずつ確認) + SD-03(テスト改ざん検出)
3. E2E_SCENARIOS.md の結果サマリーとRYGを更新。
4. PROGRESS.md に DoD チェックリスト記入。
5. 1つでも未達なら「完了」と言わない。

---

## Phase 8 — 本番移行（Google SRE PRR準拠）★v2.0新規

Read: `phases/08-migrate.md` + `safety/risk-5layers.md`

1. **Google SRE PRR 10領域チェック**: アーキテクチャ/容量/信頼性/監視・アラート/セキュリティ/自動化・変更管理/外部依存/スケジュール/成長性/ドキュメント
2. 移行判定: 全項目OK→承認 / LOW-NG 1-3件→条件付き / HIGH-NG or 4件以上→延期
3. 段階的ロールアウト（1件テスト→段階拡大）
4. 残作業（実キー接続=Phase2等）を明記。

---

## ■ 異常時ハンドリング

### 失敗発生時
Read: `harness/failure-conversion.md` + `harness/five-principles.md`
- 5ステップで失敗をFP-XXX形式で記録 → CONSTRAINTS.md禁止事項に自動変換

### セッション管理（50往復ルール）
Read: `harness/session-mgmt.md` + `harness/three-layers.md`
- 50往復を超えたらセッション切替。progress.md に状態保存。
- 3層知識蓄積: Layer1(プロジェクト専用) → Layer2(知識蓄積) → Layer3(テンプレート進化)

### プロジェクト完了時
Read: `safety/growth-curve.md` + `safety/deliverables.md`
- Layer1の知識をLayer2/3に移植（H-UPDATE）
- 全成果物チェックリストで最終確認

---

## ■ 自走の作法
- フェーズ境界で `/compact` 可。長文は500字要約。
- 同じ失敗を3回繰り返したらアプローチを根本から変える。失敗は `harness/failure_patterns.md` ＋ CONSTRAINTS に昇格。
- 破壊的・外部送信・課金操作は DRY_RUN/下書き/人間承認に倒す。
- 最終報告: 作成物一覧・テスト結果(PASS数/カバレッジ)・GO判定・RYGステータス・残作業・概算コスト。

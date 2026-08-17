# nagame-dev v2.0

**参照資料を読み込んで「作りたいもの」を伝えるだけで、ヒアリング→リサーチ→要件定義→設計→テスト→レビュー→実装→検証→本番移行までを Claude Code が完全自動で仕上げる、汎用パイプライン・スキルです。**

誰のPC（Mac / Windows / Linux）でも、Claude Code さえ入っていれば使えます。

---

## v1.0 → v2.0 の変更点

| 項目 | v1.0 | v2.0 |
|---|---|---|
| フェーズ数 | 7（リサーチ〜E2E検証） | 9（質問駆動ヒアリング〜本番移行） |
| SKILL.md | 1ファイルに全手順 | 骨格オーケストレーター（~200行） |
| サブファイル | なし | 31本（必要時だけ読み込み） |
| 知識蓄積 | なし（毎回ゼロから） | 3層構造（使うほど賢くなる） |
| レビュー | 簡易 | Codex⇄Opus非対称レビュー（最大3ラウンド） |
| 品質基準 | GO条件のみ | RYGゲート + 100点スコアリング + 7黄金ルール |
| 本番移行 | なし | Google SRE PRR準拠チェック |
| 準拠規格 | IEEE 29148, ISO 25010 | + IEEE 1016, IEEE 829, Google SRE PRR |

---

## これは何をする？

資料フォルダ（方法論・仕様メモ等）と「作りたいシステム」を渡すと、Claude Code が：

1. **Phase 0**: 7つの質問でヒアリング → スコープ確定
2. **Phase 1**: 無料リサーチ（V1→V2）で技術・規約・実装手段を調査
3. **Phase 2**: 要件定義書(SRS) — IEEE 29148/ISO 25010準拠
4. **Phase 3**: 設計書(SDD) — IEEE 1016準拠（4設計ビュー）+ CLAUDE.md自動生成
5. **Phase 4**: テスト計画・ハーネス・E2Eシナリオ — IEEE 829準拠
6. **Phase 5**: Codex⇄Opusレビュー → GO判定まで自動修正（最大3ラウンド）
7. **Phase 6**: 実装（DRY_RUN既定・境界ケース8カテゴリチェック）
8. **Phase 7**: テスト・E2E実行・スペックドリフト検出
9. **Phase 8**: 本番移行チェック — Google SRE PRR準拠

までを自走します。

## 前提（これだけ）
- **Claude Code**（[claude.com/claude-code](https://claude.com/claude-code)）がインストール済み
- 実装でNode系を作る場合のみ **Node.js 18+**
- 特別な環境・他スキルは不要（あれば自動で併用）

---

## インストール

### Mac / Linux
ターミナルでこのフォルダに入って：
```bash
bash install.sh
```

### Windows
PowerShell でこのフォルダに入って：
```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

どちらも `~/.claude/skills/nagame-dev/` に SKILL.md + docs/ (31サブファイル) を配置します。
**インストール後、Claude Code を再起動**してください。

### 手動インストール
`SKILL.md` と `docs/` ディレクトリを丸ごと `.claude/skills/nagame-dev/` に置く。

---

## 使い方
Claude Code の中で：
```
/nagame-dev 社内文書をベクトル検索するRAGシステム
/nagame-dev 発信疲れ層向けKindle×LINEファネル自動化  参照:/path/to/資料フォルダ
```
- 「参照:」のあとに資料フォルダの**フルパス**を書くと、その中身を全部読んでから作ります。
- 省略すると Phase 0 で「何を作る？」と聞いてから自走します。

## ディレクトリ構成

```
nagame-dev/
├── SKILL.md                        # 骨格オーケストレーター
├── README.md
├── install.sh / install.ps1
└── docs/
    ├── phases/                     # 各フェーズの詳細手順（9本）
    │   ├── 00-intake.md            #   質問駆動型ヒアリング
    │   ├── 01-research.md          #   リサーチ V1→V2
    │   ├── 02-srs.md              #   要件定義 SRS
    │   ├── 03-sdd.md              #   設計 SDD
    │   ├── 04-test-harness.md     #   テスト/ハーネス/E2E
    │   ├── 05-review-loop.md      #   レビュー・再リサーチループ
    │   ├── 06-implement.md        #   実装
    │   ├── 07-verify.md           #   E2E検証
    │   └── 08-migrate.md          #   本番移行
    ├── standards/                   # フェーズ横断の判断基準（7本）
    │   ├── golden-rules.md         #   7つの黄金ルール
    │   ├── id-system.md           #   ID接続体系
    │   ├── ryg-gate.md            #   RYGゲート定義
    │   ├── quality-scoring.md     #   品質スコアリング
    │   ├── no-go-conditions.md    #   NO-GO条件
    │   ├── source-reliability.md  #   情報源信頼度
    │   └── re-research-triggers.md #  再リサーチトリガー
    ├── harness/                     # ハーネス設計（8本）
    │   ├── three-layers.md         #   3層知識蓄積
    │   ├── eight-layers.md        #   8層アーキテクチャ
    │   ├── five-principles.md     #   5設計原則
    │   ├── failure-conversion.md  #   失敗→禁止事項変換
    │   ├── constraints-template.md #  CONSTRAINTS.mdテンプレ
    │   ├── spec-drift.md          #   スペックドリフト検出
    │   ├── session-mgmt.md        #   セッション管理
    │   └── claude-md-template.md  #   CLAUDE.mdテンプレ
    └── safety/                      # 安全性・品質保証（7本）
        ├── codex-opus-protocol.md  #   Codex⇄Opusレビュー
        ├── risk-5layers.md        #   リスク5層分類
        ├── boundary-checklist.md  #   境界ケース8カテゴリ
        ├── cost-management.md     #   コスト/トークン管理
        ├── scene-prompts.md       #   シーン別プロンプト
        ├── deliverables.md        #   全成果物一覧
        └── growth-curve.md        #   成長曲線
```

## 成果物（実行プロジェクトの直下に作られる）
```
CLAUDE.md  CONSTRAINTS.md  PROGRESS.md
research/  docs/(SRS/SDD/TEST_PLAN/E2E)  harness/  src/  tests/
```

## 安全について
- 外部送信・本番公開・課金を伴う操作は、明示許可がない限り **DRY_RUN/下書き/人間承認** に倒します。
- APIキーはコードに書かず環境変数ファイルのみ。テストの改ざんはしません。
- 完了条件（DoD）を満たすまで「完成」と言いません。
- 50往復でセッション自動切替（コンテキスト枯渇防止）。

## ライセンス
MIT（自由に配布・改変可）。

## バージョン
v2.0

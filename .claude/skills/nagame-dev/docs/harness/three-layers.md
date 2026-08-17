# 3層知識蓄積構造

nagame-dev ハーネスの中核イノベーション。
プロジェクトを重ねるほどハーネスが賢くなる「成長型」の仕組みを3層で実現する。

---

## 全体像

```
Layer 3 (テンプレート進化層)
  │  H-NEW でコピー ↓          ↑ H-UPDATE で反映
Layer 1 (プロジェクト固有層)  →  Layer 2 (知識蓄積層)
  [使い捨て可]                    [永続・削除しない]
```

---

## Layer 1: プロジェクト固有層（使い捨て可）

**場所**: 各プロジェクトのルートディレクトリ

**役割**: 現在進行中のプロジェクト専用のワークスペース。プロジェクト終了後は削除・アーカイブしても問題ない。

**ディレクトリ構成**:
```
project-root/
├── CLAUDE.md            # プロジェクト固有の指示書（13パート構成）
├── CONSTRAINTS.md       # 禁止事項・制約（6セクション構成）
├── PROGRESS.md          # ★最重要: Claudeの「外部記憶」
├── docs/
│   ├── SRS.md           # ソフトウェア要求仕様書
│   ├── SDD.md           # ソフトウェア設計文書
│   ├── TEST_PLAN.md     # テスト計画書
│   └── harness/         # ハーネス参照ドキュメント
└── src/                 # 実装コード
```

**PROGRESS.md が最重要な理由**:
- Claude Code はセッション間で会話を忘れる
- PROGRESS.md が唯一の「前回どこまで進んだか」の記録
- セッション開始時に必ず読む、セッション終了時に必ず更新する
- 書き方: セッション番号・完了タスク・次のアクション・未解決問題・学んだこと

---

## Layer 2: 知識蓄積層（永続・削除しない）

**場所**: `~/claude-harness/knowledge/`

**役割**: 全プロジェクトを横断する「組織の記憶」。プロジェクトが増えるほど価値が上がる。

**ディレクトリ構成**:
```
~/claude-harness/knowledge/
├── failure_patterns.md    # ★最重要: 失敗パターン集（FP-XXX形式）
├── success_patterns.md    # 成功パターン集（SP-XXX形式）
├── lessons_learned.md     # プロジェクト横断の教訓
├── code_snippets/         # 再利用可能なコード断片
│   ├── auth/
│   ├── error-handling/
│   └── testing/
└── project_history/       # プロジェクト別の振り返り記録
    ├── project-001.md
    ├── project-002.md
    └── ...
```

**failure_patterns.md が最重要な理由**:
- 同じ失敗を二度繰り返さないための唯一の仕組み
- 失敗はCONSTRAINTS.mdの禁止事項に自動変換される（→ failure-conversion.md 参照）
- FP-XXX 形式で管理: 発生状況・根本原因・対処・深刻度・CONSTRAINTS変換ルール

**運用ルール**:
- このディレクトリのファイルは削除しない
- 内容が古くなったら「deprecated」マークを付けるが削除はしない
- H-REVIEW（月次または5プロジェクトごと）で整理・統合する

---

## Layer 3: テンプレート進化層（バージョン管理）

**場所**: `~/claude-harness/templates/`

**役割**: 全プロジェクトで共有する「最善のテンプレート版」を維持する。新プロジェクトはここからコピーして始まる。

**ディレクトリ構成**:
```
~/claude-harness/templates/
├── TEMPLATE_VERSION.md        # テンプレート版数の管理
├── CLAUDE.md.template         # CLAUDE.md の雛形（13パート構成）
├── CONSTRAINTS.md.template    # CONSTRAINTS.md の雛形（6セクション構成）
├── SRS.md.template            # SRS の雛形
├── SDD.md.template            # SDD の雛形
├── TEST_PLAN.md.template      # テスト計画の雛形
└── PROGRESS.md.template       # PROGRESS.md の雛形
```

**バージョン管理ルール**:
- TEMPLATE_VERSION.md でセマンティックバージョニング（v1.0.0 形式）
- Layer 2 の知見を反映するたびにバージョンを上げる
- 変更履歴に「何の失敗パターンを取り込んだか（FP-XXX）」を記載する

---

## 3層の相互作用フロー

```
1. H-NEW 実行
   └→ Layer 3 のテンプレートを Layer 1 にコピー
   └→ Layer 2 の failure_patterns.md を参照し、CONSTRAINTS.md に自動反映
   └→ 過去の失敗が初日から禁止事項として組み込まれる

2. プロジェクト開発（Layer 1 で作業）
   └→ PROGRESS.md をセッションごとに更新
   └→ 失敗が発生したら即座に記録

3. プロジェクト完了 → H-UPDATE 実行（必須）
   └→ Layer 1 の失敗パターンを Layer 2 に移行
   └→ Layer 1 の成功パターンを Layer 2 に移行
   └→ Layer 2 の新知識を Layer 3 のテンプレートに反映
   └→ テンプレートバージョンアップ

4. 次の H-NEW で改善されたテンプレートから開始
```

---

## 4つの管理プロンプト

| プロンプト | 実行タイミング | 目的 |
|---|---|---|
| **H-INIT** | 初回のみ（1回だけ） | `~/claude-harness/` のディレクトリ構造を初期化。knowledge/ と templates/ を作成し、初期テンプレートを配置 |
| **H-NEW** | 新プロジェクト開始時 | Layer 3 から Layer 1 を生成。過去の知識（Layer 2）を自動で CONSTRAINTS.md に反映 |
| **H-UPDATE** | プロジェクト完了後（毎回必須） | Layer 1 の知識を Layer 2/3 に移行。テンプレートを進化させる |
| **H-REVIEW** | 月1回 または 5プロジェクトごと | 重複パターンの統合、古いテンプレートの更新、知識ベースの棚卸し |

**H-UPDATE を忘れると**:
- そのプロジェクトで学んだことが次に引き継がれない
- 同じ失敗を別プロジェクトで繰り返す
- テンプレートが進化しない（ハーネスが成長しない）

---

## 実践チェックリスト

- [ ] H-INIT で `~/claude-harness/` を初期化した
- [ ] 新プロジェクト開始時に H-NEW を実行した
- [ ] プロジェクト完了時に H-UPDATE を実行した（飛ばしていない）
- [ ] failure_patterns.md に失敗を記録している
- [ ] TEMPLATE_VERSION.md のバージョンが上がっている
- [ ] 5プロジェクトごと（または月1回）に H-REVIEW を実行している

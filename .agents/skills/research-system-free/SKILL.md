---
name: research-system-free
description: "完全無料ディープリサーチパイプライン。有料API一切不要。WebSearch+WebFetch+opencli-rs(認証不要) で全自動リサーチ。トリガー: 「無料リサーチ」「フリーリサーチ」「コストゼロで調査」「APIキーなしでリサーチ」"
version: "1.0"
argument-hint: "[BUILD_TARGET] -- 調査したいテーマを日本語で記述"
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch, WebSearch
disable-model-invocation: false
model: sonnet
effort: high
requires:
  tools: ["python3", "curl"]
---

# research-system-free — 完全無料ディープリサーチパイプライン v1.0

## 概要

**有料API一切不要。** Claude Code のサブスクリプションのみで動作する全自動リサーチシステム。
research-system（有料版）の無料代替。品質は有料版の70-80%だが、コストはゼロ。

## 使い方

```
/research-system-free AIエージェントで商品レビューを自動収集するシステム
/research-system-free 海外移住投資のポートフォリオ管理ツール
/research-system-free YouTube動画の自動企画・台本生成システム
```

## 有料版との違い

| 項目 | 有料版 /research-system | 無料版 /research-system-free |
|------|----------------------|---------------------------|
| 必要APIキー | 8-15個 | **0個** |
| 月額コスト | $50-300+ | **$0**（Claude Code代のみ） |
| 情報源数 | 100+ソース | 30+ソース |
| QA Gate | ChatGPT 5.4 thinking | **Claude自己レビュー（3観点）** |
| リサーチ品質 | 100% | 70-80% |
| レポートセクション | 12 | 8 |

## 必要環境

| 必須 | 任意（あれば品質向上） |
|------|---------------------|
| Claude Code（サブスクのみ） | opencli-rs（追加ソース） |

**APIキーは一切不要。**

---

## パイプライン全体図

```
[BUILD_TARGET 記述]
        ↓
  PRE-FLIGHT（環境確認・APIキー不要）
        ↓
  STEP 1 ── キーワード展開                    [Claude Sonnet]
        ↓
  STEP 2 ── 無料リサーチ × 2回               [Claude Sonnet]
        ↓
  STEP 3 ── 評価・設計・実装計画              [Claude Sonnet]
        ↓
  STEP 4 ── 8セクションレポート生成           [Claude Sonnet]
        ↓
  STEP 4.5 ── QA Gate（Claude自己レビュー・3観点）
        ↓
  ユーザー確認待ち
```

---

## PRE-FLIGHT

以下を表示して開始:

```
🚀 TAISUN v2 無料リサーチシステム起動
   対象: [BUILD_TARGET]
   コスト: $0（Claude Code サブスク代のみ）
   opencli-rs: [インストール済み→55サイト / 未インストール→WebSearchのみ]
   推定時間: 10〜20分
```

---

## STEP 1 — キーワード展開（無料）

`/keyword-free` スキルを使用（APIキー不要）:

```
「[BUILD_TARGET]」について以下を展開:
- core_keywords: コアキーワード（5〜10個）
- related: 関連キーワード
- tech_stack_candidates: 技術スタック候補
```

---

## STEP 2 — 無料ディープリサーチ（Pass 1 + Pass 2）

### Pass 1: 3エージェント並列（WebSearch + WebFetch + opencli-rs のみ）

**Agent A — MCP・ツール調査（WebSearch）**

```
WebSearch で以下を検索（各3件以上WebFetchで開くこと）:
1. "[BUILD_TARGET] MCP server"
2. "[BUILD_TARGET] Claude Code skill"
3. "[BUILD_TARGET] GitHub trending"
4. "site:github.com [KEYWORD] stars:>100"
5. "site:mcp.so [KEYWORD]"
```

出力: `research/agent_a_mcp.md`（500文字以内要約）

**Agent B — API・ライブラリ調査（WebSearch）**

```
WebSearch で以下を検索:
1. "[BUILD_TARGET] free API"
2. "[BUILD_TARGET] open source library"
3. "[BUILD_TARGET] npm package"
4. "site:npmjs.com [KEYWORD]"
5. "site:pypi.org [KEYWORD]"
```

出力: `research/agent_b_api.md`（500文字以内要約）

**Agent C — アーキテクチャ・コミュニティ調査（WebSearch + opencli-rs）**

```
# WebSearch
1. "[BUILD_TARGET] architecture best practice 2026"
2. "site:zenn.dev [KEYWORD]"
3. "site:qiita.com [KEYWORD]"

# opencli-rs（インストール済みの場合のみ）
opencli-rs hackernews search "[KEYWORD]" --limit 10 --format json
opencli-rs arxiv search "[KEYWORD]" --limit 5 --format json
opencli-rs devto search "[KEYWORD]" --limit 10 --format json
opencli-rs youtube search "[KEYWORD]" --limit 5 --format json
opencli-rs stackoverflow search "[KEYWORD]" --limit 5 --format json
opencli-rs lobsters search "[KEYWORD]" --limit 5 --format json
opencli-rs wikipedia search "[KEYWORD]" --format json
```

出力: `research/agent_c_arch.md`（500文字以内要約）

→ /compact 実行

### Pass 1.5: 無料スキル追加投入

```
/research-free — WebSearchのみの軽量リサーチ
/note-research — note.com 日本語コミュニティ
/keyword-free — 追加キーワード展開
```

→ /compact 実行

### Pass 2: ギャップ補完（WebSearch + WebFetch）

Pass 1 + 1.5 で「不明」「要確認」の項目を WebSearch + WebFetch で補完。

追加実行（opencli-rsがある場合）:
```
opencli-rs youtube transcript "[関連動画URL]" --format json
opencli-rs bloomberg --format json（金融関連の場合）
opencli-rs reddit hot --subreddit [関連] --format json（認証済みの場合）
opencli-rs twitter trending --format json（認証済みの場合）
```

→ /compact 実行

---

## STEP 3 — 設計・評価（無料）

### 3-A. TrendScore 簡易計算

WebSearchの検索結果数 + GitHub Stars + 更新日で簡易スコア:

```
hot  : 最近更新 + Stars多い + 検索結果多い
warm : 一部条件を満たす
cold : 古い / Stars少ない
```

### 3-B. アーキテクチャ設計

Mermaid C4 図を作成。

### 3-C. 実装計画（3フェーズ）

- Phase 1: MVP（1ヶ月・無料ツールのみ）
- Phase 2: 自動化（2ヶ月目）
- Phase 3: スケール（3ヶ月目〜）

---

## STEP 4 — 8セクションレポート生成（無料）

### 出力先

```
research/runs/{YYYY-MM-DD}__free-proposal/
├── report.md          ← メインレポート（8セクション）
├── architecture.mermaid
└── keyword_universe.csv
```

### レポート構成（8セクション）

1. **Executive Summary** — 価値・差別化・コスト
2. **市場地図** — ツール・ライブラリ全体マップ
3. **Keyword Universe** — キーワード展開結果
4. **データ取得戦略** — 全ソース一覧（無料のみ）
5. **TrendScore結果** — hot/warm/cold 表
6. **システムアーキテクチャ図** — Mermaid C4
7. **実装計画（3フェーズ）** — Mermaid gantt
8. **リスクと代替案** — リスク表

---

## STEP 4.5 — QA Gate（無料・Claude自己レビュー）

Claude（本スキルを実行中のモデル）自身が、独立した3つの視点でレポートを採点する。
各レビューはレポート本文だけを根拠に評価する（直前の生成過程に引きずられないこと）。

1. **網羅性レビュー** — キーワード・ツール・候補に漏れがないか / 各セクションが埋まっているか
2. **信頼性レビュー** — 引用URLが実在するか / 数値・コストに出典があるか / 矛盾がないか
3. **実用性レビュー** — Phase 1 MVP が明日から着手可能か / 抽象論で終わっていないか

各観点を100点満点で採点し、3観点すべて70点以上で PASS。
70点未満の観点があれば、その指摘を STEP 2 / STEP 4 に差し戻して該当箇所のみ補完し、再採点する（最大2回）。

---

## 品質基準

| 項目 | 基準 |
|------|------|
| 最低情報源数 | 各発見につき2ソース以上 |
| 引用 | 数値にはURL付記 |
| 抽象論禁止 | 具体的実装方法まで落とす |
| サブエージェント結果 | 500文字以内に要約 |
| コンパクト | フェーズ境界で /compact 実行 |
| コスト | **全て無料** |

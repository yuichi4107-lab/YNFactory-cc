# AIプランナーのスキル化と nagame-dev 連結 — 設計書

- 作成日: 2026-08-22
- 対象: `ai-planner` スキル新設 / `nagame-dev` スキル改修 / `/start`・`/handoff` 改修
- 状態: 設計確定（実装計画は `../plans/2026-08-22-ai-planner-nagame-integration.md`）

---

## 1. 背景

`AI共同開発プランナー` と `nagame-dev` は、担当区間が隣接しているのに接続されていない。

| | AI共同開発プランナー | nagame-dev |
|---|---|---|
| 実体 | Python CLI（Codex CLI と Claude Code CLI を別プロセス起動） | Claude Code スキル（Markdown 32本） |
| 区間 | 依頼 → 要件定義書（`REQUIREMENTS.md`）で停止 | ヒアリング → 実装 → 本番移行 |
| 品質の稼ぎ方 | 別ベンダーのモデルに非対称な2案を書かせて議論・統合 | IEEE/ISO の型を積み上げ、RYGゲートで進行判定 |

プランナーの成果物は `05_プロジェクト/<名前>/01_計画/REQUIREMENTS.md` に出るが、
現状は次の3点が手作業になっている。

1. プランナーの起動が完全対話式で、Claude Code から呼べない
2. nagame-dev が `REQUIREMENTS.md` を「ただの参照資料」としてしか扱えない
3. 要件定義が完成しても、実装へ進むきっかけが人の記憶に依存している

本設計はこの3点を埋める。

## 2. ゴールと非ゴール

**ゴール**

- G-1: Claude Code から `/ai-planner <依頼文>` で、AI同士の議論を最後まで走らせられる
- G-2: nagame-dev が `REQUIREMENTS.md` を SRS へ変換して引き継ぎ、Phase 0〜2 を短縮できる
- G-3: 完成済みかつ実装未着手の要件定義が、`/start` の当日TODOに自動で最優先として載る

**非ゴール**

- プランナーの議論ロジック・プロンプト・モデル構成の変更（`config.toml` と `prompts.py` は触らない）
- nagame-dev の Phase 3〜8 の変更
- プランナーの音声入力機能の改修
- デスクトップにある旧フォルダの削除（移設確認後、オーナーが判断する）

## 3. 全体像

```
/ai-planner <依頼文>
   ↓  Claude Code が引数を組み立てて自動起動
[Codex: 立場A] ⇄ [Claude: 立場B] → [調停] → [統合] → [最終チェック]
   ↓
05_プロジェクト/<名前>/01_計画/REQUIREMENTS.md
90_実行履歴/<ts>/91_final_checked_requirements.md   ← 完成マーカー
   ↓
planner_inbox.py が検出 → /start が当日TODOの「最優先」へ
   ↓
/nagame-dev <作りたいもの> 参照:05_プロジェクト/<名前>/01_計画
   ↓  Phase 0 = 要判断の確認 / Phase 2 = SRS へ変換
docs/SRS.md → SDD → テスト → レビュー → 実装 → 本番移行
```

---

## 4. 変更① — `ai-planner` スキルの新設

### 4.1 本体の移設

`C:\Users\fcmdt\OneDrive\デスクトップ\AI共同開発プランナー-v0.13-Codex信頼フォルダ修正版\`
の内容を `01_コード/ai-collab-planner/` へ**コピー**する。

移設対象:

```
01_コード/ai-collab-planner/
  ai_planner/          # 11モジュール
  tests/               # pytest 7本
  main.py  config.toml  pyproject.toml  requirements-voice.txt
  README.md  *.bat  音声版の準備.txt
```

移設先は git ワークツリー本体 `C:\YNFactory-cc\01_コード\ai-collab-planner\`。
Drive 側へは `sync_drive_git.py local-to-drive 01_コード/ai-collab-planner` で反映する。

- **コピーであって移動ではない。** デスクトップ側は残す。削除はオーナーの判断（承認ルール）
- `config.toml` の `default_workspace` は現行 `G:\マイドライブ\YNFactory-cc` のまま変更しない（§6.1 参照）
- `__pycache__` は移設しない
- 移設後、`C:\YNFactory-cc\01_コード\ai-collab-planner` で `py -3 -m pytest` が通ることを確認する

**配置場所の解決順序**（スキルが実行時に決める）:

1. `C:\YNFactory-cc\01_コード\ai-collab-planner\main.py`（git ワークツリー本体。Mac は `~/YNFactory-cc`）
2. `G:\マイドライブ\YNFactory-cc\01_コード\ai-collab-planner\main.py`（Drive 側のコピー）

先に存在した方を使う。どちらも無ければ理由を出して停止する。

### 4.2 自動起動モード（`ai_planner/app.py`）

用語: 本書で「自動起動モード」とは、**人がキーボードで入力する工程がゼロになる**ことを指す。
立場A⇄立場Bの議論、調停、統合、最終チェックはすべて従来どおりAI同士で行われ、工程は1つも減らない。

**追加する引数**

| 引数 | 型 | 意味 | 省略時 |
|---|---|---|---|
| `--goal` | str | 依頼文。**これを渡すと自動起動モードになる** | 対話モード（現行動作） |
| `--name` | str | プロジェクト名 | `suggest_project_name(goal)` の結果を採用 |
| `--level` | `light`/`standard`/`complex`/`critical` | 作業レベル | `router.decide_level()` の結果を採用 |
| `--resume` | path | 承認待ちで停止した `run_dir` から再開 | — |
| `--json` | flag | 結果を JSON で stdout へ | 人間向けテキスト |
| `--print-project-path` | flag | プロジェクトの保存先を出力して即終了（AIを呼ばない） | — |

`--print-project-path` は §4.8 のために必要。スキルが参考資料を置く先を、
`sanitize_project_name` の結果を推測せずに確定させるためのもの。

既存の `--check` `--demo` `--voice` `--whisper-model` `--project` は変更しない。
`--goal` を渡さない限り現行の対話モードがそのまま動く（後方互換）。

**終了コード**

| code | 意味 | Claude Code 側の対応 |
|---|---|---|
| 0 | 完走 | 結果を要約し、TODO登録と引き渡しコマンド提示へ |
| 10 | 承認待ちで停止 | 分岐点をチャットへ提示し、承認後 `--resume` |
| 2 | 前提不足（Python / CLI未検出 / 未ログイン） | 何を直すか提示して停止 |
| 1 | エラー | エラー文をそのまま提示して停止 |

**`--json` の出力（完走時）**

```json
{
  "ok": true,
  "exit_reason": "completed",
  "project_name": "AI利用ルール整備ツール",
  "project_root": "G:\\マイドライブ\\YNFactory-cc\\05_プロジェクト\\AI利用ルール整備ツール",
  "requirements_path": ".../01_計画/REQUIREMENTS.md",
  "run_dir": ".../90_実行履歴/20260822-170500",
  "level": "complex",
  "level_label": "複雑",
  "matched_keywords": ["API連携"],
  "debate_enabled": true,
  "team": {
    "fork_extractor": "claude/claude-opus-5",
    "primary_planner": "codex/gpt-5.6-sol",
    "secondary_planner": "claude/claude-opus-5",
    "plan_reviewer": "claude/claude-opus-5",
    "final_decider": "codex/gpt-5.6-sol",
    "requirements_final_checker": "claude/claude-opus-5"
  },
  "rounds_used": 2,
  "stop_reason": "統合完了",
  "issue_ids": ["A-1", "A-2", "A-3"],
  "requirements_created": true
}
```

**`--json` の出力（承認待ち・exit 10）**

```json
{
  "ok": false,
  "exit_reason": "needs_approval",
  "pending_reason": "injection_warning",
  "forks_path": ".../90_実行履歴/20260822-170500/01_forks_and_stances.md",
  "run_dir": ".../90_実行履歴/20260822-170500",
  "project_root": "...",
  "level": "complex",
  "level_label": "複雑"
}
```

`pending_reason` は `injection_warning` または `no_forks`。

### 4.3 承認ゲート — 原則自動・例外のみ停止

現行 `workflow.execute()` の分岐は次のとおり。

```python
no_forks = _has_no_forks(forks)
if no_forks and not injection:
    # approve を呼ばずに素通りし、議論せず要件定義へ進む
elif not self.approve(injection_warning(injection) + forks):
    # 中止
elif not no_forks:
    debate = True
```

**分岐点0件のとき `approve` が呼ばれない**ため、コールバックを差し替えるだけでは
「分岐点0件なら止める」を実現できない。

**変更点**: `CollaborationWorkflow.__init__` に `confirm_no_forks: bool = False` を追加する。
`True` のとき、`no_forks and not injection` のケースも `self.approve` を経由させる。
既定 `False` なので対話モードの挙動は変わらない。

自動起動モードの approver の振る舞い:

| 状況 | 戻り値 | 結果 |
|---|---|---|
| 分岐点あり・警告なし | `True` | そのまま議論へ（AI同士） |
| インジェクション警告あり | `False` | exit 10。`pending_reason: injection_warning` |
| 分岐点0件 | `False` | exit 10。`pending_reason: no_forks` |
| `--resume` 実行時 | 常に `True` | 承認済みとして続行 |

### 4.4 再開時に分岐点を再抽出しない

`--resume <run_dir>` は `<run_dir>/01_forks_and_stances.md` を読み、その内容をそのまま使う。

**理由**: 再抽出すると「ユーザーがチャットで承認した文書」と「実際に議論される文書」がずれる。
承認の意味が失われるため、ディスク上の文書を正とする。

**実装**: `CollaborationWorkflow.execute()` に省略可能引数を2つ追加する。

- `forks_override: str | None` — 与えられたら `_build_forks_document()` を呼ばない
- `run_dir_override: Path | None` — 与えられたら `create_run_directory()` を呼ばず既存を使う

どちらも既定 `None` で、現行呼び出しには影響しない。

### 4.5 実行時間

`config.toml` の `timeout_seconds = 3600`。複雑レベルで9〜15回のAI呼び出しがあり、
1回あたり数十秒〜数分かかるため、実行全体が30分を超えることがある。

**Bashツールの上限は10分**なので、スキルは必ず `run_in_background: true` で起動し、
完了通知を待つ。ポーリングはしない。

### 4.6 スキル `ai-planner` の仕様

配置: `.claude/skills/ai-planner/SKILL.md`（`C:\YNFactory-cc` 側に作成し、Drive 側へ反映する。§11 R-1 参照）

frontmatter:

```yaml
---
name: ai-planner
description: >
  Codex CLI（GPT系）と Claude Code CLI に非対称な2つの立場で要件定義案を書かせ、
  争点を整理・調停して1つの要件定義書へ統合するスキル。実装は行わず要件定義で停止する。
  「要件定義を作って」「2つのAIに議論させて」「何を作るか固めたい」と言われたとき、
  またはユーザーが `/ai-planner` と入力したときに使う。
  完成した要件定義は `/nagame-dev` へ引き渡して実装へ進む。
argument-hint: "[依頼文] -- 作りたいものを日本語で。任意で --level を指定"
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---
```

**実行手順**

| Step | 内容 |
|---|---|
| 1 | 本体の場所を 4.1 の順序で解決する |
| 2 | `py -3 <本体パス>/main.py --check` を実行。exit≠0 なら何を直すか提示して停止 |
| 3 | 依頼文からレベルを判定させ、**判定結果とモデル構成をチャットに表示**する（4.7参照） |
| 4 | `py -3 <本体パス>/main.py --goal "..." --json` を **バックグラウンドで**実行 |
| 5 | exit 10 なら `forks_path` を読んでチャットへ提示し、承認を得て `--resume` |
| 6 | exit 0 なら `REQUIREMENTS.md` を読み、要約と「要判断」を提示 |
| 7 | 当日TODOへ登録（`planner_inbox.py` を呼ぶ。手順の重複を避ける） |
| 8 | `/nagame-dev <作りたいもの> 参照:05_プロジェクト/<名前>/01_計画` を提示 |

### 4.7 作業レベルの明示

`config.toml` の `models.light` は `max_debate_rounds = 0` で、
`fork_extractor` `secondary_planner` `plan_reviewer` がすべて `none`。
すなわち **`light` に判定されると議論工程が丸ごとスキップされ**、
Codex単独の案を Claude が最終チェックする3工程で終わる。

`light_keywords` には `誤字` `文言` `文字修正` `名前変更` `コメント` `色変更` `余白` `README` `単純` `軽微`
が含まれるため、依頼文にこれらが混ざると意図せず降格しうる。

**対策**:

- Step 3 で、判定されたレベル・一致キーワード・各工程のモデルを表として出す
- `light` に判定された場合は「**議論を行わずに進みます**」と明示し、続行するか確認する
- `--level` で明示指定できることを案内する

### 4.8 `04_インプット` からの取り込み

**実測（2026-08-22 時点）**: 681ファイル / 475MB。`.md` 280本のうち25MBが
`inputs/notion_mirror/lifelog原文/` の日次会話記録。`organized/` `clients/` `competitors/`
`reviews/` `misc/` `references/` `indexes/` は実質空（`desktop.ini` と `README.md` のみ）。
プランナー自身の検出器で379ファイルを走査した結果、**秘密情報0件・インジェクション0件**。

丸ごと渡すことはできないため、**機械的に絞ってから Claude Code が最終選別する**2段構えにする。

#### 新規スクリプト `01_コード/scripts/company/input_digest.py`

責務は**候補の抽出のみ**。要約はしない（それは Claude Code の仕事）。

```bash
py -3 01_コード/scripts/company/input_digest.py --goal "<依頼文>" --json
```

**常時対象** — 依頼文によらず必ず候補に入れる。合計30KB程度。

- `inputs/context-map.md` — コンテキスト階層と情報源の優先順位を定義した判断地図
- `inputs/CLAUDE.md` — フォルダの役割とルール

**除外** — 候補にしない。

| 対象 | 理由 |
|---|---|
| `logs/` `__pycache__/` `intake/` | 同期ログ・raw原本。要件定義に使えない |
| `*.py` `*.bat` `*.sh` `*.ini` `*.log` `*.json` | 取り込み自動化の実装 |
| 画像・PDF等のバイナリ | テキストとして渡せない |

**候補の絞り込み** — 残った `.md` に対して行う。

1. 依頼文から検索語を抽出する。日本語は形態素解析が使えない（標準ライブラリのみ）ため、
   `[一-龥ァ-ヶー]{2,}` と `[A-Za-z][A-Za-z0-9_-]{1,}` を取り出し、
   ストップワード（する / こと / ため / もの / よう / システム / ツール / 作成 / 開発 等）を除く
2. **汎用語を落とす**: 候補ファイル全体の50%超に出現する語はスコアに数えない。
   「AI」のような語がすべてのファイルに一致して選別が機能しなくなるのを防ぐ
3. スコア = 一致した検索語の種類数。同点なら**新しい日付を優先**
4. 上限 = **8件 / 合計400KB**（`--max-files` `--max-bytes` で変更可）

**安全** — 候補に残ったファイルだけを検査する（全681ファイルの走査は毎回行わない）。

- `scan_secrets` / `scan_injection` を実行し、検出されたファイルは**候補から外す**
- `safety.blocked` に**種類と行番号だけ**を記録する。値そのものは出力しない

出力:

```json
{
  "generated_at": "2026-08-22T17:05:00+09:00",
  "root": "C:\\YNFactory-cc\\04_インプット",
  "always": [
    {"path": "inputs/context-map.md", "bytes": 4200, "reason": "恒久コンテキスト"}
  ],
  "candidates": [
    {"path": "inputs/conversations/2026-08-03-lifelogs.md", "bytes": 180000,
     "date": "2026-08-03", "matched": ["アンケート", "業務効率化"], "score": 2,
     "excerpt": "冒頭200字…"}
  ],
  "scanned": 280,
  "excluded": 401,
  "safety": {"secrets": 0, "injection": 0, "blocked": []}
}
```

#### スキル側の手順

`ai-planner` スキルの Step 3（モデル構成提示）と Step 4（実行）の間に入る。

1. `input_digest.py --goal "<依頼文>" --json` を実行
2. `always` は無条件で採用
3. `candidates` を読み、**本当に関係するものだけ** Read する（キーワード一致しただけの無関係な会話を落とす）
4. `py -3 <本体パス>/main.py --goal "..." --name "..." --print-project-path` で保存先を確定する
5. 採用した資料の要約を `<project>/00_依頼/REFERENCE.md` へ書く
6. **採用ファイルの一覧をユーザーに提示する。**
   「これらの内容が Codex（OpenAI）と Claude へ送られます」と明示する
7. `safety.blocked` が空でなければ、種類と件数を提示する（値は出さない）

依頼文の末尾に1行を足して起動する。**プランナー本体への改修は不要**
（`--goal` はそのまま `GOAL.md` へ保存され、全工程のプロンプトに埋め込まれるため）。

```
--goal "<依頼文>

参考資料: 00_依頼/REFERENCE.md に、04_インプット から抽出した関連資料の要約がある。必要に応じて参照すること。"
```

`initialize_project_files` が書き込むのは `GOAL.md` `REQUIREMENTS.md` `PLAN.md`
`AGENTS.md` `CLAUDE.md` 等の定型ファイルだけで、`REFERENCE.md` は対象に含まれない。
また `--print-project-path` は `initialize_project_files` より前に return するため、
`00_依頼/` はこの時点でまだ存在しない。無ければ先に作る。

#### この設計にした理由

- **475MBを毎回モデルに探させない**。機械的に落としてから見せる
- **要約をプロジェクト内に置く**ので、読み取り専用サンドボックス（`cwd = project_root`）の
  内側から普通に読める。外部パスへの参照権限を広げる必要がない
- **個人の会話記録が外部AIへ渡る前に一覧が見える**。CLAUDE.md の承認ルール
  （外部送信は承認を取る）に沿う

---

## 5. 変更② — nagame-dev の引き継ぎモード

触るのは3ファイル。`C:\YNFactory-cc\.claude\skills\nagame-dev\` を編集し、Drive 側へ反映する（§11 R-1）。

- `SKILL.md`（Phase 0 節・Phase 2 節）
- `docs/phases/00-intake.md`
- `docs/phases/02-srs.md`

### 5.1 取り込み判定

Phase 0 の冒頭に判定を置く。次のいずれかを満たすとき「プランナー引き継ぎモード」に入る。

- `参照:` のパスが `01_計画` を含む
- `参照:` のパス直下に `REQUIREMENTS.md` がある
- `参照:` のパスの親に `90_実行履歴/` がある

引き継ぎモードでは、同じプロジェクトの
`90_実行履歴/*/91_final_checked_requirements.md` の有無を確認する。
**無い場合は「最終チェック未了の要件定義です」と明示**したうえで続行する（停止はしない）。

### 5.2 Phase 0 の差し替え

引き継ぎモードでは、既存の**7つの初期質問を「要判断の確認」に差し替える**。

- `REQUIREMENTS.md` の `## 12. 未決事項・確認質問` と `## 14. 争点と統合結果` を読む
- 14章の表は `| 争点ID | 状態 | 統合後の結論 | 立場Aから採った要素 | 立場Bから採った要素 | 要判断の場合の人間への質問 |`。
  **状態が `要判断` の行だけ**を抽出してユーザーに確認する（争点IDは `A-1` 形式）
- 状態が `統合済み` の争点は**聞き直さない**（議論済みのため）
- **14章の `状態` が取る値は `統合済み` / `要判断` の2つだけ。**
  `prompts.py:447` が最終統合に対して「`未整理` を残さず `統合済み` か `要判断` にする」と
  指示しているため、`未整理` は14章には現れない。3値（`統合済み`/`要判断`/`未整理`）なのは
  ラウンド中間の `round*/mediation.md` の表（`prompts.py:377`）であって、最終文書ではない
- 議論が打ち切られたかどうかは `round*/mediation.md` の `## 継続判定`
  （`続行` / `終了：統合完了` / `終了：停滞`）で分かる
- BUILD_TARGET・制約・成功条件・スコープは `REQUIREMENTS.md` から転記し、
  欠けている項目だけを質問する

完了条件は現行のまま（BUILD_TARGET + 制約 + 成功条件 + スコープが確定）。

### 5.3 Phase 1 の扱い — 残す

プランナーは Web リサーチを行わない（対象フォルダの読み取りとモデルの内部知識のみ）。
外部API・規約・課金・ライセンスの一次ソース確認は nagame-dev 側の責務として**残す**。

ただし引き継ぎモードでは V1 の3観点を次のように絞る。

| 観点 | 通常 | 引き継ぎモード |
|---|---|---|
| ①ツール/MCP/OSS | 候補探索 | `REQUIREMENTS.md` で確定済みなら**裏取りのみ** |
| ②API/ライブラリ/規約 | 候補探索 | **そのまま実施**（規約・課金は一次ソース必須） |
| ③アーキ/コミュニティ | 候補探索 | 確定済みなら裏取りのみ |

V2 は変更しない。

### 5.4 Phase 2 の変換仕様

Phase 2 を「ゼロから SRS 作成」から「`REQUIREMENTS.md` → SRS 変換」へ差し替える。
章マッピングを `docs/phases/02-srs.md` に追加する。

左列は `prompts.py` の `FINAL_HEADINGS` に定義された**正式な見出し名**を使う。
字面が違うと変換時に章を取りこぼす。

| REQUIREMENTS.md | → docs/SRS.md | 変換で新たに付与するもの |
|---|---|---|
| `## 1. 背景と目的` / `## 2. 想定利用者と利用場面` | はじめに・全体説明 | 成功指標の数値化 |
| `## 3. 現状と解決する課題` | はじめに（目的） | — |
| `## 4. 対象範囲` / `## 5. 対象外` | スコープ In / Out / DEFER | — |
| `## 6. 機能要件` | 機能要件 | **FR-\* 採番** / Given-When-Then 受入基準 / 検証方法 / **Evidence ID** |
| `## 7. 非機能要件` | 非機能要件 | **ISO 25010 の9品質特性へ割り付け** / 未定量項目を Phase 1 の根拠で数値化 |
| `## 8. 画面・操作・業務の流れ` | 画面（空状態文言まで） | 空状態・エラー時の文言 |
| `## 9. データ・外部連携` | データ / 外部IF | — |
| `## 10. 完了条件・受入基準` | 受入基準トレーサビリティ | **TC-\* 採番と要件への接続** |
| `## 11. 制約・リスク・依存関係` | 制約 / リスク | リスク5層分類 |
| `## 12. 未決事項・確認質問` + 14章の要判断 | 未決・変更管理 | Phase 0 で確認した結論 |
| `## 13. 実装プラン`（13.1 実装工程 / 13.2 テスト方針） | フェーズ計画 | **Exit Criteria** |
| `### 13.3 AIモデルの役割分担` | 付録（参考情報） | — |

`docs/SRS.md` の冒頭に出典ブロックを置く。

```markdown
> 出典: 05_プロジェクト/<名前>/01_計画/REQUIREMENTS.md
> 実行履歴: 90_実行履歴/<timestamp>/
> 変換日: YYYY-MM-DD / 変換元の争点数: N件 / うち要判断: M件
```

### 5.5 変換後チェック（新設）

Phase 2 の自己検証（8観点・100点スコアリング）に、引き継ぎモード専用の項目を追加する。

- **要件の欠落検出**: `REQUIREMENTS.md` の機能要件・非機能要件が SRS からすべて追跡できること。
  1件でも落ちていたら変換をやり直す
- **争点IDの追跡**: 14章の争点ID（`A-1` 形式）が SRS の該当箇所から参照できること。
  消えていたら止める（プランナー側の `_validate_issue_coverage` と同じ発想）
- **要判断の明示**: 要判断として残った項目が SRS の「未決・変更管理」に必ず載っていること

この3項目のいずれかが未達なら Phase 3 へ進まない。

---

## 6. 変更③ — `planner_inbox.py` と `/start`・`/handoff`

### 6.1 走査範囲

新規: `01_コード/scripts/company/planner_inbox.py`

プランナーの出力先は `config.toml` の `default_workspace`（Drive 側）だが、
`C:\YNFactory-cc\05_プロジェクト` 配下は 37件中30件がジャンクション、7件が実フォルダの混在で、
**Drive 側に新規作成されたプロジェクトはローカルにジャンクションが作られない**。

したがって**両方の root を走査し、プロジェクト名で重複排除する**。

| 優先 | root |
|---|---|
| 1 | `<git root>/05_プロジェクト`（`C:\YNFactory-cc` / Mac は `~/YNFactory-cc`） |
| 2 | `G:\マイドライブ\YNFactory-cc\05_プロジェクト`（Mac は `~/Library/CloudStorage/.../YNFactory-cc/05_プロジェクト`） |

**なぜ Drive 側も見るのか**: git ワークツリー本体は `C:` 側だが、
`config.toml` の `default_workspace` は `G:\マイドライブ\YNFactory-cc` を指しており、
プランナーが新規作成したプロジェクトはまず Drive 側に現れる。
`05_プロジェクト` 配下の大半が Drive へのジャンクションであるという既存構成
（`02_設定/docs/link-architecture.md`）とも整合するため、
`default_workspace` は変更せず、走査側で両方を見る。

走査は `glob("*/01_計画/REQUIREMENTS.md")` の**2階層固定**。深い再帰はしない
（ジャンクション経由で Drive の巨大ツリーを走査してしまうため）。
アクセス不能なエントリ（Drive オフライン等）は例外を握りつぶしてスキップし、
件数を stderr に出す。

### 6.2 判定条件

| 条件 | 判定 |
|---|---|
| `90_実行履歴/*/91_final_checked_requirements.md` が1つ以上ある | **完成** |
| プロジェクト直下に `docs/SRS.md` も `src/` も無い | **実装未着手** |
| `## 14. 争点と統合結果` の表で、`状態` 列が `要判断` の行が1つ以上ある | **要判断あり** |

`status` の値:

| status | 意味 |
|---|---|
| `ready_for_nagame` | 完成 かつ 実装未着手 → **TODOに載せる対象** |
| `in_progress` | 完成 だが 実装着手済み |
| `draft` | 最終チェック未了 |

### 6.3 出力

- 既定: 人間向けテキスト（1件1行）
- `--json`: 機械可読

```json
{
  "generated_at": "2026-08-22T17:05:00+09:00",
  "scanned_roots": ["G:\\...\\05_プロジェクト", "C:\\YNFactory-cc\\05_プロジェクト"],
  "skipped": 0,
  "items": [
    {
      "project_name": "AI利用ルール整備ツール",
      "requirements_path": "05_プロジェクト/AI利用ルール整備ツール/01_計画/REQUIREMENTS.md",
      "plan_dir": "05_プロジェクト/AI利用ルール整備ツール/01_計画",
      "completed_at": "2026-08-22",
      "status": "ready_for_nagame",
      "decisions_pending": ["A-3 認証をSSOに寄せるか個別IDにするか"]
    }
  ]
}
```

`--status ready_for_nagame` で絞り込めるようにする。

### 6.4 `/start` への組み込み

`start/SKILL.md` の Step 3 と Step 4 の間に **Step 3.5** を挿入する。

```bash
python 01_コード/scripts/company/planner_inbox.py --status ready_for_nagame --json
```

TODOへの書き込みルール:

| 検出内容 | 書き込む節 | 書式 |
|---|---|---|
| `ready_for_nagame` | `## 最優先` | `- [ ] **<プロジェクト名>**: 要件定義が完成済み・実装未着手。`/nagame-dev <名前> 参照:<plan_dir>` で着手する \| 優先度: 高` |
| `decisions_pending` が空でない | `## オーナー操作` | `- [ ] **<プロジェクト名>: 要判断 N件** — <1件目の要旨>。`01_計画/REQUIREMENTS.md` の14章を確認する \| 優先度: 高` |

- **重複防止**: 当日TODOに同じプロジェクト名を含む行が既にあれば追加しない（部分一致）
- 要判断は `## 最優先` ではなく `## オーナー操作` へ入れる。判断はオーナーの仕事であり、
  AIが代わりに決める性質のものではない

Step 5 の報告テンプレに1行足す。

```
同期: <...>
現況: <...>
今日: <...>
要件定義待ち: <N件。0件なら省略>
注意: <...>
```

### 6.5 `/handoff` への組み込み

`handoff/SKILL.md` の Step 2（TODO更新）で同じスクリプトを実行し、
**そのセッション中に新しく完成した要件定義**を当日TODOへ反映する。
判定と書式は 6.4 と同一。

Step 3 の `commit-push` の引数に、更新した TODO とプロジェクトの `01_計画/` を含める。

---

## 7. エラー処理

| 事象 | 挙動 |
|---|---|
| Codex CLI / Claude CLI が未検出・未ログイン | `--check` が exit 2。スキルが何を直すか提示して停止 |
| プランナー実行が timeout（3600秒） | 実行済みの `90_実行履歴/<ts>/` を提示し、`--resume` を案内 |
| インジェクション警告 | exit 10。警告文と分岐点をチャットへ。承認するか対象フォルダを確認するかをユーザーが選ぶ |
| 秘密情報検出 | プランナーが例外で停止（既存動作）。スキルは種類と行番号だけを提示し、**値は表示しない** |
| Drive がオフライン | `planner_inbox.py` はローカル root のみ走査し、その旨を出力 |
| `REQUIREMENTS.md` はあるが14章が無い | `decisions_pending` を空として扱い、`status` は通常判定 |

## 8. テスト方針

| 対象 | 方法 |
|---|---|
| プランナーの自動起動モード | 既存 `tests/` に追加。`DemoModelRunner` を使い、`--goal` 経路で `input()` が呼ばれないことを確認 |
| 承認ゲートの例外条件 | 分岐点0件・インジェクション警告の各ケースで exit 10 になること |
| `--resume` | 分岐点が再抽出されない（`_build_forks_document` が呼ばれない）ことをモックで確認 |
| 後方互換 | `--goal` を渡さない既存の呼び出しで挙動が変わらないこと。既存7本のテストが全て通ること |
| `planner_inbox.py` | tmp ディレクトリに 3 status 分の疑似プロジェクトを作って判定を確認。重複排除も |
| nagame-dev の改修 | Markdown のため自動テスト不可。`REQUIREMENTS.md` のサンプルで1回通し、変換後チェック3項目を手で確認 |

## 9. 触るファイル一覧

**新規**

- `01_コード/ai-collab-planner/`（デスクトップからのコピー一式）
- `01_コード/scripts/company/planner_inbox.py`
- `01_コード/scripts/company/tests/test_planner_inbox.py`
- `01_コード/scripts/company/input_digest.py`
- `01_コード/scripts/company/tests/test_input_digest.py`
- `.claude/skills/ai-planner/SKILL.md`

**変更**

- `01_コード/ai-collab-planner/ai_planner/app.py`（引数・自動起動モード・JSON出力）
- `01_コード/ai-collab-planner/ai_planner/workflow.py`（`confirm_no_forks` / `forks_override` / `run_dir_override`）
- `01_コード/ai-collab-planner/tests/test_workflow.py`, `tests/test_clients.py`（追加分）
- `.claude/skills/nagame-dev/SKILL.md`
- `.claude/skills/nagame-dev/docs/phases/00-intake.md`
- `.claude/skills/nagame-dev/docs/phases/02-srs.md`
- `.claude/skills/start/SKILL.md`
- `.claude/skills/handoff/SKILL.md`

**触らない**

- `ai_planner/prompts.py`, `ai_planner/safety.py`, `ai_planner/clients.py`, `config.toml`
- `nagame-dev` の Phase 3〜8 と `docs/standards/`・`docs/harness/`・`docs/safety/`

## 10. 実装順序

1. プランナー本体の移設＋既存テストが通ることの確認（他に依存しない）
2. `planner_inbox.py` ＋ テスト（既存の完成済みプロジェクトが無くても tmp で検証可能）
3. `input_digest.py` ＋ テスト（独立。2と並行可）
4. `/start`・`/handoff` の改修（2に依存）
5. プランナーの自動起動モード＋テスト（1に依存）
6. `ai-planner` スキル（3と5に依存）
7. nagame-dev の引き継ぎモード（独立。1〜6と並行可）

## 11. リスクと未決事項

| # | 内容 | 対応 |
|---|---|---|
| R-1 | Drive とローカルでスキルが二重管理される。スキル同期は「不足分の追加のみ・上書きしない」運用のため、**片方だけ更新すると恒久的にずれる** | 編集は git ワークツリー本体（`C:\YNFactory-cc`）で行い、`sync_drive_git.py local-to-drive <パス>` で Drive 側へ明示的に反映する。実装計画に手順として入れる |
| R-1b | `sync_drive_git.py commit-push` は **`drive-to-local` 方向**にコピーしてから commit する。C 側で書いた変更は、Drive 側に古い版があるとその時点で巻き戻る | `/handoff` で `commit-push` する前に、必ず `local-to-drive` で C→G を先に通す。Drive 側にファイルが無い場合は `missing source, skipped` となり巻き戻りは起きない（`copy_path` で確認済み） |
| R-2 | 自動承認により、軸のずれた立場設定のまま議論が走る可能性 | 完走後の要約で「どの立場で議論したか」を必ず提示し、やり直しの判断材料にする |
| R-3 | `light` への意図しない降格 | 4.7 の明示と `--level` 指定で対応。ただしユーザーが表示を読み飛ばすと防げない |
| R-4 | 変換後の SRS が `REQUIREMENTS.md` の意図を取りこぼす | 5.5 の3項目チェック。ただしMarkdown上の規範であり、機械的な強制ではない |
| R-5 | `planner_inbox.py` の走査が Drive のレイテンシで遅い | 2階層固定 glob により1プロジェクトあたり数回の stat に抑える。3秒を超えるようなら計測して見直す |
| R-6 | `input_digest.py` のキーワード一致は形態素解析を使わないため、無関係な会話記録を候補に上げうる | 候補は Claude Code が最終選別する。スクリプト側は再現率を優先し、上限8件で切る。汎用語（出現率50%超）はスコアから除く |
| R-7 | 個人の会話記録が Codex（OpenAI）と Claude へ送られる | 採用ファイルの一覧を実行前に必ず提示する。候補に残ったファイルは秘密情報・インジェクションを検査してから渡す |
| U-1 | プランナーの `--goal` に長文（数千字）を渡したときの挙動は未検証 | 実装時に確認。必要ならファイル渡し（`--goal-file`）を追加する。§4.8 の参考資料は `--goal` に埋めず `REFERENCE.md` へ置くため、この制限には当たりにくい |

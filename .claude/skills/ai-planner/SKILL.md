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

# AI共同開発プランナー (/ai-planner)

Codex CLI と Claude Code CLI に**別々の立場で案を書かせ、議論させて統合する**。
どちらか優れた方を選ぶのではなく、両方の良いところを1つの要件定義へまとめる。
本当に両立しないトレードオフだけが「要判断」として人間へ残る。

**このスキルは実装しない。** 要件定義書ができたら停止し、`/nagame-dev` へ引き渡す。

## Step 1: 本体の場所を解決する

次の順に探し、先に見つかった方を使う。

1. `C:\YNFactory-cc\01_コード\ai-collab-planner\main.py`（Mac は `~/YNFactory-cc/...`）
2. `G:\マイドライブ\YNFactory-cc\01_コード\ai-collab-planner\main.py`

どちらも無ければ、探した場所を提示して停止する。

## Step 2: 前提を確認する

```bash
py -3 main.py --check
```

exit≠0 なら、出力をそのまま提示して停止する。よくある原因:

| 症状 | 対処 |
|---|---|
| CLIが見つからない | `npm i -g @openai/codex` / Claude Code の再インストール |
| 未ログイン | `codex login` / `claude auth login` |

## Step 3: モデル構成を提示する

依頼文からレベルが自動判定される。**実行前に必ず次を表示する。**

- 判定されたレベルと一致キーワード
- 立場Aの案 / 立場Bの案 / 調停 / 最終チェック の各モデル

**`light`（軽い・定型）に判定された場合は特に注意する。**
`max_debate_rounds = 0` なので**議論工程が丸ごとスキップ**され、
Codex単独の案を Claude が最終チェックする3工程で終わる。
`light_keywords` には `誤字` `文言` `文字修正` `名前変更` `コメント` `色変更` `余白` `README` `単純` `軽微`
が含まれるため、依頼文にこれらが混ざると意図せず降格する。

`light` のときは「**議論を行わずに進みます**」と明示し、続けてよいか確認する。
議論させたい場合は `--level standard` 以上を指定する。

## Step 3.5: 04_インプットから参考資料を集める

`04_インプット` は 681ファイル・475MB あるので、丸ごとは渡せない。
機械的に絞ってから、本当に関係するものだけを選ぶ。

```bash
py -3 01_コード/scripts/company/input_digest.py --goal "<依頼文>" --json
```

1. **`always`（`context-map.md` / `CLAUDE.md`）は無条件で採用する。**
   ワークスペースの判断前提が書かれており、依頼内容によらず効く
2. `candidates` を読む。**キーワードが一致しただけの無関係な会話記録を落とす。**
   `excerpt` と `matched` を見て、依頼内容の判断材料になるものだけを Read する
3. `safety.blocked` が空でなければ、**種類と件数だけ**を提示する。
   検出した値そのものは表示しない（画面表示自体が漏洩経路になるため）

保存先を確定させる。`sanitize_project_name` の結果を推測しない。

```bash
py -3 main.py --goal "<依頼文>" --name "<プロジェクト名>" --print-project-path --json
```

採用した資料の要約を `<project_root>/00_依頼/REFERENCE.md` へ書く。
原文をそのままコピーしない。**依頼内容に効く事実だけを、出典パス付きで箇条書きにする。**

```markdown
# 参考資料（04_インプット から抽出）

抽出日: YYYY-MM-DD / 候補 N本中 M本を採用

## inputs/context-map.md
- （要点）

## inputs/conversations/2026-08-03-lifelogs.md
- （要点）
```

**採用したファイルの一覧をユーザーに提示する。**
「これらの内容が Codex（OpenAI）と Claude へ送られます」と明示する。
会話記録には個人のやりとりが含まれるため、送る前に見えている必要がある。

## Step 4: 実行する

**必ずバックグラウンドで実行する。** 複雑レベルで9〜15回のAI呼び出しがあり、
30分を超えることがある（Bashツールの上限は10分）。

Step 3.5 で参考資料を置いた場合は、依頼文の末尾に1行足す。

```bash
py -3 main.py --name "<プロジェクト名>" --json --goal "<依頼文>

参考資料: 00_依頼/REFERENCE.md に、04_インプット から抽出した関連資料の要約がある。必要に応じて参照すること。"
```

参考資料が無かった場合はこの1行を付けない。任意で `--level <レベル>` を足す。

**`REFERENCE.md` が上書きされない理由**: `initialize_project_files` は
`_write_if_missing` を使うため、先に置いたファイルはそのまま残る。

## Step 5: 終了コードで分岐する

| exit | 意味 | 対応 |
|---|---|---|
| 0 | 完走 | Step 6 へ |
| 10 | 承認待ちで停止 | 下記へ |
| 2 | 前提不足 | `detail` を提示して停止 |
| 1 | エラー | `detail` を提示して停止 |
| 130 | 中断 | 途中の実行記録を提示する |

**タイムアウトした場合**（`config.toml` の `timeout_seconds = 3600` を超えた、
またはバックグラウンド実行が返らない）: `05_プロジェクト/<名前>/90_実行履歴/` の
最新ディレクトリを探して提示し、`01_forks_and_stances.md` があれば
`--resume <run_dir>` で続きから再開できることを案内する。**最初からやり直さない。**

**exit 10 の対応**: JSON の `pending_reason` を見る。

| pending_reason | 意味 | 提示のしかた |
|---|---|---|
| `injection_warning` | 対象フォルダにAIを誘導する文が仕込まれている可能性 | **警告を先頭に置き**、`forks_path` の内容を提示する。心当たりが無ければ承認せず、対象フォルダを確認するよう促す |
| `no_forks` | 分岐点が抽出できなかった。依頼文が曖昧すぎるか具体的すぎる | `forks_path` を提示し、依頼文を書き直すか、このまま議論なしで進めるかを聞く |

ユーザーが承認したら再開する。**分岐点は再抽出されず、提示したものがそのまま使われる。**

```bash
py -3 main.py --resume "<run_dir>" --json
```

## Step 6: 結果を要約する

`requirements_path` を読み、次を提示する。

- どの立場で議論したか（`90_実行履歴/<ts>/01_forks_and_stances.md` の立場Aと立場B）
- 議論ラウンド数と終了理由（`rounds_used` / `stop_reason`）
- **`## 14. 争点と統合結果` の表で `状態` が `要判断` の行**（争点IDは `A-1` 形式）

`stop_reason` が `統合完了` 以外（`停滞` / `上限`）なら、その旨を明示する。
残った争点は要判断として12章・14章に載っている。

## Step 7: TODOへ登録する

```bash
python 01_コード/scripts/company/planner_inbox.py --status ready_for_nagame --json
```

追記ルールは `start` スキルの Step 3.5 と同一。`## 最優先` と `## オーナー操作` に分けて書き、
プロジェクト名の部分一致で重複を防ぐ。

## Step 8: nagame-dev へ引き渡す

次を提示して終える。

```
/nagame-dev <作りたいもの> 参照:05_プロジェクト/<プロジェクト名>/01_計画
```

要判断が残っている場合は、「**先に要判断を決めてから実装へ進むほうが手戻りが少ない**」と添える。
nagame-dev 側は Phase 0 で要判断を確認してくるので、決めずに進めることもできる。

## 注意事項

- **AI呼び出しはすべて読み取り専用。** Codex は `--sandbox read-only`、
  Claude は `--permission-mode plan --tools Read,Glob,Grep --strict-mcp-config` が必ず付く
- 秘密情報が検出されると要件定義書を一切書かずに停止する。
  **検出した値そのものは表示しない**（画面表示自体が漏洩経路になるため）。種類と行番号だけを伝える
- 議論は必ず有限回で終わる。上限ラウンドはプログラム側で強制される
- 実装・コード変更・テスト実行・Git操作・デプロイは行わない

## 関連

| 目的 | 参照先 |
|---|---|
| 要件定義から実装まで | `nagame-dev` スキル (`/nagame-dev`) |
| 設計の経緯 | `02_設定/docs/superpowers/specs/2026-08-22-ai-planner-nagame-integration-design.md` |
| 本体のソース | `01_コード/ai-collab-planner/` |

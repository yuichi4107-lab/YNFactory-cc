---
name: handoff
description: セッション終了時のハンドオフ処理。HANDOFF.md更新、TODO更新、git commitを一括実行して次回セッションへの引き継ぎを完了する。
---

# ハンドオフスキル (/handoff)

## 概要

セッションの作業内容を記録し、次回セッション（別端末含む）で確実に引き継げるようにする。
「おわり」「また明日」と言わなくても、このスキルを呼ぶだけでハンドオフが完了する。

## 実行手順

### Step 1: HANDOFF.md 更新

`.company/secretary/HANDOFF.md` を以下のように更新する:

1. **frontmatter を更新**:
   - `last_updated`: 今日の日付 (YYYY-MM-DD)
   - `last_device`: わかれば端末名
   - `last_session_summary`: このセッションで行った作業の要約（1-3行）

2. **「現在進行中の作業」セクションを更新**:
   - 各プロジェクトの状態を最新化
   - 完了した項目はチェック
   - 新たに発覚した問題・ブロッカーを追記
   - 「次のアクション」を更新

3. **技術的なメモ**:
   - VPS の状態変更があれば記録
   - 環境変数やAPI設定の変更があれば記録
   - 既知のバグや回避策を記録

### Step 2: TODO 更新

`.company/secretary/todos/YYYY-MM-DD.md` (今日の日付) を更新:
- ファイルが存在しなければ、前日のTODOから未完了タスクを引き継いで新規作成
- 完了したタスクにチェックを入れる
- 新たに発生したタスクを追加

### Step 3: git commit（Google Drive同期 一時停止 必須）

Google Drive同期と `.git/` の競合でハンドオフが失敗・破損するため、**毎回必ず先にDrive同期を一時停止する**。
（過去は失敗時のみ案内していたが、停止し忘れによる事故が複数回発生したため、ハンドオフのたびに必須化した。）

#### 3-1. 【必須】オーナーに Drive 同期の一時停止を依頼する

**先に commit を試行してはいけない。** 必ずユーザーに以下を一言で依頼し、停止完了の返事を待ってから次へ進む:

> 「ハンドオフ前に Google Drive for desktop の同期を一時停止してください。
> （タスクバーのGoogle Drive アイコン → 歯車 → 『同期を一時停止』）
> 完了したら『停止した』とお返事ください。」

ユーザーが「停止した」「OK」「進めて」等の確認を返すまで Step 3-2 以降に進まない。

#### 3-2. 事前チェック（lock残留の除去）

```bash
cd "g:/マイドライブ/YNFactory-cc"

# .git/index.lock が残っていれば削除（Drive同期で残ることがある）
if [ -f .git/index.lock ]; then
  echo "[WARN] .git/index.lock 残留を検出 → 削除"
  rm -f .git/index.lock
fi
```

#### 3-3. ステージ前に想定外の巻き込みをチェック

```bash
# desktop.ini / *.tmp.drivedownload / __pycache__ などが status に出ていないか
git status --short | grep -E "(desktop\.ini|\.tmp\.drive|__pycache__|\.pyc$)" | head -5
```

**何か出たら `.gitignore` 漏れ。ユーザーに報告してから続行する。**

#### 3-4. commit（最大3回リトライ）

```bash
git add -A
for i in 1 2 3; do
  if git commit -m "handoff: [作業サマリーを1行で]

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"; then
    echo "[OK] commit 成功 (試行 $i 回目)"
    break
  fi
  echo "[WARN] commit 失敗 (試行 $i 回目) → 10秒待って再試行"
  sleep 10
  rm -f .git/index.lock  # lock残留再除去
done
```

- コミットメッセージのプレフィックスは必ず `handoff:` にする
- 作業内容を簡潔に記述する
- `git add .` ではなく `git add -A` を使う（削除も検出）

#### 3-5. 【必須】Drive 同期を再開してもらう

commit 成功・失敗にかかわらず、最後にユーザーに同期再開を必ず依頼する:

> 「commit が完了しました。Google Drive の同期を再開してください。
> （同じメニューから『同期を再開』）」

再開漏れ防止のため、Step 4 の完了報告と同じレスポンスで案内すること。

### Step 4: 完了報告

ユーザーに以下を一言で報告:
- 「ハンドオフ完了しました。」
- 更新した内容の要点（1-2行）

## 使い方

- `/handoff` — セッション終了時に手動で呼ぶ
- 会話の最後に自動で実行されることもある（CLAUDE.md のルールに基づく）

## 注意事項

- HANDOFF.md は全端末で共有される最重要ファイル。正確に記述すること
- **Drive 同期の一時停止依頼は必ず最初に行う**（条件付きではなく毎回）
- git commit が失敗した場合（lock等）はリトライし、それでもダメなら手動対応を案内する
- 機密情報（APIキー等）は HANDOFF.md に直接書かず、「.env参照」と記述する

## 3回リトライしても失敗する場合

Drive 同期は既に停止しているはずなので、以下を案内する:

1. `.git/index.lock` を再度削除
   ```bash
   rm -f .git/index.lock
   ```
2. 手動で commit 実行
   ```bash
   cd "g:/マイドライブ/YNFactory-cc"
   git add -A
   git commit -m "handoff: ..."
   ```
3. それでも失敗する場合は Drive 同期再開前にユーザーに状況報告する

根本対応として `.git/` 自体を Drive 同期から除外する手順は
[.company/engineering/docs/gdrive-git-setup.md](.company/engineering/docs/gdrive-git-setup.md) を参照。

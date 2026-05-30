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

### Step 3: git commit（Google Drive同期 一時停止 任意）

#### 3-1. （任意）Drive 同期の一時停止

`.git` はローカル `C:\dev\YNFactory-git` に移設済みのため、commit が Drive 同期で壊れる問題は解消した。Drive 同期の一時停止はもう必須ではない（HANDOFF/TODO 書き込み中の "(1)" 重複ファイル発生をやや減らす程度の効果）。停止せずそのまま進めてよい。

念のため停止したい場合のみ、以下をユーザーに案内する（停止完了を待つブロッキングは不要）:

> 「（任意）気になる場合は Google Drive for desktop の同期を一時停止できます。
> （タスクバーのGoogle Drive アイコン → 歯車 → 『同期を一時停止』）」

#### 3-2. 事前チェック（lock残留の除去）

```bash
cd "g:/マイドライブ/YNFactory-cc"

# index.lock が残っていれば削除（.git はローカル C:\dev\YNFactory-git に移設済み）
LOCK="C:/dev/YNFactory-git/.git/index.lock"
if [ -f "$LOCK" ]; then echo "[WARN] lock 残留 → 削除"; rm -f "$LOCK"; fi
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

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"; then
    echo "[OK] commit 成功 (試行 $i 回目)"
    break
  fi
  echo "[WARN] commit 失敗 (試行 $i 回目) → 10秒待って再試行"
  sleep 10
  rm -f "C:/dev/YNFactory-git/.git/index.lock"  # lock残留再除去
done
```

- コミットメッセージのプレフィックスは必ず `handoff:` にする
- 作業内容を簡潔に記述する
- `git add .` ではなく `git add -A` を使う（削除も検出）

#### 3-5. GitHub へ push

```bash
# GitHub軸: commit後に main を push（複数台同期の要）。最大3回リトライ
for i in 1 2 3; do
  if git push origin main; then echo "[OK] push 成功 (試行 $i)"; break; fi
  echo "[WARN] push 失敗 (試行 $i) → pull --rebase して再試行"
  git pull --rebase origin main 2>&1 | tail -3
done
```

push が認証で失敗する場合は `gh auth status` を確認する。リモートが無い／別構成の端末ではこの Step をスキップしてよい。

#### 3-6. （任意）Drive 同期を再開してもらう

もし Step 3-1 で Drive 同期を一時停止した場合のみ、再開を依頼する:

> 「commit が完了しました。Google Drive の同期を再開してください。
> （同じメニューから『同期を再開』）」

停止した場合は再開漏れ防止のため、Step 4 の完了報告と同じレスポンスで案内すること。

### Step 4: 完了報告

ユーザーに以下を一言で報告:
- 「ハンドオフ完了しました。」
- 更新した内容の要点（1-2行）

## 使い方

- `/handoff` — セッション終了時に手動で呼ぶ
- 会話の最後に自動で実行されることもある（CLAUDE.md のルールに基づく）

## 注意事項

- HANDOFF.md は全端末で共有される最重要ファイル。正確に記述すること
- Drive 同期の一時停止は任意（`.git` はローカル移設済みのため必須ではない）
- git commit が失敗した場合（lock等）はリトライし、それでもダメなら手動対応を案内する
- 機密情報（APIキー等）は HANDOFF.md に直接書かず、「.env参照」と記述する。コード／設定ファイルにもトークン・パスワードを直書きしない。必ず環境変数か .env 経由。2026-05-30 に機密混入の GitHub 誤push が発生したため、push 前に機密スキャンを行うこと。

## 3回リトライしても失敗する場合

以下を案内する:

1. index.lock を再度削除
   ```bash
   rm -f "C:/dev/YNFactory-git/.git/index.lock"
   ```
2. 手動で commit 実行
   ```bash
   cd "g:/マイドライブ/YNFactory-cc"
   git add -A
   git commit -m "handoff: ..."
   ```
3. それでも失敗する場合はユーザーに状況報告する（Drive 同期を停止していた場合は再開前に報告する）

`.git` をローカル `C:\dev\YNFactory-git` へ移設した経緯・構成は
[.company/engineering/docs/gdrive-git-setup.md](.company/engineering/docs/gdrive-git-setup.md) を参照。

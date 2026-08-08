# 技術・環境メモ（常設）

旧 HANDOFF.md の「前回セッションのメモ」を移設した常設リファレンス。
セッションごとの進捗は書かない。環境・接続情報・既知の落とし穴だけを置く。
追記時は日付を添える。機密（APIキー・トークン・パスワード）は書かず `.env参照` と記す。

## 環境・接続

- **git導入済み（2026-04-05）**: プロジェクトルートに `.git` 初期化済み。Google Drive上のためロック競合が発生しやすい（`index.lock` が残ることがある → `rm -f .git/index.lock` で対処）
- **自動ハンドオフ**: CLAUDE.mdにルール追加済み。タスク完了時・終了の挨拶時にClaude が自動でHANDOFF更新+git commit。手動は `/handoff` で呼べる
- **VPS SSH接続**: IP `163.44.101.31`、鍵 `~/.ssh/conoha-vps`(ed25519)。UFWでIP許可が必要（動的IPのため接続できなくなることがある）。authorized_keysが消えることがある→paramiko+パスワード(`[REDACTED-vps-root-pw]`)で再登録可能
- **ConoHa API**: シリアルコンソール経由でUFW操作可能。Identity: `https://identity.c3j1.conoha.io/v3`、ユーザー `gncu76068682`
- **netkeibaスクレイピング**: User-Agentが短いと400エラーになる。フルChrome UAが必須（2026-04-05に発覚）
- **ローカルのkeiba-unifiedコードはVPSと同期されていない**: 修正は必ずVPS上で行うこと
- **Node.js 24インストール済み（2026-04-05）**: wingetで導入。パス: `/c/Program Files/nodejs`
- **GitHub CLI インストール済み**: wingetで導入。`gh auth login` 済み（yuichi4107-lab）
- **Vercel CLIインストール済み**: `npm install -g vercel`、ログイン済み
- **Google Drive上でのnpm install**: tar エラーが発生するため、ローカルディスク(`C:/Users/fcmdt/projects/`)にコピーして作業すること
- **ローカルPCにPython環境あり**: `C:\Users\fcmdt\AppData\Local\Programs\Python\Python312\python.exe` (3.12.10)。旧パス(Python313/User)は無効
- **Nginx WebSocket対応済み**: `/etc/nginx/sites-enabled/yn-tools` にmap + Upgrade/Connectionヘッダー設定追加。新しいWebSocketツール追加時はそのまま動く
- **websocketsバージョン注意**: requirements.txtで13.1にピン留め中。v14+はOrigin検証がデフォルト有効でuvicorn経由のWS接続が403になる
- **Limitless自動同期**: セッション開始時フック(`.claude/settings.json`)で`sync_limitless.py --chats`が自動実行される。タスクスケジューラは不使用(PC電源依存のため)
- **ローカルのバッチファイル/タスクXML**: G:\に書き換え済みだが、本番はVPSのcronで動いているので使わない
- **Coincheck環境変数**: コンテナ内では`COINCHECK_API_KEY`と`COINCHECK_SECRET`（`_API_SECRET`ではない）
- **ai-traderデプロイ手順**: ローカルで修正 → `scp -i ~/.ssh/conoha-vps` でVPSの `/opt/ai-trader/` にファイル転送 → `docker compose down && docker compose build && docker compose up -d`（src/はイメージにCOPYされるためrestartではなくrebuildが必要）
- **CoincheckはSL注文非対応**: `exchange.py` でCoincheckの場合は `stop_loss_order` が即return None。SL/TPは `_manage_positions` の日次チェック（自前監視）で対応。24時間周期のため急落には対応できない制約あり
- **Claude Code権限設定変更（2026-04-06）**: `~/.claude/settings.json` に `defaultMode: "bypassPermissions"` を追加。全ツール自動承認（承認ダイアログなし）。allowリストの300行以上の個別コマンドは残存しているが不要（整理は任意）
- **品質ループ体制構築（2026-04-09）**: 全作業に「要件定義→実行→品質チェック」の3エージェント体制を導入。ルートの`CLAUDE.md`を新規作成（全体ルール）。エージェント3つ追加: `requirements-definer`(要件定義), `executor`(実行), `quality-checker`(品質チェック85点合格/5回上限)。複数工程の作業は工程ごとにチェックループを回す設計
- **スキルの保存場所の整理（2026-04-09確認）**: プロジェクトスキル(`.claude/skills/`)はそのディレクトリでのみ有効だがGDrive経由で他PCから利用可。パーソナルスキル(`~/.claude/skills/`)は全プロジェクトで有効だがPC固有

---
title: 3デバイス運用移管プロジェクト 要件定義書
created: "2026-04-12"
revised: "2026-04-14"
status: approved
author: requirements-definer
---

# 要件定義書 — 3デバイス運用移管プロジェクト（v2）

## 2026-04-14 方針変更（v2 改訂）

**変更点**:
- **Telegram Bot の配置先を Surface → Mac Mini に変更**（既に Mac Mini で Bot 受信・返信可能な状態にセットアップ済み）
- **Surface は Genspark Claw 専用機に位置付け変更**（メイン化しない、負荷集中回避）
- **Mac Mini は「SSH 経由で触る裏方サーバー」として運用**（オーナーが Mac の GUI 操作に不慣れなため、Windows ノートから SSH で全操作する運用に固定）
- **朝のブリーフィングは Mac Mini の launchd に移管**（Windows Task Scheduler → launchd）

**変更の背景**:
- オーナーが Mac GUI 操作に不慣れ → 物理操作を最小化し、SSH 経由 CLI 操作に統一
- VPS 容量拡張は避けたい → VPS 寄せ案（案B）は採用せず
- Surface に負荷集中させたくない → Surface の役割は Genspark Claw のみに限定
- Mac Mini は手元に残す方針 → 24h 稼働ハブとして最大活用

---

## ゴール

現状 Windows ノート 1 台に集中している自動化タスクを Mac Mini M4（24h 自動化ハブ、Telegram + watchdog + 朝ブリーフィング）と Surface（24h Genspark Claw 専用機）に移管し、Windows ノートをシャットダウンしても夜間・外出中も自動処理が継続する状態を実現する。**Mac Mini は SSH 経由でのみ操作し、物理 GUI 操作は初回セットアップ時のみとする。**

---

## スコープ

### やること

- Windows ノートから Mac Mini への SSH 鍵設定（工程0）
- Mac Mini の SSH 有効化 + tmux 常駐 + launchd 登録（Telegram 継続稼働 + 朝ブリーフィング移管）（工程2）
- Surface への Genspark Claw 移管（note 定期投稿指示書消化、4/13〜4/27）（工程3）
- Google Drive `_queue/` フォルダ設計 + Mac Mini watchdog 常駐スクリプト実装（launchd 登録）（工程4）

### やらないこと

- ConoHa VPS 上の本番デーモン（AI 投資戦略・競馬 AI 学習/配信・YN Tools）への変更・移管
- Mac Mini のコンテンツ生成 Pipeline（comicle-pipeline / ebook-produce / video-auto-editor / Instagram リール）の本格稼働（watchdog 基盤完成後の次フェーズ）
- Surface の契約書更新 Bot（win32com）移植（将来工程として保留）
- Surface への Telegram 移管（方針変更により廃止）
- FX Phase 1 方針決定、展示会ブース印刷発注、KDP 入稿（Windows ノート担当のまま維持）
- 既存スクリプトのフル機能テスト・バグ修正（稼働状態の確認のみ）

---

## 前提・制約

| 項目 | 内容 |
|------|------|
| Telegram Bot | @ynfactorycode_bot のトークンは `~/.claude/channels/telegram/.env` に設定済み（Windows ノート）。**Mac Mini にも配置済みで Bot 受信・返信は動作確認済み（2026-04-14）** |
| Telegram Channels 手順書 | `OneDrive/デスクトップ/telegram-channels-setup.md` に記載済み |
| 朝のブリーフィング | 現在 Windows ノートの Windows Task Scheduler（`YNFactory-MorningBriefing`）で稼働中。**Mac Mini の launchd に移管する（v2 変更点）** |
| Genspark Claw | 現在 Windows ノートのみで稼働中。note 定期投稿第 2 弾（月水金 12:00）の指示書 7 件は `.company/genspark/queue/` 配置済み |
| Google Drive | YNFactory-cc フォルダが全端末から参照可能（Google ドライブ経由）|
| Mac Mini | Claude Code インストール済み。Telegram Bot 受信・返信は動作確認済み。**tmux 常駐・launchd 登録・SSH 設定は未実施** |
| Surface | Claude Code インストール状況は要確認。Genspark Claw 未インストール |
| **オーナー制約** | **Mac GUI 操作に不慣れ → 初回物理操作以降は Windows ノートからの SSH 接続で全操作を完結させる** |

---

## 工程一覧（v2）

| 工程 | 工程名 | 担当端末 | 中間成果物 | 入力 | 所要時間目安 |
|------|--------|---------|-----------|------|-------------|
| 工程0 | Mac Mini SSH 有効化 + Windows ノートからの SSH 鍵認証設定 | Mac Mini（物理操作・最後の物理操作）／ Windows ノート | Windows ノートから `ssh mac-mini` でパスワード入力不要でログインできる | Mac Mini 管理者パスワード | 20分 |
| 工程2 | Mac Mini tmux 常駐 + Telegram Bot 永続化 + 朝ブリーフィング launchd 移管 | Mac Mini（SSH 経由） | tmux セッション常駐・再起動後も自動復帰・朝ブリーフィングが launchd で発火 | 工程0完了（SSH 接続確立） | 1.5時間 |
| 工程3 | Surface Genspark Claw 移管 | Surface | Surface 上で Genspark Claw が稼働・note 定期投稿を消化できる状態 | 独立（工程0・2と並走可） | 30分 |
| 工程4 | Google Drive `_queue/` 設計 + Mac Mini watchdog 常駐（launchd 登録） | Mac Mini（SSH 経由）／ 全端末（利用） | `_queue/` フォルダ構造作成 + watchdog スクリプト launchd 起動 | 工程2完了（tmux 稼働） | 2時間 |

### 工程依存関係

```
工程0（Mac Mini SSH 有効化）
    │
    └─→ 工程2（Mac Mini tmux + Telegram 永続化 + 朝ブリーフィング launchd）
            │
            └─→ 工程4（watchdog launchd）   ← tmux 常駐 + SSH 運用が前提

工程3（Surface Genspark Claw）              ← 独立、工程0・2と並走可
```

### ブロッカーリスク

| リスク | 影響工程 | 対処方針 |
|--------|---------|---------|
| Mac Mini の SSH が初期設定で無効 | 工程0 | システム設定 →「共有」→「リモートログイン」を ON（物理操作、初回のみ） |
| Mac Mini の IP が動的で変わる | 工程0 | 固定 IP 設定または `.local`（mDNS/Bonjour）名で接続。Windows 側は OpenSSH クライアントで対応 |
| launchd の plist 構文エラーで自動起動失敗 | 工程2・工程4 | `launchctl load -w` 後に `launchctl list | grep ynfactory` で状態確認、ログは `~/Library/Logs/` に出力するよう設定 |
| 既存 Windows Task Scheduler の朝ブリーフィングとの二重発火 | 工程2 | launchd 稼働確認後、Windows ノート側のタスクを無効化（削除ではなく disable でロールバック可能に） |
| Mac Mini 再起動後の tmux 自動復帰 | 工程2 | launchd で tmux new-session を起動する wrapper スクリプトを用意 |
| Google Drive watchdog のリアルタイム検出 | 工程4 | Google Drive for Desktop（ストリーミング）を Mac Mini にインストール済みである前提。未インストールの場合は先行インストールが必要 |
| Genspark Claw の Surface 版インストール手順が不明 | 工程3 | Windows 版 Genspark Claw の公式インストール手順に従う。不明な場合はブラウザ版 Genspark で代替 |

---

## 工程0: Mac Mini SSH 有効化 + Windows ノートからの SSH 鍵認証設定（新規追加）

### 担当端末
**Mac Mini M4**（初回のみ物理操作）、**Windows ノート**（鍵生成・クライアント設定）

### 作業内容
1. Mac Mini で「システム設定 → 共有 → リモートログイン」を ON（物理操作、約 2 分）
2. Mac Mini のローカル IP アドレスを確認（`ifconfig en0 | grep inet` または システム設定 → Wi-Fi → 詳細）
3. （推奨）ルーターで Mac Mini を DHCP 固定割り当て、または `.local` 名で接続できることを確認
4. Windows ノート側で SSH 鍵ペアを生成（未生成の場合、`ssh-keygen -t ed25519 -f ~/.ssh/mac_mini_ed25519`）
5. Windows ノートから `ssh-copy-id` 相当で公開鍵を Mac Mini の `~/.ssh/authorized_keys` に登録
6. Windows ノートの `~/.ssh/config` に以下のエイリアスを追加:
   ```
   Host mac-mini
       HostName <Mac Mini の IP or .local>
       User <Mac ユーザー名>
       IdentityFile ~/.ssh/mac_mini_ed25519
   ```
7. `ssh mac-mini` でパスワード入力なしで接続できることを確認

### 完了条件
- [ ] Mac Mini のリモートログインが有効化されている
- [ ] Windows ノートから `ssh mac-mini` でパスワード認証不要でログインできる
- [ ] Mac Mini の IP または `.local` 名が記録され、HANDOFF.md に記載されている
- [ ] Windows ノート側の `~/.ssh/config` に `mac-mini` エイリアスが設定されている

### 品質チェック項目（工程0）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | Windows ノートから `ssh mac-mini` でパスワード不要でログインできる | 機能要件 | 50 |
| 2 | `ssh mac-mini "uname -a"` など非対話コマンドが実行できる | 機能要件 | 20 |
| 3 | `~/.ssh/config` に `mac-mini` エイリアスが設定されている | 設定完全性 | 15 |
| 4 | Mac Mini の接続情報（IP or .local 名、ユーザー名、鍵パス）が HANDOFF.md に記載されている | 引き継ぎ完全性 | 15 |
| 合計 | | | 100 |

---

## ~~工程1: Surface Telegram Channels ペアリング移管~~ ❌ **廃止（2026-04-14）**

方針変更により Telegram は Mac Mini に配置。Surface への Telegram 移管は実施しない。

---

## 工程2: Mac Mini — tmux 常駐 + Telegram Bot 永続化 + 朝ブリーフィング launchd 移管（v2 改訂）

### 担当端末
**Mac Mini M4**（工程0 完了後、Windows ノートからの SSH 経由で作業）

### 作業内容
1. Windows ノートから `ssh mac-mini` で接続
2. Mac Mini に tmux をインストール（未設定の場合、`brew install tmux`）
3. 以下の tmux セッション構成を作成・起動:
   ```
   session: claude-main
   └── claude --dangerously-skip-permissions（Telegram Channels 有効化、常駐）
   ```
4. `~/.claude/settings.json` に `channelsEnabled: true` と Telegram プラグイン設定を追加（既に Bot 受信可動作確認済みだが、tmux 起動時にも有効になるよう設定ファイルで永続化）
5. launchd plist を `~/Library/LaunchAgents/com.ynfactory.claude-main.plist` に作成（Mac Mini 起動時に tmux セッションを自動立ち上げる）
6. `launchctl load -w ~/Library/LaunchAgents/com.ynfactory.claude-main.plist` で登録
7. **朝のブリーフィング移管**:
   - 既存の朝ブリーフィングスクリプト（内容：`.company/secretary/inbox/` 生成 + 通知）を Mac Mini に移植
   - launchd plist を `com.ynfactory.morning-briefing.plist` として作成（StartCalendarInterval で毎朝 6:30 起動）
   - `launchctl load -w` で登録
   - Windows ノートの `YNFactory-MorningBriefing` タスクを無効化（削除ではなく Disable）
8. ConoHa VPS への SSH 接続（`ssh -i ~/.ssh/conoha_ed25519 root@163.44.101.31`）が Mac Mini から疎通できることを確認（鍵を Mac Mini にコピー）
9. Mac Mini を再起動して tmux セッションと launchd が自動復帰することを確認

### 完了条件
- [ ] Mac Mini 上で tmux セッション `claude-main` が起動・常駐していること
- [ ] スマホ Telegram から @ynfactorycode_bot を通じて Mac Mini の Claude Code が受信・返信できること（既存動作の継続確認）
- [ ] Mac Mini 再起動後に tmux セッションが launchd で自動復帰すること
- [ ] 朝 6:30 に launchd が朝ブリーフィングを発火し、Telegram に通知が来ること
- [ ] Windows ノートの `YNFactory-MorningBriefing` タスクが無効化されていること（二重発火防止）
- [ ] Mac Mini から ConoHa VPS への SSH 疎通が確認できること
- [ ] `~/.claude/settings.json` に `channelsEnabled: true` が設定されていること
- [ ] launchd plist 2 本（`claude-main`, `morning-briefing`）のパスと起動コマンドが HANDOFF.md に記録されていること

### 品質チェック項目（工程2）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | スマホ Telegram → Mac Mini Claude Code の受信・返信が動作する | 機能要件 | 25 |
| 2 | tmux セッション `claude-main` が常駐し、SSH 切断後・Mac Mini 再起動後も launchd で自動復帰する | 機能要件 | 25 |
| 3 | 朝 6:30 の launchd 発火で朝ブリーフィングが Telegram に届く（または発火時刻のログ確認） | 機能要件 | 20 |
| 4 | Windows ノートの朝ブリーフィング Task Scheduler が無効化されている（二重発火なし） | 整合性 | 10 |
| 5 | Mac Mini から ConoHa VPS への SSH 疎通が確認できる | 機能要件 | 10 |
| 6 | launchd plist 2 本のパス・起動コマンドが HANDOFF.md に記録されている | 引き継ぎ完全性 | 10 |
| 合計 | | | 100 |

---

## 工程3: Surface — Genspark Claw 移管（note 定期投稿 消化）

### 担当端末
**Surface**（工程0・2 と独立、並走可）

### 作業内容
1. Surface に Claude Code CLI をインストール（未インストールの場合）
2. Surface に Genspark Claw をインストール
3. Google Drive の `.company/genspark/queue/` を Genspark Claw の読み取り先として設定
4. note 定期投稿 第 2 弾（月水金 12:00、4/13〜4/27、7 本）の指示書を Surface の Genspark Claw が消化できる状態にする
5. Surface の Windows Task Scheduler に「Genspark 定期起動」を登録（または Genspark Claw の自動スケジュール機能を利用）
6. Windows ノートで動作していた Genspark Claw を停止・無効化

### 完了条件
- [ ] Surface に Genspark Claw がインストールされ、起動できること
- [ ] `.company/genspark/queue/` の指示書ファイルを Surface の Genspark Claw が読み取れること
- [ ] note 定期投稿のスケジュール（月水金 12:00）で Surface から投稿が実行される仕組みが設定されていること
- [ ] Windows ノートで動作中の Genspark Claw が停止・無効化されていること（二重実行防止）
- [ ] 初回投稿が Surface から実行され、note に公開されること（または翌日の確認で公開済みを確認）

### 品質チェック項目（工程3）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | Surface の Genspark Claw が `.company/genspark/queue/` の指示書を読み取れる | 機能要件 | 30 |
| 2 | note 定期投稿スケジュール（月水金 12:00）が Surface から実行される仕組みが設定されている | 機能要件 | 30 |
| 3 | Windows ノートの Genspark Claw が停止・無効化されている（二重実行なし） | 整合性 | 20 |
| 4 | 初回投稿の実行確認または翌朝の公開確認ができる | 機能要件 | 15 |
| 5 | 失敗時のエラーが `.company/genspark/` 配下に記録される仕組みがある | エラーハンドリング | 5 |
| 合計 | | | 100 |

---

## 工程4: Google Drive `_queue/` 設計 + Mac Mini watchdog 常駐（launchd 登録）

### 担当端末
**Mac Mini M4**（Windows ノートからの SSH 経由）、全端末（利用）

### 作業内容

#### 4-1. Google Drive フォルダ設計・作成
以下の構造を Google Drive に作成する:
```
Google Drive/
└── _queue/
    ├── manga-requests/       ← MD を置くと Mac Mini がマンガ生成 Pipeline を起動
    ├── sns-posts/            ← 投稿予約キュー（将来使用）
    └── keiba-analysis/       ← 分析依頼キュー（将来使用）
```

#### 4-2. watchdog スクリプト実装（Mac Mini 常駐、SSH 経由で実装）
- `_queue/manga-requests/` を監視する Python スクリプトを Mac Mini に作成
- 新規ファイル検出時にマンガ生成 Pipeline を起動するロジックを実装
- 処理済みファイルは `_queue/manga-requests/done/` に移動
- エラー時はログを `_queue/logs/` に記録

#### 4-3. launchd 登録（tmux ではなく launchd で直接管理）
Mac Mini の launchd に `com.ynfactory.queue-watchdog.plist` を作成:
- プログラム：watchdog スクリプトのパス
- RunAtLoad: true
- KeepAlive: true（異常終了時に自動再起動）
- StandardOutPath / StandardErrorPath: `~/Library/Logs/ynfactory-watchdog.log`

#### 4-4. 運用ルール文書化
`_queue/README.md` に以下を記載:
- フォルダ別用途と使い方
- ファイル命名規則
- 処理失敗時の対処手順

### 完了条件
- [ ] Google Drive に `_queue/manga-requests/`、`_queue/sns-posts/`、`_queue/keiba-analysis/`、`_queue/logs/` フォルダが存在すること
- [ ] `_queue/README.md` に運用ルールが記載されていること
- [ ] watchdog スクリプトが Mac Mini の launchd で常駐稼働していること（`launchctl list | grep ynfactory` で確認）
- [ ] Windows ノートから `_queue/manga-requests/` にテスト MD ファイルを置いたとき、Mac Mini が検出・ログ記録することを確認できること
- [ ] 処理済みファイルが `_queue/manga-requests/done/` に移動されること
- [ ] watchdog スクリプトのパス・launchd plist パス・起動コマンドが HANDOFF.md に記録されていること

### 品質チェック項目（工程4）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | `_queue/manga-requests/` にファイルを置いたとき Mac Mini watchdog が検出・ログを記録する | 機能要件 | 35 |
| 2 | Google Drive `_queue/` のフォルダ構造が設計通りに作成されている | 機能要件 | 15 |
| 3 | launchd 登録で常駐し Mac Mini 再起動後も自動復帰する（`launchctl list` 確認） | 機能要件 | 20 |
| 4 | 処理済みファイルが `done/` に移動され、ログが `logs/` に記録される | エラーハンドリング | 15 |
| 5 | `_queue/README.md` に運用ルール・ファイル命名規則・失敗時対処が記載されている | ドキュメント | 10 |
| 6 | HANDOFF.md にスクリプトパス・launchd plist パス・起動コマンドが記録されている | 引き継ぎ完全性 | 5 |
| 合計 | | | 100 |

---

## 完了後の理想状態（v2）

| 状況 | 状態 |
|------|------|
| 夜間（Windows ノートをシャットダウン中） | Mac Mini が launchd で tmux 常駐・Telegram Bot 応答・watchdog 稼働。Surface で Genspark Claw が note 投稿処理 |
| 外出先（スマホのみ） | Telegram から @ynfactorycode_bot に指示 → Mac Mini（SSH で Windows から制御可）が処理 → 成果物が Google Drive に保存 |
| 作業時（Windows ノート起動） | `ssh mac-mini` で Mac Mini を CLI 操作。`_queue/manga-requests/` に MD を置くだけで Pipeline 起動 |
| メンテナンス時 | Windows ノートから `ssh mac-mini` でログ確認・設定変更（Mac GUI 操作不要） |
| 朝 6:30 | Mac Mini の launchd が朝ブリーフィングを発火 → Telegram に届く |
| VPS デプロイ作業 | Mac Mini から SSH で ConoHa VPS に接続（Windows ノート不要）|

---

## 備考

- **ConoHa VPS は移管対象外**: 既存本番デーモン（AI 投資戦略・競馬 AI・YN Tools）はすべて VPS 側で継続稼働。今回の作業で VPS 側のコードは変更しない。
- **VPS 寄せ案は不採用**: VPS 容量拡張を避けるため、Telegram・watchdog・朝ブリーフィングは VPS に載せず、Mac Mini で処理する。
- **Mac GUI 操作の最小化**: オーナーが Mac GUI に不慣れなため、工程 0 の初回物理操作（リモートログイン ON、約 2 分）以降は、全操作を Windows ノートからの SSH 経由で実施する。日常メンテナンス（ログ確認・設定変更・スクリプト編集）もすべて SSH で完結させる。
- **朝のブリーフィング**: Windows Task Scheduler → Mac Mini launchd に移管。launchd は Mac 標準の常駐プロセス管理機構であり、cron より推奨される。StartCalendarInterval で時刻指定が可能。
- **note 定期投稿第 2 弾の即時公開リスク**: 第 1 弾で Genspark Claw が予約投稿を即時公開した事故あり。工程 3 では投稿方法（予約 vs 即時）を手順書で明示し、Surface での初回実行後は翌朝に公開状態を必ず確認する。
- **Telegram Bot トークンの扱い**: Mac Mini が Telegram Bot の唯一の受信端末となる。Windows ノート側の Bot 接続は停止させる（二重ポーリング回避）。
- **優先着手順の確認（オーナー承認済み・2026-04-14）**: 工程0 → 工程2 → 工程4 の順。工程3は独立で並走可。

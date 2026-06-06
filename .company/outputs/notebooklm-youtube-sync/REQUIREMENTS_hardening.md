# 要件定義書 — NotebookLM YouTube自動同期システム 3弱点対策

作成日: 2026-06-06

---

## ゴール

`notebooklm-sync` の運用上の弱点（Telegram通知未設定・セッション短命・再認証完全手動）の3点を対策し、cronによる無人運用が正常通知・長寿命セッション・半自動再認証で安定稼働する状態にする。

---

## スコープ

### やること
- 弱点1: `secrets.yaml` にTelegram bot_token/chat_id の受け口を整備し、動作を検証する
- 弱点2: `notebooklm.py` の揮発性 `new_context(storage_state=)` を `launch_persistent_context(user_data_dir=...)` に切り替え、セッション寿命の延長を図る（best-effort）
- 弱点3: Windowsタスクスケジューラ用の再認証ジョブ（`.bat` + `.ps1`）を作成し、ローカル→VPS自動転送を実現する。加えて `SessionExpiredError` 検知時にTelegram即通知する（弱点1基盤を利用）

### やらないこと
- NotebookLM Enterprise / Google Data API への切り替え（個人版ノートブックに未対応のため対象外）
- セッション寿命の保証（延長は best-effort。永続コンテキスト化でも切れる場合がある）
- Telegram bot の作成・BotFather操作（ユーザーが別途実施。実装側はtoken/IDの受け口のみ）
- Google認証フロー自体の自動化（CDPログイン手順は手動継続。自動化はアカウント停止リスクあり）
- VPS Playwright/Pythonバージョンアップ、yt-dlp更新等の本変更と無関係なメンテ

---

## 工程一覧

| 工程 | 作業名 | 中間成果物 | 入力 |
|---|---|---|---|
| 工程1 | Telegram通知の受け口整備と動作検証 | `secrets.yaml` 記入・動作確認済みの通知基盤 | ユーザー提供の bot_token/chat_id |
| 工程2 | セッション永続化（persistent_context化） | `notebooklm.py` 改修版 + VPS反映 | 工程1完了後のコードベース |
| 工程3 | 定期再認証半自動化 + セッション切れ通知 | タスクスケジューラジョブ一式 + 通知拡張 | 工程1・2完了後のコードベース |

---

## 工程1: Telegram通知の受け口整備と動作検証

### 背景
`secrets.yaml` が空のため `bot_token=""`, `chat_id=""` で動作中。`notify.py` は未設定時にログのみ出す安全設計だが、実際には通知が届かない。

### 中間成果物
- VPS上の `secrets.yaml` に bot_token/chat_id が記入された状態
- `--dry-run` もしくは専用テストスクリプトでTelegramへテストメッセージが届くことを確認

### 機密が必要な箇所（実装フェーズでユーザー提供を要するもの）
- `telegram.bot_token` : BotFatherで発行したトークン（形式: `123456:ABCdef...`）
- `telegram.chat_id` : 通知先チャットID（形式: 数値文字列。`@userinfobot` で確認可）
- VPS SSH接続情報（IPは既知: 163.44.101.31。接続ユーザー・鍵ファイルパスをユーザー確認）

### 完了条件
- [ ] `secrets.yaml.example` に `bot_token` / `chat_id` の記載例と取得方法コメントがある
- [ ] VPS上の `secrets.yaml` に実値が記入されている（gitignore対象のため確認はssh経由）
- [ ] `notify.py` の `send_alert` / `send_summary` が実際にTelegramメッセージを届ける
- [ ] bot_token/chat_id が空のとき `send_alert` / `send_summary` がクラッシュせずログのみ出す
- [ ] テスト実行結果（メッセージ受信のスクリーンショットまたはAPI応答）をユーザーが確認している

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | 実値設定時に `send_alert` がTelegramメッセージを正常送信し、APIがHTTP 200を返す | 機能要件 | 35 |
| 2 | 実値設定時に `send_summary` がTelegramメッセージを正常送信し、APIがHTTP 200を返す | 機能要件 | 20 |
| 3 | bot_token/chat_id が空のとき両関数が例外なく継続し、WARNログを出す | エラーハンドリング | 25 |
| 4 | `secrets.yaml.example` に取得手順コメントがあり、gitignoreが `secrets.yaml` を管理外にしている | 可読性・セキュリティ | 10 |
| 5 | VPSのcronが次回実行でサマリ通知を受信できる（実通知確認） | 完了条件の充足率 | 10 |
| 合計 | | | 100 |

---

## 工程2: セッション永続化（persistent_context化）

### 背景
現行の `_start()` は `browser.new_context(storage_state=path)` で揮発コンテキストを生成する。リフレッシュされたCookieがプロファイルに書き戻されないためセッション寿命が約2時間で尽きる。Playwright の `launch_persistent_context(user_data_dir=...)` はブラウザ起動と同時にユーザーデータディレクトリを使用し、セッション更新をディスクに書き戻す。

### 変更の核心（実装者向け参照情報）
- **変更前**: `chromium.launch()` → `browser.new_context(storage_state=path)`
- **変更後**: `chromium.launch_persistent_context(user_data_dir=str, headless=bool, args=[...])` を使用。`launch_persistent_context` は `BrowserContext` を直接返す（`Browser` オブジェクトは存在しない）。`storage_state=` パラメータは不要になる（user_data_dir が代替）。
- `_start()` / `_stop()` のライフサイクルを `Browser`なし構造に調整する。
- `user_data_dir` は既存の `cfg.playwright.user_data_dir` (= `./.auth/chromium`) をそのまま流用。VPS上の `.auth/chromium/` が persistent profile として機能する。
- 初回移行時: 既存の `storage_state.json` から `user_data_dir` へCookieをインポートする手順または移行スクリプトを用意する（既存stateがある場合の互換性担保）。

### リスクとフォールバック
- **リスク**: persistent_context化でもNotebookLMのセッション寿命が延びない場合がある（Googleがセッション更新を行わないUI遷移パターンの場合等）。このため「best-effort」と位置づける。
- **フォールバック**: 延びなかった場合は工程3の半自動再認証（定期的にCookieを新鮮に保つ）で対応する。工程3は工程2の成否によらず実施する。
- **UIセレクタ変更耐性**: 全セレクタは `notebooklm.py` 上部定数に集約済み。persistent_context化後もセレクタは変更しない。

### 中間成果物
- 改修済み `notebooklm.py`（`launch_persistent_context` 使用）
- 移行手順メモ（または移行スクリプト）
- VPSへ反映し、次回cronで `SessionExpiredError` なしに動作することを確認

### 機密が必要な箇所
- VPS SSH接続情報（user_data_dir の確認・ファイル操作に使用）
- `storage_state.json` の現在の存在場所（VPS `/opt/notebooklm-sync/.auth/chromium/storage_state.json`）

### 完了条件
- [ ] `notebooklm.py` の `_start()` が `launch_persistent_context` を使用している
- [ ] `Browser` オブジェクトを保持する変数 `self._browser` が削除されている（またはNoneのまま不使用）
- [ ] VPS上で `python src/sync.py --dry-run` が正常終了する
- [ ] VPS上で実際に新規動画追加の cron run が `SessionExpiredError` なしに完了する（または認証が維持されていることをログで確認）
- [ ] ローカルの `setup_auth.py` が persistent_context 構造でも引き続き `storage_state.json` を生成できる（互換性維持。setup_auth は CDP接続のため変更不要だが、VPS側の配置先が変わる場合は確認する）
- [ ] `_stop()` が `context.close()` のみで完結し、`browser.close()` を呼ばない構造になっている

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | `_start()` が `launch_persistent_context` を使い、`browser.new_context` を呼ばない | 機能要件 | 30 |
| 2 | `_stop()` が `Browser.close()` を呼ばず `context.close()` のみで正常終了する | 機能要件 | 15 |
| 3 | VPS上で `--dry-run` 実行が正常終了し、ログに `SessionExpiredError` が出ない | 機能要件 | 25 |
| 4 | 既存 `storage_state.json` がある場合の初回移行手順が明示されている | 可読性 | 10 |
| 5 | `self._browser` の残留参照が除去されており、型アノテーションと `_stop()` が整合している | 可読性 | 10 |
| 6 | `add_youtube_source` / `rename_source` / `delete_source` 等の公開メソッドのシグネチャが変わっていない（後方互換） | 既存コードとの一貫性 | 10 |
| 合計 | | | 100 |

---

## 工程3: 定期再認証半自動化 + セッション切れ通知

### 背景
セッションが切れた場合の回復が完全手動（ローカルで `setup_auth.py` → VPSへ手動scp）。工程2で寿命は延びるが、最終的には切れる。対策は2層:
- **(a) プロアクティブ**: Windowsタスクスケジューラで定期的（例: 毎週月曜朝）に自動再認証→自動scp転送
- **(b) リアクティブ**: `SessionExpiredError` 発生時にTelegramアラートを即送信（工程1の通知基盤を利用）

> 注: 弱点3の時点で `sync.py` 内 `SessionExpiredError` catch ブロックには既に `send_alert` 呼び出しがある。工程1のsecrets設定完了後は自動的に通知が届くようになる。工程3の実装作業は主に **(a) プロアクティブ自動化** の側。

### 作成するファイル一覧

```
notebooklm-sync/
  scripts/
    auto_reauth.bat          # タスクスケジューラのアクション。本文ASCII限定
    auto_reauth.ps1          # 実処理: setup_auth.py実行 + scp転送
    README_auto_reauth.md    # 手順・セットアップ案内（日本語可）
```

### `auto_reauth.ps1` の処理フロー

1. Chrome（`--remote-debugging-port=9222`）が未起動なら `start_chrome_for_auth.ps1` を呼ぶ
2. 起動確認後 `python scripts/setup_auth.py` を実行し `storage_state.json` を生成
3. `scp` または `ssh + cat` で VPS `/opt/notebooklm-sync/.auth/chromium/storage_state.json` へ転送
4. 転送成功/失敗をWindowsイベントログに記録（またはローカルログファイルへ追記）

### タスクスケジューラ設定仕様

| 項目 | 値 |
|---|---|
| タスク名 | `YNFactory-NotebookLMReAuth` |
| トリガー | 毎週月曜日 05:00（朝ブリーフィング YNFactory-MorningBriefing より前） |
| アクション | `cmd.exe /c "scripts\auto_reauth.bat"` |
| 開始場所 | `notebooklm-sync/` の絶対パス |
| バックグラウンド実行 | あり（ログオン不要ではなくログオン時のみ。Chrome UIが必要なため） |

### `.bat` ファイルのASCII制約対応
- `auto_reauth.bat` 本文はASCII英語のみ（CP932誤読防止）
- 日本語のセットアップ手順・注意書きはすべて `README_auto_reauth.md` に記載

### scpに必要な情報（実装フェーズでユーザー確認を要するもの）

| 情報 | 備考 |
|---|---|
| SSH接続ユーザー | 例: `root` または専用ユーザー |
| SSH秘密鍵パス（ローカル） | 例: `%USERPROFILE%\.ssh\notebooklm_vps` |
| VPS上の転送先パス | `/opt/notebooklm-sync/.auth/chromium/storage_state.json` |
| VPS IPアドレス | 163.44.101.31（既知） |

### 機密が必要な箇所
- SSH秘密鍵ファイルのパス（`auto_reauth.ps1` にハードコードせず設定ファイルまたは環境変数で参照する設計にする）
- VPS SSH接続ユーザー名

### 完了条件
- [ ] `auto_reauth.bat` が存在し、本文がASCII英語のみである
- [ ] `auto_reauth.ps1` が `setup_auth.py` を呼び出し、成功後に `scp` でVPSへ転送する
- [ ] SSH秘密鍵パス・ユーザー名がスクリプト本文にハードコードされず、設定可能な変数として冒頭にまとめられている
- [ ] `README_auto_reauth.md` にタスクスケジューラ登録手順（UIまたは `schtasks` コマンド例）が記載されている
- [ ] Windowsタスクスケジューラへの登録が完了し、手動実行（「今すぐ実行」）で `storage_state.json` のVPS転送が成功する
- [ ] `sync.py` の `SessionExpiredError` catch ブロックが `send_alert` を呼んでおり、工程1のsecrets設定後にアラートが届くことをログで確認している（既存実装の確認）
- [ ] `README_auto_reauth.md` にフォールバック手順（手動scp手順）が記載されている

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | `auto_reauth.ps1` が `setup_auth.py` → scp転送の一連を正常実行できる | 機能要件 | 30 |
| 2 | タスクスケジューラ手動実行で `storage_state.json` がVPSへ正常転送される | 機能要件 | 25 |
| 3 | `.bat` 本文がASCII英語のみで、CP932環境で正常実行できる | 機能要件 | 15 |
| 4 | SSH鍵・ユーザー名が変数として冒頭に集約され、ハードコードされていない | セキュリティ | 15 |
| 5 | `README_auto_reauth.md` にタスクスケジューラ登録手順とフォールバック手順が揃っている | 可読性 | 10 |
| 6 | `SessionExpiredError` 発生時にTelegramアラートが届くことをログ/実機で確認している | 完了条件の充足率 | 5 |
| 合計 | | | 100 |

---

## 全体の完了条件

- [ ] 工程1: VPS上の `secrets.yaml` に実値が入り、TelegramでサマリとアラートをTestで受信できる
- [ ] 工程2: `notebooklm.py` が `launch_persistent_context` を使い、VPSで `--dry-run` 正常完了
- [ ] 工程3: タスクスケジューラの手動実行で `storage_state.json` がVPSへ自動転送される
- [ ] 工程3完了後: `SessionExpiredError` 発生時にTelegramアラートが届くことが確認されている
- [ ] git commit が作成されている（secrets.yaml・storage_state.json・.auth/ はgitignore対象のため含まない）

---

## リスク一覧

| リスク | 影響 | 緩和策 |
|---|---|---|
| persistent_context化でもセッション寿命が延びない | 工程2の効果なし | 工程3の定期再認証（週1）で最新Cookieを維持 |
| NotebookLM UIのセレクタ変更 | `add_youtube_source` 等が失敗 | セレクタは `notebooklm.py` 上部定数に集約済み。変更時はそこだけ修正 |
| タスクスケジューラ実行時にChromeが既に起動している | scp転送が成功してもCookieが古い可能性 | `start_chrome_for_auth.ps1` の既存Chrome検出ロジックで対処（既に実装済み） |
| VPS SSH接続の失敗（鍵不備等） | scp転送が完了しない | スクリプト終了コードで失敗を検出しWindowsイベントログに記録。Telegram通知は別手段（工程1依存）では行わない（ローカル側の障害のため） |
| secrets.yaml の git 誤コミット | 認証情報の露出 | `.gitignore` で `secrets.yaml` を管理外に。VPSのみに置く |

---

## 備考

- 各工程は必ず **executor → quality-checker (85点以上で合格、最大5回)** のループで実行する
- 工程1が完了するまで工程2・3の VPS 反映で通知検証はできない（工程1を先行させること）
- VPS反映手段: `git pull` + `.venv` 環境はそのまま流用。新規 pip パッケージの追加がある場合は `pip install -r requirements.txt` も実施
- `storage_state.json` / `.auth/` / `secrets.yaml` はgitignore対象。VPS上は `/opt/notebooklm-sync/` 直下にローカル配置
- 実装フェーズ開始前にユーザーから提供が必要な情報: (1) Telegram bot_token, (2) Telegram chat_id, (3) VPS SSH接続ユーザー名, (4) VPS SSH秘密鍵のローカルパス

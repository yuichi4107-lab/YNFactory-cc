# 要件定義書
# NotebookLM YouTube自動同期システム VPS→Mac移設

作成日: 2026-06-06
起票: 秘書（実機確認済み事実を前提に策定）

---

## ゴール

ConoHa VPS(163.44.101.31)で稼働中のNotebookLM YouTube自動同期システムを、このMac（residential IP・実Chrome永続プロファイル認証）へ移設し、Google セッション失効を根本解消した上で30分間隔の自動同期を安定稼働させる。

---

## スコープ

### やること
- Mac上にPython 3.11 venvとPlaywright(chrome channel)を構築する
- `src/notebooklm.py`のブラウザ起動を `chromium.launch()` + `storage_state静的注入` から `launch_persistent_context(user_data_dir=..., channel="chrome")` へ改修する
- ランタイム一式（venv・`.auth`Chromeプロファイル・`state.sqlite`・`logs/`）をDrive外（`~/notebooklm-sync/`）へ配置する
- VPSの`state.sqlite`をMacへ移行する（既存53動画の重複追加を防ぐ）
- 専用Telegram botの`secrets.yaml`を作成し失効アラートを有効化する
- `com.ynfactory.notebooklm-sync.plist`をlaunchdに登録し30分毎に自動実行する
- VPSのcronを停止する（VPSは削除せずフォールバックとして存置）
- E2Eで動作検証しHANDOFF・READMEを更新する

### やらないこと
- VPSの削除・インフラ変更（cron停止のみ）
- 既存`@bijinh_bot`の流用（新ボット専用）
- Drive上の`notebooklm-sync/`ディレクトリの削除（ソース/バックアップとして維持）
- NotebookLMのUI自動化ロジック（セレクタ等）の変更
- `config.yaml`のチャンネル設定変更（AI仙人/株式会社AXの2チャンネルのまま）
- caffeinate等のMacスリープ対策（launchd復帰時自己回復を前提とし任意扱い）
- `state.py`の`db_path`デフォルト値の変更（off-Drive cwdで実行することで自然解決）

---

## オーナー依存事項（ブロッカー）

以下2点はオーナーの操作が必要であり、該当工程の着手前に完了していること:

| # | 依存事項 | 必要タイミング |
|---|---|---|
| A | BotFatherで新規bot作成→トークンを提供 | 工程3着手前 |
| B | 新botに`/start`を送信（chat_id=`8571447808`で受信確認） | 工程3着手前 |
| C | Mac上でブラウザを起動しGoogleアカウントへ対話的ログイン | 工程2着手時（executorが手順を案内、オーナーが実操作） |

---

## 工程一覧

| 工程 | 内容 | 中間成果物 | 入力 |
|---|---|---|---|
| 工程1 | Macランタイム構築 | `~/notebooklm-sync/`環境・venv・state.sqlite移行完了 | ユーザー入力・VPS state.sqlite |
| 工程2 | 認証永続化改修 | `notebooklm.py`改修・Chromeプロファイル初期ログイン完了 | 工程1の成果物・オーナー依存(C) |
| 工程3 | 専用Telegram通知設定 | `secrets.yaml`作成・通知疎通確認 | 工程1の成果物・オーナー依存(A)(B) |
| 工程4 | スケジューラ設定・VPS切替 | launchd plist登録・VPS cron停止 | 工程1〜3の成果物 |
| 工程5 | E2E検証・ドキュメント更新 | 全条件通過・HANDOFF/README更新 | 工程1〜4の成果物すべて |

---

## 工程1: Macランタイム構築

### 完了条件
- [ ] `brew install python@3.11` が完了し `python3.11 --version` が `3.11.x` を返す
- [ ] `~/notebooklm-sync/` ディレクトリがDrive外に存在し、Drive上 `notebooklm-sync/` のソースがコピーされている
- [ ] `~/notebooklm-sync/.venv/` が `python3.11 -m venv` で作成されている
- [ ] `requirements.txt` の依存パッケージがvenv内にすべてインストールされている
- [ ] `playwright install chrome` が完了し `/Applications/Google Chrome.app` をPlaywrightが認識できる
- [ ] VPSから`state.sqlite`（および`-wal`/`-shm`があれば）をMacの `~/notebooklm-sync/state.sqlite` へ移行済みである
- [ ] `~/notebooklm-sync/.auth/` ディレクトリが作成されている（Chromeプロファイル格納先）
- [ ] `~/notebooklm-sync/logs/` ディレクトリが作成されている
- [ ] Drive上の `notebooklm-sync/` は削除されていない（ソース維持）

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | `python3.11 -c "import sys; print(sys.version)"` が 3.11.x を出力する | 機能要件 | 20 |
| 2 | venv内で `python -c "import playwright"` がエラーなく完了する | 機能要件 | 20 |
| 3 | `~/notebooklm-sync/` がDrive外（`~/Library/CloudStorage`配下でない）に存在する | 機能要件 | 20 |
| 4 | `~/notebooklm-sync/state.sqlite` が存在し `sqlite3 state.sqlite "SELECT count(*) FROM processed_videos"` が53以上を返す | データ完全性 | 25 |
| 5 | `.auth/` および `logs/` ディレクトリが存在する | 機能要件 | 10 |
| 6 | Drive上の `notebooklm-sync/` が引き続き存在する（削除されていない） | 完了条件の充足 | 5 |
| 合計 | | | 100 |

---

## 工程2: 認証永続化改修（notebooklm.py改修 + 初回ログイン）

### 背景
現行コードは `chromium.launch()` + `new_context(storage_state=storage_state.json)` 方式。
これをPlaywrightの `launch_persistent_context(user_data_dir=..., channel="chrome")` に置き換え、
実ChromeがCookieを自動更新する方式へ移行する。`STORAGE_STATE_FILENAME` 定数および
`_storage_state_path()` メソッドは削除対象となる。

### 改修対象
- ファイル: `~/notebooklm-sync/src/notebooklm.py`
- 変更箇所: `NotebookLMClient.__init__()` のコンストラクタシグネチャ、`start()` メソッド内のブラウザ起動処理

### 改修仕様
```
# 変更前（概念）
browser = playwright.chromium.launch(headless=True)
context = browser.new_context(storage_state="path/to/storage_state.json")

# 変更後（概念）
context = playwright.chromium.launch_persistent_context(
    user_data_dir="~/notebooklm-sync/.auth",
    channel="chrome",
    headless=True,   # 初回ログイン後はTrue。初回のみFalseで起動してログイン操作
)
browser = context.browser
```

### 初回ログイン手順（オーナー操作）
1. executorが `headless=False` で一時起動スクリプトを用意
2. オーナーがターミナルで実行→Chromeウィンドウが開く
3. オーナーがNotebookLM / Google アカウントへログイン
4. ログイン完了を確認後スクリプト終了→`.auth/`にプロファイルが永続化される
5. 以降は `headless=True` で起動・セッション継続

### 完了条件
- [ ] `notebooklm.py` が `launch_persistent_context(user_data_dir=..., channel="chrome")` を使用している
- [ ] `STORAGE_STATE_FILENAME` 定数・`_storage_state_path()` メソッドが削除またはDead Code化されている（storage_state静的注入が行われていない）
- [ ] `~/notebooklm-sync/.auth/` 配下にChromeプロファイルファイル（`Default/`, `Cookies`等）が生成されている
- [ ] `python src/sync.py --dry-run` を `~/notebooklm-sync/` をcwdとして実行し、`SessionExpiredError` が発生せず差分候補ログが出力される
- [ ] `--dry-run` のログに「Google session expired」が含まれていない

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | `launch_persistent_context` + `channel="chrome"` が使われており `new_context(storage_state=...)` が消えている | 機能要件 | 30 |
| 2 | `.auth/` にChromeプロファイルデータが存在する | 機能要件 | 20 |
| 3 | `--dry-run` がSessionExpiredErrorなしで完走する | 機能要件 | 30 |
| 4 | `--dry-run` ログにセッション失効を示す文字列がない | エラーハンドリング | 15 |
| 5 | 改修後のコードに既存のUIセレクタ定数・ロジックが保持されている（回帰なし） | 既存コードとの一貫性 | 5 |
| 合計 | | | 100 |

---

## 工程3: 専用Telegram通知設定

### 前提条件
- オーナー依存(A): 新規botトークン提供済み
- オーナー依存(B): 新botに `/start` 送信済み（chat_id=`8571447808` で受信可能な状態）

### 完了条件
- [ ] `~/notebooklm-sync/secrets.yaml` が作成されており `bot_token` に新ボットのトークン、`chat_id` に `8571447808` が設定されている
- [ ] `secrets.yaml` は `.gitignore` に含まれており（既存の除外設定）Driveに同期されないことを確認済み
- [ ] `python tests/test_notify.py`（または相当のスクリプト）を実行し、chat_id `8571447808` にテストメッセージが届く
- [ ] `secrets.yaml` が存在しない状態で `notify.py` の `send_alert` を呼び出してもプロセスがクラッシュしない（既存の「スキップして継続」挙動を確認）

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | `secrets.yaml` が正しいトークン・chat_idで作成されている | 機能要件 | 25 |
| 2 | テスト送信でTelegramにメッセージが実際に届く | 機能要件 | 40 |
| 3 | `secrets.yaml` がgit管理外であることを `git status` で確認 | セキュリティ | 20 |
| 4 | secrets未設定時のフォールバック（ログのみ出力・クラッシュなし）が機能する | エラーハンドリング | 15 |
| 合計 | | | 100 |

---

## 工程4: スケジューラ設定・VPS切替

### launchd plist仕様
- Label: `com.ynfactory.notebooklm-sync`
- ProgramArguments: `[python3.11 (venv内), src/sync.py]`
- WorkingDirectory: `~/notebooklm-sync/`（off-Drive絶対パス、state.sqlite等の相対パスがDrive外に自然解決）
- StartInterval: `1800`（30分毎）
- StandardOutPath: `~/notebooklm-sync/logs/launchd-stdout.log`
- StandardErrorPath: `~/notebooklm-sync/logs/launchd-stderr.log`
- RunAtLoad: `false`（誤発火防止）
- 保存先: `~/Library/LaunchAgents/com.ynfactory.notebooklm-sync.plist`

### VPS側作業
- VPS SSH接続して `crontab -e` または `crontab -r` でNotebookLM同期cronを停止
- VPSのcron設定変更内容をメモしてHANDOFFに記録（フォールバック復活手順として）

### 完了条件
- [ ] `~/Library/LaunchAgents/com.ynfactory.notebooklm-sync.plist` が存在する
- [ ] `launchctl load ~/Library/LaunchAgents/com.ynfactory.notebooklm-sync.plist` が成功する
- [ ] `launchctl list | grep notebooklm` でサービスが登録されている
- [ ] launchdが1回発火した後（または手動で `launchctl start com.ynfactory.notebooklm-sync` ）、`logs/launchd-stdout.log` にsyncログが出力される
- [ ] VPS(163.44.101.31)のcrontab から NotebookLM同期の行が削除（またはコメントアウト）されている
- [ ] plistの `WorkingDirectory` がDrive外の絶対パスに設定されている

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | launchd plistが正しい形式で登録・ロードされている | 機能要件 | 25 |
| 2 | `launchctl start` 手動発火でsyncが実行されログが出る | 機能要件 | 30 |
| 3 | `WorkingDirectory` がDrive外の絶対パスである | 機能要件 | 20 |
| 4 | VPS crontabのNotebookLM同期エントリが停止されている | 完了条件の充足 | 20 |
| 5 | VPS停止設定がHANDOFFに記録されている（フォールバック手順付き） | 完了条件の充足 | 5 |
| 合計 | | | 100 |

---

## 工程5: E2E検証・ドキュメント更新

### 検証シナリオ

#### シナリオA: dry-run差分確認
- `python src/sync.py --dry-run` をcwd=`~/notebooklm-sync/` で実行
- 期待結果: SessionExpiredError発生なし、未処理動画候補がログ出力される

#### シナリオB: 実追加1件検証
- テスト用YouTubeURLを1件指定（またはconfig.yamlの既存チャンネル最新動画1件）
- `sync.py`（dry-runなし）を実行し、NotebookLMの対象ノートブックにソースが追加されることを確認
- `state.sqlite`の`processed_videos`テーブルに同video_idが記録されていることを確認
- 同じURLで再実行しても重複追加されないことを確認

#### シナリオC: Telegram通知確認
- sessionExpiredをモック、またはsend_summaryを直接呼び出し
- chat_id `8571447808` に通知が届くことを実機で確認

#### シナリオD: スケジュール自動発火確認
- Macをスリープ→復帰後、launchdが自動実行されてログが更新されることを確認（またはStartIntervalの30分待機で確認）

#### シナリオE: 重複追加なし確認
- VPSから移行した`state.sqlite`の既存53動画のIDが `processed_videos` に存在することをSQLで確認
- 同IDの動画でsyncを実行しても追加がスキップされることを確認

### 完了条件
- [ ] シナリオA: dry-runがSessionExpiredErrorなしで完走する
- [ ] シナリオB: NotebookLMのノートブックUIで新ソースの追加が目視確認できる（または追加試行のログが成功を示す）
- [ ] シナリオB: 同URLで再実行しても「already processed」等でスキップされる
- [ ] シナリオC: Telegramアプリで通知メッセージを実機確認する
- [ ] シナリオD: launchdの自動発火でログが更新される（手動発火での代替可）
- [ ] シナリオE: 既存動画IDがDBに存在し重複追加されない
- [ ] `README.md` にMac移設後の実行環境・セットアップ手順が記載されている
- [ ] `.company/secretary/HANDOFF.md` がMac移設完了・VPS停止状態・次アクションを反映している

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | dry-runがSessionExpiredなしで完走する（シナリオA） | 機能要件 | 20 |
| 2 | 実追加1件がNotebookLMで確認できる（シナリオB） | 機能要件 | 25 |
| 3 | 重複追加が発生しない（シナリオB・E） | データ完全性 | 20 |
| 4 | Telegram通知が実機に届く（シナリオC） | 機能要件 | 15 |
| 5 | launchd自動発火でログが更新される（シナリオD） | 機能要件 | 10 |
| 6 | README・HANDOFFが移設後の状態を正確に反映している | 完了条件の充足 | 10 |
| 合計 | | | 100 |

---

## 備考

### パス設計の整理

| 種別 | パス | Drive同期 |
|---|---|---|
| ソースコード（正本） | Drive上 `notebooklm-sync/` | あり（意図的） |
| ソースコード（実行コピー） | `~/notebooklm-sync/src/` | なし |
| venv | `~/notebooklm-sync/.venv/` | なし |
| Chromeプロファイル | `~/notebooklm-sync/.auth/` | なし |
| state.sqlite | `~/notebooklm-sync/state.sqlite` | なし |
| logs | `~/notebooklm-sync/logs/` | なし |
| secrets.yaml | `~/notebooklm-sync/secrets.yaml` | なし（.gitignore済み） |
| launchd plist | `~/Library/LaunchAgents/com.ynfactory.notebooklm-sync.plist` | なし |

### 既知リスク

| リスク | 影響 | 対策 |
|---|---|---|
| Macが長時間スリープ | 同期遅延（最大スリープ時間分） | launchd復帰時自己回復で許容。caffeinate任意 |
| Google Chrome 148がPlaywright chromiumと非互換 | 工程2ブロック | playwright install chrome で確認。問題時はchannelを"chromium"に戻す検討 |
| VPS state.sqlite取得時のWALロック | データ破損リスク | VPS cronを先に停止してからsqlite3 `.backup`コマンドで安全コピー |
| 新bot /start未送信 | secrets.yaml設定しても通知不到達 | 工程3前にオーナー依存(B)を必ず確認 |
| NotebookLM UI変更 | セレクタ不一致でソース追加失敗 | 工程5シナリオBで発覚→UIセレクタ定数を修正（本要件定義のスコープ外） |

### VPS存置・復活手順（フォールバック）
- VPSはcron停止のみ。インスタンスは削除しない
- Mac側が長期停止する場合: VPS cronを再有効化すれば即時フォールバック可能
- ただしVPS側のstate.sqliteはMac移行後に更新されないため、再有効化時は差分同期に注意

---

## 実施結果（2026-06-06 完了）

**全工程完了。システムはこのMacで launchd により自動稼働中。**

### 重要な実装上の変更（実測に基づく要件からの逸脱）
工程2の認証方式は、要件記載の `launch_persistent_context(channel="chrome")` ではなく
**「常駐させた素の実Chrome（`--headless=new --remote-debugging-port=9222`、自動化フラグなし）に
Playwright が `connect_over_cdp` で接続する方式」** を採用した。
理由: 実測で launch_persistent_context（Playwright自前起動）は headless/自動化フラグにより
Google にログインへリダイレクトされ失効した（residential IP でも不可）。素の実Chrome＋CDPなら通る。
副次対応として、狭いビューポートでソースパネルが畳まれセレクタが出ないため `set_viewport_size(1600x1000)` を強制。

### 完了条件の達成状況（証跡）
- ✅ python@3.11(3.11.15) venv + 依存 + 実Chrome(channel=chrome) が Drive外 `~/notebooklm-sync/` で動作
- ✅ `notebooklm.py` は CDP接続方式（`connect_over_cdp`）。storage_state静的注入は除去済
- ✅ `check_session.py` で SESSION OK（リダイレクトなし）・ソース読取 44 件
- ✅ 実追加1件成功（`bogsZSiAwmY`「Claude Mythos…」を AI仙人へ）→ ソース 44→45
- ✅ Chrome再起動後もセッション維持を実証（Mac再起動でも復帰見込み）
- ✅ 専用bot @mnb121_bot の `secrets.yaml`（Drive外・600・git管理外）で test_notify 送信成功（HTTP200）
- ✅ launchd `com.ynfactory.notebooklm-chrome`（headless常駐・KeepAlive）＋ `com.ynfactory.notebooklm-sync`（30分毎）登録・手動発火で `sync complete`
- ✅ VPS cron停止（`/opt/notebooklm-sync/crontab.backup.20260606` 保存・VPS存置）＋ state.sqlite 53件移行・重複追加なし
- ✅ README更新（Mac運用・再ログイン手順）／新コードをDriveソースへrsync反映

### 既知の軽微な残課題
- 新着追加時の `[YYYY-MM-DD]` リネームは時々 `rename_skipped`（元々87%・見た目のみ・追加自体は確実）

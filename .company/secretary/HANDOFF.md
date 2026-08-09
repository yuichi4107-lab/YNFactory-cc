---
last_updated: "2026-08-09"
last_device: "Windows"
last_session_summary: "再編で移動した `.company/*` 参照を実行系101ファイル・約3,900箇所で正規パスへ統一し（shorts-factoryの出力先を 03_成果物/outputs/shorts-factory へ変更、壊れていたDriveミラーとSNS認証パスも修復）、廃止済み運用を記述していた `.company/CLAUDE.md`・`.company/secretary/CLAUDE.md` を 99_その他/company-records/ へ退避して規範を 02_設定/docs/ に一本化した（固有内容は owner-profile.md と company-ops.md へ移設、company スキルに廃止バナー）。さらに `/handoff` の対となる `/start` スキルと session_start.py を新設。pull-sync がDriveを上書きする危険に対し、pullで書き換わるパスだけを照合して別PCの未push編集を検出したら止まる仕組みにし、最新時・衝突時・正常pull時の3ケースを実機検証した。commit 8786c49 / aa6ce83 / ba563e2 / f6e40cd / f1c3c6e。"
next_action: "Mac側で `bash 05_プロジェクト/shorts-factory/scripts/deploy.sh`（installなし）を実行し、shorts-factory の出力先変更とDriveミラー・SNS認証パスの修正を runtime へ反映する（未実行のうちは旧パスを見たまま動く）。あわせて04:00のTopview定期補充が8本完了し、3動画が当日バッチから6素材を消費して予備2素材が残るかを確認する。"
---

# セッション引き継ぎ

## このファイルの書き方（2026-08-08 改定）

- **frontmatter は上記4キー固定**。`last_updated` / `last_device` / `last_session_summary` / `next_action` のみ。
  **キー名に日付やトピックのサフィックスを付けない。毎回まるごと上書きする**（追記しない）。
- **本文は「今の状態」だけ**。進行中・ブロック中・稼働中・保留のみを置く。1案件は原則10行以内。
- **完了した案件は本文から消して `archive/` へ移す**。完了報告を本文に残さない。
- **セッション要約の履歴は `handoff-log/YYYY-MM.md` へ追記する**。このファイルには積まない。
- **技術・環境メモは `tech-notes.md`**。ここには書かない。
- **上限 400行 / 60KB**。超えたらハンドオフ時に必ず整理してから終える。
- 各項目には `(最終更新: YYYY-MM-DD)` を付け、古い記述が見分けられるようにする。

## 進行中（要アクション）

### shorts-factory — 定刻生成・Topview在庫 (最終更新: 2026-08-09)

- **状態**: 8/9の09時・14時はTopview混在動画を生成し、19時は**未使用素材0本／必要2本**で安全停止した。動画・キュー・投稿は作成されていない。runtime healthは `ok=true`、queue=243、媒体欠損・台帳異常なし。
- **定期補充**: Codex cron `topview-4-8` を有効化。毎日04:00（Asia/Tokyo）にTopviewで実写素材8本を生成・書き出し・登録する。当日9/14/19時の3動画は登録時刻で当日バッチを優先し6素材を使い、残り2素材を予備として残す。前日以前の未使用素材は当日分が不足した時だけ使う。既存クレジットのみを利用し、追加購入・プラン変更・投稿はしない。ログイン切れ、クレジット不足、重複、8本未完了では安全停止する。
- **通知**: TelegramはTopview在庫の安全停止だけを簡潔に伝え、生の外部応答・URL・旧経路名を転送しない。修正はMac runtimeへ `deploy.sh`（installなし）で反映済み。
- **要対応**: 次枠の前にTopview素材を補充する。未使用素材は最低2本、3枠/日を安定運用するなら6本以上必要。720p素材を使う場合は初回の仕上がりを目視する。
- **次の補充**: Canvas `654e5964324b4707b12c890e13249039` に未書き出しの Video 3〜7・10・11 が残る。まずここから確認し、足りなければ新規生成（1本約15クレジット）をオーナー承認のうえ実施。
- **書き出し手順**: Canvasでクリップ選択 → ツールバーの ⬇ → 数十秒待って `~/Downloads` を確認 → `~/shorts-factory/topview_assets/` へ移動 → `cd ~/shorts-factory/app && ~/shorts-factory/.venv/bin/python scripts/register_topview_assets.py <file...>`。保存の反映に時間差があるので、直後にファイルが無くてもブロックと即断しない。投稿済み素材（`Video_12`）は再登録しない。
- **注意**: Windowsからは `fcntl` 依存で pipeline 実行・deploy ともに不可。runtime操作はMacで行う。
- **詳細**: `05_プロジェクト/shorts-factory/`、`.company/projects/shorts-factory/2026-07-16-drive-lock-root-fix-debug-log.md`

### Drive↔GitHub 同期の確立 — 完了 (最終更新: 2026-08-09)

- **到達点**: Drive を正として GitHub を合わせ、そのうえで **Drive も6バケット構成へ移行**して両者を一致させた。追跡2,384件で Driveに無い0件・内容相違0件（開始時は Driveに無い544件・内容相違296件）。
- **運用サイクル（これが本題）**: **セッション開始時に `pull-sync`（GitHub→Drive）／終了時に `/handoff` で `commit-push`（Drive→GitHub）**。`CLAUDE.md`・`02_設定/docs/company-ops.md`・`multi-pc-rules.md` §5・handoffスキルに明記済み。
  ```bash
  cd C:\YNFactory-cc   # Mac は ~/YNFactory-cc
  python 01_コード/scripts/company/sync_drive_git.py pull-sync
  ```
- **`.company/` の現在**: `secretary/`・`DASHBOARD.md`・`codex/`・`logs/` のみ。旧部署15フォルダは `99_その他/company-records/`、requirements は `02_設定/requirements/`、scripts は `01_コード/scripts/company/`、outputs は `03_成果物/outputs/` へ移動済み（Drive側の移動記録 `99_その他/2026-08-09-cleanup/MANIFEST.md`）。
- **復元点**: タグ `pre-drive-mirror-2026-08-08` / `pre-bucket-remirror-2026-08-09`（いずれもGitHubへpush済み）。commit `0b80c0f` → `70c2a0b` → `72f7ec5`。
- **注意1**: `pull-sync` は「pullで新たに取得した差分」しかDriveへ流さず、対象パスは**上書き**する。別PCがDrive上で同じファイルを編集中だと古い内容で潰れうる。実際 2026-08-09 に Windows 整理中と Mac セッションが `HANDOFF.md` と `shorts-factory/src/pipeline.py` で同時編集した。
- **注意2（対応済み・Mac反映待ち）**: 再編で移動した `.company/*` 参照を、スキル・設定・コード計101ファイル／3,900箇所超で正規パスへ統一した（commit `8786c49`）。shorts-factory は `drive_outputs_dir` → `03_成果物/outputs/shorts-factory`、`drive_marketing_dir` → `99_その他/company-records/marketing/shorts-factory`、`drive_sns_env_path` → `99_その他/company-records/engineering/sns-credentials/.env`。**Mac runtime へ `deploy.sh`（installなし）を実行するまで実機の挙動は変わらない。**
- **規範の一本化（完了 2026-08-09）**: 廃止済み運用を記述していた `.company/CLAUDE.md` と `.company/secretary/CLAUDE.md` を `99_その他/company-records/` へ退避（廃止注記つき）。固有内容は `02_設定/docs/owner-profile.md`（オーナー情報・対話スタイル）と `company-ops.md`（定期巡回）へ移設。両ファイルを前提にしていた `company` スキルにも廃止バナーと現行参照先の対応表を付けた。`.company/` は `secretary/`・`DASHBOARD.md`・`codex/`・`logs/`・`handoff/` のみ。
- **障害と復旧**: ローカルGitの `refs/heads/main` ほか3refがNUL埋めで破損（commitは成功済みでreflogから復旧）。破損refは `_archive/git-drive-quarantine/2026-08-09-broken-refs/` に隔離、`git fsck` クリーンを確認。

## ブロック中（オーナー操作・外部要因待ち）

| 案件 | ブロッカー | 解除に必要な操作 | 最終更新 |
|---|---|---|---|
| SNS導線の受け皿（営業） | Googleフォームの編集権限が `yuichi4107@gmail.com` に無い（オーナーは `y-nakada@yn-factory.com`） | オーナーアカウントでフォームを14項目仕様へ更新／LPのCloudflare Pages公開承認 | 2026-06-19 |
| Meta SNS 自動投稿 Step6 | use case追加のみで個別権限が未有効。`pages_manage_posts` 等がGraph API Explorerに出ない | Meta Console でアプリの権限を個別に Add | 2026-05-06 |
| ebook-to-manga vol2-4 再生成 | CSV完了・codex-handoffバンドル3本投入済みで Codex CLI 起動待ち | Codex側で画像生成を実行 | 2026-04-26 |
| マンガ版『ChatGPT 5.5時代の結論』 | シナリオv3までQC97点PASS。次フェーズ（パネルCSV→画像→EPUB）が承認待ち | オーナーが仕上がりを見て次フェーズ着手を判断 | 2026-05-12 |
| AI投資 ショート戦略 Phase2 | Binance Futures API Key 未発行 | オーナーがKey発行・設定（工程7の本番最小額検証） | 2026-04-18 |
| 日本株デイトレ `jp-stock-daytrade` | J-Quants認証情報 未設定 | 認証情報の取得・登録 | 2026-04-18 |
| 3デバイス運用移管 | 工程0未着手。Mac Miniの物理操作（リモートログインON）が必要 | オーナーがMac Miniを操作 | 2026-04-14 |
| Claude Code Telegram Channels | 別PCでの常時稼働が未セットアップ | 別PCにインストール→ペアリング→tmux常駐 | 2026-04-12 |

## 稼働中システム（原則監視のみ）

| システム | 状態 | 実行環境 | 最終更新 |
|---|---|---|---|
| 競馬予想AI（JRA/ばんえい） | 本番稼働・cron自動運用。朝予想とライブ予想は**別々に集計** | ConoHa VPS `/opt/keiba-unified/` | 2026-07-05 |
| AI投資（BTC/JPY） | 本番デーモン稼働・下げ相場購入抑制 `trend_filter` 適用済み | ConoHa VPS `/opt/ai-trader/` | 2026-06-06 |
| FX自動売買 Phase1（パターンC） | フォワードテスト dry_run 稼働中 | ConoHa VPS | 2026-04-18 |
| AIニュース配信 | 毎朝7:00 JST cron。Google Docsアーカイブ連携済み | ConoHa VPS | 2026-04-04 |
| YN Tools（36ツール） | 本番稼働。サブスク2000円／1ツール100円 | ConoHa VPS `tools.ynfactory.online` | 2026-04-30 |
| 朝のブリーフィング | 毎日6:30 トースト通知 | Windows Task Scheduler `YNFactory-MorningBriefing` | 2026-04-12 |
| Sales OS 軸C（法人アウトバウンド） | cron稼働・`DRY_RUN=true` の安全側待機。自動本番送信は未解放 | ConoHa VPS | 2026-06-23 |
| shorts-factory | 09:00/14:00/19:00 の3枠 launchd。承認はTelegram | Mac `~/shorts-factory/` | 2026-08-08 |

## 保留・低優先

- **Instagram転職アカウント リール制作**: 休止中（7社完了時点、2026-03-29）。再開時は8社目・フックAから。
- **YouTube日本史チャンネル**: 棚卸し待ち。
- **short-video-editor**: スキル刷新・サブエージェント3つ作成済み。実動画での動作テスト未実施。
- **note定期投稿 / GenSpark Claw連携**: 第2弾7本まで公開済み。第1弾は予約投稿の即時公開事故あり（GenSpark側の虚偽報告、2026-04-12判明・そのまま公開維持）。再発防止策はテンプレとCLAUDE.mdに反映済み。
- **AI副業（ココナラ等）Phase2**: プロフィール更新済み。サービス説明文の改善draftあり。
- **グルメシェア**: v1.0本番公開済み。横展開は必要に応じて。
- **メタ系SNS自動投稿**: FB本番投稿は稼働。IGフィードは公開画像URL必須、Threadsはトークン未発行。

## 参照

| 用途 | 場所 |
|---|---|
| 技術・環境メモ（VPS・API・既知の落とし穴） | `.company/secretary/tech-notes.md` |
| セッション要約の履歴（月次） | `.company/secretary/handoff-log/YYYY-MM.md` |
| 日次TODO | `.company/secretary/todos/YYYY-MM-DD.md` |
| 旧HANDOFF.md 全文（2026-08-08 再構成前・387KB） | `.company/secretary/archive/HANDOFF-2026-08-08-full.md` |
| 完了案件の詳細 | 上記アーカイブ、および各プロジェクトの `README.md` |

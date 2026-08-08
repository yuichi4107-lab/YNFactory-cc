---
last_updated: "2026-08-08"
last_device: "Windows"
last_session_summary: "ハンドオフ方式を現況スナップショット型へ全面変更。旧HANDOFF.md（131キー・1448行・387KB）は archive/HANDOFF-2026-08-08-full.md へ全文退避し、frontmatterの履歴131件を handoff-log/2026-04〜08.md + legacy-undated.md へ日付順に分解、技術メモを tech-notes.md へ移設。本ファイルは進行中・ブロック中・稼働中のみを持つスナップショットに再構成した。肥大化の根本原因だった .company/CLAUDE.md の「上書きしない（追記のみ）」ルールに例外を明記し、handoff スキルを新方式へ改訂。あわせて Drive 直下の壊れた .git（refs無し・desktop.ini混入）を .git.disabled-2026-08-08 へリネームして無効化した。"
next_action: "Drive側をGitHub最新へ pull-sync する。GitHub側は2026-08-06に6バケット再編とCLAUDE.md 14行圧縮が入っており、Drive側は未反映。pull前に、Drive側CLAUDE.mdにのみ存在する『ダウンロード事前承認』条項（2026-08-08オーナー承認）を 02_設定/docs/ 側へ移植しないと失われる。"
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

### shorts-factory — 定刻生成・Topview在庫 (最終更新: 2026-08-08)

- **状態**: 8/8の4点修正（安全停止のTelegram通知／在庫低下の事前警告／`register_files`追記マージ／README・config例）をMac runtimeへ `deploy.sh`（installなし）で反映済み。Topview在庫はCanvas既存クリップ6本を書き出して登録し、**有効8本／未使用8本＝動画4本ぶん**（新規生成ゼロ、クレジット残高287.28のまま）。`validate_inventory` と `select_live_clips(2)` が通過し安全停止は解消。
- **要確認**: 本日14:00枠が通り、Telegram承認→4媒体投稿まで戻ること。新規6本は720pで既存 `Video_8/9` の1080pと混在するため、**初回の仕上がりを目視**する。
- **次の補充**: Canvas `654e5964324b4707b12c890e13249039` に未書き出しの Video 3〜7・10・11 が残る。まずここから確認し、足りなければ新規生成（1本約15クレジット）をオーナー承認のうえ実施。
- **書き出し手順**: Canvasでクリップ選択 → ツールバーの ⬇ → 数十秒待って `~/Downloads` を確認 → `~/shorts-factory/topview_assets/` へ移動 → `cd ~/shorts-factory/app && ~/shorts-factory/.venv/bin/python scripts/register_topview_assets.py <file...>`。保存の反映に時間差があるので、直後にファイルが無くてもブロックと即断しない。投稿済み素材（`Video_12`）は再登録しない。
- **注意**: Windowsからは `fcntl` 依存で pipeline 実行・deploy ともに不可。runtime操作はMacで行う。
- **詳細**: `05_プロジェクト/shorts-factory/`、`.company/projects/shorts-factory/2026-07-16-drive-lock-root-fix-debug-log.md`

### Drive↔GitHub の分岐解消 (最終更新: 2026-08-08)

- **状態**: GitHub側（`C:\YNFactory-cc`）は2026-08-06に6バケット再編・CLAUDE.md 14行圧縮・`02_設定/docs/` への文書集約が入っている（commit `28f346e` / `805a55a`）。**Drive側はこれが未反映**で、CLAUDE.mdは旧9.7KB版、`02_設定/docs/` も一部しか無い。
- **次のアクション**: `pull-sync` でDriveを最新化する。**その前に**、Drive側CLAUDE.mdにのみ存在する「ダウンロード事前承認」条項（2026-08-08オーナー承認）を GitHub側の `02_設定/docs/` へ移植する。移植せずにpullすると、Driveの旧CLAUDE.mdが14行版に置き換わり条項が消える。

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

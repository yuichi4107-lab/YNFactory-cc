---
last_updated: "2026-08-08"
last_device: "Windows"
last_session_summary: "ハンドオフ方式を現況スナップショット型へ全面変更（HANDOFF.md 387KB/1448行 → 9KB台）。旧全文は archive/HANDOFF-2026-08-08-full.md へ無損失退避し、frontmatterの履歴131件を handoff-log/2026-04〜08.md + legacy-undated.md へ分解、技術メモを tech-notes.md へ移設。肥大化の根本原因だった「上書きしない（追記のみ）」ルールに状態ファイルの例外を明記し、handoff スキルを新方式へ改訂。Drive直下の壊れた .git を .git.disabled-2026-08-08 へリネームして無効化。『ダウンロード事前承認』条項を 02_設定/docs/approval-rules.md へ移植したうえで、最後に Driveを正としてGitHub側を全面的に合わせた（付け替え330・削除215・上書き296、追跡2384件でDriveと完全一致）。commit ef1f833 / 2992f07 / 925e2eb / 0b80c0f、復元タグ pre-drive-mirror-2026-08-08。"
next_action: "shorts-factory の本日14:00枠が通り Telegram承認→4媒体投稿まで戻ったかを確認する（720p素材の仕上がりも目視）。あわせて Drive のみに残る .company/CLAUDE.md と .company/secretary/CLAUDE.md の廃止可否を決める（内容は 02_設定/docs へ一本化済みで規範が二重化している）。"
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

### Drive↔GitHub の統一 — 完了 (最終更新: 2026-08-08)

- **結果**: **Driveを正としてGitHub側を合わせた**。追跡2,384件で Driveに無い0件・内容相違0件を検証済み（施行前は追跡2,598件／Driveに無い544件・内容相違296件）。
- **内訳**: 付け替え330件（2026-08-06のバケット再編で移動したパスをDrive現物のパスへ戻した。内容は同一）／削除215件（Drive上に対応物なし。一覧は `archive/2026-08-08-drive-mirror-deleted.md`）／上書き296件。`.gitignore` 対象10件（`03_成果物/outputs`・`_archive`）は追加せず削除のみ。Git未追跡のDriveファイル（成果物・バイナリ・.env）は方針どおり追加していない。
- **復元点**: タグ `pre-drive-mirror-2026-08-08`（GitHubへpush済み）。commit `0b80c0f`。
- **ルール層**: `CLAUDE.md`（14行版）・`AGENTS.md`・`.gitignore`・`02_設定/docs/*.md`・`01_コード/scripts/company/*.py` はDrive・GitHubとも同一。旧Drive版は `archive/CLAUDE-drive-old-2026-08-08.md` / `AGENTS-drive-old-2026-08-08.md`。
- **注意**: `pull-sync` は「pullで新たに取得した差分」しかDriveへ流さない。ローカルが `origin/main` と同一なら何もしない。既存の乖離を埋めるときは `local-to-drive` にパスを明示する。
- **廃止候補（未決）**: Driveのみに残る `.company/CLAUDE.md` と `.company/secretary/CLAUDE.md`。内容は `02_設定/docs/` 側へ一本化済みで、現状は規範が二重化している。

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

---
last_updated: "2026-08-16"
last_device: "Windows"
last_session_summary: "リポジトリ構成をリンク方式へ移行完了。C:を本体とし約57.2GBをDrive側へ集約。04_インプットは素材376件をGit除外し取込スクリプト44件のみ追跡継続。05_プロジェクトの旧名/新名の二重化18組を全件SHA-1照合のうえ追跡802件を付け替え。C:直下の旧フォルダ8件も突き合わせて退避し、git statusはクリーン。ドキュメント4本を新構成へ更新しpush済み。ファイルの移動・消失は0件、削除は0件（すべて退避）。"
next_action: "Coworkの接続フォルダを C:\YNFactory-cc に切り替える（デスクトップアプリの「フォルダを追加」）。切替後、multi-pc-rules.md §1 と setup-multi-pc.md の「移行中の注意」段落を削除する。"
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

### shorts-factory — 定刻生成・Topview在庫 (最終更新: 2026-08-15)

- **状態**: 未使用`split_12s_v1`は0本／必要4本。runtime healthは`ok=true`（queue=255、媒体欠損・台帳異常なし）だが、次の定刻生成は安全停止する。動画・キュー・投稿は作成されない。
- **定期補充**: Codex cron `topview-4-8` を有効化。毎日04:00（Asia/Tokyo）に12秒のTopview実写素材4本を生成・書き出し・登録する。当日9/14/19時の3動画は各1本を前半・後半に分けて使い、4本目を予備として残す。既存クレジットのみを利用し、追加購入・プラン変更・投稿はしない。ログイン切れ、クレジット不足、重複、4本未完了では安全停止する。
- **合成**: 12秒素材は0秒付近と6秒以降を切り出し、「実写（即発話）→日本語カード1→日本語カード2→同じ実写の後半→日本語カード3→日本語カード4」の6区間で構成する。実写セリフは各5秒以内、11.5〜12.5秒・9:16・映像のみ・新形式の素材だけを使い、旧形式素材は履歴として残すが使用しない。
- **通知**: TelegramはTopview在庫の安全停止だけを簡潔に伝え、生の外部応答・URL・旧経路名を転送しない。修正はMac runtimeへ `deploy.sh`（installなし）で反映済み。
- **要対応**: 2026-08-15の補充で確認した直接動画の最大12秒を、現行仕様へ採用した。補助アセットは使わない。
- **次の補充**: 補助アセットなしで12秒・9:16・映像のみの動画4本を直接生成でき、既存クレジットで4本完了できることを生成前に確認する。確認できない場合は登録せず安全停止する。
- **注意**: Windowsからは `fcntl` 依存で pipeline 実行・deploy ともに不可。runtime操作はMacで行う。
- **詳細**: `05_プロジェクト/shorts-factory/`、`.company/projects/shorts-factory/2026-07-16-drive-lock-root-fix-debug-log.md`

### リポジトリ構成 — リンク方式へ移行 (最終更新: 2026-08-16)

- **到達点**: `C:\YNFactory-cc` を本体とし、重い領域だけをジャンクションでDriveへ逃がす構成へ移行完了。約57.2GBを集約。`git status` はクリーン。仕様と判断基準は **`02_設定/docs/link-architecture.md`**（未処理課題は §8 に集約）。
- **残る作業はCoworkの接続先切替のみ**: デスクトップアプリの「フォルダを追加」で `C:\YNFactory-cc` を接続する。切替後、`multi-pc-rules.md` §1 と `setup-multi-pc.md` の「移行中の注意」段落を削除する。
- **落とし穴（重要）**: Windowsのジャンクションは Python の `Path.is_symlink()` も `os.path.islink()` も **False** を返す。リパースポイント属性（`0x400`）でしか判定できない。`sync_drive_git.py` に `is_link()` を追加して対応済み。未対応だと `shutil.rmtree` がリンクを貫通してDrive上の成果物を消しうる。
- **リンクを外すとき**: `rmdir /s /q` を使わない。リンク先まで消える。PowerShellは `[IO.Directory]::Delete($path, $false)`。
- **命名ルール**: `05_プロジェクト` は `YYYYMMDD_` プレフィックス付きで統一。**Drive側だけでリネームするとGitHubに反映されず両方が生き残る**（今回18組の二重化の原因）。
- **退避（未削除・3か所）**: `%USERPROFILE%\_pre_link_04_インプット` / `_pre_link_projects\` / `_pre_link_root\`（13.7GB）。動作確認が済むまで消さない。済んだら削除してC:の容量を空ける。
- **`sengoku-game` に注意**: 退避した `_pre_link_root\sengoku-game` が**本流**（独立リポジトリ・master・8コミット）。Drive側は2週間古い。捨てないこと。詳細は `link-architecture.md` §8-7。
- **未処理5件（`link-architecture.md` §8）**: Drive上の入れ子`.git`（8-1）、開発ゴミ290MB（8-2）、Mac側symlink未検証（8-4）、sengoku-gameの置き場所（8-7）、win5/data 92.5MB（8-8）。
- **運用サイクルは不変**: セッション開始 `/start`（pull-sync）／終了 `/handoff`（commit-push）。

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

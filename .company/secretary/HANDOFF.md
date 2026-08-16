---
last_updated: "2026-08-17"
last_device: "Windows"
last_session_summary: "ブロック中8件を実物照合で棚卸しし4件へ削減。3件（Meta Step6・ebook-to-manga vol2-4・マンガ版ChatGPT5.5）は既に解決済みで記述だけが古かった。MetaはFB/IGとも権限付与済み・トークン無期限をdebug_tokenで実測し、投稿可能と確認。無料AI導入診断フォームをApps Script経由でv2仕様14項目へ更新し、5月末から続いた編集権限ブロックを解消（フォーム・回答シート双方の権限取得を確認）。LPは日本語の折り返し制御・見出しの改行位置指定・ヒーローの半透明パネル・フォーム整合・既存CSSバグ（.compact-gridの無効化）修正を行い本番へデプロイ、ai.yn-factory.com で配信確認。さらにSNS導線の断線を発見——CTAは全媒体「プロフィールのリンクへ」だがInstagramのウェブサイト欄が空で、動画視聴者が先へ進めない状態だった（オーナーが修正済み）。フォーム回答が2026-05-28以来0件だった原因と見られる。"
next_action: "shorts-factory の補充停止の原因を切り分ける。出力は2026-08-14 09:06が最後で2日以上停止中。補充cron topview-4-8 は「Topviewのログイン切れ／クレジット不足／重複／4本未完了」の4条件で安全停止する設計。ログはMac側 ~/shorts-factory/ にありWindowsからは追えないため、まずMacでTopviewのログイン可否と残クレジットを確認する。復旧後は導線が繋がった状態で2週間走らせ、LP流入とフォーム回答で継続可否を判断する（それ以前の実績はリンク断線中のため参考にならない）。"
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
- **導線の断線を修正 (2026-08-16)**: CTAは全媒体で「プロフィールのリンクへ」だが、**Instagramのウェブサイト欄が空**だった。bioにURL文字列はあったがInstagramではbioのテキストは押せず、動画を見た人がプロフィールから先へ進めなかった。`https://ai.yn-factory.com` を設定済み（Graph APIで確認）。TikTok・YouTubeも確認済み。**Facebookのwebsite欄は `https://www.ynfactory.online/` のままで未修正**（オーナーが後日対応）。フォーム回答が2026-05-28以来0件だった原因はこれと見られる。
- **出力停止中 (2026-08-16確認)**: 出力は `2026-08-14 09:06` が最後。以降2日以上どの枠も動いていない。素材切れによる安全停止。補充cronが機能していない原因の切り分けが必要（下記4条件のどれか）。
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

2026-08-16 に旧8件を実物照合で棚卸しし、5件に整理した（下の「棚卸しの結果」を参照）。

| 案件 | ブロッカー | 解除に必要な操作 | 最終更新 |
|---|---|---|---|
| Threads 自動投稿 | Threads は Graph API の権限候補に出ない。`graph.threads.net` の独立OAuthが必要でトークン未発行 | Threads API の OAuth を通してトークン発行。FB/IGとは別系統 | 2026-08-16 |
| 3デバイス運用移管 工程0 | **リモートログインONは完了**。残るのは接続情報（Macのホスト名またはIP、ユーザー名）が不明なこと | オーナーがMacで `whoami` と `hostname` の結果を伝える。以降の鍵設定・工程2・4はWindowsからSSHで完結できる | 2026-08-16 |
| AI投資 実発注（Phase 2b） | IB証券口座・国内暗号資産API・税理士確認・初期資金がいずれも未定 | `05_プロジェクト/quant-bot/README.md` §Phase 2b の4項目を決める | 2026-08-16 |
| 日本株デイトレ `jp-stock-daytrade` | J-Quants認証情報 未設定。2026-04-18以降4か月更新なし | **続けるか畳むかを先に決める**。続けるならJ-Quants無料プランへ登録 | 2026-08-16 |

### 棚卸しの結果（2026-08-16）

旧8件のうち3件はブロッカーが既に消えており、記述だけが古かった。

- **Meta SNS 自動投稿 Step6 → 解決済み**。2026-06-09 に `pages_manage_posts` を含む期待権限が全て付与されていた（`MISSING_EXPECTED_PERMISSIONS` は空）。2026-08-16 に debug_token で再確認し、ユーザートークン・ページトークンとも `is_valid=true` / **期限なし**。FBページ・IG `@nakada_yuichi` へ読み取り疎通も確認。**FB/IGへの自動投稿は今すぐ実行できる**。詳細は `tech-notes.md`。残るのは Threads のみで、上表に切り出した。
- **ebook-to-manga vol2-4 再生成 → 完了済み**。vol2(2026-05-06)・vol3(2026-05-20)・vol4(2026-05-22) のEPUBと `KDP出版用` が `03_成果物/outputs/ebooks-manga/manga-career-restart/` に揃っている。codexキューに該当ジョブは残っていない。
- **マンガ版『ChatGPT 5.5時代の結論』 → 完了済み**。「次フェーズ（パネルCSV→画像→EPUB）が承認待ち」とあるが実際は実行済みで、`chatgpt55_manga_kdp_safe.epub`（2026-05-14）まで到達している。画像 png1128+jpg1254、`KDP出版用` あり。
- **AI投資 ショート戦略 Phase2 → ブロッカーが別物だった**。quant-bot(2026-08-09更新)では戦略がRSI(2)平均回帰＋CMEベーシスに変わり、Binanceは**ファンディングレートの監視（公開データ・APIキー不要）**にしか使わない。「Binance Futures API Key 未発行」は無効。実発注に要るのはIB証券と国内暗号資産APIなので、上表を書き換えた。
- **3デバイス運用移管 → 工程3が不要になった**。note定期投稿は Genspark Claw ではなく `note-article-publisher` スキル（ブラウザ直投稿）に置き換わっている。残るのは工程0→2→4。
- **Claude Code Telegram Channels → ブロックではない**。Telegram Bot は本PCで現に稼働中（`~/.claude/channels/telegram/bot.pid` が当日付）。未達なのは「24時間化」だけで、これは3デバイス運用移管の工程2と同一。上表から外し統合した。
- **無料AI導入診断フォーム → 解決済み**（2026-08-16 15:22）。Apps Script（`01_コード/scripts/sales/update_ai_diagnosis_form.gs`、GAS側プロジェクトID `155XBTCwslEYl3BrerHPj-A-GE1JaPmPKLBbjwPJF_2In0jZEDwDXvfuV`）を y-nakada で実行し、**v2仕様の14項目へ更新完了**。同時に `yuichi4107@gmail.com` へフォーム・回答スプレッドシート両方の編集権限が付与され、こちらから読み書きできることを確認済み。回答用URLは変わらないのでLPのCTA差し替えは不要。**現時点の回答は0件**（2026-05-28の公開以降ゼロ）。回答シートには旧11問の列が残っているが、回答0件なので実害なし。Google Forms API はDriveコネクタに無いため、今後もフォーム構造の変更はこのApps Script経由で行う。
- **SNS導線（営業）→ 全て解決**（2026-08-16）。フォームは14項目へ更新済み、LPも本番反映済み（`https://ai.yn-factory.com/`）。**wrangler のログイン切替は不要だった** — 2026-06-19の記録では `yuichi4107@gmail.com` だったが、実際には既に `y-nakada@yn-factory.com` でログイン済みで `pages (write)` 権限もあった。以後のデプロイは `03_成果物/outputs/lp/ai-introduction-consult-publish/` で `npx wrangler pages deploy . --project-name ynfactory-ai-lp --branch main` を実行するだけ。詳細は `ai-introduction-consult-deployment.md`。
- **マンガ4冊のKDP入稿 → 完了**（オーナー確認済み・2026-08-16）。career-restart vol2/3/4 と『マンガでわかる ChatGPT 5.5時代の結論』はいずれも入稿済み。リポジトリ側に入稿記録が無かっただけ。
- **3デバイス運用移管 工程0 → Mac側の操作は完了**（オーナー実施・2026-08-16）。リモートログインON済み。残りは Windows からの SSH 鍵設定で、これはこちらで実施できる（Macのホスト名/IPとユーザー名の確認が必要）。

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
- **メタ系SNS自動投稿**: FB・IGとも権限付与済み・トークン無期限で投稿可能（2026-08-16実測）。IGフィードは公開画像URLが必須という制約は残る。Threadsのみ未発行でブロック中の表に切り出した。

## 参照

| 用途 | 場所 |
|---|---|
| 技術・環境メモ（VPS・API・既知の落とし穴） | `.company/secretary/tech-notes.md` |
| セッション要約の履歴（月次） | `.company/secretary/handoff-log/YYYY-MM.md` |
| 日次TODO | `.company/secretary/todos/YYYY-MM-DD.md` |
| 旧HANDOFF.md 全文（2026-08-08 再構成前・387KB） | `.company/secretary/archive/HANDOFF-2026-08-08-full.md` |
| 完了案件の詳細 | 上記アーカイブ、および各プロジェクトの `README.md` |

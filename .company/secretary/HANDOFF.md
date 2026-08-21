---
last_updated: "2026-08-20"
last_device: "Mac"
last_session_summary: "shorts-factoryの14時生成は完成後の字幕精度検証で、略語「コミュ力」が別語に誤認された1行だけ不合格となり安全停止した。音声用には「コミュニケーション力」へ正規化し、Topview混在候補の品質不合格は同一素材を消費せず最大2回まで自動再生成するようruntimeへ配備。targeted test・配備一致・health=okを確認し、手動生成、Telegram承認、SNS投稿は行っていない。"
next_action: "次の19時枠で品質不合格時の自動再生成と、即発話の実写cueを含む候補生成が安全停止しないことを確認する。候補はTelegram承認後にだけ投稿する既存方針を維持する。"
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

### 販売管理システム — 初期版を実装済み・自社情報待ち (最終更新: 2026-08-18)

- **状態**: 設計(PR #4)と実装(PR #6)をmainへマージ済み。必須機能 F-01〜F-06 / F-08 が動く。**残るブロッカーは自社情報の実値のみ**。
- **場所**: `05_プロジェクト/20260817_sales-management/`。`pip install -r requirements.txt` → `python run.py` で `http://<稼働マシンのIP>:8080`。`scripts/seed_demo.py` でデモ案件3件が入る。
- **構成**: Flask + SQLite(WAL) + Jinja2 + 自前CSS。CDN等の外部読み込みなし・社内LAN完結・ランニングコストゼロ。テスト44件（`python -m pytest tests/ -q`）。
- **実装した業務ルール**: 客先ごとの締め日（20日締め→6/21〜7/20、存在しない日は月末丸め、全客先一括の締めも可）／消費税は請求書単位で1回・1円未満切り捨て／管理No.は `BEGIN IMMEDIATE` 内で採番し欠番は再利用しない／請求済以降は編集ロック、請求取消で納品済へ戻り再請求可／二重請求はSQLで除外。
- **帳票**: 納品書（案件単位・客先まとめの2通り、10行/頁）と請求書（15行/頁・客先ごと改ページ）。**適格請求書の6要件を印字**、支払期限は締め日の翌月末。印刷ボタン→A4、PDFはブラウザの「PDFとして保存」。
- **オーナー作業（これが無いと請求書が完成しない）**: マスタ→自社情報に、社名・住所・電話・**適格請求書発行事業者の登録番号（T+13桁）**・振込先口座を入力する。現在はデモ用プレースホルダ。あわせて軽減税率8%の取引が発生しないかを確認。
- **運用の残作業**: 稼働マシンの決定と常時起動の設定、`scripts/backup.py "\\NAS\販売管理\backup"` の日次実行登録（VACUUM INTO・7世代保持）。
- **未実装（意図的）**: F-07 添付管理・F-09 ログインは要件定義書4.11の代替運用のまま。初期版の「1受注=1品目」制限はDB制約ではなくアプリ層に置いてあり、複数品目化は制限を外すだけでよい。
- **業務担当者向け説明資料**: https://claude.ai/code/artifact/19596d57-51db-411e-8ce8-4d093dead275 （既定で非公開。渡すときは共有メニューから共有する）
- **汎用品化は見送り継続**: 自社で3〜6か月運用し、実際に変更したくなった箇所を記録してから再判断する。

### 競馬予想AI — モデル反映の再開 (最終更新: 2026-08-21)

- **指示書**: `02_設定/requirements/keiba-model-reflection-resume-2026-08-18.md`（S0〜S6）。S0・S1判定・S5は実施済み。
- **jvdata供給を復旧 (2026-08-18)**: 停止原因は2つあった。①JV-LinkのCOMキャッシュ破損（`win32com.gen_py...has no attribute CLSIDToClassMap`）で7/18以降データが止まる ②リンク移行後もタスクの登録パスが `G:\マイドライブ\YNFactory-cc\keiba-unified\...` のままで、実体は `...\05_プロジェクト\keiba-unified\...`。8/7以降は結果コード2で起動即失敗しログすら出ていなかった。gen_pyキャッシュ削除＋パス修正＋`option=4` での再取得（SLOP 56,857件・WOOD 15,018件）で復旧し、**VPS側の最新調教日 20260718 → 20260818** を確認。
- **日次供給の復旧を確認 (2026-08-21)**: `YNFactory-JVDataUpdate` は 2026-08-21 06:05 実行・結果コード**0**、次回 8/22 06:05。`update.log` は `ALL DONE in 139s`、SLOP `period=20210102..20260820` / WOOD `period=20210727..20260820` を取り込み、VPS `/opt/keiba-unified/jra/data/jvdata.sqlite` へ scp 転送済み。**供給は正常に戻っている**。
- **JVシャドーの差替判定（S1）**: 判定基準5条件はすべて成立（サンプル 本番90R/JV78R、ROI 58.8%→**71.2%**、的中率 35.6%→34.6%＝境界ちょうど、上位1日除外でも+5.8pt、週末 JV6勝4敗、同一レース61Rの直接対決でも61.1%→69.6%）。**ただし7/19以降のシャドーは7/18で凍結した調教データで走っており前提が崩れている**ため、差替は見送り。新鮮なjvdataで **8/22-23・8/29-30 の2週末**を走らせてから再判定する（目安 8/31）。
- **S2（配当均等 vs フラット）**: `est_odds` は7/12以降ほぼ全日記録あり（例: 8/16は234件中149件）。**S1と同じ週末に変更を入れない**規則のため、S1の再判定後に着手する。
- **S5 コード一元化は完了 (PR #7)**: VPSにしか無かった28本（`auto_retrain.py` `audit_results.py` `enrich_results.py` `run_jv_shadow.py` `run_morning_retry.py` `run_santan_shadow.py` `run_c3_shadow.py` ほか）と、VPS側が新しい2本（ばんえいのTelegram通知追加・venv絶対パス化）を回収。全66本一致・機密走査0件。`jra/scripts` の追跡は37→65本。
- **cronは正常稼働**: 朝7:00 run_morning / 7:06 run_jv_shadow / 9:30 run_live / 9:35 サンタン / 19:30 check_results / 月18:00 audit / 火7:30 enrich / 四半期 auto_retrain（AUTO_SWAP=0の観察モード・次回10/02）。

### shorts-factory — 6区間の実写cue尺ガードを復旧 (最終更新: 2026-08-21)

- **出力は再開している (2026-08-21確認)**: `03_成果物/outputs/shorts-factory/` に 8/20 14:03・19:04、8/21 09:03・14:03・19:03 と5枠連続で候補が出ている。8/19・8/20に停止していた枠は解消。ただしWindowsからは**出力ディレクトリの存在しか見えない**ため、品質不合格時の自動再生成が実際に発火したか、Telegram承認・投稿がどうなったかは**Mac側でのみ確認できる**。
- **状態**: runtime healthは`ok=true`（queue=256、媒体欠損・台帳異常なし）。9時枠は実写cueの音声尺超過、14時枠は「コミュ力」の音声認識誤認による字幕精度1行不合格で安全停止した。いずれも投稿・承認は行っていない。
- **定期補充**: 毎日04:00（Asia/Tokyo）に12秒の実写素材4本を生成・書き出し・登録する。当日9/14/19時の3動画は各1本を前半・後半に分けて使い、4本目を予備として残す。既存クレジットのみを利用し、ログイン切れ、クレジット不足、重複、4本未完了では安全停止する。
- **合成**: 12秒素材は0秒付近と6秒以降を切り出し、「実写（即発話）→日本語カード1→日本語カード2→同じ実写の後半→日本語カード3→日本語カード4」の6区間で構成する。実写セリフは各5秒以内、11.5〜12.5秒・9:16・映像のみ・新形式の素材だけを使い、旧形式素材は履歴として残すが使用しない。
- **実写セリフ尺**: cue 0/3の`tts_kana`を35文字以下に必須化し、長い台本は映像生成前に不合格として再生成へ戻す。生成プロンプト・検証・フォールバックを同時更新してruntimeへ配備済み。9時の停止候補は再投稿せず、次の19時枠で確認する。
- **自動修復**: 音声用の曖昧な略語は正規化し、完成後の品質不合格は素材を消費せず同一枠で最大2回まで自動再生成する。在庫不足・素材不正・台本尺超過などは無理な代替をせず安全停止し、投稿・再投稿はしない。次の19時枠で確認する。
- **通知・投稿**: 承認ボットはPIDロックの別プロセス誤認を修正して再起動済み。`auto_post: false`のため、候補はTelegram承認後にのみ投稿する。今回の復旧では投稿・再投稿・承認操作はしていない。
- **ネタ帳**: 2026-08-19に候補プールの枯渇を修正。自動補充は初級8件未満/中級16件未満で動き、初級18件・中級36件まで補充する。使用済み・backlog・直近queueの予約済みテーマとの類似は除外する。現在は初級18件・中級36件（2026-08-19確認）。
- **導線の断線を修正 (2026-08-16)**: CTAは全媒体で「プロフィールのリンクへ」だが、**Instagramのウェブサイト欄が空**だった。bioにURL文字列はあったがInstagramではbioのテキストは押せず、動画を見た人がプロフィールから先へ進めなかった。`https://ai.yn-factory.com` を設定済み（Graph APIで確認）。TikTok・YouTubeも確認済み。**Facebookのwebsite欄は `https://www.ynfactory.online/` のままで未修正**（オーナーが後日対応）。フォーム回答が2026-05-28以来0件だった原因はこれと見られる。
- **要対応**: 2026-08-15の補充で確認した直接動画の最大12秒を、現行仕様へ採用した。補助アセットは使わない。
- **次の補充**: 補助アセットなしで12秒・9:16・映像のみの動画4本を直接生成でき、既存クレジットで4本完了できることを生成前に確認する。確認できない場合は登録せず安全停止する。
- **注意**: Windowsからは `fcntl` 依存で pipeline 実行・deploy ともに不可。runtime操作はMacで行う。
- **詳細**: `05_プロジェクト/shorts-factory/`、`.company/projects/shorts-factory/2026-07-16-drive-lock-root-fix-debug-log.md`

### リポジトリ構成 — リンク方式へ移行 (最終更新: 2026-08-18)

- **到達点**: `C:\YNFactory-cc` を本体とし、重い領域だけをジャンクションでDriveへ逃がす構成へ移行完了。約57.2GBを集約。`git status` はクリーン。仕様と判断基準は **`02_設定/docs/link-architecture.md`**（未処理課題は §8 に集約）。
- **残る作業はCoworkの接続先切替のみ**: デスクトップアプリの「フォルダを追加」で `C:\YNFactory-cc` を接続する。切替後、`multi-pc-rules.md` §1 と `setup-multi-pc.md` の「移行中の注意」段落を削除する。
- **落とし穴（重要）**: Windowsのジャンクションは Python の `Path.is_symlink()` も `os.path.islink()` も **False** を返す。リパースポイント属性（`0x400`）でしか判定できない。`sync_drive_git.py` に `is_link()` を追加して対応済み。未対応だと `shutil.rmtree` がリンクを貫通してDrive上の成果物を消しうる。
- **リンクを外すとき**: `rmdir /s /q` を使わない。リンク先まで消える。PowerShellは `[IO.Directory]::Delete($path, $false)`。
- **命名ルール**: `05_プロジェクト` は `YYYYMMDD_` プレフィックス付きで統一。**Drive側だけでリネームするとGitHubに反映されず両方が生き残る**（今回18組の二重化の原因）。
- **スキルは3か所に実体を置く (2026-08-18)**: `.claude/skills`（Claude Code）／`.codex/skills`（Codex）／`.agents/skills`（共通ミラー）に各72スキル。Drive側3か所も同数。**同名スキルでも Claude版と Codex版で中身が違うものがある**（例: `ebook-to-manga` は `.codex` 版113KB / `.claude` 版27KB）。**Drive↔ローカルのスキル同期は「不足分の追加のみ」で行い、既存ファイルを上書きしない**（`robocopy /XC /XN /XO`）。2026-08-18に上書き事故を起こし1,819行を消したが、push前に `git checkout` で復旧している。`link-architecture.md` への明文化は未了。
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

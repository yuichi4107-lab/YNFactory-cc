---
last_session_summary_v2026_08_02_left_liberal_body_source_removal: "【電子書籍『日本の左派・リベラルは、なぜ自滅するのか』本文出典追加修正】出版用原稿・EPUB原稿・最終EPUBからS001/S002を完全除外。本文引用6箇所（ID11件）と末尾出典表2行のみを派生生成時に除外し、正本・研究台帳は保持。全78節の改ページとS003〜S070の68件を維持し、EPUBCheck 5.3.0はFATAL/ERROR/WARNING=0、独立QC100/100 PASS。再生成スクリプトも新仕様へ更新。"
last_session_summary_v2026_08_02_left_liberal_epub_revision: "【電子書籍『日本の左派・リベラルは、なぜ自滅するのか』EPUB追加修正】ユーザー指定2点を反映。(1)全78節のH2へsection-startを付け、CSSでbreak-before:page/page-break-before:alwaysを指定。(2)正本・研究台帳は保持し、出版用原稿とEPUB末尾の出典一覧だけS001/S002を除外してS003〜S070の68件へ変更。本文中のS001/S002参照は保持。EPUB再生成、main/KDP版SHA一致、EPUBCheck 5.3.0 messages=0、独立QC100/100 PASS。"
last_updated_v2026_08_02: "2026-08-02"
last_device_v2026_08_02: "Windows（YN_FACTORY）"
last_session_summary_v2026_08_01_left_liberal_publication_package: "【電子書籍『日本の左派・リベラルは、なぜ自滅するのか』出版パッケージ】完成原稿を保持したまま、ChatGPT Images 2.0系で表紙1点（1024×1536）・挿絵8点（1536×1024）を制作。リフロー型EPUB 3.3を生成し、公式EPUBCheck 5.3.0でFATAL/ERROR/WARNING=0、16部78節・画像9点を確認。KDP用の書籍情報、カテゴリ3候補、検索キーワード7枠、HTML紹介文を作成。独立QCは工程1=100、工程2=97、工程3=98、工程4=100、総合99/100 PASS。KDPアップロード・公開・販売は未実施。"
last_session_summary_v2026_08_01_left_liberal_ebook: "【電子書籍『日本の左派・リベラルは、なぜ自滅するのか』】Notion正本2ページに基づき、全16部・固定78節・本文相当125,794字の統合原稿を完成。一次資料中心70件、全節に党側説明・別解・未確認事項・改善案を配置。工程1=95点、工程2=97点、全章95〜98点、最終97点PASS。成果物=.company/projects/日本の左派リベラルはなぜ自滅するのか/。表紙・EPUB・KDP公開は未実施。"
last_updated_v2026_08_01: "2026-08-01"
last_session_summary_v2026_08_01_ebook_setup_ui: "【電子書籍 初回設定UIの全ジャンル化（Windows）】健康分野に固定されていた `.company/scripts/ebook_setup_ui.py` を、theme-to-ebook Phase 0正本の6問24選択肢へ改修。健康関心層・自然療法・検証派・ソマチッド既定を除去し、読者4区分、本の型4区分、文体・文字量・画像密度を汎用化。高リスク分野の安全方針は該当ジャンル時のみ適用する一般表現へ変更。回答値・ラベル・不足項目・自由指定補足のサーバー検証とHTML/JS注入対策を追加し、既存JSON形式・latest.json・theme-to-ebook/ebook-from-theme両modeを維持。unittest 12件PASS、py_compile PASS、独立QC96/100 PASS。過去の設定JSONは未変更。"
last_device_v2026_08_01: "Windows（YN_FACTORY）"
last_session_summary_v2026_07_22_ynfactory_company_manga: "【YNファクトリー会社案内マンガ10P】scenario_ynfactory.mdを基に、9:16フルカラーPNGの本編10ページ（計46コマ）をChatGPT Images 2.0/gpt-image-2で制作。ミカ・矢野・ユキの参照シートとページ別プロンプトを残し、P10のTEL 050-5367-2629・名古屋市中区栄の住所を公式サイトと照合。P9にフィクション・成果非保証注記を追加。QC90点PASS。成果物=.company/outputs/ebooks-manga/ynfactory-company-guide-10p/。P5は『本は捨てられない』の絶対表現を『読まれて、残る』へ安全調整。"
last_session_summary_v2026_07_21_notion_master_v2: "【Notion原本化v2＋lifelog全量投入（Windows・同日続き）】オーナー決定=Notionを全ソースの原本に変更(編集の正=Notion/ローカルはミラー+原資料アーカイブ)。(1)lifelog欠落対応: Limitless取得が6/24で停止していたため--range 27で6/25〜7/20の741件を回収。conversations/*-lifelogs.md原文155件(count:0除外)をソース=lifelog原文としてNotion登録対象に追加。(2)sync_notion.pyをcreate-only化: Notion既存ページを絶対に上書き/archiveしない。ローカル変更はstateにlocal_changed_at記録のみ。タイムアウト120s化・GETのみネットワークリトライ・作成前に元ファイル検索で孤児ページ回収(archive→再作成)し二重作成防止(タイムアウト失敗1件をこの機構で回復済み)。(3)mirror_notion.py新設: Notion→notion_mirror/<ソース>/<日付>-<タイトル>-<pageid8>.mdの一方向ミラー。last_edited_time差分・Notion側削除の反映・タイトル変更時の旧ファイル削除。notion_mirror/はgitignore(Drive+ZSlimで保全)。ミラーの手編集は次回実行で消える(編集はNotionで)。(4)日次バッチ(Task Scheduler YNFactory Notion Sync 07:30)=sync_limitless --range 3→sync_notion(新規登録)→mirror_notion の3段。(5)検証: Notion登録247件(organized92+原文155)failed=0、初回フルミラー248件(オーナーがNotion側で作った無題ページ1件含む=正しく拾えている)failed=0、上り下りとも再実行で全skipの冪等性確認。commit e050683/2479309/794a596/81a0ac1。【残注意】Mac側launchd未設定(Notion同期はWindows専用)。既存パイプライン(extract_insights等)はまだconversations/等ローカル読み。notion_mirror/を読むよう移行するかは未決。"
last_session_summary_v2026_07_21_notion_input_sync: "【インプットデータNotion自動蓄積システム構築（Windows）】7/15音声メモの指示を実装完了。(1)要件定義=.company/requirements/notion-input-sync-2026-07-21.md（接続=Notion公式API+トークン/範囲=organized全部/単一DB+ビュー/1日1回、オーナー確認済み）。(2)実装=.company/inputs/sync_notion.py: organized/{lifelogs,zoom,google-meet,external}/*.mdをNotion「インプットDB」へ同期。frontmatter→プロパティ(タイトル/日付/ソース/タグ/関連プロジェクト/優先度/TODO候補/input_id/元ファイル/取込日時)、本文→Notionブロック変換(2000字分割・100件バッチ)。冪等性=intake/state/notion_synced.jsonにsha256+page_id記録、変更時は旧ページarchive→再作成。レート制限0.35s+429/5xxリトライ、逐次state保存、logs/notion_sync_*.log。QC97点PASS。(3)認証=.company/inputs/.env.notion(NOTION_TOKEN+NOTION_PARENT_PAGE_ID、.gitignore追加済み・git非コミット)。インテグレーション名=n8n-YNFactory(オーナー既存作成を流用)。Notion側はブラウザ操作で「YNFactory インプット」ページ(プライベート配下、id=3a3204bd-6a10-80f6-97b2-d3ae12a37f17)を新規作成しコネクト接続、DB自動作成(id=3a3204bd-6a10-817a-83f5-c2da72523c21)。(4)全92件バックフィル成功(failed=0)・再実行で全skipの冪等性確認・Task Scheduler「YNFactory Notion Sync」毎日07:30登録+手動トリガーexit 0確認。今後organized/に増えた分は毎朝自動でNotionへ蓄積される。コードはcommit af3d4e7でGitHub反映済み。注意: Mac側で同期する場合はlaunchd未設定(現状Windows専用)。"
last_session_summary_v2026_07_16_shorts_drive_lock: "【shorts-factory Driveロック根本改善（Mac）】Drive上のqueue/topics同期I/Oがapproval watchdog再起動130回と生成時EDEADLK 12/12件の根因と確定。正本を ~/shorts-factory/ のローカル制御プレーンへ移し、Driveは5分間隔の失敗許容・一方向非同期ミラーへ変更。queue177件、topics backlog45/used70、deferred16件解消、認証16項目mode0600で移行。unittest 111件PASS、QA96点、health ok、queue走査0.0156秒。10:40のオーナーTelegram承認による既存1件はX/Instagram/TikTok/YouTubeへ各1回で投稿成功し、再起動中も二重投稿なし。次は14:00の切替後初回定刻生成を通常監視。過去ログ内Telegram tokenの再発行・旧ログ整理は別途明示承認が必要。"
last_session_summary_v2026_07_31_shorts_generation_recovery: "【shorts-factory 定刻生成復旧（Mac）】連続エラーの主因はClaude CLIがloggedIn=falseとなり、固定フォールバックが重複ガードに必ず拒否されていたこと。通常フォールバックをtopic/difficulty別の12候補（重複時は次候補）へ変更し、同一タイトル・字幕シグネチャを返さない安全停止を維持。QA92点PASS、対象4テストPASS、runtime appへ同期後health ok（queue219、ledger異常0、mirror ok）。SNS投稿/再投稿、Telegram承認、認証変更、launchd変更は未実施。Claude CLIの再ログインは生成品質を戻すため別途オーナー操作・承認が必要。"
last_session_summary_v2026_07_12_jv_model: "【JRA-VAN調教特徴量モデル開発＋シャドー配備セッション（Windows・Sonnet/Fable分担）】(1)Sonnet5×2体: WCウッド調教103バイトレイアウト完全解読(恒等式99.87%)、血統SK/HN/UM解読+bloodテーブル23.5万頭構築(ID突合30/30・二重文字化けSJIS→cp1252→UTF-8も解読)。(2)Fable: parse_wc(wood75.2万行)、model_v2_jv=調教8特徴量(坂路+ウッド統合・種別×トレセン別z正規化・リーク機械検証合格)+血統4特徴量(ID基準)。(3)実験(単一ビルド列選択・学習≤2025・OOS2026-03-14〜07-12・標準プロトコル3/14-15除外): 朝C5b@0.92でベース88.1%→＋調教94.4%(+6.3pt)・@0.94で100.7%、優位が6-7月に集中(調教=モデル鮮度を補う機序と整合)。＋血統は80.3%に劣化→不採用。ライブFULLは+7.9pt改善も絶対水準低く現状維持。採用基準(+2pt)合格。(4)オーナー決定=2週間シャドー先行: model_jv_no_odds.pkl(84特徴量・学習≤2026-07-11)をsource=morning_jvで並走(run_jv_shadow.py・土日7:06cron・🔬表示・jvdata鮮度ガード付)。E2Eで無限再帰バグ検知→修正(_ORIG_BFFインポート時捕捉)→再合格。【差替判定=7/26頃、2週末分(7/18,19,25,26)のmorning vs morning_jv比較。合格時はrun_morningのビルダー/モデル差替+auto_retrainのTRACKS更新が必要】。(5)git事故: add ディレクトリ指定で91ファイル誤削除commit→即HEAD~1復元(net差分0)・メモリ化(sparse-git-no-dir-add)。(6)QC91点PASS(指摘2点反映済)。レポート=2026-07-12-JVデータ新モデル実験とシャドー配備.md。commit 53f3fb2/a6bbe34+。"
last_session_summary_v2026_07_12_geo_diagnosis_pipeline: "【GEO無料ミニ診断パイプライン構築セッション（Windows）】オーナー指摘『営業はできたがサービスの中身は？』→未整備と正直に報告し承認を得て構築。要件定義=計画/要件定義書_ミニ診断パイプライン_2026-07-12.md（無料版スコープ=10問(5カテゴリ×2)・競合2〜3院・改善3つ・費用ゼロ、有料ライト診断3万円=改善10項目と区別）。(1)工程1 91点PASS: 実施手順書（申込→ヒアリング→4AI実測→採点→レポート→送付→フォローの7ステップ、担当・所要時間付き）・スコア算定基準（言及有無/推薦順位/引用元/誤情報→素点0-10→AI別0-100→総合=実測AI平均、サンプル41点と互換）・スコアシートCSV・ヒアリングシート。QC指摘3件修正済み=①1位基礎点7→8点（旧設計は理論上限90点で満点不可だった）②『好意的な説明』判定の具体例追記③No.1ほがらか整体院のみ15分約束のためヒアリング前チェック追加。(2)工程2 100点PASS: report_generator.py（標準ライブラリのみ、スコア自動計算+バリデーション+顧客名入りHTML生成）・テスト用データ・使い方.md。QCが独立実行・手計算検算（3AI全一致、満点/クリップ/実測不可按分の境界込み）・異常系・Playwright表示確認済み。成果物=GEO監査/診断パイプライン/。【注意】GEO送信は送信済1/30で停止中（7/8の初日オーナー手動4件も未送信、7/9以降のバッチ未実施）。再開はオーナー指示待ち"
last_session_summary_v2026_07_11_payout_eq_parallel: "【配当均等再検証＋並走記録実装セッション（Windows・同日3本目）】オーナー依頼で配当均等配分を現行レジーム（修復済みDB・修復後学習モデル・3/14-15除外プロトコル）で再検証。(1)結果: 朝C5b@0.92でフラット86.8%に対し配当均等92.6%(+5.8pt)と7/5から逆転（頑健性指標=利益上位3日投資ごと除外70.7%vs82.2%・CI下限・月次3勝も配当均等優位）。ライブ系は差なし。穴厚めは不採用継続。逆転理由=データ修復でモデルの堅め組合せ精度が向上した構造変化。(2)オーナー決定=「両方記録して比較」→本番実装: predictions.est_odds列追加(ALTER・bak.20260711_estodds)、run_today.save_predictionsでest_odds保存、check_resultsに_counterfactual_eq_payout＋17:30報告へ💱行並記（est_odds未記録日は非表示）。7/12朝から自動記録開始、約1か月後に切替判断。(3)テスト: 方向・None経路・本番リプレイ合格（test_cf_eq.pyとして保存）。副次発見=本番フラットは端数処理で最終組合せに余りが乗る(三連複8点=600×7+800円、軽微・現状維持)。(4)run_today.pyのDrive正本が古くVPS版(DAILY_BUDGET/UTF-8/JRA日付遡り入り)で更新してから編集（Drive/VPS乖離に注意）。(5)QC87点PASS(指摘3点反映済: 指標明示・revert手順・テスト保存)。レポート=2026-07-11-配当均等再検証と並走記録.md。commit 4f70306+。"
last_session_summary_v2026_07_11_jvdata_pipeline: "【JVデータ日次パイプライン完成セッション（Windows・同日続き）】(1)HCパーサ: 坂路調教58字レイアウトを実データの累積タイム整合(4F-lap=3F等)で完全解読、260.7万行をjvdata.sqlite化(83秒・重複はdata_date新しい方採用)。(2)決定的検証: 血統登録番号=netkeiba horse_id同一体系、JOIN率99.6%(2987/3000頭)・直近1か月調教あり86.2%→調教特徴量の実現性確定。(3)重要発見: 旧形式DIFF/BLODは2023-07-31で凍結(馬マスタに2022年生まれ以降ゼロ)→現行形式DIFN/BLDNへ切替、UM馬マスタ21.6万頭(2024年生まれまで)・繁殖1.2万/産駒4.1万を取得。(4)自動化完成: jv_dump差分状態管理(state.json/auto)、rc=-1新着なし正常系、jv_update(dump→parse_hc→VPS scp、Teeログ=C:\\Users\\fcmdt\\jvdata\\update.log)、Task Scheduler『YNFactory-JVDataUpdate』毎日06:05(WakeToRun)登録済み。E2Eテスト合格・jvdata.sqliteはVPS /opt/keiba-unified/jra/data/へ同期済み。(5)残: WCウッド調教のレイアウト解読とパース、UM/SKパース(血統特徴量用)、調教・血統特徴量→OOS検証(タスク#15)。commit 02d7f27。データ実体=C:\\Users\\fcmdt\\jvdata\\(raw 580MB+sqlite)。17:35に新モデル初フォワード結果の自動確認を仕掛け済み。"
last_session_summary_v2026_07_11_jravan_datalab: "【JRA-VAN Data Lab開通セッション（Windows）】オーナー既契約だが未活用だったData Labを予想AIのデータ源として完全開通。(1)オーナー作業: JV-Linkインストール＋利用キー設定(JVSetUIPropertiesダイアログ)。(2)技術突破3点(詳細=メモリjvlink-python-setup): ①JV-Linkは32bit COM→専用32bit Python環境(C:\\Users\\fcmdt\\py312-32)、②typelibのJVRead宣言ミス→InvokeTypes手動型指定((16392,3),(16387,3),(16392,2))、③BSTRのSJIS化け→cp1252→cp932復元。497レコード読取実証。(3)実装: keiba-unified/jra/jvdata/{jvlink_client.py,jv_dump.py}(commit d125302)。(4)一括ダンプ: SLOP=坂路調教261万レコード(2021〜)取得完了、WOOD+BLOD実行中(C:\\Users\\fcmdt\\jvdata\\raw\\)。(5)次セッション: JV-Data仕様書に沿ったパーサ→調教(追切タイム等)・血統特徴量→確立済みプロトコルでOOS対決→勝てば本番(タスク登録済)。(6)本日=新モデル初本番稼働日(朝12レース推奨配信済、17:30初フォワード集計)。"
last_session_summary_v2026_07_08_keiba_g2_ev: "【競馬予想AI G2（isotonic較正×EV選別）検証セッション（Windows・同日続き）】(1)OOF較正: ≤2025学習データをレース単位GroupKFold5分割、OOF予測からiso_top3/iso_winの2曲線を学習（OOS不接触・リーク安全）。OOF上のBrier改善は僅少=2026年の3-6pt過小評価は最近のドリフトでモデル構造欠陥ではない。(2)EV選別実験: 較正勝率→Harville近似で馬連/三連複の組合せ確率→レースEV=Σ(組合せ確率×est_odds×掛金)/投資額。est_oddsは発走前単勝オッズ積×経験係数で払戻逆算でないことをソース確認。見かけEV≥0.9でROI146.8%(n=188,的中54.3%)だが敵対的検証で崩壊: 3/14-15(OOS窓初日を含む週末)は無選別でも288%の異常週末で、除外後はEVスイープ帯68-85%(EV≥0.9=85.0%,n=137,的中56.9%)。(3)結論: 実弾不可(控除率の壁は不変)だが「レース選択器」としては現行品質閾値0.86(61.5%)をスイープ帯全体で上回り的中率最大1.6倍→ライブ配信の選択器換装候補としてシャドー並走を推奨(オーナー判断待ち)。C5b較正注入は+1.0ptで採用基準未満→不採用。(4)プロトコル改訂: 3/14-15は今後のOOS評価で除外/分離表記を標準化(7/5のFULL評価・バイアス実験も歪めていた)。(5)QC86点PASS(指摘3点=上位3日除外の計算誤り81-86%→正しくは69-80%に修正済・閾値非単調の不確実性明記・中立呼称化、全て反映済)。レポート=2026-07-08レポート§5、実験コード=実験コード/g2_*.py。較正pkl=VPS/tmp/g2_cal_{no_odds,full}.pkl。【判断待ち】EV選択器のシャドー並走(live_ev)開始の可否。"
last_session_summary_v2026_07_08_pdf_annotator: "【PDF書き込みツール(pdf-annotator)新規作成セッション（Windows・Sonnet/Fable分担）】オーナー要望『Adobe風にPDFへ日本語で書き込めるツールをOSS10個調査の上で作成』。(1)GitHub OSS 12個調査: pdf.js内蔵FreeText注釈はCJKで表示崩れの既知バグ(#20117)→pdf.jsは表示専用に限定し、保存はpdf-lib+fontkitでコンテンツストリーム焼き込み方式を採用。(2)要件定義書=.company/projects/PDF書き込みツール/要件定義書.md（3工程・各85点合格制）。(3)実装=リポジトリルート直下 pdf-annotator/。ビルド不要静的Webアプリ（pdf-annotator/で python -m http.server 8000 → index.html）、vendor同梱でCDN依存ゼロ・オフライン動作。機能=PDF読込(選択/D&D)・ページ送り・ズーム・日本語テキスト(IME対応・編集/移動/削除/サイズ/色)・ペン・蛍光ペン・undo・NotoSansCJKjpサブセット埋め込み保存(annotated_*.pdf)。QC3工程とも合格(100/97/100点)、保存PDFはpypdf/pikepdf/PyMuPDF独立検証で文字化けなし・未書込ページはピクセル完全一致。【重要知見】@pdf-lib/fontkitはCJK CFFフォントのsubset埋め込みでフォント破損する既知バグ(pdf-lib#1232)→修正フォークpdf-fontkit(MIT)のUMDに差し替えて解決(vendor/fontkit.umd.min.js)。既知の制限: 回転ページ(/Rotate≠0)は変換式実装済みだが未検証、テキスト新規作成直後にフォーカスが当たらず再クリックが必要な場合あり(次回改修候補)。"
last_session_summary_v2026_07_08_keiba_model_search: "【競馬予想AI「もっと勝てるモデル探し」セッション（Windows・JRA限定・Sonnet/Fable分担）】オーナー指示=中央競馬のみ・簡単タスクはSonnet5/難しいタスクはFable5。(1)Sonnet5×3体並列: 特徴量棚卸し(80特徴量マップ・バイアス系は不在・未使用=weather/prize/start_time)、データ実現性調査、較正測定(G1)。(2)本番データ障害3件を発見・修復【最重要成果】: ①races.track_conditionが2026-03-16以降4か月空(日次パイプラインに書込処理が無い)→enrich_results.py新設(欠損のみUPDATE・INSERTなし)で1,077レース補完・100%回復、②passing/last_3fが2026年9開催日欠損(ライブ経路は着順しか書かない)→13,547行補完・96.9%回復、③未精算5開催日(3/21,4/5,4/12,5/3,6/6=JRA403障害期に17:30失敗→再試行なしで恒久欠損・36レース分の予想が累計から抜け落ち)→check_resultsリプレイで精算。付随: 券種混在レースの精算バグ修正(旧構成の三連複+馬連併用で片方の的中未計上、3/28例4050→7570円)、監査に未精算日検知を追加、週次enrichcron(火曜7:30)新設。修復後の正直な累計=朝35日ROI85.2%(旧報告89.2%から下方修正)・ライブ80.6%。(3)馬場バイアス特徴量(ロードマップ③)実験: ラッパー方式5特徴量(bias_draw/front/fit×2/samples)、リーク機械検証合格、修復後データで無bias/bias両学習の単一変数比較→OOS1,103レースで全閾値劣化(C5b@0.92: 91.1%vs85.9%、@0.94: 87.1%vs62.0%)→【不採用・据え置き】(45日窓の開催バイアスは持続性なしと結論)。(4)副次発見: 7/5のFULL系OOS評価は壊れた馬場状態フラグでスコアリングしていた(品質0.86通過554→修復後108レースで本番挙動と初整合)。FULL@0.86のROI180.9%は上位3除外で74.9%の裾依存。ライブ現行維持は不変。(5)G1較正: 新モデルは中高確率帯で3-6pt系統的過小評価→isotonic較正に余地。G2(較正×EV選別)は組合せ確率設計が必要で次回課題【最有望】。(6)QC98点PASS。レポート=.company/projects/競馬予想AI/2026-07-08-データ修復とバイアス特徴量実験.md、実験コード同フォルダ実験コード/。git commit 1f09fed(修復コード)+レポートcommit。【監視】次の土曜=修復後初の本番稼働(新モデル×正常特徴量入力・3月以来初の正常状態)+サンタンシャドー初記録。"
last_session_summary_v2026_07_08_geo_lp_deploy: "【GEO LP本番公開セッション（Windows・7/5セッションの続き）】(1)オーナーが `npx wrangler login` を実行（今回は正しいCloudflareアカウント、ynfactory-ai-lp プロジェクト確認）→ `npx wrangler pages deploy . --project-name ynfactory-ai-lp --branch main` で公開成功。(2)検証済: https://ai.yn-factory.com/geo/ がGEO版title『AI検索対策(GEO)無料ミニ診断』で配信、hero-seitai.jpg(159KB)配信OK。6/19から未反映だったトップページ(SNS導線版)も同時反映。※デプロイ前の /geo/ への200応答はPagesのルートフォールバックでありGEO版ではなかった（今後の公開確認はtitleで判定すること）。(3)残る承認待ち: ①GEO 30社送信の最終承認（全件未送信・LP公開済で送信可能、送信方法AI代行/手動の指定待ち）②codeximageキュー ai-product-photo-portfolio_20260705_1929 未処理（絵本キュー多数と同居）。7/6-7/8の他セッション（MV制作・楽天ROOM・Seedance・電子書籍スキル改良・投資戦略104件）は todos/2026-07-08.md 参照"
last_updated_v2026_07_22: "2026-07-22"
last_device: "Mac"
last_session_summary_v2026_07_08_mv_factory_pipeline: "【MV制作パイプライン(tools/mv-factory)新規構築＋パイロット制作セッション（Mac）】オーナー要望『レボリンク(EvoLink)でMVを曲から一から仕組み化して作りたい』を受け、要件定義→実行→品質チェックのループで完走。(1) requirements-definerが調査: EvoLink経由Suno(非公式リセール・著作権リスクあり)は不採用と判明後、オーナー判断で動画=Atlas Cloud・曲=Suno公式API(準備中)採用に方針転換、要件定義書=`.company/projects/MV制作/2026-07-07-MV制作パイプライン要件定義書.md`。(2) executorが`tools/mv-factory/`実装: 1曲=1プロジェクト(project.yaml)、run_pipeline.pyでワンコマンド全自動(曲生成→構成解析→絵コンテ→参照画像→Atlas Cloud動画生成→ffmpeg合成)。曲生成は2モード(suno_api=仕様確定待ちで安全に停止/manual=手持ち音源)。QC94点PASS。(3) オーナーがSuno用Chrome拡張を設定したため、既存の[[suno-music-gen-ops]] opensuno Bridge(localhost:3001)を`song_source: suno_bridge`として追加統合(0円)。(4) パイロット曲『タイムライン』(J-POP・女性ボーカル・青春ポジティブ、AI作詞)を生成、60秒/9:16版+3分/16:9版を全自動生成。QC1周目81点FAIL(絵コンテプロンプトの自己矛盾『anime-style live-action-look』が原因で画風混在)→実写統一プロンプトで21本部分再生成→QC2周目 short90/full97点PASS。(5) オーナー視聴フィードバックで恒久品質基準3点を追加指定: ①画風統一必須 ②人物の服装/髪型統一 ③物理破綻(靴の履き違え・自転車の進行方向矛盾・エスカレーター等の方向矛盾)の検査と作り直し。要件定義書に反映済み、メモリ[[mv-quality-standards]]に永続化。(6) 品質ゲート実装: step5b_inspect.py(時系列5フレームのcontact sheet生成)、storyboardにcharacter_sheet必須化、スタイル矛盾バリデータ、run_pipeline.pyの工程6前ゲート。全47クリップ検査→物理破綻等でNGの10本(short8+full2、うちshort scene_03/full scene_05が『靴に両足』該当カットで特定・解消)を再生成→再合成完了。(7) 【中断】QC3周目(品質ゲート通過後の最終採点)実行中にオーナーが『一旦ストップ』指示→バックグラウンドタスク2件(executor継続作業・QC3周目)を明示的にTaskStopで停止。QC3周目は未完了のまま終了(採点はほぼ終わっていたがレポート追記前に停止)。(8) オーナーから新しいAtlas Cloud APIキーを受領し`tools/mv-factory/.env`のATLAS_CLOUD_API_KEYを更新・認証確認済み(無課金の照会でHTTP応答確認、キー値は.env参照)。(9) パイロット総消費 約$39〜44程度(初回$27+画風修正$12〜13+物理破綻修正$5.6)。成果物: `tools/mv-factory/projects/20260707-jpop-pilot/final_mv_short_9x16.mp4`(60秒・1080x1920)・`final_mv_full_16x9.mp4`(161.76秒・1920x1080)、いずれも物理破綻修正・再合成済みだが**QC3周目の最終合格判定は未取得**。QC結果ログ=`.company/projects/MV制作/2026-07-07-QC結果_パイロットMV.md`(1周目・2周目まで記録、3周目は未記載)。【次回最優先】(a) QC3周目の再採点を実施し85点以上を確認する(独立フレーム抽出で靴破綻解消・自転車進行方向・服装髪型一貫性・画風統一の最終検証)、(b) 合格したらパイロット完了として2本目のMV制作に進める、(c) Suno公式APIキーが届いたら`mvfactory/providers/music.py`のSunoApiProviderに実装追加、(d) コード変更一式(tools/mv-factory/配下)のgit commitはWindows側で実施(Macはgit可能=`/Users/yuichi/YNFactory-cc`だが今回はDrive側での作業のみ、次回コミット予定。.envは絶対に含めないこと)。"
last_session_summary_v2026_07_08_rakuten_room_full_auto: "【楽天ROOM自動投稿 全自動化セッション（Mac）】既存のrakuten-room-auto（シート承認制・launchd 12/20/22時投稿）を、要件定義→実行→品質チェックのループで4工程拡張。(1)障害復旧: launchdがdisabled化していたのをenable+bootstrapで復旧、404でっち上げURL8行を要確認へ。(2)工程3=ステータス自動化: approveコマンド新設（紹介文空/URL404/完了済重複を自動で要確認へ退避、それ以外は自動で承認済へ）。QC1回目78点→2回目97点PASS（エラーメッセージ全面日本語化＋回帰テスト）。(3)工程4=ネタ切れ自動補充: replenishコマンド新設。楽天デイリーランキング3ジャンル（インテリア/日用品/キッチン）をCDP Chrome経由で取得（直curlは403のためCDP必須）、残りネタ5件以下で自動的に5件補充。誇大表現（No.1/最強/圧倒的等）を紹介文から自動除去（景表法対策）。QC1回目82点FAIL（FALLBACK_NAME同士が誤って完全一致判定される統合バグをQCが発見）→修正→2回目97点PASS。(4)工程5=同一商品スキップ: 実際にROOMでtenkapas/glove001とglove002が重複投稿された事故を受け、同ショップ型番違い＋紹介文類似度(文字バイグラム閾値0.28、実データ校正済み)の複合判定を補充/承認/投稿直前の3段階に組込み。QC1回目74点FAIL（誇大表現除去とFALLBACK_NAMEの交差で別商品が誤検知される統合バグを再度QCが発見）→修正→2回目96点PASS。(5)テスト計25件全合格、実投稿1件成功（ROOM反映確認済み）。(6)【重要発見】Codex側に同一システムを操作する2つのオートメーション（rakuten-room-post=毎日12/20/22時投稿、room-20=水土15時に候補20件補充）が既に存在しており、launchdと完全に同一スケジュールのrakuten-room-postが原因で7/7に1日5件の二重投稿が発生。オーナーがCodex側の両オートメーションをPAUSED化して解消。AGENTS.mdに『launchd稼働中はCodexオートメーション再開禁止』を明記し排他ルール確立。(7)rakuten-room-auto/AGENTS.md新設（Codexが自動参照する引き継ぎ文書、システム全体像・過去障害・運用ルールを集約）。次アクション=①次回launchd実行(本日12:00)で自動補充+投稿の正常動作を確認 ②404の要確認行7件は実在URLへの差し替えが必要 ③行5,6の手書き紹介文に残る効果標榜表現（『履くだけで美脚』等）の要確認・修正 ④コード変更（rakuten-room-auto/一式）のgit commitはWindows側で実施（Macは/Users/yuichi/YNFactory-ccに.git確認済みだが今回はDrive側での作業のみ、次回セッションでcommit予定）。"
last_session_summary_v2026_07_08_ebook_skill_brushup: "【電子書籍スキル ブラッシュアップセッション（Mac・7/7夜〜7/8）】挿絵が単調なフラット図解・ピクトグラム調になる問題と表紙の訴求力不足を修正。(1)挿絵=ebook-from-theme(Claude側)/theme-to-ebook(Codex側)の共通スタイル指示をアニメ・マンガ調ポップ画風へ全面変更（フラットインフォグラフィック/ピクトグラム調は禁止指定に）＋読者代理キャラクター(recurring_characters)を全画像へ一貫登場させ『悩み→気づき→実践→成長』の感情表現で共感を誘う設計を新設。図解にもデフォルメキャラのリアクションを添える（構造線・矢印・ラベル視認性最優先のガード付き）。(2)表紙=kdp-cover-and-metadata＋ebook-to-manga Step6（Claude/Codex両側 計4ファイル）にbuzz_elementsブロック追加=数字入り帯風キャッチコピー・大きな表情・高コントラスト高彩度・バッジ装飾・情報3階層化、生成後にサムネイル幅100px相当でタイトル判読チェックを絶対ルール化。品質チェック96点PASS（quality-checker）。(3)並行して別セッション(task_4c40be86)がClaude/Codex版設計差異整理＋全18スキルブラッシュアップを実施しcommit 4a48c44でpush済（.agents/ebook-to-mangaはreferences/分割構造化、buzz_elementsはreferences/step6-cover-prompt.mdへ正しく移設済を確認）。(4)Macのgit環境が/Users/yuichi/YNFactory-cc(.gitあり・sync_drive_git.py可)で稼働中と確認=旧メモリ[[mac-git-not-configured]]は陳腐化。本handoffで.codex/skills側3ファイル(theme-to-ebook/kdp-cover-and-metadata/ebook-to-manga)＋HANDOFF/TODOをMacからcommit-push。次アクション=次回の書籍制作1冊で新画風を実地確認しキャッチコピーの型・キャラ描き込み度を微調整。"
last_session_summary_v2026_07_08_seedance_ready_check: "【Seedance初回本番前チェックセッション（Mac・早朝）】水曜14:00の初回AI版自動生成に向けた準備確認のみ実施。config(enabled/週5枠/共通動画モード)・launchd(shorts-generate正常)・APIキー認証と残高(約$82)すべてOK。誤ってprompt無しリクエストが実ジョブ受理されたがByteDance側でMissingParameter失敗=無課金で無害。コード変更なし。次アクション=14:00のTelegramプレビューをオーナー確認、Windows側でSeedance統合一式のgit commit(7/7のTODO参照)。"
last_session_summary_v2026_07_07_seedance_integration: "【Seedance 2.0動画生成のshorts-factory統合セッション（Mac）】動画生成AIのコスト調査から始まり、TopView→Atlas Cloud API直叩きへの移行を完遂。(1)調査=Seedance 2.0はクローズドで自作不可、プロバイダ比較でAtlas Cloud採用(全解像度一律$0.09/s fast、EvoLinkの半額)。比較ツール=tools/seedance-api-compare(両API検証済み・キーは.env)。(2)サンプル=Seedanceネイティブ日本語音声版を3版制作し人物統一の正解=i2v連鎖(前カット最終フレーム→start_image)+服装/部屋/カメラ固定句を確立。reference-to-video(顔参照)は権利フィルタでブロック=使用不可。(3)実装=src/video_bg_gen.py新設+pipeline統合。週5枠(mon-09/wed-14/fri-19/sat-14/sun-09)のみAI版、共通動画モード(platform_variant_videos:false、説明文は媒体別維持)、月$130上限+コストログ(~/shorts-factory/logs/seedance_costs.jsonl)、全異常系で静止画版へ自動フォールバック。QC90点合格・全74テストパス。(4)E2E=5回実行で4件修正(402フォールバック実証/台本セリフ{{LINE}}機械注入化/bg保存先をwork直下へ/concat時lanczosで1080x1920化)→5回目完全合格(avg_cer0.019・一発)。実測1本13分・$3.60(40秒)。(5)残高=オーナーが2回チャージ、消費$14.40+サンプル$8。次回AI版自動生成は水曜14:00枠。要件定義書=.company/projects/shorts-factory/2026-07-07-seedance-atlas統合要件定義.md。git commitはWindows側で要実施(Macはgit不可)。【同日夜の追加】(6)オーナーFBで読み分離方式を実装=セリフはtts_kana(全カタカナ)をvideo_promptへ注入・テロップは漢字のまま(音読み/訓読み誤読対策、VOICEVOX版と同思想)。tts_text⇔tts_kanaの読み整合をpykakasiで検証、TERM_READINGS適用。全84テストパス。(7)Seedance版のクレジット誤表記(VOICEVOX:ずんだもん)を「音声・映像はAIで自動生成」へ修正(動画内+captions.md)。(8)カタカナ方式の新デモ=.company/outputs/shorts-factory/2026-07-07_200412_100-chatgpt-seedance(合格avg_cer0.037)。本日生成コスト計$18.0。(9)オーナーが別のAtlas Cloudキー(Coding Planタイプ)を提示→動画生成には使えない(coding plan残高別枠)ため現行キー継続で確定。注意=このプロジェクトのテストは ~/shorts-factory/.venv/bin/python3 で実行(システムPythonはpykakasi無しで結果が変わる)。"
last_session_summary_v2026_07_05_keiba_improvements: "【競馬予想AI改良①②実装セッション（Windows・同日3本目）】オーナー承認の優先順位に沿い①②を本番反映、③④は要件定義のみ。(1)改良①データ品質ゲート: check_results.pyに_data_quality_warnings追加（未知券種=文字化け/買い予測ありで着順未取得/払戻行6未満/的中0の二項分布動的判定※直近90日的中率から偶然確率<2%のみ発火）→17:30 Telegram報告の冒頭に自動警告。audit_results.py新設=本番check_hitと独立の着順ベース再判定で直近14日のprediction_resultsを突合、cron月曜18:00。検知実証=修復前バックアップDBで文字化け1136行＋偽外れ11件を全件検知、現行DBは異常0。(2)改良②四半期自動再学習: auto_retrain.py新設=DBコピー→特徴量並列ビルド→候補学習(OOS13週除外)→本番vs候補OOS対決(朝C5b@0.92/ライブ@0.86)→差替条件【両者OOS60R以上・ROI+3pt超・的中率-1pt以内】→全量学習→_validate_model_file(pickle構造検証)→swap_model(バックアップ+サイズ検証+自動revert)→Telegram報告。--test-swapリハーサル済・SMOKE合格(11.5分)。cron=1,4,7,10月の2日01:00でAUTO_SWAP=0観察モード(数四半期観察後に無人差替を有効化する運用、有効化前に「全量学習モデル自体は未バックテスト」の構造ギャップを議論すべき=QC指摘)。bet_constants.py=券種定数の単一ソース化。(3)品質ループ: 1回目82点FAIL(差替安全性等4指摘)→修正→2回目94点PASS。(4)③馬場バイアス特徴量・④キャリブレーション×EV選別の要件定義書作成=.company/projects/競馬予想AI/2026-07-05-改良ロードマップ要件定義.md【オーナー承認待ち】。(5)git commit 63a0353 push済(feat/win5-data-foundation)。VPS check_results.pyはトークン差分のためパッチ適用(上書き禁止継続)。掛け金配分検証(配当均等<フラット再確認)と視覚レポートartifactは同日前セッション参照。"
last_session_summary_v2026_07_05_geo_sales_week2: "【AIスモールビジネス3事業/GEO営業開始（第2週）セッション（Windows・同日ai_small_biz_3の続き）】オーナー決定『GEO監査から営業開始』を受け、要件定義書=計画/要件定義書_第2週GEO営業開始_2026-07-05.md で2工程を完走。(1)工程A 98点PASS: 地域=宇都宮/高崎/浜松/倉敷/松山の5都市分散、実在整体院・接骨院30社リスト（公式サイトWebFetch到達確認・出典URL付き・チェーン/到達不可/電話のみは除外）。QC抜き取り8社全一致・捏造ゼロ。チャネル=フォーム15/メール1/IG DM4/LINE10。(2)工程B 96点PASS: 30社個別化文面（チャネル別4フォーマット・全社免責維持・info@ynfactory.online統一）、送信管理表(csv/md)、送信手順書（オーナー承認必須・1日5社上限・特定電子メール法配慮・辞退時停止ルール）。QC指摘対応済み=商談化メモ列追加・MD/CSV列構成整合・フォーム定型文3パターンローテーション追記。成果物=GEO監査/営業/ 配下。現状=全30社『未送信』でオーナーの送信承認待ち。承認後は送信手順書に従い1日5社×7営業日で分散送信（提案起点2026-07-08、承認日にスライド可）。申し送り=No.11/13はLINEバナー経由（直リンクなし）、No.21はチェーン断定根拠なしで残置"
last_session_summary_v2026_07_05_ai_small_biz_3: "【AIスモールビジネス3事業 立ち上げセッション（Windows）】オーナー承認の実装計画（①AI検索対策/GEO監査 ②AI電話受付・予約導入代行 ③AI商品写真・ECモックアップ、元HTMLはデスクトップoutputから取込）を .company/projects/AIスモールビジネス3事業/ に新規プロジェクト化し、第1週=営業デモ制作3工程を品質ループで完走・全合格。(1)要件定義書=計画/要件定義書_第1週営業デモ制作_2026-07-05.md。(2)工程1 GEO監査 94点PASS: 業種=整体院・接骨院、質問テンプレ30問、架空サンプル診断レポートHTML（スコア表・競合4社比較・免責）、ミニ診断オファー文面。QC指摘（未置換プレースホルダー・Q11注記）修正済み。(3)工程2 AI電話受付 98点PASS: 業種=整体院、応答シナリオ4種（キャンセル分岐を追記済）、FAQ・禁止回答リスト（医療/法律/金融判断禁止）、営業デモ台本、電話取り逃し診断文面。(4)工程3 AI商品写真 92点PASS: カテゴリ=雑貨、Before/Afterプロンプト10例（商品特徴固定）、営業用HTML（プレースホルダー方式）、料金表（1万/8万/15万）、AI生成有無管理表。実画像は openai-image-gen スキルがAPI生成禁止ガードレール化済み（メモリも更新済）のため未生成 → codeximageキュー ai-product-photo-portfolio_20260705_1929（計20枚・プロンプト/サイズ埋込済）に投入済み。次アクション: ①Codex側でキュー処理→images/へコピー→ポートフォリオ一覧.htmlの差し替え→例1/2から目視確認（手順=画像生成ステータス.md） ②2週目=どの事業から営業開始するかオーナー判断（GEO=無料ミニ診断30社/電話=取り逃し診断20店舗/写真=無料1枚サンプル）。連絡先は info@ynfactory.online 統一"
last_session_summary_v2026_07_05_keiba_model_versionup: "【競馬予想AIモデル検証＋バージョンアップセッション（Windows）】(1)払戻文字化け障害を発見・本番修復: netkeibaライブ結果ページが6/20頃UTF-8化→EUC-JP固定デコードでpayouts.bet_typeが化け、的中11件が外れ扱い＝1か月間Telegram成績が大幅過小報告（朝C5b報告35%→真値81.9%）。scraper_legacy.pyに_decode_result_html(自動判定)追加・DB1,136行修復・6/20,6/27,7/4再集計、当日7/5の17:30集計で正常動作実証。訂正後の朝C5b累計34日ROI89.2%(93/246)。バックアップ=keiba_live.db.bak.20260705_170413_mojibakefix等。(2)モデルバージョンアップ: 学習窓を2022-2024固定→≤2025で再学習し2026-03-14〜07-04の917レースOOS対決。朝C5b(NO_ODDS)は新が全閾値域で優位(0.92時ROI91.1%vs84.9%・的中31.1%vs27.7%)→学習≤2026-07-04のfinalへ本番差替済(model_v2_no_odds.pkl、旧=.bak.20260705_pre_v3、閾値0.92維持)。ライブFULLは新98.0%vs旧101.0%で現行維持。(3)ROI130%探索(オーナー追加指示): 全7券種19構成×フィルタ=19.4万構成を発見2025/確認2026の二段検証→安定130%超は不存在。発見期間292%の構成が確認期間145R的中0の過学習実例。唯一の生存構成(三連単1点×新馬未勝利ダ≤1400m15頭+、conf147%だが1的中依存)は実弾化せずサンタンシャドーとして旧C3枠(9:35cron)に転用(run_santan_shadow.py新規、source=live_santan、記録のみ)。C3は2/60的中で廃止。_normalize_comboの→対応・check_resultsのlive_santan独立集計追加。E2E・合成テスト合格。(4)ばんえい検証: モデル(4/18学習)は1番人気ベースラインに全面劣後(勝率17.4%vs37.2%・単勝ROI75.6%vs82.1%)、結果CSVオッズ欠損4月100%/5月33%、的中集計の仕組み無し→再学習+ベースライン超えリリース条件+自動集計を別件推奨。(5)品質チェック96点PASS。レポート=.company/projects/競馬予想AI/2026-07-05-モデル検証とバージョンアップ.md(新プロジェクト保存ルール適用)。【要対応】VPSのcheck_results.pyにTelegramボットトークンがハードコード残存(Drive正本は環境変数化済)→ローテーションTODOに追加済。【監視】次の土曜: 朝C5b新モデル初稼働・🎯サンタンシャドー記録開始・17:30集計。"
last_session_summary_v2026_07_05_root_reorg: "【ルートフォルダ整理セッション（Windows）】Drive側YNFactory-ccルートを3分類で整理。(1)散乱スクリプト: gen_vol4_*.py×8/check_*.py×2→scripts/ebook-vol4/、organize_drive.ps1/telegram_reset.sh→scripts/。(2)ナレッジ: キャラ画像サンプル→.company/context/references/。(3)成果物: 学校パンフレット提案資料→.company/sales/proposals/、AYC→.company/outputs/AYC/、ルートoutputs/→.company/outputs/へ統合（nichibiスライド移動、絵本nijiiro旧スナップショットは.company側が新しいため_archiveへ退避）。(4)ジャンク: ログtxt×10/デバッグPNG×8/test_jp.pdf/zip→_archive/2026-07-05-root-cleanup/（削除せず退避）。空フォルダtmp/・video-auto-editor/削除。.gitignoreに_archive/追加。ローカルGit(C:/dev/YNFactory-git)へ29ファイルのrename/deleteをミラーしcommit f9c221f、新規ブランチfeat/win5-data-foundationとしてorigin push済み。【要注意】ローカルGitのmainがorigin/mainとahead3/behind4で乖離、作業はfeat/win5-data-foundationブランチ上（mainを完全包含・17コミット先行）。次回mainへの統合方針を決めること。参照切れチェック済み（.claude/settings.local.jsonの古い許可エントリのみ、実害なし）。"
last_session_summary_v2026_06_23_sales_os_first_send: "【Sales OS 初回本番送信セッション（Mac）】Sales OS軸Cの初回送信を完了。Peatix公開イベント問い合わせ先を `y-nakada@yn-factory.com` へ統一し、CalendlyはGoogle Meet運用。TDC向け Queue ID 282 を本文修正・オーナー承認後に送信試行、Gmail API未有効で一度ブロック→Google Cloud project `YN Tools` の Gmail API を有効化→1通上限で再送成功。送信先 `tdc@mirror-polish.com`、Gmail message id `19ef20982a6e1bc5`、sent_at `2026-06-23T01:12:50.675619` UTC。`approval_queue.status='sent'`、`conversations` に conversation_id 1 として記録。VPS `.env` は `SALES_OPS_DRY_RUN=true` のままで自動本番送信は未解放。DMテンプレート3種とVPS fallbackに `配信停止` 明記の停止表記を反映。cron 02:00/02:30 は同日ログで正常実行確認。次は返信・Peatix申込・Calendly予約の確認と、追加送信候補の選定・承認。"
last_session_summary_v2026_06_19_sns_cta_receiver: "【shorts-factory／SNS導線の受け皿（営業）整備セッション（Mac）】ショート動画(X/Instagram/TikTok/YouTube)からの視聴者を『無料AI導入診断』で受け止め、AI顧問・AI導入コンサルの法人リードへつなげる導線を整備。(1) LP公開状態を更新: `ai.yn-factory.com` がCloudflare Pagesで公開済みになったため、CTAライブラリ `.company/marketing/social-auto-ops/cta/ai-introduction-cta-library.md` のLP URLを旧Google Sites→`https://ai.yn-factory.com/` に統一、status draft→active。(2) `cta/short-video-cta-receiver.md` 新規作成: SNS→LP→Googleフォーム(無料AI導入診断)の受け皿運用メモ。プラットフォーム別UTM付きプロフィールURL(x/instagram/tiktok/youtube)、動画末尾CTA定型、フォーム回答後のA(個別Zoom相談+予約URL)/B(無料診断のみ)/C(情報収集)別の返信文、公開反映チェックリスト。(3) `forms/free-ai-diagnosis-v2-sns-consult-form-spec.md` 新規作成(status:proposed): 無料AI導入診断フォームをSNS/法人リード判別向けに改修する仕様。質問14項目(会社名/従業員規模/役職/相談内容/流入元等)、推奨タイトル・説明文・送信後メッセージ、A/B/Cリード判定メモ。(4) ローカルLP文面(`.company/outputs/lp/ai-introduction-consult-publish/` 配下、git管理外=Drive側のみ)をSNS導線向けに更新済。公開反映はCloudflare Pagesデプロイのオーナー承認後。【ブロッカー】フォームのライブ更新は未実施: Drive接続ユーザー `yuichi4107@gmail.com` に対象フォーム(オーナー `y-nakada@yn-factory.com`)の編集権限がなくDrive APIで File not found・編集URLは回答画面へリダイレクト・アカウント選択にy-nakadaが出ない。次回は `y-nakada@yn-factory.com` でログインしてGoogleフォーム編集画面を開き本仕様へ更新。【残/次アクション】①フォーム改修をy-nakadaログインで反映、②LP文面のCloudflare Pages公開反映を承認、③SNS各プロフィール/概要欄のリンクを `ai.yn-factory.com`(UTM付)に統一。git commit/push 本Macで実施。"
last_session_summary_v2026_06_18_shorts_factory_multiplatform: "【shorts-factory 複数媒体・1日3回投稿・初中中バランス拡張セッション（Mac）】要件定義2本(.company/requirements/shorts-factory-autopost-improvements-2026-06-16.md / shorts-factory-3x-multiplatform-midlevel-2026-06-16.md)を承認→実装→QC。(A)自動投稿改良(approved): ①Drive正本→runtime同期を SHORTS_REPO_ROOT/YNFACTORY_ROOT/スクリプト位置から解決(scripts/shorts_env.sh)、②Telegramログのbot token URLを[REDACTED]マスク(src/logging_utils.py)、③一部媒体失敗時もqueueをpostedにせず再処理可能に残し、成功媒体は二重投稿しない+失敗媒体だけ再試行する scripts/retry_failed_posts.py 追加、④README更新。(B)3回投稿・初中中・複媒体(implemented_waiting_external_login, QC90点): ①launchd com.ynfactory.shorts-generate を 09:00/14:00/19:00 の3枠化、②content.scheduled_slots 追加で 09:00=beginner / 14:00・19:00=intermediate、pipelineに --difficulty 追加+実行時刻からの自動判定、③topics.json に中級ネタ24本追加(現backlog beginner26/intermediate24)、台本プロンプトを難易度別方針に、queue item とTelegram preview に difficulty を保持・表示、④~/shorts-factory/config.yaml を staged 作成(queue.platforms=[x,youtube,instagram,tiktok], queue.auto_post:false)、⑤scripts/check_platforms.py で実投稿なしに platform readiness を preflight、scripts/login_tiktok.sh 追加+login_youtube.sh/start_chrome_shorts.sh が目的URLを開くよう修正。検証=json.tool/bash -n/py_compile/unittest(4件)/plutil -lint 全PASS、runtime ~/shorts-factory/app 同期済、launchd generate/approval 再読込済。preflight現況=X ready / Instagram Reels ready / YouTube not ready / TikTok not ready(YouTube・TikTokは専用Chromeプロファイル未ログイン)。【残オーナー作業】①~/shorts-factory/app/scripts/login_youtube.sh と login_tiktok.sh でログイン、②~/shorts-factory/.venv/bin/python ~/shorts-factory/app/scripts/check_platforms.py で全ready確認、③queue.auto_post:true 化・実テスト投稿・公開操作は実行直前に明示承認。git commit/push 本Macで実施。"
last_session_summary_v2026_06_15_kdp_japanese_folktales: "【KDP絵本 日本の昔話シリーズ automation kdp】2026-06-15(月)実行。新作『かさじぞう ふゆの おくりもの』（日本の昔話えほんシリーズ巻1、元話=かさじぞう、主人公=原話に沿い老夫婦、テーマ=思いやり・感謝・冬のぬくもり）を `.company/outputs/picture-books/japanese-folktales/2026-06-15-kasajizou-fuyu-no-okurimono/` に作成。ユーザー指示により最終画像は1ページ1コマの単独画像32枚で生成・統合し、初期2x2コンタクトシートは `KDP出版用/_not_for_upload/unused_contact_sheets/` に退避。KDP出版用UPLOAD_4ファイル生成済、EPUB zip test None、XHTML32、画像32、PDF本文32P、表紙PDF1P、QC 91点PASS。成果物本体はDrive側保存、`outputs/picture-books/` はGit ignore対象のためGitHubへは送らない。残=Kindle Previewer/KDPペーパーバックプレビュー目視、AI生成コンテンツ申告、最終申請は明示承認後。"
last_session_summary_v2026_06_13_shorts_factory: "【shorts-factory構築セッション（Mac）2026-06-13(土)】日本語ショート動画の全自動生成・自動投稿システムを/goalからゼロ構築し稼働開始。(1) 構成: ネタ帳(.company/marketing/shorts-factory/topics.json)→台本claude CLIヘッドレス生成(スキーマ検証付)→VOICEVOXずんだもん文単位TTS(読み仮名突合+ユーザー辞書31語)→PILデザインカード4枚→FFmpeg合成(zoompan+xfade+ASS字幕焼込+loudnorm)→whisper.cpp large-v3-turbo逆文字起こし音韻CER検証(行≤0.20/平均≤0.10、pykakasi+数字かな化+長音/濁点/促音折畳)→不合格行かな直読み再合成ループ(≤5)→キュー(queue/)→Telegram動画プレビュー+承認ボタン→X投稿(scripts/post_to_x.py --video chunked upload追加)。ランニングコスト0円(このMacにOPENAI/GEMINIキー無のため。secrets.yamlへキー投入でAI画像切替可)。(2) コード正本=shorts-factory/(Drive)、ランタイム=~/shorts-factory/(venv/VOICEVOX0.25.2/whisper large-v3-turbo)。launchd3ジョブ稼働: shorts-generate(毎朝7:30)/shorts-approval(常駐・@mnb121_botのgetUpdates占有=他ツールがポーリングすると409衝突注意)/shorts-chrome(CDP9223)。(3) 品質: 工程1動画=quality-checker 93点PASS(1本目51秒・avgCER3.65%・修正ループ0回)、工程2-5インフラ=88点PASS。発音知見=ChatGPTは『チャットジィーピィーティィー』表記でwhisper聞き取りが直る(src/jp_text.py TERM_READINGS)。(4) 1本目『【コピペOK】議事録を3分で作るChatGPT術』がTelegram承認待ち(message_id28)。IG Reels=resumable upload実装済dry-runPASS、YouTube/TikTok=CDP実装済(未ログイン)。(5) 残オーナー作業: ①Telegram✅ボタンでX初投稿 ②YouTube初回ログイン(scripts/login_youtube.sh→README手順) ③専用bot作成(任意・現@mnb121_bot流用) ④IG/YouTube有効化は~/shorts-factory/config.yamlのqueue.platformsに追記。運用手順=shorts-factory/README.md。git commitはMac不可→次回Windowsでcommit。"
last_session_summary_v2026_06_12_daily_handoff: "【デイリーhandoffセッション（Mac）2026-06-12(金)】(1) 本日のパイプライン成果を確認・記録: KDP絵本デイリー automation 新作『むすびめのゆっくりひも』(.company/outputs/picture-books/musubime-no-yukkuri-himo/) 完成 — Codex gpt-image-2 で表紙+本文32P生成・統合済、QC 90点 PASS（残=Kindle Previewer/ペーパーバックプレビューの手動目視のみ）。主人公交互ルールPASS（前作女の子→今回男の子）。前作『あめあがりのひかりポケット』もQC 90点 PASS 記録更新。Codex入力は archive/ へ複製済（queue フォルダの削除は明示承認待ちで残置）。(2) todos/ にDrive競合『2026-06-12 (1).md』を発見 → 双方に片方にしかないタスクがあったため本体 2026-06-12.md へ union マージ（(1)側から Sales OS本番ローンチ・士業パートナー・notebooklm-sync 2件を救済、本体側のJRA競馬・Meta SNS等は維持）。(1)ファイル自体の削除は明示承認待ち→TODO化。(3) 6/11仕込みの朝配信一本化（6/12は6:45の1通のみか）の確認はオーナー未報告のためTODO継続。(4) inbox/2026-06-12.md（6/12 07:00生成・2.6KB）はDriveクラウドプレースホルダ未ダウンロードでMacから読めず（Resource deadlock avoided。実害なし、Windows側で確認可）。(5) git commit はこのMacから不可 [[mac-git-not-configured]] → 本更新はDrive同期で全端末へ伝播、次回Windowsセッションのhandoff commitに含めること。"
last_session_summary_v2026_06_11_morning_briefing_dedup: "【朝の『今日のやることbot』二重配信解消セッション（Mac・Telegram @bijinh_bot経由）】(1) 発端=オーナー『6時半と6時45分にそれぞれ配信が来てる。6時半の方を削除したい』。(2) 調査で朝配信2系統を特定: 6:30=Windows Task Scheduler『YNFactory-MorningBriefing』(.company/secretary/scripts/morning-briefing.ps1、毎朝6:30、Telegram送信＋当日TODOファイル自動生成(前日未完了の引き継ぎ)＋Winトースト) / 6:45=Mac launchd com.yn.daily-priority(/Users/yuichi/scripts/run_daily_priority.sh→daily_priority.py、AI優先順位付けTODOをTelegram送信)。なお .company/secretary/morning_notify.py(LINE/メール版・タスク未登録らしくログ無し)は今回無関係。(3) 対応: morning-briefing.ps1 はTODO自動生成という重要機能を兼ねるためスクリプト/タスク登録は残し、`$SendTelegram = $false` フラグ追加でTelegram送信ブロックのみスキップ(無効化時はログに'Telegram send disabled by config'記録)。Drive上ファイルのためMac編集→Windows同期で反映、明朝6/12から6:45の1通に一本化見込み。復活は $true に戻すだけ。タスクごと完全削除したい場合のコマンド(Unregister-ScheduledTask -TaskName 'YNFactory-MorningBriefing')もTelegramで案内済(id 649)。(4) ハンドオフ時に todos/2026-06-11.md がMacに未同期(Windows側6:30生成分が届いていない)と判明→Macで新規作成(6/10未完了引き継ぎ＋本件完了記録)。Drive競合『(1)』が出たら本体へマージのこと。『2026-06-08 (1).md』は消えており(オーナーかWindows側で削除済か)、『2026-06-10 (1).md』のみ残存=削除可。【次アクション】明朝6/12の配信が6:45のみか確認(2通ならWindowsのDrive同期遅れ)。git commitはMac不可→次回Windowsセッションのcommitに本変更を含めること。"
last_session_summary_v2026_06_10_telegram_check_handoff: "【Telegram疎通確認＋ハンドオフのみの軽量セッション（Mac・@bijinh_bot経由）】(1) オーナーから『繋がってますか？』(6/10 07:01 JST)→reply ツールで疎通確認応答(id 645/647)。プロジェクト作業なし。(2) ハンドオフ実行時に todos/ 配下でDrive同期競合の重複ファイル2件を発見: 『2026-06-08 (1).md』『2026-06-10 (1).md』。diff の結果いずれも旧スナップショット（本体側が営業Sales OS・notebooklm-sync タスクを含む最新版）。ただし (1) 側にのみ存在した『Meta SNS Step6 再開（Console で use case 権限追加→Graph API Explorer でトークン取得）』を本体 2026-06-10.md の通常欄へ救済マージ済。(1) ファイル自体の削除は明示承認が必要なため未実施→オーナー判断待ち（Windows端末での git 管理外なら単純削除でOK）。(3) git commit は本Macから不可（.git が C:/dev/YNFactory-git 固定 [[mac-git-not-configured]]）のため、HANDOFF/TODO の更新は Drive 同期で全端末へ伝播。次回 Windows セッションで handoff commit に含めること。【次アクション】todos の最優先4件（Sales OS 本番GO・士業パートナー・シークレットローテーション・マンガ第4巻KDP申請）は未着手のまま継続。"
last_session_summary_v2026_06_09_kdp_picture_book_mikke: "【KDP絵本 毎日1冊作成 automation kdp-1】2026-06-09(火)実行。新作『みっけの あおい ボタン』（女の子主人公・テーマ=なくしもの/観察/深呼吸）を `.company/outputs/picture-books/mikke-no-aoi-button/` に作成後、ChatGPT Images 2.0 / gpt-image-2 のCodex側生成でP01-P32全32枚を生成・統合。P16は音符記号混入のため再生成して差し替え。`images/pages_gpt_image2/` と `.company/codex/done/picture-book-mikke-no-aoi-button-gpt-image2-20260609/pages/` に保存し、P01を表紙背景へコピー。`python3 tools/build_book.py` 再実行でKDP出版用UPLOAD_4ファイルを正式生成、status=`completed_ready_for_owner_preview`、QA 88点PASS。EPUB zip test None、XHTML32、画像32、PDF本文32P/表紙1P。queue入力は archive にコピー済みだが、削除は明示承認が必要なため queue には残置。"
last_session_summary_v2026_06_09_sales_system: "【営業オペレーティングシステム構築（Mac・/goal経由）】(1) 既存Sales OS(軸C法人アウトバウンド)が2026-05-04以降 約5週間休眠(DRY_RUN/本番GO待ち/ウェビナー未開催/成約ゼロ)と判明。直近TODOにも営業の記載なし。(2) 方針=高単価AIコンサル(AI活用アドバイザー)×キャリコン差別化×オーナー週5時間商談集中。5月の戦略・コンテンツ・システムを作り直さず『動かす』。要件定義=.company/requirements/sales-system-2026-06/REQUIREMENTS.md。(3) 全5工程を要件定義→executor→quality-checker(85点以上)で構築。成果物: 入口=.company/sales/SALES_SYSTEM.md / STRATEGY.md(87) / LAUNCH_CHECKLIST.md(90) / system-2026-06/booking-ops/(7ファイル,88) / weekly-sales-reviewスキル+daily-ops-checklist.md+weekly-review-checklist.md(91) / .company/DASHBOARD_SALES.md(88) / EARLY_LEADS_PLAYBOOK.md(86)。(4) オーナー回答で温かい人脈ゼロ判明→早期リードは士業パートナー化(最優先)・バリューファーストDM・有料広告・リードマグネット・意図プラットフォームの5打ち手にコールドスタート再設計。(5) KGI再設定オーナー承認(3ファイル一致): 7/31までに商談3〜5件+士業パートナー接触1〜2件+広告/LM稼働+DM累計100通、ウェビナー1回7/15、初契約9/30、MRR20万12/31。(6) 実システム既知欠陥3点を文書化: conversationsテーブル未記録(gmail_sender未実装)、ウェビナー/予約URLは.env無効でpersonalizer.py(src/tracks/c_outbound)のPROMPT_TEMPLATE直書き要、From表示は案C(gmail.com送信/Reply-To・署名info@yn-factory.com)で運用。品質チェックが実コード突合で動かないSQL・架空メソッド・廃止済Meta職業ターゲ等を複数検出し修正済。【次アクション(オーナー手動)】LAUNCH_CHECKLISTの本番送信GO(DRY_RUN=false→自分宛1通確認→DAILY_LIMIT 1→5→30…)＋士業パートナー勧誘の着手＋Peatixウェビナー7/15公開。以後は毎朝/sales-briefing・毎週月曜/weekly-sales-review。"
last_session_summary_v2026_06_07_keiba_result_fetch_fix: "【JRA競馬 結果(着順)自動取得の修復セッション（Mac・Telegram @bijinh_bot経由）】(1) 発端=オーナー『競馬予想の結果について、推奨レースがあるのに推奨レースないとなってます』。本番VPS(163.44.101.31 /opt/keiba-unified/jra)のDB(data/keiba_live.db)・ログ(data/logs/results.log)を直接調査。(2) 切り分け: 予想は正常で6/7朝C5bは推奨2レース(阪神2R/6R 馬連)・ライブ1(東京5R)・C3 2(阪神7R/9R 三連複)がDBに正しく保存。だが結果照合(17:30 cron check_results.py)で全23レース finish_position=0 → 照合可能な完走レース0 → 各ソース『推奨レースなし』表示。レポートのヘッダ『推奨:N』と本文『推奨レースなし』矛盾もこれが原因。(3) 根本原因2つ同時故障: ①JRA公式 `_build_jra_cname_map` が0件=JRA thisweekページが全URL HTTP403ブロック(56KBブロックページ。4/4までOK→6/6回帰。DC-IP/bot対策疑い・URL構造変更は未確定)。②netkeibaフォールバック `scrape_race` が `db.netkeiba.com`(履歴DB=当日反映遅)参照で当日『No result table』。一方 `race.netkeiba.com/race/result.html` は当日中に着順・払戻をEUC-JPで掲載済(ResultTableWrap/All_Result_Table・Payout_Detail_Table)と実証。(4) 修正: `scripts/scraper_legacy.py` に当日ライブ取得関数 `scrape_result_live_netkeiba(race_id,conn)` 新規追加(EUC-JPデコード→着順は既存results行を UPDATE finish_position でエントリ情報を壊さず更新、払戻は payouts へ INSERT OR REPLACE。bet_type正規化 3連複→三連複/3連単→三連単、combination `\"a - b\"` 昇順、try/exceptで堅牢化)。`scripts/check_results.py` の scrape_day_results 取得順を JRA公式→当日ライブnetkeiba→db.netkeiba(履歴) に変更＋import追加。(5) 検証: 6/7バックフィルで23/23『OK (live)』取得、check_day_results/format_result_message で『推奨レースなし』消滅し各ソース『推奨Nレース中X的中・ROI%』表示、手動復元値と完全一致(朝阪神2R[10,5,3]/阪神6R[4,11,15]・ライブ東京5R[2,4,3]・C3阪神7R[8,5,16]/阪神9R[4,10,14]、全0的中ROI0%)。冪等性(再実行で finished>0 スキップ・payouts不変)・非破壊・過去日db.netkeiba経路温存も確認。(6) 品質ループ: requirements `.company/requirements/keiba-result-fetch-live-fallback-2026-06-07.md`、quality-checker PASS 88点(指摘2点=JRA403調査メモ・try/except補強とも対応済)、JRA403調査メモ `.company/engineering/debug-log/2026-06-07-jra-thisweek-403.md`。(7) 反映: 本番VPS反映＋Drive正本(keiba-unified/jra/scripts/)へ scp 同期(MD5一致 9c21cbf.../510d071...)＋VPSバックアップ `*.bak.20260607_182802/182825/183828`。【効果】次週末17:30 cronから自動で的中/回収/ROI集計が復活。JRAが403でも当日ライブで担保。【残/次アクション】(a)任意=結果未取得時の『推奨:N/推奨レースなし』表示を『結果取得待ち(着順未確定)』に変える _format_source_section 小改修(今回スコープ外・未実施)、(b)JRA403の恒久対応は別チケット(別UA/Referer/Cookie/プロキシ検証 or 当日ライブnetkeibaを正規ルート化)=フォールバックで実害なし、(c)C5b朝予想の閾値0.92フォワード検証は継続。【ハンドオフ】本Mac端末はgit不可(.gitがWindowsパス C:/dev/YNFactory-git)のためDrive同期で共有。関連=last_session_summary_v2026_06_06_keiba_no_odds。"
last_session_summary_v2026_06_06_notebooklm_notify_filter: "【NotebookLM Sync 完了サマリ通知のノイズ抑制セッション（Mac・Telegram @bijinh_bot経由）】(1) 発端=オーナーTelegram『NotebookLM Sync 処理完了サマリのテレグラム通知について、エラーと完了があった時のみの通知にして欲しい』。背景: launchd com.ynfactory.notebooklm-sync が30分毎に実行され、毎回 send_summary() で『追加=0』の空サマリを @mnb121_bot に送りノイズ化していた。(2) 対象=src/notify.py の send_summary()。先に total_added / total_errors を集計し、両方0なら logger.info『Skipping Telegram summary』を残して return（Telegram送信せず）。新規追加ありまたはエラーありの時のみ従来サマリを送信。空 channel_results（処理対象チャンネルなし）も追加0/エラー0扱いで送信抑制に統一。(3) send_alert（Google session expired / 動画取得失敗）は無変更＝重大エラーは従来通り即時通知。(4) ランタイム ~/notebooklm-sync/src/notify.py を編集→Drive正本 notebooklm-sync/src/notify.py へ cp 同期（diff一致 SYNCED-OK）。(5) .venv/bin/python で send_summary を4パターン単体テスト: 変化なし=送信なし / 追加あり=送信 / エラーあり=送信 / 対象なし=送信なし、全て期待通り。【成果物】~/notebooklm-sync/src/notify.py（runtime）＋ Drive notebooklm-sync/src/notify.py（source）。【効果】次回30分定期実行から、追加0・エラー0の回はTelegram無通知。launchd再読込不要（コードのみ変更）。【次アクション/監視】次の新着動画でサマリが届くこと・空回しで無通知になることをログ ~/notebooklm-sync/logs/sync.log で観察。関連=last_session_summary_v2026_06_06_notebooklm_mac_migration。【ハンドオフ】本Mac端末からgit commit/push実施。"
last_session_summary_v2026_06_06_multipc_migration: "【マルチPC同時運用への移行 git正典化(Phase A)＋同時運用ルール(工程5)セッション（Windows YN_Factory）】要件定義書 .company/requirements/multi-pc-git-migration-2026-06-06.md（全6フェーズ・各完了条件/品質基準/ロールバック付）をオーナー承認。決定3点=①大物出力プロダクトを丸ごとgit管理外化しjunction合成、②git整理も実施、③10GB移動はMac等他端末のDrive同期停止が前提。【完了】(A)git正典化 Phase A=QA93点: 正典はクローン C:\\dev\\YNFactory-cc（自前.git・通常clone）で、Drive作業ツリー(.git=C:\\dev\\YNFactory-git)はorigin重複の陳腐化と判明(ahead3/behind4だが内容はorigin反映済=作業消失なし)。Drive churnをパッチ退避(.git_drivebackup/drive-churn-2026-06-06.patch)→多PC分岐(origin=Mac分のtelegram/notebooklm、Drive=このPC分のJRA)を todos 2ファイルで保全マージ(両立・作業消失ゼロ)→クローンをorigin/mainへFF→正典一本化(HEAD=281b5c3・push済)。HANDOFFはorigin版が最完全のため維持。(B)工程5=QA97点: docs/multi-pc-rules.md 作成push(pull先行/rebase優先/1日1PC書込/force push禁止/Drive競合回避を今回の分岐事故の実例付きで規定)。(C)工程2プレップ完了: 移動対象 計9.71GB確定(ebooks-manga7.88+ai-stock1.14+keiba data0.38+picture-books0.27+codex0.04+AYC≒0)、G:空き658GB、ファイルはローカル実体あり=移動高速。【保留(Mac同期停止待ち)】工程2(クローンで対象を git rm -r --cached＋.gitignore丸ごと化＋commit/push→停止下で YNFactory-cc-data へ9.71GB移動)→工程3(クローンへjunction6本[ebooks-manga/ai-stock/picture-books/AYC/codex/keiba-data・要管理者]＋自動化4スクリプト[morning-briefing.ps1の$TodosDir/$LogDir・register-task.ps1の$scriptPath・sync_all.bat/sync_limitless.batのcd行]をC:\\dev\\YNFactory-cc参照へ修正＋register-task.ps1再実行でTask Scheduler『YNFactory-MorningBriefing』再登録)→工程4(docs/setup-multi-pc.md・工程3後に検証)。【次アクション】オーナーがMac(+2台目Win)のDrive同期を一時停止→『工程2再開』で工程2-4を品質ループ実行。Macダウンタイムは移動の数分のみ。【移行期の鉄則】git操作は必ずクローン C:\\dev\\YNFactory-cc で行う(Drive側repoは陳腐化・触るとchurnでrebase失敗)。ハンドオフのcommit/pushもクローン側で実施し、次セッションがG:\\を読むためHANDOFF.md等はDrive作業ツリーにも反映する。"
last_session_summary_v2026_06_05_telegram_bot_recovery: "【Telegram常駐bot 復旧テスト＋自動復旧改善の診断セッション（Mac・tg-bot常駐セッション経由）】(1) オーナーから『PC再起動のたびにchannels設定をやり直すのがストレス、改善案は？』と相談。まず復旧後の動作テストとして reply ツールで chat_id 8571447808 宛に送信成功（地の文はTelegramに届かないため必ず reply 経由、というCLAUDE.md鉄則を遵守）。(2) 現状診断: LaunchAgent `com.ynfactory.telegram-channel`(RunAtLoad=true, plist=~/Library/LaunchAgents/, 実体=~/.local/bin/start-tg-bot.sh) は登録済みで今朝07:29にも自動起動ログあり。だが `tmux ls` の tg-bot セッションは本日11:29:39 created＝07:29自動起動分は死んでおり11:29に手動で作り直されている。これが『毎回手動設定』の正体＝自動起動が立つが生存しない。(3) 根本原因(推定): ①plistに KeepAlive が無く一度死ぬと再起動されない(起動1回きり)、②作業フォルダが Google Drive(CloudStorage)上で再起動直後は未マウント→cwd未準備でbot起動失敗の可能性、③CLI版claudeの認証(Keychain)切れだと起動しても応答せず手動 /login 要。launchd err ログは空。(4) 改善案を3段構えで提示(reply送信済 id=610): A=watchdog(launchd StartInterval 5分でtg-bot死活確認→死んでたらstart-tg-bot.sh再実行、手動復旧ゼロ化)、B=起動スクリプトに待機ガード追加(Google Driveマウント＋ネット接続が整うまで待ってから起動)、C=認証セルフチェック(未認証検知でTelegramへ『/loginして』通知)。(5) 既存資産: start-tg-bot.sh は多重起動防止(tmux has-session判定)＋PATHに ~/.bun/bin 明示済(bunが無いとbot無反応の最大ハマりどころ)。daily-handoff も同じ tg-bot セッションへ send-keys する方式([[daily-handoff-automation]])。【次アクション】オーナー承認待ち。承認後 A+B(+C) を実装すれば『再起動のたび手動設定』は解消見込み。A+Bだけでも大半解決。関連メモリ [[telegram-channel-remote-ops]]。【ハンドオフ運用】git commit/push 実施。"
last_updated: "2026-08-01"
last_device_v2026_06_26: "Mac（23時自動デイリーhandoff。手動作業なし。2026-06-25分インプット自動取り込み=lifelogs/zoom/Google Meetを取り込みindexes再生成、inboxに2026-06-25-lifelog-insights生成。lifelogのアクション項目は0件、ビジネスアイデア6件（AI動画自動化ツール★5・自動再作成システム・給与計算年齢別自動控除・請求書/出勤簿承認フロー自動化 等）。todos/2026-06-25は6/26朝にオーナーがTelegramで3件除外（士業勧誘・住民税照合・銀行決算書提出）。todos/2026-06-26へ繰り越し。ショート動画系コミット（Prevent duplicate topics 等）は別経路で本日コミット済。git push完了）"
last_session_summary_v2026_06_26_daily_handoff: "【23時自動デイリーhandoffセッション（Mac）2026-06-26(金)】手動プロジェクト作業なし。当日07:00のインプット自動取り込みで 2026-06-25 分の lifelogs / zoom / Google Meet を取り込み、各 indexes を再生成。新規=会話原本2件(2026-06-25-lifelogs.md / 2026-06-25-zoom.md)、organized 2件、secretary/inbox に 2026-06-25-lifelog-insights.md（Gemini 2.5 Flash：ビジネスアイデア6・アクション項目0・リサーチトピック1[Claude 2.1復帰動向]・連絡先1[鈴木千春 面接応募者56歳]）。注目アイデア=AI動画自動化ツール(★5)、不合格成果物の自動再作成システム、給与計算の年齢別自動控除、請求書/出勤簿承認フロー自動化。todos/2026-06-25 はオーナーがTelegramで3件除外（士業パートナー勧誘・住民税データ照合・銀行決算書提出）→残タスクを todos/2026-06-26.md へ繰り越し。ショート動画系の自動修正コミット（Prevent duplicate shorts topics / Recover deferred shorts topic consumption）は別経路で本日コミット済。git push 完了。"
last_device_v2026_06_25: "Mac（デイリーhandoff。手動作業なし。2026-06-24分インプット自動取り込み=lifelogs/zoom/Google Meetを取り込みindexes再生成、inboxにlifelog-insights生成。注目アクションをtodos/2026-06-25.mdへ転記。ショート動画自動復旧/再生成コミットは別経路で本日コミット済。git push完了）"
last_session_summary_v2026_06_25_daily_handoff: "【デイリーhandoffセッション（Mac）2026-06-25(木)】手動プロジェクト作業なし。当日のインプット自動取り込みパイプライン（07:00実行）が 2026-06-24 分の lifelogs / zoom / Google Meet を取り込み、各 indexes（external/google-meet/lifelog/zoom 系）を再生成。新規=会話原本2件(2026-06-24-lifelogs.md / 2026-06-24-zoom.md)、organized 2件、secretary/inbox に 2026-06-24-lifelog-insights.md（Gemini 2.5 Flash 抽出：ビジネスアイデア5・アクション項目11・リサーチトピック6）。注目アクション=Instagram投稿の失敗原因調査(high)、ビケン社面接準備、営業アシスタント資料圧縮/データ入力自動化、銀行決算書提出準備、住民税データ照合(PCA/Excel)、契約満了手続き/マイナンバー変更確認。これらは todos/2026-06-25.md に候補として転記。ショート動画系の自動復旧/再生成コミット（Remake failed-quality shorts 等）は本日別経路で既にコミット済。git push 完了。"
last_session_summary_win5: "WIN5予想モデルをkeiba-unified/win5へ移植し案Bで構築。P0(JRA5年データ移植17457レース/240330着順)+P1(WIN5イベント326件 date=方式)+P2(較正勝率モデル)完了。結論=予測でも配当構造(CO)でも+EVエッジ無し→実弾非推奨。ブランチfeat/win5-data-foundation(未push)。詳細はメモリ project_win5_model と win5/docs/superpowers/。"
last_device: "Mac（Sales OS軸Cの初回本番送信を完了。Peatix/Calendly/DM本文の連絡先を y-nakada@yn-factory.com に統一、Google Cloud project YN Tools の Gmail API を有効化し、Queue ID 282 を tdc@mirror-polish.com へ1通送信成功。approval_queue=sent、conversations=conversation_id 1、VPS .env は SALES_OPS_DRY_RUN=true 維持。次は返信・Peatix申込・Calendly予約確認と追加送信候補の選定。詳細は last_session_summary_v2026_06_23_sales_os_first_send。前回=last_session_summary_v2026_06_19_sns_cta_receiver）"
last_device_obsolete_shorts: "Mac（shorts-factory を複数媒体・1日3回投稿・初中中バランスへ拡張。launchdを09:00/14:00/19:00の3枠化、難易度ルーティング、中級ネタ24本追加、Drive→runtime同期安定化、Telegramログのtokenマスク、失敗媒体だけ再試行、複数媒体preflight(check_platforms.py)、staged config(auto_post:false)。QC90点PASS。残=オーナーがYouTube/TikTokログイン後 check_platforms で全ready確認→auto_post有効化と実投稿は明示承認。詳細は last_session_summary_v2026_06_18_shorts_factory_multiplatform。前回=last_session_summary_v2026_06_15_kdp_japanese_folktales）"
last_device_prev_keiba: "Mac（JRA競馬 結果着順自動取得を修復=当日ライブnetkeiba(race.netkeiba)フォールバック追加 scraper_legacy.py/check_results.py、6/7バックフィル23/23・QA88点PASS・本番VPS+Drive同期MD5一致。前段でNotebookLM Sync通知のノイズ抑制も実施）"
last_session_summary_v2026_06_06_keiba_no_odds: "【JRA競馬予想 オッズ非依存モデル検証＋オッズ取得バグ修正＋C5b朝予想本番化セッション（Windows）】全てVPS 163.44.101.31 /opt/keiba-unified/jra/。【A.考察(実払戻バックテスト)】問い=『予想はオッズ非依存・賭け金は配当均等』が現状を上回るか。NO_ODDSモデル(model_v2 FEATURE_COLS_NO_ODDS,76特徴,CV0.503 vs FULL0.546)を/tmpのindex付きDBコピーで並列再学習。4セルA/B(C1現状FULL+value/C2提案NO_ODDS+no_value/C3 NO_ODDS+value/C4 FULL+no_value,全662R実払戻)＋C3深掘り＋C5完全オッズ抜き(C5a順位のみ/C5b自前value=v2確率z-score)。結論:(1)提案C2は現状を上回らない。(2)配当均等<flatで配当均等が最悪→本番flat化。(3)『非人気で勝つ』実体は7番人気以下の大穴ロト(的中8.4%・約11的中依存)で再現性なし(3月マイナス)=実弾は時期尚早・配信コンテンツ運用が妥当。(4)オッズを残すべきはモデルでなく妙味選定(value_score)。(5)完全オッズ抜きC5bは月別98.6-101.3%で極めて安定・後知恵なし・ほぼトントン。レポート=.company/research/topics/2026-06-06-jra-keiba-no-odds-investigation.md。【B.オッズ取得バグ修正(今朝の朝予想が該当0=オッズ0/23)】根本原因3層:①netkeiba APIが&action=update必須に変化(スクレイパー未対応で常に空)②JRA公式経路403死亡(WAF)③no-odds品質上限~0.795<閾値0.86で必ず0件。修正:run_today.pyにaction=update追加＋取得順をnetkeiba主→JRA公式フォールバックへ入替、run_morning/run_liveのno-odds閾値0.86→0.70。本番でオッズ23/23取得・朝予想再配信・9:30 live正常を確認。【C.システム再構成(本番稼働中・明日6/7初稼働)】朝7:00=C5b完全オッズ抜き(run_morning.py MORNING_FULLY_ODDS_FREE=True/NO_ODDSモデル+generate_bets_c5b+evaluate_race_quality_no_odds+C5B_MORNING_THRESHOLD=0.92/flat、predictor_v1.pyにC5b関数追加、model=data/models/model_v2_no_odds.pkl)／ライブ9:30=現状FULL維持／9:35=run_c3_shadow.py新規(C3=NO_ODDS+value+オッズ品質0.86,source='live_c3',Telegram/X通知なし記録のみ,cron追加)／結果集計17:30&月初=check_results.pyにlive_c3追加でmorning/live/live_c3を合算せず3独立集計(検証OK)。【本番変更7点・全backup有】run_today.py(.bak.20260606_oddsfix/_oddsorder) run_morning.py(_oddsfix/_c5b) run_live.py(_oddsfix) predictor_v1.py(_flatstake/_c5b) check_results.py(_livec3)＋新規run_c3_shadow.py/model_v2_no_odds.pkl＋crontab(/tmp/crontab.bak.20260606_livec3,9:35追加)。【DB】本番keiba_live.dbはresultsにhorse_id等index無く学習/採点が遅い→検証は/tmp index付きコピーで実施(本番DB無改変)。【次アクション/監視】(a)明日6/7(日)朝C5b・C3並走の初稼働→17:30の3独立集計をモニタ、(b)C5b閾値0.92のROI影響は未検証→フォワード監視、(c)朝レポートの『暫定』表記が残存(軽微cosmetic要microfix)、(d)C3 vs live並走成績を蓄積し採用判断、(e)即revert=MORNING_FULLY_ODDS_FREE=False。メモリ追加: jra-odds-scraper-fix / jra-no-odds-ab。分析スクリプトC:\\dev\\jra_*.py。【ハンドオフ】git commit/push実施。"
last_session_summary_v2026_06_06_notebooklm_mac_migration: "【NotebookLM YouTube自動同期 VPS→Mac移設セッション】(1) 発端=オーナー『ノートブックLMのソース自動追加が途中で止まっている、確認して進めたい』。調査で判明: VPS(163.44.101.31 /opt/notebooklm-sync/)のcronは稼働中だが 2026-06-04 16:38 を最後にGoogleセッション(storage_state.json)が失効、以降30分毎の全実行が『Google session expired』で失敗＝約2日間ソース追加ゼロ。通知コードは完成済だが secrets.yaml 未設定で『Skipping notification』となりオーナーが気づけなかった。根本原因=認証が storage_state 静的注入(Cookie自動更新なし)＋ローカル取得CookieをVPS(データセンターIP)で再生→Googleが約2時間でセッション無効化。(2) オーナー判断で『同期をこのMacへ移設』『専用Telegram bot新規作成』を決定。(3) 移設(要件定義=.company/requirements/notebooklm-sync-mac-migration-2026-06-06.md): ランタイムをDrive外 ~/notebooklm-sync/ に構築(python@3.11 via brew・venv・依存・Chrome148)、VPSから state.sqlite 移行(processed_videos 53件・重複防止)。(4) **認証方式を実測に基づき要件から変更**: launch_persistent_context(channel=chrome) も headless/自動化フラグでGoogleにbot判定され失効→『常駐させた素の実Chrome(--headless=new --remote-debugging-port=9222・自動化フラグなし)にPlaywrightが connect_over_cdp 接続する方式』へ改修(src/notebooklm.py の _start/_stop/__init__、config.py/sync.py/config.yaml に cdp_endpoint 追加)。residential IP＋素Chromeのため通る。ビューポート1600x1000強制も追加(狭いとソースパネルが畳まれセレクタ非表示)。(5) 検証: check_session.py で SESSION OK・ソース読取44、実際に新着1件(bogsZSiAwmY『Claude Mythos…』)を AI仙人へ追加成功(44→45)、Chrome再起動後もセッション維持を実証(Mac再起動でも復帰見込み)、headlessでも通ることを確認。(6) launchd 2本: com.ynfactory.notebooklm-chrome(scripts/start_chrome_mac.sh・headless常駐・KeepAlive・RunAtLoad)＋com.ynfactory.notebooklm-sync(StartInterval1800=30分毎)。手動トリガーで sync complete 確認。(7) VPS cron停止(/opt/notebooklm-sync/crontab.backup.20260606 保存・フォールバック可・VPS削除せず存置)。(8) 専用bot @mnb121_bot 作成、~/notebooklm-sync/secrets.yaml(Drive外・chmod600・git管理外)に token/chat_id=8571447808、test_notify.py で送信成功(HTTP200)。(9) 新コードをDriveソース(notebooklm-sync/)へrsync反映(secrets/runtime除外)・README更新(Mac運用/再ログイン手順)。【成果物】~/notebooklm-sync/(runtime) / Drive notebooklm-sync/(source) / scripts/{login_mac.sh,check_session.py,start_chrome_mac.sh,com.ynfactory.notebooklm-{chrome,sync}.plist} / ~/Library/LaunchAgents/com.ynfactory.notebooklm-{chrome,sync}.plist。【再ログイン手順(セッション切れ時)】Telegramに『Google session expired』が来たら: (1)launchctl unload ~/Library/LaunchAgents/com.ynfactory.notebooklm-chrome.plist (2)bash ~/notebooklm-sync/scripts/login_mac.sh でログイン→窓を閉じる (3)launchctl load 同plist (4)cd ~/notebooklm-sync && .venv/bin/python scripts/check_session.py で SESSION OK 確認。【既知の軽微】新着追加時の[日付]リネームは時々skip(元々87%・見た目のみ・追加は確実)。【次アクション/監視】(a)次の新着動画で自動追加＆Telegram完了サマリが届くか観察(launchd30分毎・ログ ~/notebooklm-sync/logs/sync.log)、(b)数日〜1週間セッション持続を監視(切れたら上記再ログイン)、(c)Mac長時間スリープ中は同期遅延(launchd復帰時自己回復)。【ハンドオフ】本Mac端末はgit commit不可(.gitがWindowsパス)のためDrive同期で共有。"
last_session_summary_v2026_06_05_keiba_jra_review: "【JRA競馬予想 3か月見直し→2施策を本番実装セッション】(1) 見直しレポート作成 `.company/research/topics/2026-06-04-jra-keiba-3month-review.md`。所見: 本予想(三連複/馬連)はROI98%でほぼトントン(エッジあり・5月黒字転換)、穴予想ワイドはROI65.6%・-65,660円で最大の出血源。本命(軸)は74-75%が3着内で優秀＝強み。ボトルネックは相手の中穴取りこぼし(取りこぼし相手の88%が7番人気以下)＋買い目間引き。**バックテスト(実払戻決済)で『相手拡張・買い目フルながしは全案ROI悪化＝中穴は追わないのが正解、効くのはレース絞り込み』と判明**。(2) 【実装①: 朝予想/ライブ予想の独立集計化(オーナー指示・合算禁止)】prediction_resultsにsource列追加・PK=(date,race_id,source)、daily_summaryを(date,source)別に移行(旧テーブルは*_legacy_bak保全)、check_results.pyのTelegram『📋合計』欄廃止・🌅朝/🔴ライブを各自累計付き独立表示・monthly_summaryもsource別・--no-notify追加、longshot_wide_tracker.pyを cumulative_morning.json/cumulative_live.json に分離＋daily_historyから再計算で冪等化。過去3か月(25開催日)を source別に再集計(replay_main.py/replay_longshot.py)。検証: 旧合算daily_summary -156,670円 = 朝-58,900+ライブ-97,770で完全一致。穴予想は朝ROI75.5%>ライブ56.0%という合算では隠れていた差が判明。(3) 【実装②: 閾値0.86化(黒字化策)】predictor_v1.py `QUALITY_THRESHOLD 0.80→0.86`(唯一のマスター定数。run_morning/run_liveが参照、no-oddsフォールバックも統一)。過去3か月実績で morning -51,500→+66,250(ROI124%)、live -97,770→+4,690(ROI102%)、合算-149,270→+70,940に黒字化。買い目約半減(高信頼レースのみ)。穴予想(別ロジック)は非対象。(4) 全てVPS(163.44.101.31 /opt/keiba-unified/jra/)に本番反映・py_compile/ロード値/メッセージ形式/月次まで検証OK・DB&スクリプトをバックアップ済(*.bak.20260605_*)。6/6(土)cronから新挙動で稼働。【次アクション】(a)数週末フォワードテストで閾値0.86の再現性モニタリング、(b)データ上liveのみ0.88が更に良い(+30,100/ROI124%)ため検討、(c)残る最大課題=穴予想ワイドの抜本見直し(特にlive穴ROI56%)。閾値ノブはQUALITY_THRESHOLD一箇所・sweep_threshold.pyで掃引可。【ハンドオフ運用】git commit/push実施。"
last_session_summary_v2026_06_04_notebooklm_youtube_sync: "【NotebookLM YouTube自動同期システム新規構築セッション】(1) 要望: 登録済みYouTubeチャンネルの新規動画をNotebookLMに自動でソース追加する仕組み。NotebookLM個人版はAPIなし→Playwrightで自動操作する方式を採用。(2) 全工程6を要件定義→executor実装→quality-checker(91/100 PASS)→VPSデプロイの品質ループで完走。対象チャンネル2: AI仙人(UCRxPq02pjQS_ax60gcTSDHQ) / 株式会社AX(UCORVt7JG44UjGdPrhPIBetQ)。各チャンネル1冊ずつ別ノートブック(notebook_id: 05b5c139-/e00c7721-)。(3) 技術スタック: Python3.11 + yt-dlp(初回全動画取得) + feedparser(差分RSS監視, 15件上限) + Playwright Chromium headless + SQLite state DB。VPS=ConoHa(163.44.101.31, Ubuntu22.04)に `/opt/notebooklm-sync/` でデプロイ、.venv隔離、playwright install済。(4) Google認証突破: PlaywrightのChromiumをGoogleがbot判定するため、ローカルWindowsで標準Chromeを `--remote-debugging-port=9222` で起動→CDP接続でstorage_state.json取得→VPSへscp転送する方式 (`scripts/setup_auth.py`+`start_chrome_for_auth.ps1`)。(5) NotebookLM UIセレクタは日本語版に対応: 'ソースを追加'/'ウェブサイト'/'URL を入力'(textarea)/'挿入'/'もっと見る'(⋮)/'ソース名を変更'/'ソースを削除'。CSSセレクタの属性値ダブルクォートはエスケープ必須(`_css_escape_attr`)。(6) 公開日付きソース名リネーム機能を後追い追加: `rename_source`+`bulk_rename`、yt-dlp extract_flatではupload_date空のため video_dates.json (ローカルyt-dlpで個別取得→JSON出力→VPSへ転送) 経由で補完。state.pyにpublished_atカラム追加・スキーマ自動マイグレーション。sync.pyで動画追加直後にrename_source連携。(7) 初回--init全動画取り込み成功(53動画 added=53 errors=0、約8分)。複数パスbulk_renameで46/53リネーム完了(87%)。残7件は「この動画はインポートできません。文字に変換できません。」のNotebookLM側永続エラーソース→delete_error_sources.pyで一括削除→sync.py --initで再追加(7件)。(8) cron `*/30 * * * *` 自動稼働確認(17:30/18:00/18:30実行成功)、logrotate(/etc/logrotate.d/notebooklm-sync, daily/rotate14/maxsize50M/copytruncate)設定済。(9) 既知リスクR2発生中: VPS上storage_state.jsonのGoogleセッションが約2時間で期限切れ→既存処理済み動画のskipのみのcronは影響なしだが、新規動画追加時にSessionExpiredErrorでsys.exit(1)。secrets.yamlのTelegram通知は未設定のため自動アラート届かず。【成果物】 `g:/マイドライブ/YNFactory-cc/notebooklm-sync/` (src/*.py 6本=sync/youtube/notebooklm/state/notify/config、scripts/=setup_auth.py/start_chrome_for_auth.ps1/install_cron.sh/fetch_dates_local.py/bulk_rename.py/delete_error_sources.py、config.yaml/secrets.yaml.example/requirements.txt/.gitignore/README.md/tests/test_state.py)、要件定義書 `.company/outputs/notebooklm-youtube-sync/REQUIREMENTS.md`、ローカル認証作業ディレクトリ `C:/dev/notebooklm-sync-auth/`。【次アクション】(a)強推奨=Telegram通知設定(secrets.yamlにbot_token/chat_id追加)、(b)定期再認証スクリプト(setup_auth.pyを24h毎にユーザー実行＋storage_state自動転送)、(c)Cookie長寿命化検討(NotebookLM Enterprise API/Google Data API代替)。【ハンドオフ運用】git commit実施予定。"
last_session_summary_v2026_06_04_ai_stock_ebook_manga: "【『AI株に投資すべきか？』文字本＋マンガ版 同時制作セッション（成果物はDrive同期で受領、23時自動ハンドオフで追記。同日の notebooklm-youtube-sync 構築は別キー last_session_summary_v2026_06_04_notebooklm_youtube_sync に既記録）】(1) テーマ「AI株に投資すべきか？」から theme-to-ebook→ebook-to-manga パイプラインを一気通貫実行し、文字本とマンガ版の2点を統合フォルダ`.company/outputs/ai-stock-investment/`に制作。Phase0回答=1A/2B/3A/4B/5B/6A/7A。(2) 文字本(タイトル『AI株に投資すべきか？』、目標50,000字)=quality-checker 91/100 PASS、本文画像16点(AI生成由来)、EPUB`文字本/KDP出版用/AI株に投資すべきか？.epub`。文字本サブ成果物=project.md/QUALITY_REPORT.md/IMAGE_GENERATION_REPORT.md/REVISION_REPORT.md/handoff_to_manga_check.md/progress.json。(3) マンガ版(タイトル『マンガでわかる！AI株に投資すべきか？』)=pages 100点(AI生成/AI派生加工PNG)、EPUB`マンガ版/KDP出版用/...epub`。マンガCSVは『4コマ基本』固定を廃止しテンプレ1〜7＋標準コマ別テキストJSONスキーマへ修正。表紙は文字本・マンガ版とも ebook-to-manga Step6の5ステップ構造を流用しAI生成アート背景＋正確な日本語文字合成で作り直し。修復レポート=PIPELINE_REPORT/IMAGE_REPAIR_REPORT/MANGA_STEP4_TEMPLATE_REPAIR_REPORT/AI_IMAGE_REPLACEMENT_REPORT/AI_DERIVED_PAGES_REPORT。主要スクリプト=remake_manga_step1_4_ebook_to_manga.py/build_ai_image_replacement.py/repair_images_epub_v2.py/repair_manga_step4_templates.py/generate_ai_stock_packages.py。要件定義2本=`.company/requirements/{theme-to-ebook-to-manga-ai-stock-investment,ai-stock-manga-remake-ebook-to-manga}-2026-06-04.md`。(4)【その他本日成果】JRA中央競馬AI予想 3か月見直しレポート=`.company/research/topics/2026-06-04-jra-keiba-3month-review.md`(対象2026-03-14〜05-31の実データ約2.5か月/12週末/21開催日、的中率・回収率・モデル改善・運用安定性・収益コストを`keiba_live.db`等から分析)。【次アクション】文字本・マンガ版の両EPUBをKindle Previewerで目視→KDP申請。【ハンドオフ運用】23:00 launchd自動ハンドオフ正常発火(ログ6/4 23:00:02)。git commitは本Mac端末では不可(`.git`がWindowsパスを指すgitfile構成)のためスキップ＝更新はDrive同期で共有。"
last_session_summary_v2026_06_03_inputs_auto_import_system: "【インプット自動取り込みシステム構築セッション（成果物はDrive同期で受領、23時自動ハンドオフで記録）】(1) `.company/inputs/`（旧 `.company/context/`、概念的にリネーム＝実体は外部一次情報の格納庫）に、複数ソースからの自動取り込み基盤を構築。共通アーキテクチャ=raw原本保存(`intake/.../raw/YYYY-MM-DD/`)→Markdown正規化(`normalized/`)→会話原本(`conversations/`)→活用版(`organized/`)→横断索引(`indexes/`)、重複取り込みはstate JSONで防止。(2) ソース別: ①Google Drive投入口`00_INPUT_BOX/`=`import_drive_inbox.py`(raw保存+正規化+`intake/state/drive_inbox_imported.json`重複防止+`organized/external/`+`indexes/external-*.md`、原本は削除しない)、②Google Meet投入口`00_GOOGLE_MEET_BOX/`=`sync_google_meet.py`/`organize_google_meet_inputs.py`(.txt/.md/.docx/.pdf対応、会話原本`conversations/YYYY-MM-DD-google-meet.md`+整理版+3索引meetings/next-steps/topics、.gdocは本文なしのためneeds_export状態保存)、③Zoom=`sync_zoom.py`/`organize_zoom_inputs.py`、④Limitless=`sync_limitless.py`、⑤横断要約=`extract_insights.py`。(3) 自動実行運用一式: Mac/Windows両対応の`auto_import_loop.py`+`auto_import_mac.sh`/`.bat`、`setup_auto_import_{mac,windows,windows_logon}`+`remove_*`、`run_daily.sh`、`sync_all.bat`、アップロードサーバ`upload_server.py`+`start_upload_server_*`。`inputs/CLAUDE.md`を新構成に改訂(投入口・サブフォルダ・運用ルール記載)。(4) 要件定義5本を`.company/requirements/`に作成(いずれも-2026-06-03): zoom-organized-inputs / drive-inbox-input-registration / limitless-organized-inputs / google-meet-input-registration / google-meet-drive-auto-export。(5) 本日のinbox`secretary/inbox/2026-06-03.md`は約70KB(取り込み済み会話多数)。【目的】Limitless/Zoom/Meet/Drive投入の会話・議事録から予定・約束・TODO候補・人物情報を抽出し短期コンテキスト/日別TODOへ反映する導線づくり。【次アクション】各端末で setup_auto_import を有効化し定常運用へ／取り込み結果(organized/indexes)をTODO反映フローに接続。【ハンドオフ運用】23:00 launchd自動ハンドオフ正常発火(ログ6/3 23:00:09)。git commitは本Mac端末では不可(`.git`がWindowsパスを指すgitfile構成)のためスキップ＝更新はDrive同期で共有。"
last_session_summary_v2026_06_02_ebook_ai_agent_workflow: "【新規電子書籍『AIが勝手に仕事する会社の作り方』制作セッション（成果物はDrive同期で受領、23時自動ハンドオフで記録）】(1) 新刊『AIが勝手に仕事する会社の作り方』（副題:属人化したPC業務を分解し、AIエージェントと自動化で回す実践入門／著者Yuichi）を制作完了。テーマ=AI活用を文章生成で終わらせず、属人化PC業務を分解しAIエージェント・ブラウザ自動化・AIコーディングで仕事が進む仕組みに変える実践入門。想定読者=中小企業経営者/管理職/AI導入担当/個人事業主。(2) 全8ステップdone（0要件approved→1リサーチ→2project→3原稿→4画像設計→5KDPメタ→6品質チェック→7表紙→8EPUB）。本文22,660字（はじめに2,260+第1章3,744+第2章3,707+第3章3,501+第4章3,406+第5章4,503+おわりに1,539、25,000字目標の±10%内）。(3) 本文画像18点を生成（**API不使用**=OPENAI_API_KEY/openai-image-gen/client.images.generate等は使わずCodex/ChatGPTの画像生成経路で再生成、旧画像は`_images_source/images_pre_chatgpt_image2_backup/`へ退避、旧API実行サンプルも削除）＋表紙PNG/JPEG＋表紙プロンプト整備。(4) 品質チェック=quality-checker 94/100 PASS（原典反映18・構成18・実践性19・2026根拠補強17・KDP整備20）。表紙つきリフロー型EPUB生成・必須構造/章数確認済。created 2026-06-02T17:45→updated 20:22(JST)。【成果物】`.company/outputs/ebooks/ai-agent-workflow/`配下=manuscript/(00はじめに+01〜05章+06おわりに)、KDP出版用/(AIが勝手に仕事する会社の作り方.epub・cover各種・書籍情報.md・ジャンル・キーワード.md)、QUALITY_REPORT.md・IMAGE_GENERATION_REPORT.md・progress.json・source/original_transcript.md。【次アクション】EPUBをKindle Previewerで目視→KDP申請。【ハンドオフ運用】23:00 launchd自動ハンドオフ正常発火（ログ6/2 23:00:03）。git commitは本Mac端末では不可（`.git`がWindowsパスC:/dev/YNFactory-git/.gitを指すgitfile構成）のためスキップ＝更新はDrive同期で共有。"
last_session_summary_v2026_06_01_auto_handoff_fired: "【2026-06-01 23:00 自動ハンドオフ（無作業日）】前日構築したlaunchd `com.ynfactory.daily-handoff` が予定どおり発火（ログ `~/Library/Logs/daily-handoff.log` に `2026-05-31 23:00:06` と `2026-06-01 23:00:05` の2回送信記録あり＝自動化は正常稼働を実証）。本日(6/1)はこの23時ハンドオフ時点で `.company` 配下に新規作業の変更なし（完了タスク0・直近90分のファイル更新0）。よって作業サマリーは捏造せず、TODO `2026-06-01.md`（朝6:30自動生成・前日未完タスクを正しく引き継ぎ済）の状態維持のみ。最優先の継続タスクは変わらず: ①漏洩シークレットのローテーション、②Meta SNS Step6、③マンガ第4巻KDP申請。git commitは本Mac端末では不可のためスキップ（`.git`がWindowsパスを指すgitfile構成）。"
last_session_summary_v2026_05_31_daily_handoff_automation: "【毎日23時 自動ハンドオフ構築セッション（Mac・Telegram経由）】オーナーから『毎日23時にハンドオフするように』と依頼。(1) 方式検討: /schedule（リモートCCR）はGitHubリモート必須かつローカルファイル/当日セッション文脈に触れないため不適（本worktreeはGoogle Drive上・`.git`はgitfileでC:/dev/YNFactory-git/.gitを指すWindows構成、Macからはcommit不可）。CronCreate(durable=true)もディスク未永続でセッション限り＋7日失効のため恒久運用に不適。→既存の常駐インフラ（[[telegram-channel-remote-ops]] のtmuxセッション`tg-bot`でclaude --channels常駐）へ、launchdから`tmux send-keys`でhandoff指示を注入する方式を採用。(2) 成果物: `~/.local/bin/daily-handoff.sh`（tg-bot存在チェック→handoffプロンプトをsend-keys→Enter送信、ログ`~/Library/Logs/daily-handoff.log`）＋LaunchAgent `~/Library/LaunchAgents/com.ynfactory.daily-handoff.plist`（StartCalendarInterval Hour=23 Minute=0）。`launchctl load`済、`launchctl list | grep ynfactory`でstatus 0確認。一時作成したsession-only cron(5ed3abc0)は二重発火回避のため削除。(3) メモリ`daily-handoff-automation.md`保存＋MEMORY.md索引追加。【注意】Macがスリープ/シャットダウン中の23時は発火しない（次回起動後の23時から再開）。本Mac端末は`.git`がWindowsパスを指すためgit commit/push不可＝HANDOFF/TODO更新はDrive同期で共有（commitは別端末で実施）。明日23時から稼働。"
last_session_summary_v2026_05_31_voice_apps: "【音声録音アプリ + 常時録音文字起こしサービス voice-journal 新規開発セッション】(1) /goal『音声録音アプリ』→ voice-recorder/ をバニラJSで新規作成(ブラウザ完結: 録音/停止/一時停止/再開・リアルタイム波形・録音リスト 再生/WebMDL/WAV変換DL/リネーム/削除・IndexedDB永続・マイク選択・日本語UI/レスポンシブ/ダークモード)。要件定義(.company/requirements/voice-recorder/REQUIREMENTS.md)→executor実装→quality-checker 97点PASS。(2) 起動トラブル対応(systematic-debugging): file://直開きはgetUserMediaがsecure context必須で不可→localhostサーバ必須。ダブルクリック起動用 start.bat を作ったが『黒い画面が一瞬で消える』発生=日本語Windowsのcmdが.batをCP932解釈しUTF-8の日本語が文字化け→コマンド解析破壊→即終了。start.batを完全ASCII化(別ウィンドウでpyサーバ起動+単純なstart URL方式)で解消。Playwright/curlでlocalhost稼働確認OK。教訓をメモリ windows-bat-ascii-only に保存。(3) 追加要望で常駐サービス voice-journal/ を新規開発: PC起動時自動起動→1時間ごとにマイク+PC再生音(WASAPIループバック)録音→ローカルfaster-whisper(small/int8)で日本語文字起こし→.company/secretary/inbox/YYYY-MM-DD.md に時刻見出しで追記→成功した音声は削除(失敗はリトライ→failed/退避)。設計はsuperpowers:brainstorming経由でA案(2トラック録音→文字起こし時16kモノにミックス)採用。音声一時保存はDrive外のC:\\voice-journal-temp、inboxにはテキストのみ。設計書=.company/requirements/voice-journal/REQUIREMENTS.md。executor実装(sounddevice/soundfile/faster-whisper/soxr 導入、ユニット20件+スモーク+5秒ライブ録音 全pass)→quality-checker 91点PASS。実機で2バグ修正: (a)設計書記載のPC音不可時inbox注記を未実装→実装、(b)setup_autostart.ps1がPS7専用構文『?.』でWindows PowerShell5.1だと構文エラー→PS5.1互換へ修正。タスクスケジューラ登録は管理者権限が要りアクセス拒否→無管理者のスタートアップフォルダ方式 setup_autostart_startupfolder.ps1 を追加しVoiceJournal.lnkを登録済(次回ログオンから稼働)。pythonwブート検証OK(PAUSE.flag併用で録音/inbox汚染なし、temp残骸0確認)。(4)【次回観察】CPUで1時間分の文字起こしが1時間以内に終わるか(small/int8は通常実時間より速いが未実測)→詰まればモデル降格/GPU化。PC音は既定出力デバイスのみ録音(切替時は再起動要)。プライバシー(通話相手の声も記録)はオーナー配慮。【成果物】voice-recorder/(index.html,style.css,app.js,README.md,start.bat) / voice-journal/(service.py,recorder.py,transcriber.py,audio_mix.py,inbox_writer.py,config.json,requirements.txt,setup_autostart.ps1,remove_autostart.ps1,setup_autostart_startupfolder.ps1,remove_autostart_startupfolder.ps1,start.bat,README.md,tests/) / 各REQUIREMENTS.md。"
last_session_summary_v2026_05_31_github_migration: "【作業ディレクトリ GitHub軸移行セッション + 機密誤pushインシデント対応】(1) 前日復旧した .git(ローカルC:\\dev\\YNFactory-git)を土台に、複数台運用に耐える恒久構成を設計→実装。設計書=docs/superpowers/specs/2026-05-30-workdir-git-architecture-design.md、実装計画=docs/superpowers/plans/2026-05-30-workdir-git-architecture.md。確定構成=【3レイヤー】作業ツリー(G:\\マイドライブ\\YNFactory-cc・Drive同期・パス不変)/大容量バイナリ(画像/動画/keibaデータ=gitignore除外・Drive配布)/.git(各PCローカル)↔GitHub private(yuichi4107-lab/YNFactory-cc, branch main)で同期。(2) スリム化: 追跡7.2GB/11847ファイル→258MB/5998ファイル(画像5.6GB・keiba 100MB超pkl/csv/db等を除外)。orphan新規履歴で初期コミット作成、旧履歴は archive/pre-github-2026-05-30(旧codex/sagyo)+master+codex/ebookgpt5.5+.git_drivebackup(4.7GB)に温存。(3) **【重大ミス→対応済】機密誤push**: 移行中にTelegram/Gemini/Stripe/Google/DB/VPSパスワードを含むコミットをprivate GitHubへpushしてしまった(push直前の機密ゲートで検出が出ていたのにバッチ化で止まらなかった)。→即リモート削除で外部撤回→13ファイルから機密除去(運用コード=os.environ.get化、手順書=伏字化、settings.local.json=gitignore、.claude/settings.jsonのパスワード行削除)→Telegram/VPSパスワードはUser環境変数に退避(TG_BOT_TOKEN/TG_TOKEN_JRA/TG_TOKEN_BANEI/TG_CHAT_ID/VPS_ROOT_PW)→クリーンなorphan履歴を再構築しGitHub Push Protection通過でpush成功(現HEAD=7cbedcd)。(4) handoffスキルをpush対応に更新(Drive停止を任意化・git push origin main追加・lockパスをC:/dev/...に・機密スキャン注記)、gdrive-git-setup.mdを確定構成+2台目セットアップ手順に全面改訂。(5) gh認証アカウントは yuichi4107-lab(yuichi121ではない)。delete_repoスコープ付与済。【次回最優先(オーナー作業)】漏洩シークレットのローテーション: Stripe(sk_live/whsec)・Google OAuth(GOCSPX)・DBパスワード・VPS rootパスワードを再発行。手順書=.company/engineering/debug-log/2026-05-31-secret-rotation-after-github-leak.md。【残り(Task11)】最終検証(push/pull往復・別PC clone再現・ロールバック確認)。【その後】数日 git正常稼働確認後に .git_drivebackup(4.7GB)+Driveゴミ箱旧worktree(12.69GB)削除で約17.5GB解放、他端末(職場PC/Mac)セットアップ。"
last_session_summary_v2026_05_30_git_recovery: "【git作業ディレクトリ復旧セッション】(1) 症状: 全gitコマンドが `fatal: not a git repository: C:/dev/YNFactory-git/.git` で失敗しコミット不能。(2) 根本原因(2故障の重複): ①Git×Drive Phase2の移設先 C:/dev/YNFactory-git/ が未作成(.gitポインタの参照先が不在)、②唯一の実体 .git_drivebackup(4.7GB) の HEAD が書込み途中で消失しHEAD.lockのみ残存。(3) 復旧(Claude Codeが実施・systematic-debugging): 事前検証で .git_drivebackup は Offline 0件・loose ref refs/heads/codex/sagyo=d0a777c クリーン・remote無を確認 → robocopyで C:/dev/YNFactory-git/.git へ復元(desktop.ini/*.lock除外・38ファイル) → HEADを `ref: refs/heads/codex/sagyo` で再作成 → `git fsck --full` 問題なし → `git reset` で幽霊削除7307件解消(作業ツリー無変更) → core.longpaths=true 設定(chrome_profiles長パス対策) → .gitignoreに .git_drivebackup/ 追加(4.7GB再肥大化防止)。(4) 在庫を一括コミット: 107ファイル/46.2MB(50MB超0件・backup混入0件)、commit 06fa0d0、**commitは3.3秒で完走しPhase2のハング解消を実証**。pushはなし(このrepoにremote無し・Drive保全のみ)。手順書=.company/engineering/debug-log/2026-05-30-git-head-recovery.md に「実施結果」追記済。【残タスク(手動・任意)】(a) 数日 git 正常稼働を確認後 .git_drivebackup(4.7GB)+Driveゴミ箱の旧worktree(12.69GB)を削除し約17.5GB解放、(b) git pack-refs --all で packed-refsの古い codex/sagyo=6ba70f0 を整理、(c) .wrangler/cache/ と LP配布zip(ai-introduction-consult-publish.zip 14.6MB)を gitignore化検討(今回は一括指示で含めた)。【その他継続】Meta SNS Step6/JRA cron土日監視/Stripe本番移行/FX。"
last_device: "自宅Windows（NotebookLM YouTube自動同期システム構築：ConoHa VPSへ /opt/notebooklm-sync/ をデプロイ、cron 30分ごと稼働中、AI仙人+株式会社AXの2チャンネル計53動画の自動取り込み+46/53公開日プレフィックス[YYYY-MM-DD]付与完了、残7件はNotebookLM側のインポートエラーで削除→再追加済み。Cookie寿命≒2時間でstorage_state.json再認証が運用課題、Telegram通知未設定）"
last_device_prev: "自宅Windows（マンガ第4巻 プレビュー全数検証→描き文字4枚修正→CTA挿入→髪型再修正→EPUB再製本55ページ まで完了）"
last_session_summary_v2026_05_22_manga_career_vol4_textfix_cta_hairfix: "【第4巻 プレビュー検証→画像修正→CTA挿入→髪型修正セッション】(1)前回(5/21)完成の第4巻EPUB(54P/29MB)を目視確認支援。展開して構造OK(54xhtml+45画像、spine=表紙+1..54、テキスト10枚、著者名Yuichi)。(2)漫画44枚を全数スキャンし描き文字4件発見: p025(第8章扉の振込通知に¥38,500捏造→本編p033-037は1,280円で矛盾)/p031(『深夜0時のリビング』が『ビング』脱字)/p042(本の背表紙が文字化け『ライリタ』)/p050(エピローグ『あの日退職届を出した』が『逆境屈』化け)。Codexバンドル(manga-career-restart_vol4_20260520_235905/manual/prompts)のプロンプト原文を確認、4件ともプロンプトは正しくChatGPT Plus手動生成時の描き文字ミスと判明。(3)現44画像はChatGPT Plus手動生成と判明→同系のOpenAI gpt-image-2(openai-image-genスキル,画質high,キャラ参照ミサキ.png等+テンプレ)で4枚再生成。p025は金額を一切描かない指示で捏造回避。(4)オーナー指示で著者紹介(53)の後にvol3共通CTA(LINE登録画像page_cta.png 1024x1536,QR=https://lin.ee/PjCf7vw)をp054画像として挿入、奥付をp054→p055へ繰り下げ。本番ビルドは _scripts/build_vol_epub.py(pages_jpeg画像+text_pages xhtmlをページ番号順に組む。--csv-fileなしのファイル存在ベースで実行)。(5)オーナーから『エピローグ最後p050のミサキの髪が後ろで結ぶ長さでない』指摘。キャラ参照=短い黒髪ボブ(下ろし)と確認、私の再生成3枚(p031/p042/p050)が服装欄『髪を緩くまとめ』に引っ張られ後ろ結びにしていた。3枚を髪=短いボブ下ろし強制で再生成。p042はナレーション全文(4つの『どれくらい〜』)が揃いClaude表記も正しい候補c2採用。(6)EPUB再製本=55P/画像45/29.1MB、spine=表紙+1..55、p54=CTA画像・p55=奥付テキストを実画像で最終確認。CSV(comicle_output.csv)・progress.jsonも55P構成に更新。【旧版退避】pages_backup_20260522_textfix/(5/20オリジナル)、regen_20260522/(髪結び中間版)、regen_20260522b/(髪修正採用版)、_epub_backup_pre_textfix_cta_20260522.epub.bak。【スクリプト】C:/dev/regen_vol4_4pages.py,apply_vol4_fixes.py,update_vol4_csv_progress.py,regen_vol4_hairfix.py。【次回最優先】(a)第4巻.epub(55P)をKindle Previewerで最終目視→KDP申請、(b)git commit未実施(Git×Drive問題継続。.gitローカル移設Phase2後にまとめてコミットが最短)、(c)CTA配置はvol3実体(著者→奥付→CTA最後)と異なり今回は著者→CTA→奥付にした点を要確認。【継続】Meta SNS Step6/FX MS1/Git×Drive Phase2/JRA cron土日/Stripe本番移行。"
last_session_summary_v2026_05_21_manga_career_vol4_finish: "【マンガ career-restart 第4巻（完結巻）Codex画像受領→EPUB製本→KDPメタ完了セッション】(1) オーナーから『キャリアのvol4の画像生成がCodexで完了、続きの作業を』と指示。状況把握: 4/29 の50字+outfit_id 再構築よりさらに後、vol3=5/19・vol4=5/20 に全面再ビルド（vol3 と同系）が走っており、Codex バンドル `manga-career-restart_vol4_20260520_235905`（54ページ＝本文44+テキスト10）が `done/` に status=success・44画像 pass・needs_manual_review 0・cover成功 で返却済みだった。HANDOFF最上部(5/12)には未記録だったため codex/done と vol3 完成版(5/20 EPUB 23MB)を突き合わせて経緯を再構築。(2) パイプライン特定: `_scripts/gen_text_pages_from_csv.py`(汎用) + `_scripts/build_vol_epub.py`。ただし汎用レンダラーはコラム見出しの h2/h3 整形ができず vol3 品質に届かないため、vol4 専用レンダラー `_scripts/gen_text_pages_vol4.py` を新規作成（コラム番号=h2／サブタイトル=h3／キャリコン行=subtitle／奥付=colophon、◆指示行とセクションマーカー除去、旧番号付きxhtml一掃）。(3) 検収: done/pages の44画像ページ番号が CSV 非テキスト44ページと完全一致（欠番・余剰ゼロ）を検証。(4) 配置: 44画像→vol4/pages/、Codex新表紙 cover.png(1024x1536) を PIL で cover.jpg(596KB) 変換＋cover.png も保存。旧4月版 cover.jpg は cover_april_backup.jpg.bak に退避。(5) テキストページ10枚生成: P1目次/P2前巻あらすじ/P23-24コラム⑧/P38-39コラム⑨/P51-52コラム⑩/P53著者紹介/P54奥付。vol3 同等の整形を確認。(6) EPUB製本: 初回 PNG だと125MB→vol3(23MB)と乖離。vol3 が JPEG(48枚~300KB) と判明したため PNG→JPEG q90 変換(計19.7MB)し pages_jpeg で再ビルド→**29MB**・PAGE_XHTML 54・PAGE_IMAGE 44。spine 検証: mimetype先頭・spine=cover+1..54連番・cover-imageメタ有・pre-paginated(固定レイアウト)。旧4月版 EPUB2本は vol4/_archive_april_epub/ に退避。(7) KDPメタ3点: 書籍情報.md(発行日追記)／ジャンル・キーワード.md(完結巻テーマ=初収益・個人で稼ぐ・自己肯定感に刷新)／書籍紹介文_HTML.html(7要素・完結巻フレーミング)。**重要修正**: 4月版メタは主人公をミサキの娘『ひなた』と取り違え・報酬額523円・章立て第9話/第10話 と実内容に反していたため、ミサキ・1,280円・第7章フォロワー100人の夜/第8章初めての振込通知/エピローグ私のキャリアは私が決める に全面修正。(8) 著者名は『Yuichi』が正（vol3 書籍情報.md も Yuichi。メモリの『暮らしの貯蓄研究所』は別書籍用なので本シリーズには適用しない）。(9) done→archive移動済。vol4/progress.json に全工程done記録。**【git commit 未完＝要対応】** 成果物は全てディスク保存済(Drive同期=バックアップ済)だが、git commit は失敗。原因は Drive 上の巨大リポ＋index破損(Drive同期由来の7307件 phantom deletion がステージ済)で git の index 全書き込みが病的に低速になり、`git reset`(0バイトlockで6分超ハング)・`git commit <pathspec>`(3257バイトlock残し未コミット)・ローカル一時index方式(`GIT_INDEX_FILE`+`read-tree HEAD` も3分超未完)すべてが完走しなかったため。stale lock と temp index は掃除済でリポジトリはロックなしのクリーン状態に戻してある(HEADは42d8c6e=5/12のまま)。これは継続TODO『Git×Drive共存問題 Phase2(.gitをC:/dev/YNFactory-git/へ移動)』そのもの。**次回: .gitローカル移設を先に実施→その後 vol4 成果物(下記パス)を commit するのが最短**。コミット対象: `_scripts/gen_text_pages_vol4.py` / `vol4/text_pages/page_{001,002,023,024,038,039,051,052,053,054}.xhtml`(旧番号xhtmlは削除) / `vol4/progress.json` / `vol4/KDP出版用/{書籍情報.md,ジャンル・キーワード.md,書籍紹介文_HTML.html,cover.jpg,cover.png}` / HANDOFF.md / todos/2026-05-21.md（EPUBは.gitignore対象なのでコミット不要、Drive保全）。【成果物】vol4/KDP出版用/{第4巻.epub(29MB), cover.jpg, cover.png, 書籍情報.md, ジャンル・キーワード.md, 書籍紹介文_HTML.html} / vol4/text_pages/page_{001,002,023,024,038,039,051,052,053,054}.xhtml / vol4/pages/(44png) + vol4/pages_jpeg/(44jpg) / _scripts/gen_text_pages_vol4.py(新規) / vol4/progress.json。【次回最優先】(a) オーナーが第4巻.epub を Kindle Previewer で開いて目視確認（特にコラム⑧⑨⑩・奥付のテキスト表示、画像44ページの抜け/順序）、(b) 問題なければ KDP 申請（vol1は審査済、vol2/vol3 の出版状況と合わせて第4巻=完結巻として登録）、(c) **vol3 も done(`manga-career-restart_vol3_rebuild_20260519_104524`)が archive 未移動のままなので、vol3 が KDP 申請まで完了済みか要確認**（EPUB は5/20生成済）。【その他継続タスク】Meta SNS Step6（Console 権限追加→Graph API Explorer トークン）／FX MS1(OANDA)／Git×Drive Phase2／JRA cron 土日監視／Stripe本番移行(4商品Price ID待ち)。【オーナーへの注意点】(a) EPUBは固定レイアウト(pre-paginated)・JPEG q90で29MB、KDP配信コスト的にも適正。PNG版125MBは不採用。(b) cover はCodex新規生成版を採用（旧4月版は .bak 退避）。(c) gen_text_pages_vol4.py は vol4 のコラム見出し書式(【コラム⑧】タイトル——サブタイトル)前提。vol5 以降や書式変更時は要調整。"
last_session_summary_v2026_05_12_chatgpt55_manga_redo: "【マンガ版『ChatGPT 5.5時代の結論』シナリオ全面書き直しセッション（C案＝段階進行：シナリオ書き直しのみ完了、パネル/画像再生成は次フェーズ判断）】(1) オーナーから『第◯話の区切りがなくダラっとした印象、章扉と章末まとめを追加、メリハリある躍動感のあるマンガに作り直したい。現状はアーカイブ』と指示。対象: `.company/outputs/ebooks-manga/chatgpt55-now-only-manga/`（120P・629行のシナリオ.txt + パネルCSV + パネル画像 pages_openai_generated + EPUB + 表紙すべて完成済）。進め方A/B/C のうち C（段階進行：シナリオのみ書き直し→仕上がりを見てパネル再生成判断）を選択。(2) 旧一式を `archive_20260512_pre-redo/` にアーカイブ完了（manuscript・panels・pages_openai_generated・build・KDP出版用・progress.json・QUALITY_CHECK.md・project.md・tools・共通テンプレ）。(3) requirements-definer で要件定義書 `.company/requirements/chatgpt55-manga-redo-v2.md`（271行→ADDENDUM v1/v2/v3 追記で約700行）作成。基本仕様: プロローグ＋第1-5話＋エピローグの全7部に章扉1P＋本編＋章末まとめ1P、120-135P範囲、起承転結（起20/承30/転25/結25%）、転に驚き大ゴマ・結に大ナレーション枠、効果音テロップ、ナレーション3コマ連続禁止。呼称は『第◯話』に統一。承認後 executor で v2 初稿作成（120P、QC 95点 PASS）。(4) **オーナーから論旨の根幹修正フィードバック1回目**: 旧版の『比較疲れ・選ぶより進めろ』軸は誤り。正本は『ChatGPT/Claude/Gemini は3社とも総合力高い／1か月前は Claude＋Gemini Nanobanana の二刀流（Claude＝テキスト/コード/思考整理、Gemini＝画像補完）が現実解／GPT-5.5 で画像が ChatGPT 内で完結→組み合わせ不要に』。ADDENDUM v1 を要件定義書に追加（採点項目A 配点25を新設）。executor で本文全面改訂（プロローグ・第1-5話・エピローグの骨格を差し替え／旧 P108-P117 の繰返し構造廃止／P101-P107 実践補足7Pに圧縮）。QC 93点 PASS。(5) **論旨修正フィードバック2回目（トーン）**: 『完璧化』『十分』など断定NG、『私の体感では Nanobanana 日本語表記80点 →gpt-image-2.0 で95点くらい』と主観表現を必須、結論は『高いレベルで一本化なら ChatGPT 5.5 がしっくりくる』。ADDENDUM v2 追記（必須表現7項目／禁止表現5項目／普遍化防止）。executor で再度上書き改訂（P002章扉サブタイトルを『ミナの場合、最後のピースは画像だった』に変更、『あなたにとっての最後のピースは違うかもしれない』を4箇所、Opus 4.7時代の言及、80→95点の体感、ChatGPT 5.5 は Opus 4.7 より少し優秀／普段は差を感じない 等）。QC 97点 PASS。(6) **論旨修正フィードバック3回目（水面下レイヤー）**: ClaudeCode/Codex の使用は大前提。1か月前 Claude が中心だった真の理由は『ClaudeCode の存在』、いま ChatGPT 5.5 の真の理由は『Codex 前提だから』。Gemini の真の強みは『マルチモーダル＋将来展開力＋Google サービス連携（Drive・Meet・Calendar・Gmail）』。業界原則『抜きつ抜かれつ／どれも使えるようにしておく／自分が一番使いやすいものに慣れる』。説明スタイルは B 案（用語そのまま＋初出時に簡単な説明）。ADDENDUM v3 追記（採点項目A を9要素に拡張＋項目B 新規）。executor で v3 反映: Codex 初出説明 P013、ClaudeCode 初出説明 P038、第3話に Gemini 3強み 拡張ページ P039-b 追加、抜きつ抜かれつ P044、自分が使いやすいもの P044/P093/P094、自分にとっての最適解≠他人の最適解 P099/P100、章扉サブタイトル更新（第1話『画像という最後のピース＋Codexという水面下の本丸』、第4話『リレーから単独走行へ＋ClaudeCodeからCodexへ』、エピローグ『高いレベルで一本化…＋ただし——それは私にとっての最適解だ』）。QC 97点 PASS。(7) 現在の成果物: `manuscript/シナリオ_v2.txt`（120P・約1018行・最新版）／`manuscript/章構成サマリ.md`／要件定義書（ADDENDUM v1+v2+v3 反映済）／旧一式は `archive_20260512_pre-redo/`。QC指摘の軽微改善余地: P039-b の通し番号化（次フェーズで P040 以降にリナンバーして P121 まで／または他ページ統合で P120 維持）。【次回最優先】(a) オーナーがシナリオ_v2.txt をエディタで通し読み→トーン/論旨の最終OK判断、(b) OK なら P039-b リナンバー（軽微修正）→ 次フェーズ要件定義（パネルCSV再生成 → OpenAI gpt-image-2 で120P画像再生成 → EPUB再構築 → KDP表紙・メタデータ再生成）に進む、(c) NG ならさらに改訂。【その他継続中タスク】Meta SNS Step6（Console で use case 権限追加→Graph API Explorer トークン取得）／FX MS1（OANDA接続）／Git × Drive 共存 Phase 2／JRA予想 cron 監視（土日のみ）／Stripe本番移行（4商品Price ID待ち）等は別途。【オーナーへの注意点】(a) シナリオ_v2.txt はオーナー目線で全文通読が前提。今回 QC 97 点だが、QC は要件定義書の充足チェックなので、最終トーン判断はオーナーのみが下せる。(b) パネル画像再生成は OpenAI gpt-image-2 で1枚あたり数十秒〜数分かかり、120P 全再生成で1-3時間規模の作業。(c) ChatGPT 5.5 と Codex の言及は要件定義書で「2026-05-12 時点の現状」として扱っているため、もし将来 model 名が変わった場合の差し替え範囲を意識しておく必要あり。(d) ClaudeCode/Codex の説明は『B 案＝用語そのまま＋初出時に簡単な説明』スタイルで一貫させた。"
last_session_summary_v2026_05_06_ebook_skill_meta_sns: "【ebook-to-manga skill 恒久改修 全5工程完了 + Meta SNS Step6 試行・中断セッション】(1) 朝のTODO確認→『チケット 2026-04-24（Pillow撤廃 + Vision-check緩和 + OCR正規化強化）の整理』着手。skill.md 現状ギャップ分析: Pillow関連3項目は実質完了済み（ファイルから既に消去）、残6項目を改修対象として要件定義書 `.company/secretary/notes/2026-05-05-ebook-to-manga-skill-refactor-requirements.md` を作成（5工程に分割）。 (2) 工程1（Vision-check緩和、95点）→工程2（OCR正規化強化+fuzzy matching+--strict-ocr、93点）→工程3（max_iter デフォルト3→1、--qc off/lite/full フラグ、92点）→工程4（コスト試算 simple/lite/full 3モード対応、93点）→工程5（E2E手順 4ケース刷新、95点）すべて executor→quality-checker ループで合格。最終仕上げで軽微指摘9項目を一括修正→最終QA 91点 PASS。 (3) skill.md は 2330→2314行（-16行）。チケット完了条件 9/9 充足。チケット 2026-04-24 を done に更新、TODO反映、要件定義書保存。 (4) 続いて Meta SNS Step6 着手。Claude in Chrome MCP で Browser 2 (Windows) 接続、Graph API Explorer 起動成功、Meta App「YN Factory SNS Poster」選択済確認、Facebook ログイン済確認、ユーザートークン取得モード選択、許可を追加 dropdown を開いた → **発覚: 「Events Groups Pages」カテゴリしか無く、business_management と pages_show_list のみ選択可能。pages_manage_posts/instagram_*/threads_* が選択肢に無い**。Step 5 でユースケースを『追加』しただけで個別権限を Customize → Add していなかったことが原因。今日はここでハンドオフ。 (5) 次回再開ポイント: Meta Developer Console (https://developers.facebook.com/apps/1747727225992867/use_cases/) で『ページのすべてを管理』『Threads APIにアクセス』をそれぞれ Customize → 必要権限を Add → Graph API Explorer に戻ってトークン取得 → ファイル保存 → Step7 長期化。"
last_session_summary_v2026_05_05_sales_complete_keiba_retry: "【営業戦略 pivot 全工程実装完了 + JRA穴予想リトライ機構実装セッション】(1) 営業戦略 Week 2 残工程の並列実行: 工程3a(調査+設計、高品質完了) → 工程3b(87 PASS、gBizINFO+Google Maps実装、dryrun 143件採用) → 工程4a(高品質 PASS、ウェビナーLP+メール5種+Peatix設定) → 工程5a(高品質 PASS、Calendly手順書+メール6本) → 工程6(93 PASS、L1/L2/L3+補助金+契約書8ファイル) → 工程7(87 PASS、VPSパイプライン改修、{{double-brace}}対応) → 工程8a(完了、dryrun 25件取得+5件DM生成+本番チェックリスト)。要件定義書も最終更新で工程3/4/5/8 を全て a/b 分割（成果物=executor達成 / 実セットアップ=オーナー手動）。executor達成範囲は100%完了。(2) gBizINFO API 取得・本番化: オーナー手動でトークン発行(qw4nKtvN...FBtNi)→VPS .env 反映→疎通確認(長野県prefecture=20で200・3件取得)→工程3b/7 で動作確認したコードがprefecture_codeパラメータで400エラー判明→sed修正→prefecture パラメータで正常動作確認→工程8a で実APIから長野県20件+Google Maps 5件=25件取得成功。実API対応の追加修正: location抽出/公的機関フィルタ/start_page=5推奨/環境変数 GBIZINFO_START_PAGE/PAGES_PER_PREFECTURE/PREFECTURES 追加。(3) JRA予想 穴予想機能調査・改善: オーナー指摘「土曜は機能、日曜は機能なし」→ ログ分析で原因特定: 5/3(日) は morning.py で『オッズ取得 0/35 + 注目0レース + 穴予想0件』、live.py(直前予想 9:30-16:23)も『0レース選定 / 投資0円』。技術的不具合ゼロ、モデルの正常な防御挙動（pred_proba max=0.057 で全戦略候補ゼロ）。5/2(土) は『オッズ取得 35/35』だったため注目11件・穴予想3スレッド成功。差は朝7時時点でのJRA オッズ公開タイミング。改善実装: (a) 穴予想0件でも Telegram に「該当なし」通知（patch_no_pick.py 適用、x_poster.py の post_longshot_to_x 経由ではなく run_morning.py の else 節に直接追加）。(b) 朝9時リトライ機構 run_morning_retry.py 新規作成→cron に '0 9 * * 6,0' 追加→判定ロジック: オッズ0+注目0 → morning.py 再実行 / 既に注目あり → スキップ / オッズ取得済み・注目0 → モデル防御挙動を尊重しスキップ。テストで5/2(注目11件)→retry=False、5/3(オッズ0+注目0)→retry=True 確認済み。(4) SSH 設定改善: ~/.ssh/config を新規作成（Host 163.44.101.31 / IdentityFile ~/.ssh/conoha-vps / IdentitiesOnly yes / StrictHostKeyChecking no）。BatchMode=yes でもパスワード不要で通る状態確認。今後はSSH操作で「Git for Windowsパスワードプロンプト」が出ない。(5) 全工程進捗最終形（13サブ工程）: 工程1✅95 / 工程2✅88 / 工程3a✅高品質 / 工程3b✅87 / 工程4a✅高品質 / 工程4b⏳オーナー手動 / 工程5a✅高品質 / 工程5b⏳オーナー手動 / 工程6✅93 / 工程7✅87 / 工程8a✅完了 / 工程8b⏳オーナー手動 / 工程9✅91 / 工程10✅91。executor達成: 10サブ工程 PASS, オーナー手動: 3サブ工程(4b/5b/8b)。【次回最優先（オーナー手動）】(a) Peatix イベント作成・公開（工程4b、20分: 第1回ウェビナー 2026-06-17 19:00 を Peatix で公開）、(b) Calendly Event Type 作成 + Zoom 連携（工程5b、15分）、(c) Google Forms アンケート作成 + URL を post-webinar-followup.md に反映（10分）、(d) WEBINAR_URL/CONSULT_BOOKING_URL を VPS .env に実URL反映（5分）、(e) 朝のsales-briefing で approval_queue ID=270 を確認・承認 → 自分宛1件送信→受信確認→残り（工程8b）、(f) 必要ならテストデータ削除 (DELETE FROM companies WHERE id IN (232,233,234,235,236); DELETE FROM approval_queue WHERE id=270;)。【次回最優先（自動・運用）】(a) 5/9(土) 朝7:00 cron で morning.py + 9:00 run_morning_retry.py 動作確認（リトライが必要なら自動実行されるか）、(b) 穴予想0件通知が動作するか確認、(c) FX Saxo Sim トークン定期更新運用継続。【主な成果物】.company/outputs/sales-content/ 配下に webinar-platform/(8+1ファイル) + calendly-setup/(10ファイル) + offer-materials/(8ファイル) + webinar-v1-jinzai-busoku/(5ファイル：script+outline+slides.pptx+PDF2種) + individual-zoom-30min/(4ファイル) / .company/sales/templates/ai-advisor-dm/(4ファイル) / .company/sales/LAUNCH.md / .company/research/sales-source-legal-review.md / chamber-of-commerce-sources.md / list-builder-v2-design.md / list-builder-v2-progress.md / personalizer-v2-dryrun-result.md / step8-dryrun-result.md / step8-prelaunch-checklist.md / .company/engineering/docs/list-builder-v2-design.md / .company/requirements/sales-ops-pivot-ai-advisor/REQUIREMENTS.md(600行+8a/8b分割) / VPS /opt/sales-ops/migrations/{001_pivot_schema, 002_source_check_expansion}.sql / src/tracks/c_outbound/{gbizinfo_fetcher, list_builder_v2, employee_size_estimator, personalizer}.py / scripts/{run_list_builder, run_personalizer}.py / VPS /opt/keiba-unified/jra/scripts/run_morning_retry.py + run_morning.py(穴予想0件通知パッチ)。GitHub反映なし（VPS直接配置のみ）。【オーナーへの注意点】(a) gBizINFO は朝のオッズと違い API 経由なので時間帯を選ばず取得可能。(b) Calendly 無料プランは Event Type 1個のみだが個別Zoom 1本で十分。リマインダーは無料プランで1件のみなので24h前を優先（reminder-1h.md は予備）。(c) Peatix の自動メールは2件/イベントの制限ありなので前日リマインダー1件 + 1時間前リマインダー1件で運用。3日前リマインダーは追加メール送信機能が必要なら別途オーナー判断。(d) 工程8b の本番送信は「自分宛1件→受信確認→翌日残り4件→本番運用」の段階的推奨。スパム判定回避のため。(e) approval_queue ID=270 のテストDM内容は dryrun-result.md で確認可能、製造業v1テンプレ・1070字・特電法表記あり。(f) JRA cron は土日のみ稼働、平日は morning_retry.py も動かない（待機状態）。"
last_session_summary_v2026_05_04_sales_week2: "【営業戦略 pivot Week 2 並列実行・電源断ロスト・シャットダウン前ハンドオフ】(1) 5/2 セッションで工程1（DB整理）+工程2（DMテンプレ）+工程9 一部（script.md+outline.md）完成済み、5/4 朝セッションで Week 2 主要3工程（工程6・工程9残・工程10）を並列起動。(2) 工程6完了・QC 93/100 PASS: .company/outputs/sales-content/offer-materials/ 配下に8ファイル合計1516行作成 — plans/L1-light-advisor.md(159行,月4万) / L2-standard-advisor.md(192行,月8万) / L3-3month-implementation.md(211行,3ヶ月30万) / comparison-table.md(148行,3プラン比較表+フローチャート) / subsidy/subsidy-guide.md(209行,小規模事業者持続化補助金+IT導入補助金、免責文6項目) / subsidy-flyer.md(121行,1ページパンフ) / contracts/contract-L1-L2-monthly.md(216行,11条+別表AB) / contract-L3-project.md(260行,13条+別表AB,中途解約不可・着手金50%/完了金50%)。全契約書冒頭に「弁護士確認推奨」明記、税抜・税込両方併記、「2026年度時点」明記、過度なコミット表現排除。キャリコン差別化を全8ファイルに最低1箇所盛り込み。指摘: 保存先パス相違（要件は .company/sales/proposals/ai-advisor/ だが実装は outputs/sales-content/offer-materials/）、L2説明書のL3比較自己完結性弱、subsidy-guide のIT導入補助金部分の専門用語密度。(3) 工程10完了・QC 91/100 PASS: .company/outputs/sales-content/individual-zoom-30min/ 配下に4ファイル — script.md(197行,30分台本,スピーカーノート付,キャリコン差別化8箇所) / hearing-questions.md(36行,Q1-Q10+各狙い併記,Q4採用課題でキャリコン視点深掘り) / closing-flow.md(110行,A即決→契約書送付/B検討→Calendly+1週間後フォロー/C見送り→将来リタッチ) / slides.pptx(13枚321KB,紺×オレンジデザイン,1枚1メッセージ,キャリコン差別化5枚)。30分時間配分:0-5自己紹介/5-15ヒアリング/15-25プラン提示/25-30クロージング。指摘: 10分ヒアリングで10問タイト（実運用5-7問目安）、closing-flow.md と script.md の参照分離による台本単体完結度低、PPTX視覚確認がテキスト抽出のみで限界。(4) 工程9 残作業（slides.pptx 30-50枚 + handout-prompt-collection.pdf + handout-roadmap-worksheet.pdf）は **電源断で2回連続ロスト**。1回目は5/2 セッション中に未完成のまま中断、2回目は本日 5/4 並列起動した executor もまた電源断でロスト。outline.md(146行)とscript.md(967行,90分台本)は4/30セッションで完成済みで残存。次回再起動時には3回目チャレンジになる、PPTX/PDF生成は重いタスクのため anthropic-skills:pptx で30-60分、anthropic-skills:pdfで5-10分かかる見込み。途中保存指示は2回目のexecutor起動時に追加済みだが、それでもロスト。電源断対策が必要。(5) 全工程進捗まとめ — 工程1✅95/工程2✅88/工程3⏳未着手（リスト構築、Wantedly規約確認も含む）/工程4⏳未着手（ウェビナーLP）/工程5⏳未着手（Calendly）/工程6✅93/工程7⏳未着手（VPSパイプライン改修、{single} vs {{double}} 形式統一含む）/工程8⏳未着手（テスト5件）/工程9 部分完成（台本のみ、PPTX/PDF未）/工程10✅91。Week 1 と Week 2 の主要 9 工程中 5工程完成 + 1工程部分完成 = 約60%進捗。【次回最優先】(a) 工程9 残作業（slides.pptx + 持ち帰りPDF 2種）を3回目挑戦、今度は途中保存を強制（5-10分ごとにディスク書き出し）、または PPTX を 1スライドずつ append 方式で生成、(b) 工程3 リスト構築（先に migrations/002_source_check.sql でCHECK制約追加 → Wantedly/リクナビ規約確認）、(c) 工程6 軽微指摘の対応（保存先パス整合性、L2単体での自己完結性向上）、(d) 工程10 軽微指摘の対応（ヒアリング5-7問への絞り込み台本注記、closing-flow と script の統合検討）。【主な成果物】.company/outputs/sales-content/offer-materials/ 8ファイル / .company/outputs/sales-content/individual-zoom-30min/ 4ファイル / .company/outputs/sales-content/webinar-v1-jinzai-busoku/{outline.md, script.md} (PPTX/PDFは未完成)。【オーナーへの注意点】(a) 工程9 残作業は電源断耐性を上げるため、次回は executor に「2スライドごとにディスク保存しログ出力」「PDF は完成度95%でも一旦保存」を厳命する、(b) 並列実行中の電源断対策として、重い工程（PPTX/PDF生成）は単独実行が安全（並列だと負荷で電源系統に影響する可能性ゼロではない）、(c) yntools EPUBバリデーター実機動作確認（admin / dashboard / メガメニュー / vol1 EPUB アップロード）はまだ未実施。【別件の状況】Codex vol2-4 完了通知待ち（vol3/4 は新CSV+50字+outfit_id 反映済バンドル投入済）。FX Saxo Sim トークン定期更新運用継続。Meta SNS Step6 Graph API Explorer トークン取得継続。"
last_session_summary_v2026_05_02_keiba_x_recovery: "【JRA予想 X自動投稿障害復旧 + 通知強化セッション】(1) オーナーから「競馬予想のXへの自動投稿がされてない」指摘 → /opt/keiba-unified/jra/data/logs/morning.log 末尾で原因特定: 5/2 朝7時の自動実行で shared.x_poster の Gemini API 呼び出しが 403 Forbidden → 「Your project has been denied access. Please contact support」エラー → リライト失敗 → X投稿失敗（穴予想・モーニング両方）。Telegram送信と予想生成は正常完了、X投稿だけが Gemini リライト依存で全滅していた。(2) 原因深掘り: ListModels (緩い API) は HTTP 200 だが generateContent は 403。gemini-2.0-flash-lite では「API key expired. Please renew the API key」が出るなど混在 → アカウント全体が制限状態（過剰利用検知 or 不正利用判定）と判明。(3) オーナーが新Geminiキー発行を試行 → 1回目 AIzaSy...VqOOMY (旧キー、BAN)、2回目 AIzaSy...iWa3c (NG)、3回目 AIzaSy...AAfi4 (NG)、4回目 [REDACTED-gemini-key] で成功（おそらく別プロジェクトor別アカウント）。（同アカウント内では新規プロジェクト指定しても denied 継続のパターンを確認）。(4) VPS /opt/ai-news-system/.env の GEMINI_API_KEY を 4回目の新キーに更新（バックアップ: /opt/ai-news-system/.env.bak.20260502）→ 直接 curl で疎通200確認 → shared.x_poster._call_gemini() でリライト関数も成功（「朝から競馬日和」を返却）。(5) run_morning.py 手動再実行（nohup &）→ Monitor で進捗追跡 → モーニング X投稿成功、穴予想スレッド 3/3 全成功（tweet_id: 2050350299815325894 / 2050350344048386049 / 2050350388285751666）。完全復旧確認。(6) フォローアップ実装: x_poster.py に _notify_x_failure(label, reason) 関数を追加し、9箇所の失敗パスから呼び出し: モーニング/直前/穴予想 各3パス（リライト失敗・chunk空・例外）。Telegram 通知は環境変数 TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID 優先、なければ run_morning.py のハードコード値（TG_TOKEN=8718145068:AAGD..., TG_CHAT_ID=8571447808）をフォールバック。バックアップ: /opt/keiba-unified/shared/x_poster.py.bak.20260502。Python パッチスクリプト C:/Users/fcmdt/AppData/Local/Temp/patch_xposter.py 経由で 9/9 箇所適用、py_compile OK。動作テスト: 無効キー設定で post_morning_to_x() 呼び出し → リライト失敗 → 「Telegram配信完了」+「[notify] Telegram失敗通知送信: label=モーニング reason=Geminiリライト失敗（APIキー失効 or レート制限の可能性）」確認、オーナー Telegram に通知到達確認済み。(7) 今後の障害検知フロー: もし再BAN/レート制限/その他障害が起きても、cron 実行時点で即 Telegram に「⚠️ X投稿失敗 / 種別: ... / 時刻: ... / 理由: ... / → /opt/ai-news-system/.env の GEMINI_API_KEY や API レート制限を確認してください」が届く → オーナーは X を開かずに即検知可能。【次回最優先（営業）】(a) 営業戦略 pivot Week 1 残作業: 工程9 残（ウェビナーPPTX 30-50枚 + 持ち帰りPDF 2種、script.md と outline.md は完成済み）/ 工程3 リスト構築（先に migrations/002_source_check.sql でCHECK制約拡張 → Wantedly規約確認）/ 工程6 L1/L2/L3+補助金資料+契約書 / 工程10 個別Zoomコンテンツ。(b) yntools EPUBバリデーター動作確認（admin で 402 出ない / dashboard カード表示 / メガメニュー / vol1 EPUB 197MB アップロード→score確認）。(c) Codex vol2-4 完了通知待ち（vol3/4 は新CSV+50字+outfit_id 反映済バンドル投入済）→ done受取→ EPUB(Step7)→ KDPメタ(Step8)。(d) FX Saxo Sim トークン定期更新運用継続。(e) Meta SNS Step6 Graph API Explorer トークン取得。【主な成果物】/opt/keiba-unified/shared/x_poster.py（466→526行+ _notify_x_failure 関数 + 9箇所呼び出し追加） / /opt/keiba-unified/shared/x_poster.py.bak.20260502 / /opt/ai-news-system/.env（GEMINI_API_KEY 新キー） / /opt/ai-news-system/.env.bak.20260502 / C:/Users/fcmdt/AppData/Local/Temp/patch_xposter.py（再現可能なパッチスクリプト）。【オーナーへの注意点】(a) 旧Geminiキー3つはBAN/expired状態のため使い回し不可。新キー(AIzaSyDh3...wt2rE)もまた同様にBANされる可能性ゼロではないため、Telegram通知が来たら同手順（ListModels で稼働確認 → 別プロジェクトで再発行 → /opt/ai-news-system/.env 更新）で対処。(b) Gemini → OpenAI API 移行（恒久対応案）は未実装、必要なら別タスクで提案可能（コスト試算: gpt-4o-mini で1リライト約 $0.0001、月数十円程度）。(c) JRA予想 cron は土日のみ稼働（07:00 morning / 09:30 live / 17:30 results）、ばんえい cron は毎日13時台。明日（5/3 日曜）07:00 の自動実行で動作再確認できる。"
last_session_summary_v2026_04_30_sales_pivot_start: "【営業戦略 pivot Week 1 着手セッション・中断】(1) 4/29 にリリースした yntools EPUBバリデーター（37番目ツール、500MB対応）の動作確認は次回オーナーが実機検証する宿題として残置。(2) 営業戦略の大転換決定: 旧Sales OS（軸C 法人アウトバウンド、yn-tools 月2,000円ツール販売、ターゲット=士業・コンサル/首都圏）を全面 pivot → 新方針「AI活用アドバイザー positioning」「地方の非首都圏（東京・大阪・名古屋・福岡 以外）」「従業員30-100名」「全業種OK（除外: AI/IT系・フランチャイズ大手）」「無料ウェビナー → 無料個別Zoom 30分1回 → L1月4万/L2月8万/L3 3ヶ月30万 の3階建てオファー」「補助金提案あり（小規模事業者持続化・IT導入補助金、申請保証なし免責込み）」「キャリアコンサルタント国家資格を最大の差別化要素に活用（AI×HR、人を活かす視点）」。(3) 既存 pending DM 212件 + rejected 50件 = 計262件は全件 rejected_archive 化（首都圏99% & DMが yn-tools 訴求 & 規模情報 None で新方針と完全不適合）。(4) 要件定義書 .company/requirements/sales-ops-pivot-ai-advisor/REQUIREMENTS.md (430行) 作成完了。10工程構成: 工程1=DB整理+212件却下 / 工程2=新DMテンプレ3バリエーション / 工程3=新リスト構築（a3 Wantedly + a4 商工会議所 + a5 maps改良）/ 工程4=ウェビナーLP+申込フォーム+自動メール / 工程5=Calendly個別Zoom予約 / 工程6=L1/L2/L3説明書+補助金資料+契約書 / 工程7=VPSパイプライン改修 / 工程8=テスト5件→本番運用 / 工程9=ウェビナーコンテンツ完成版（台本+PPTX 30-50枚+持ち帰りPDF）/ 工程10=個別Zoomコンテンツ完成版（30分台本+PPTX 10-15枚+補助金パンフ）。KGI再評価: 旧目標「6/30 MRR 20万円」を「6/30 初契約1件（MRR 4-10万円）」に修正、20万円は9月へ後ろ倒し。(5) 工程1完了 95/100: VPS 163.44.101.31:/opt/sales-ops/ で DBバックアップ→approval_queue 262件 rejected_archive 化→companies に prefecture/is_metro/size_employees_estimated 3カラム追加→approval_queue に positioning(DEFAULT 'yn_tools')/funnel_stage 2カラム追加→既存214社全件 prefecture自動判定（東京73/大阪73/愛知68=全件 metro=1）→migrations/001_pivot_schema.sql + rollback + run_migration_v2.py 作成→sent 1件保持確認。指摘事項: companies.source CHECK制約に 'wantedly' 'chamber_of_commerce' 未追加 → 工程3着手時に migrations/002_source_check.sql で対応必要。(6) 工程2完了 88/100（要件定義書側を実装に整合させて PASS）: .company/sales/templates/ai-advisor-dm/ 配下に dm_v1_human_resource.md(950字, 製造/建設/運輸/飲食宿泊向け) + dm_v2_career_growth.md(970字, 教育/医療/介護/士業向け、キャリコン最大活用3箇所) + dm_v3_management_decision.md(1010字, 小売/サービス/汎用) + template_design.md(配信ロジック+A/Bテスト指針)。各5案ずつ計15案の件名、特電法表記全件含む、{{double-brace}}+新変数群（{{webinar_url}} 等）。当初 QC 71点 FAIL（要件書500-800字 vs 実装950-1010字、ファイルパス相違）→ オーナー指示で要件書側を更新（800-1200字、新パス、変数仕様）し PASS 扱い。技術的注意: 既存 personalizer.py は {single-brace} 形式 + {company_name}/{industry}/{personalization_hint} の3変数のみ → 工程7 改修で対応必要。(7) 工程9 一部完了で中断: .company/outputs/sales-content/webinar-v1-jinzai-busoku/ に script.md と outline.md は生成済み（90分ウェビナー台本想定、テーマ「人手不足に悩む地方中小企業のための、今すぐ使えるAI活用5選」）が、slides.pptx と handout-prompt-collection.pdf / handout-roadmap-worksheet.pdf は未生成。タスクは TaskStop で停止しようとしたが既に終了済みでID found nothing（バックグラウンドで自然完了 or 途中中断のいずれか）。(8) 中断時点の宣言済み次回最優先: (a) 工程9 残作業（PPTX 30-50枚 + 持ち帰り資料2種PDF）を再起動 or 新規 executor に依頼、(b) 工程3 リスト構築（先に 002_source_check.sql マイグレ実施 → Wantedly/商工会議所スクレイピング法的確認 → 実装）、(c) 工程6 L1/L2/L3 + 補助金資料 + 契約書、(d) 工程10 個別Zoom コンテンツ。Week 2 で並列着手予定。【次回最優先（営業以外）】(a) yntools EPUBバリデーター動作確認（admin で 402 出ない / dashboard カード表示 / メガメニュー / vol1 EPUB 197MB アップロード→score 確認）。(b) Codex 完了通知待ち（vol2 part4b 進行中、vol3/4 は新CSV+50字+outfit_id 反映済バンドル投入済で着手待ち）→done受取→EPUB(Step7)→KDPメタ(Step8)。(c) FX Saxo Sim トークン定期更新運用継続。(d) Meta SNS Step6 Graph API Explorer トークン取得。【主な成果物（営業）】.company/requirements/sales-ops-pivot-ai-advisor/REQUIREMENTS.md(430行) / .company/sales/templates/ai-advisor-dm/(4ファイル) / .company/outputs/sales-content/webinar-v1-jinzai-busoku/{script.md,outline.md} / VPS /opt/sales-ops/migrations/{001_pivot_schema.sql, _rollback.sql, run_migration_v2.py} / VPS /opt/sales-ops/data/sales_ops_backup_20260430.db。【オーナーへの注意点】(a) 既存 personalizer.py の {single-brace} と新DMテンプレの {{double-brace}} の不整合は工程7 で吸収予定（DMテンプレを {single} に書き戻す or personalizer 側を Jinja に拡張）。(b) ウェビナーCTA URL `https://ynfactory.online/webinar` と個別Zoom予約 `https://ynfactory.online/consult` は仮プレースホルダー、工程4-5 で実URL化。(c) DMテンプレに含めた変数 {{contact_name}} {{size_employees}} {{location_prefecture}} {{webinar_url}} は personalizer 側で生成ロジック追加が必要（工程7）。(d) Wantedly/リクナビ スクレイピング規約は工程3 着手前に必ず法的確認、違反なら a4(商工会議所) + a5(google_maps改良) に切替。(e) キャリコン差別化を全工程で一貫させる（DM・ウェビナー・個別Zoom・契約書まで）。"
last_session_summary_v2026_04_30_yntools_epubcheck: "【yntools EPUBバリデーター 5工程実装+本番リリースセッション】(1) yntools にKDP出版前チェック用ツールを新規追加。確定方針: バリデーションLevel 2（基本+KDP特化）/ ファイルサイズ上限200MB→途中で500MB拡張 / 結果保存しない（メモリのみ）/ MVP優先（Level3 epubcheck.jar は次フェーズ）/ 課金ユーザー向け 100円/月 + all_tools 2000円に含める。要件定義書 .company/requirements/yntools-epub-validator/REQUIREMENTS.md (588行) 作成。(2) 工程1完了 97/100: yn-tools/app/tools/epubcheck/validator.py 新規作成。zipfile + lxml 標準ライブラリのみで完結。Level 1 基本10項目（zip/mimetype/container/opf valid/メタデータ4種/href切れ/NAV-NCX）+ Level 2 KDP特化7項目（cover有無/coverサイズ Pillowフォールバック/固定レイアウト/フォント埋め込み/サイズ警告/画像枚数/文字数概算）合計17項目を実装。セキュリティ対策3種（ZIPエントリ10000上限/パストラバーサル検出/展開後5GB上限）。validate_epub(file_bytes: bytes) -> dict の純粋関数設計。vol1 EPUB 197MB で実測 pass=15/warn=2/fail=0/score=94.1。(3) 工程2完了 96/100: yn-tools/app/tools/epubcheck/router.py 新規（GET /tools/epubcheck/ + POST /tools/epubcheck/api/validate）。両エンドポイント require_tool_access(\"epubcheck\") 保護。Content-Length 事前+読込後の二重サイズチェック、finally で del file_bytes 明示解放、ディスク書込みなし。templates/tools/epubcheck/index.html UI 新規（ドラッグ&ドロップ・PASS/WARN/FAIL色分け・メタデータカード・スコアバー・レスポンシブ）。(4) 工程3完了 93/100: stripe_product_ids.json と stripe_live_product_ids.json に epubcheck エントリ追加（当初プレースホルダー）、main.py に from app.tools.epubcheck.router import router as epubcheck_router + app.include_router 追加 + ToolDefinition シード追加（slug=epubcheck/display_order=37/icon=📚/100円月額）。(5) 工程4完了 90/100: dashboard.html ツールカード+icons SVG追加（全36→37ツール表記更新）/ landing.html「コンテンツ制作」セクションにカード追加+ヒーロー文も37に / base.html メガメニュー「画像・ファイル」列とモバイルメニュー両方にリンク追加 / guide.html に #tool-epubcheck セクション追加（既存ハッシュ方式に統一、Level1/Level2チェック表+使い方4ステップ+FAQ4問+使用例 vol1実績）。(6) 工程5完了: 過去の create_stripe_products_5tools.py パターンを参考に scripts/create_stripe_product_epubcheck.py を新規作成（API key の sk_test_/sk_live_ プレフィックスから自動でモード判定+保存先JSON切替+冪等チェック）。ローカルで sk_test 実行→prod_UQQ4B0EDbgzpCl / price_1TRZEhKAVaivWwqwoiUavxgj 取得+JSON保存。VPS では docker cp で script を container に投入→docker compose exec で sk_live 実行→prod_UQQ6dAhplgZn31 / price_1TRZG2KAVaivWwqw3aVVjJSd 取得→ docker cp で /opt/yn-tools/stripe_live_product_ids.json に戻し。main.py プレースホルダーも実IDに置換。git push (commit 8bc187a) → VPS git pull → 競合発生（VPS側 docker cp で json更新済みだったため）→ git stash で回避→ pull→ docker compose up -d --build →コンテナ再起動→ ToolDefinition.epubcheck 自動シード確認（log: \"Seeded 1 tool definitions: ['epubcheck']\"）→ HTTP 401 で route 存在確認。(7) 追加対応: 200MB→500MB 拡張要望→ validator.py file_size_warning 閾値変更 / router.py MAX_FILE_SIZE変更 / index.html 表示+JS変更 / nginx /etc/nginx/sites-enabled/yn-tools の HTTPSサーバとHTTP→HTTPSリダイレクトサーバ両方に client_max_body_size 600M 追加（500MBアップロードのヘッダ余裕確保）+ nginx -t→ systemctl reload nginx → docker compose up -d --build (commit 11fb2a2)。(8) 重要: 本番デプロイ前のオーナー作業（Stripe ダッシュボード手動登録）はスクリプト自動化で完全省略可能になった→ 今後の新ツール追加では create_stripe_product_<slug>.py を流用するのが標準パターン。【次回最優先】(a) 動作確認継続（vol2/3/4 の200MB超 EPUB を実機でアップロードして score 確認、メガメニュー/landing/dashboard 全画面でカード表示確認、admin で 402 出ないこと、一般ユーザーで 402 が出て購読導線が動くこと）。(b) Codex 完了通知待ち（vol2 part4b 進行中、vol3/4 は新CSV+50字+outfit_id 反映済バンドル投入済で着手待ち）→ done受取→ EPUB(Step7)→ KDPメタ(Step8)。(c) FX Saxo Sim トークン定期更新運用継続。(d) note記事 #1 が4/29 08:00 予約投稿された確認。(e) Meta SNS Step6 Graph API Explorer トークン取得（継続）。【主な成果物】yn-tools/app/tools/epubcheck/{__init__.py,router.py,validator.py} / yn-tools/app/templates/tools/epubcheck/index.html / yn-tools/scripts/create_stripe_product_epubcheck.py / yn-tools/{stripe_product_ids,stripe_live_product_ids}.json (epubcheck 実ID追加) / yn-tools/app/main.py (router登録+ToolDefinitionシード) / yn-tools/app/templates/{base.html,dashboard.html,landing.html,guide.html} (ナビ4箇所追加) / .company/requirements/yntools-epub-validator/REQUIREMENTS.md (588行) / VPS /etc/nginx/sites-enabled/yn-tools (client_max_body_size 600M)。GitHub: 8bc187a→11fb2a2。本番: https://tools.ynfactory.online/tools/epubcheck/ で稼働中。【オーナーへの注意点】(a) admin (yuichi4107@gmail.com) は is_admin=True で課金バイパス、一般ユーザーは 100円/月 で個別購読 or 2000円月額の all_tools プランで利用可。(b) 一般ユーザーが /tools/epubcheck/ にアクセスして 402 を受けたとき購読導線が表示される（既存ツールと同じパターンが流用される）が、未動作確認。(c) アップロードされた EPUB はメモリ内で処理→ del で即解放、ディスク書込みなし。同時アップロード複数で発生する潜在的メモリ枯渇は MVP 段階では許容（要件定義書のリスク欄に記載）。"
last_session_summary_v2026_04_29_yntools_admin: "【yntools 管理者アカウント機能 4工程実装+本番デプロイセッション】(1) yntools (FastAPI/ConoHa VPS 163.44.101.31:/opt/yn-tools/, postgres:15-alpine) に「フリーで全ツール使える管理者アカウント」を追加。確定方針: ユースケース=オーナー用 / 権限=フル管理者(全ツール+他ユーザー管理) / 実装=既存 User.is_admin フラグ活用 / アカウント=yuichi4107@gmail.com (個人Gmail、info@ynfactory.online のWorkspace化はコスト過剰のため不採用、CTA公開メアドは引き続き info@ で運用)。要件定義書 .company/requirements/yntools-admin-account/REQUIREMENTS.md (345行) 作成。(2) 工程1完了 95/100: yn-tools/app/users/models.py の has_active_plan / has_full_access プロパティ先頭に if self.is_admin: return True を追加（2行追加+docstring1行更新）。is_in_trial 等の他プロパティは無変更。require_tool_access は has_full_access 経由で自動透過。(3) 工程2完了 97/100: yn-tools/app/admin/router.py 新規作成（6エンドポイント: GET /admin / GET /admin/users / GET /admin/users/{id} / POST /admin/users/{id}/update / POST /admin/users/{id}/logout / GET /admin/billing、全て require_admin 依存）。テンプレート4本新規 (admin/index.html / users.html / user_detail.html / billing.html、すべて base.html 継承)。app/main.py に admin_router include 追加。app/templates/base.html の PCドロップダウン+モバイルメニューに {% if user and user.is_admin %} 限定で「🛡️ 管理者ダッシュボード」リンク追加。重要: app/auth/dependencies.py の get_current_user に「if user and not user.is_active: return None」チェックを追加（強制ログアウト=is_active=False 化を実現するため）。billing 集計は status='succeeded' のみ。(4) 工程3完了 88/100: yn-tools/scripts/promote_admin.py 新規作成。位置引数 email + --demote/--list オプション。冪等（既に admin なら exit 0）、未登録時は明確エラー+exit 1。app.database の async_session を直接インポートする非同期パターン採用。--list で全管理者一覧表示。指摘事項: DATABASE_URL 未設定時の警告がない・docstring に依存関係未記載（実害なし）。(5) 工程4完了: VPS 本番デプロイ実施。git push (commit 4ef95c9) → ssh root@163.44.101.31 で /opt/yn-tools/ git pull → docker compose up -d --build → 84.9s で再ビルド完了 → HTTPS 200 確認。yuichi4107@gmail.com は既に過去登録済み（id=1, plan=per_tool）。docker compose exec app python scripts/promote_admin.py yuichi4107@gmail.com で is_admin: False→True 昇格成功。--list で1名確認。Stripe 状態調査: stripe_customer_id=None / stripe_subscription_id=None で実体なし、UserToolSubscription 2件(sales/gems active) は stripe_subscription_item_id=None のテストデータ的残骸。「お金は実は払っていない」状態。/account/cancel が反応しない原因はこれ（stripe_subscription_id=None で即リダイレクト=仕様通り）。クリーンアップとしてオーナー判断β採用→ DBで User.plan を per_tool→free に更新（docker compose exec app python -c で直接更新）。最終状態: id=1 / yuichi4107@gmail.com / plan=free / is_admin=True / is_active=True / has_full_access=True (admin bypass)。(6) git 関連の罠: yn-tools サブモジュールが index 大量deletion状態（Drive同期由来のindex壊れ）→ git reset HEAD で復旧→ 今回の admin 関連10ファイル(+799行)のみ commit/push。【次回最優先】(a) 動作確認継続（admin で全ツール 402 出ないこと、/admin が 200、一般ユーザーが /admin で 403）。実機未確認の項目は: 別アカウントで /admin にアクセスしたとき 403 返るか、/admin/users/{id}/update でフォーム保存→DB反映、強制ログアウト動作。(b) Codex 完了通知待ち（vol2 part4b 進行中、vol3/4 は新CSV+50字+outfit_id 反映済バンドル投入済で着手待ち）→ done受取→ EPUB(Step7)→ KDPメタ(Step8)。(c) FX Saxo Sim トークン 4/29 15:32 JST 失効 → bash scripts/update_saxo_token.sh <NEW_TOKEN> で更新運用継続。(d) note記事 #1 が4/29 08:00 予約投稿された確認。(e) Meta SNS Step6 Graph API Explorer トークン取得（継続）。【主な成果物】yn-tools/app/admin/router.py (234行) / yn-tools/app/templates/admin/{index,users,user_detail,billing}.html (合計418行) / yn-tools/scripts/promote_admin.py (123行) / yn-tools/app/users/models.py (is_admin バイパス2箇所追加) / yn-tools/app/auth/dependencies.py (is_active チェック追加) / yn-tools/app/main.py (admin_router 登録) / yn-tools/app/templates/base.html (admin リンク2箇所追加) / .company/requirements/yntools-admin-account/REQUIREMENTS.md (345行)。GitHub: yuichi4107-lab/yn-tools main ブランチ commit 4ef95c9。本番: https://tools.ynfactory.online で稼働中。【オーナーへの注意点】(a) admin の plan を free にしたが、UserToolSubscription 2件 (sales/gems) は active 状態で残存（管理者バイパスで実害なし）。(b) /account/cancel は stripe_subscription_id=None なら即リダイレクトする仕様（バグではない）、本物の Stripe 課金がある場合のみ動作する。(c) admin ダッシュボードでの plan 手動編集は Stripe Webhook により上書きされるリスクあり、緊急対応用途のみで使用すること（テンプレート内で警告文表示済み）。"
last_session_summary_v2026_04_29_vol34_redesign: "【vol3/vol4 CSV再構築 + skill恒久更新セッション】(1) vol1 はオーナー判断で残7枚（縦長不揃い page_002/006/007/008/010/011/013）の差し替えなしでそのまま出版完了。(2) ebook-to-manga スキルから KDP出版用メタ生成と表紙制作だけを切り出した独立ポータブルスキル `.claude/skills/kdp-cover-and-metadata/` 作成（SKILL.md + scripts/generate_cover.py + templates/書籍情報.md・ジャンル・キーワード.md・書籍紹介文_HTML.html）。OPENAI_API_KEY 環境変数 + pip install openai だけで他PCでも動作。(3) vol3/vol4 の CSV 再構築を5工程で実行（要件定義書 .company/requirements/ebook-to-manga-vol34-50char-outfit/REQUIREMENTS.md 443行）。確定方針: 1コマ50字目安(soft limit、超過率10%未満が望ましい) / 目標ページ数任せ / vol2はこのまま完走 / 旧バンドル上書き / skill本体も恒久書き換え / 服装はCSV+outfit_presets方式 / Claudeが原稿スキャン→オーナー確認→採用 / 季節感無視。(4) 工程0完了 90/100: skill.md に「1コマあたりの文字数目安（50字 soft limit）」独立ブロック追加(576-584行)、Step 3-1b「場面別服装ルールの定義（outfit_id 参照方式）」追加(309-347行)、CSV 4列→5列に拡張（ヘッダー・列説明・確認項目）、コマ別テキストJSON text フィールドにも50字注記。(5) 工程1完了: vol3/vol4 シナリオから outfit_presets 案抽出→オーナー判断（A残B残C残D追=ミサキ3個・タクヤ2個・ケンタ2個・山田課長 yamada_suit 新規追加=合計8プリセット）→ character_defs.json 反映済（outfit_presets キー追加41行、バックアップ character_defs_pre_outfit_presets.json 作成）。(6) 工程2完了 88/100: vol3 CSV 200→136ページ（32%削減）、コマ数296、50字超過率0.34%(1/296)、5列フォーマット、テキストページ7+登場人物紹介(P3)、outfit_id分布: misaki_casual多用+misaki_work_home+takuya_zoom_mentor+kenta系。P3のoutfit_id空欄をmisaki_casualに事後修正済。テンプレ偏り(T1=2.9%/T5-7=61.8%)が改善余地。(7) 工程3完了 89/100: vol4 CSV 122→80ページ（34%削減）、コマ数171、50字超過率0%、テキストページ9（前付2+コラム⑧×2+コラム⑨+コラム⑩×2+著者紹介+奥付）、outfit_id分布: misaki_casual(37)+misaki_work_home(20)+takuya_zoom_mentor(7)+kenta_work_casual(5)+misaki_formal(2)。takuya_casual/kenta_casual/yamada_suit は vol4 内に該当シーンなしのため未使用（許容）。(8) 工程4完了 93/100: queue/manga-career-restart_vol3_20260426_150500/ と vol4_20260426_150600/ それぞれの csv/comicle_output.csv を新版に上書き、manifest.json 再生成（vol3=137 items: cover1+manga129+text7、vol4=81 items: cover1+manga71+text9、json valid）、TASK.md 更新（更新履歴・5列CSV構成・outfit_id 説明セクション追記）、character_defs.json (outfit_presets入り) を vol3/vol4 の characters/ に新規配置、vol2 未干渉確認済（最終更新Apr 28まで）。バックアップ命名は混同防止のため queue 由来は `comicle_output_queue_pre_50char_redesign.csv`、原本由来は `comicle_output_pre_50char_redesign.csv` に分離保存。(9) コスト効果: 322→216ページで約$20削減見込み。【次回最優先】(a) オーナーが Codex CLI で vol3/vol4 並列起動（cd .company/codex/queue/manga-career-restart_vol{3,4}_*/ && python gen_manga_bundle.py）→ done/受取→ vol3/vol4 pages/ に配置→ EPUB(Step7)→ KDPメタ(Step8)。(b) gen_manga_bundle.py が outfit_id 列を読んで character_defs.json の outfit_presets を展開する処理が未対応の場合、TASK.md の注記に従って Codex 側改修 or プロンプト本文に直接 description を埋め込む方針へ切替。(c) FX Saxo Sim トークン 4/29 15:32 JST 失効 → bash scripts/update_saxo_token.sh <NEW_TOKEN> で更新運用継続（中期はOAuth refresh自動化）。(d) note記事 #1 が4/29 08:00 予約投稿されたか検証（プロフィールトップ非表示+予約タブ確認）。(e) Meta SNS Step6 Graph API Explorer トークン取得（継続）。【主な成果物】.claude/skills/ebook-to-manga/skill.md（50字+outfit_id 反映、2320行） / .claude/skills/kdp-cover-and-metadata/（新規スキル一式） / .company/requirements/ebook-to-manga-vol34-50char-outfit/（REQUIREMENTS.md+OUTFIT-PRESETS-PROPOSAL.md+QC各ループ記録） / vol3/panels/comicle_output.csv（136P）+ vol4/panels/comicle_output.csv（80P）+ それぞれのバックアップ2系統 / queue/manga-career-restart_vol{3,4}_*/csv/+manifest.json+TASK.md+characters/character_defs.json / manuscript/character_defs.json（outfit_presets 8個追加、49行）。【オーナーへの注意点】vol2 のCSVは旧30字制限・4列のまま（Codex生成中のため変更禁止）。シリーズ内で vol2(4列) と vol3/vol4(5列) でフォーマットが異なるが、画像生成品質（読みやすさ）は向上するためオーナー了承済み。"
last_session_summary_v2026_04_28_evening: "【vol1 KDP申請完了 + note再委託 + FX運用回復セッション】(1) vol1 KDP申請オーナー実施完了→DASHBOARD更新（manga-career-restart vol1 審査待ち）。vol2-4 はすべて Codex 側で生成中に変更。(2) GenSpark Claw 完了通知5件確認→全件「原稿コンテンツが見つかりませんでした」エラーで未公開判明（昨日4/27の#1も期日経過）。原因はローカルファイルパス参照（docs/note/...md）でブラウザベースのGenSpark Clawが読めなかったこと。done/5件をarchive/へ移動、queue/に再委託指示書5本を新規生成（原稿全文を本文に直接埋め込み + 画像はGoogle Drive共有フォルダURL方式 + 【画像位置N: filename.png】マーカーで挿入位置明示）。投稿日を1スロット後ろにシフト（#1=4/29水, #2=5/1金, #3=5/4月, #4=5/6水, #5=5/8金、月水金パターン）。genspark/CLAUDE.md に「ローカルファイル参照禁止」ルール永続化（再発防止チェックリスト付き）。(3) Sales OS pending DM 207件（HANDOFFの50件から積上）確認→今日はskip判断、送信トリガー叩かず。(4) AI投資ショート Phase2 工程7（本番最小額検証）の前提となる Binance Futures Testnet API Key が未発行のため引き続きブロック → スキップ。(5) FX Phase1 フォワードテスト確認→Saxo Sim トークンが2026-04-17更新後に未更新で10日間401失効状態と判明（毎時のスキャンが全FLAT @ N/A、実データ蓄積ゼロ）。新トークン受領→ scripts/update_saxo_token.sh を新規作成（VPSの.env更新+docker compose up -d --force-recreate ai-trade-forward+ログから401/200判定）→ .claude/settings.json の permissions.allow に Bash(bash scripts/update_saxo_token.sh:*) 恒久allow追加→初回実行で SAXO_TOKEN→SAXO_SIM_TOKEN 修正→ /balances/me で HTTP 200 OK 確認、フォワードテスト復活。【次回最優先】(a) FX Saxo Sim トークン明日 2026-04-29 15:32 JST失効、毎日 bash scripts/update_saxo_token.sh <NEW_TOKEN> で更新運用継続。中期的にOAuth refresh_token自動更新フローを実装（HANDOFF TODO残）。(b) note記事 #1 が4/29 08:00 に予約投稿されているか検証（プロフィールトップ非表示+予約タブ確認）。(c) GenSpark Clawが yuichi4107@gmail.com でログインしていることが前提条件（オーナー確認済）。(d) vol2-4 Codex 生成完了通知待ち。【新規スクリプト/設定】scripts/update_saxo_token.sh / .claude/settings.json (permissions.allow) / .company/genspark/queue/ に5本の指示書 / .company/genspark/CLAUDE.md にローカル禁止ルール追加。"
last_session_summary_v2026_04_28_vol1_final: "【vol1 EPUB 確定 + Step 8 KDPメタデータ完了セッション】(1) テキストページの表示行数オーバー問題を修正→ visual_lines() で h2/h3/p/subtitle 別に折り返し行数を推定し、20行バジェットで貪欲パッキング+heading orphan回避する `C:\\tmp\\repaginate_vol1.py` を作成。元9 text pages → 16 text pages に分割（033:2→3 / 053:2→5 / 082:2→4 / 084:1→2、全ページ最大19.6行以内）→ manga-career-restart-vol1-manga_text1_5x_v2.epub（196.5MB）。(2) 著者紹介(page_083) と 奥付(page_084) の間に CTA固定ページ追加→ ChatGPT Image 2026年4月28日 03_06_04.png（1024×1536 RGB）を spine ID `page_cta` で挿入→ manga-career-restart-vol1-manga_text1_5x_v3.epub（197.9MB / 96 spine items）→ オーナー確認で **確定**。(3) CTA画像をスキル恒久アセット化: `.claude/skills/ebook-to-manga/assets/cta.png`（1.5MB）。skill.md に「後付けページ（必須）」セクション追加（著者紹介→CTA→奥付の順序を必須化）+ Step 7 にテキストページ20行改ページルール（実装例: repaginate_vol1.py参照）+ CTA固定ページ挿入コード追加。次回以降 vol2-4 や他書籍でも自動適用。(4) Step 8 KDPメタデータ更新: 書籍情報.md（タイトル「マンガでわかる」プレフィックス付与・サブタイトル【マンガ版】追加・全96ページ形式情報・主人公「美咲（ミサキ）」明記）/ ジャンル・キーワード.md（7枠×3ワード=21ワードに再構築・マンガ固有語 マンガでわかる/マンガ/漫画/コミック/図解 を5枠に分散・各枠の検索意図マトリクス追加）/ 書籍紹介文_HTML.html（ヒロイン名 ひなた→ミサキ修正・第1〜3話あらすじを実EPUB準拠に書き直し・フルカラー78p/コラム3本/キャリアコンサルタント監修等のマンガ版アピール追加）。(5) 確定版以外のEPUB 8本削除（合計 726.3 MB 解放）→ KDP出版用/ には manga-career-restart-vol1-manga_text1_5x_v3.epub のみ残置。【次回最優先】(a) vol1 を Kindle Previewer で最終チェック後 KDP申請（EPUB+表紙PNG+書籍情報+ジャンル・キーワード+書籍紹介文HTML 揃い）。(b) vol2 manual_ready の画像生成（ChatGPT Plus 手動176本生成→manual/import/に保存→--import-manual）→ 同じスキル設定（20行改ページ+CTA固定）で自動EPUBビルド→ Step 8 メタデータ生成。(c) vol3/4 の Codex 完了待ち。(d) 残 7枚（縦長不揃い page_002/006/007/008/010/011/013）の差し替え判断は実機確認後。【主な成果物】vol1/KDP出版用/manga-career-restart-vol1-manga_text1_5x_v3.epub / 書籍情報.md / ジャンル・キーワード.md / 書籍紹介文_HTML.html / .claude/skills/ebook-to-manga/assets/cta.png / .claude/skills/ebook-to-manga/skill.md（後付けページ + 20行改ページ + CTA固定挿入の3点を恒久追記） / C:\\tmp\\repaginate_vol1.py。【オーナーへの注意点】vol2-4 のEPUB生成では『テキストページ20行max + CTA固定挿入』が自動適用されるため、これらに反した独自実装は避ける。CTAデザイン変更は assets/cta.png を上書きするだけで全巻に反映される。"
last_session_summary_v2026_04_27_textfont: "【vol1 EPUB テキストページ仕上げ + ebook-to-manga skill 更新セッション】(1) manga-career-restart vs -validation の違いを説明（前者=本番120P制作中、後者=4/23の5Pパイプライン検証）。(2) manga-career-restart-vol1-manga.epub のテキストページ（目次/コラム/著者紹介/奥付）が小さすぎる問題→ style.css のフォントサイズを最初2倍化、収まりが悪く1.5倍に再調整（text-page 28→42px / h2 36→54 / h3 30→45 / subtitle 22→33 / colophon 30→45 / colophon h2 36→54）。(3) 49・50ページを 1.png/2.png（時給800円→1200円・月6万→7.2万円に修正版）に差し替え。(4) フォントが中華フォールバックする問題→ Noto Sans JP Regular/Bold (.otf 約9MB) を OEBPS/fonts/ に埋め込み、@font-face 追加、font-family 先頭に Noto Sans JP 指定、content.opf manifest にフォント登録、ZIP_STORED 格納で再パッケージ。最終 EPUB: KDP出版用/manga-career-restart-vol1-manga_text1_5x.epub 約197MB。元 manga-career-restart-vol1-manga.epub は保持。(5) .claude/skills/ebook-to-manga/skill.md Step 7 を恒久更新: フォント自動DLキャッシュ機構（~/.cache/noto-sans-jp/）+ style_css に @font-face とテキストページCSS(1.5倍標準) + content.opf manifest にフォント2点追加 + EPUB書き出し時に ZIP_STORED でフォント格納。次回以降 vol2-4 や他書籍でも自動でNoto Sans JP埋め込み + 1.5倍テキストページが適用される。(6) 作業ディレクトリ vol1/_epub_resize/ は残置（gitignore外）。"
last_session_summary_v2026_04_27_vol1epub: "【ebook-to-manga vol1 EPUB完成セッション（codex 完了→Step5-C→Step7）】(1) Codex CLI で manga-career-restart_vol1_prod_20260425_201900 完了通知受領、done/<job>/ から 78画像 + cover.png 受け取り。Codex は gen_manga_bundle.py を実行せず ChatGPT 内蔵画像生成で出力（generation_mode: chatgpt_plus_image_generation_manual_codex / OPENAI_API_KEY 不使用 / API課金 $0）。表紙の著者名は当初 manifest 指示「中田 雄一」を Codex が独自判断で「Yuichi」に改変→オーナー判断『Yuichi が正、vol2-4 全巻 Yuichi で統一』→メモリ project_ebook_manga_author.md 作成済。(2) 全78ページ目視確認（A案）: page 002-081（テキストページ 33・53 はスキップ）+ cover、すべて高品質マンガ調イラスト・キャラ一貫性・日本語テキスト描画・物語整合 OK。3話構成（第1話=陽性反応と、描いていた未来 / 第2話=保育園落ちた / 第3話=退職届）スムーズに繋がる。(3) 出力サイズ不揃い検出: 7枚（page_002/006/007/008/010/011/013）が 1024×1536 ではない（縦長狭い）+ 8枚が 1023×1537（1px差・許容範囲）。コンテンツ品質は OK のため C案『このまま本番反映 → EPUB ビルド → 違和感が出たら個別差し替え』採用。(4) vol1 本番反映: 既存 vol1/pages/page_*.png 33枚を _backup_before_codex_prod_20260426/ に退避→done/<job>/pages/ から78枚コピー→cover.png を KDP出版用/ に配置→done と queue を archive/ に移動（input は _input サフィックス付き）。staging に並行コピー: codex_test_output_20260425/。(5) Step 7 EPUB v1 ビルド (画像のみ): 78枚 + 表紙、188 MB、固定レイアウト EPUB3。(6) テキストページ追加要望→旧 _v3_1.epub から 9 XHTML 抽出（page_001/033/033b/053/053b/082/082b/083/084）、viewport 1080×1920 → 1024×1536（2:3）に書き換え、新 EPUB に組み込み。フォント font-size 38px+1.7行間。EPUB v2: 88 spine items, 188.5 MB。(7) 縦長不揃いページが横幅基準フィットで切れる問題→ CSS を height-fit に変更（`.page img { display:block; height:100%; width:auto; max-width:100%; margin:0 auto; }`）。EPUB v3。(8) コラム②(053+053b) 下が切れる→4ページ分割再構成（053/053b/053c/053d、各セクション分け）。コラム③(082+082b+083) → 4ページ統合再構成（082/082b/082c/082d、前編/後編タイトル削除して『コラム③：キャリア・アイデンティティの喪失——〝何者でもない自分〟の恐怖』で統一、page_083 廃止）。CSS font-size 38→32px / line-height 1.7→1.6 / box-sizing border-box でテキストオーバーフロー防止。EPUB 最終: 91 spine items（cover + 78image + 12text）、188.6 MB。(9) ビルドスクリプト C:/tmp/build_vol1_epub.py + テキストページ素材 C:/tmp/old_epub_extract/OEBPS/text/*.xhtml 12ファイル（053a-d / 082a-d / 084 / 001 / 033a-b）。【次回最優先】(a) vol1 EPUB を Calibre/Kindle Previewer で最終確認、コラム②③の表示問題が解消したか確認、(b) 残 7枚（縦長不揃い）の差し替え判断（実機確認後）、(c) Step 8 KDP メタデータ生成（書籍情報.md / ジャンル・キーワード.md / 書籍紹介文_HTML.html、著者名 Yuichi）、(d) vol2-4 の Codex 生成（queue 投入済 manga-career-restart_vol{2,3,4}_20260426_15040{0,5,6}）→ done 受取 → 同様にテキストページ統合 EPUB ビルド。【主な成果物】.company/outputs/ebooks-manga/manga-career-restart/vol1/KDP出版用/manga-career-restart-vol1-manga.epub（188.6 MB、91 spine items）/ vol1/pages/page_002〜081.png（Codex版、78枚）/ vol1/KDP出版用/cover.png（Yuichi 著者）/ codex/archive/manga-career-restart_vol1_prod_20260425_201900{,_input,_input_moved_*}/ / .codex/skills/codeximage/SKILL.md（QC 4フェーズループ・最大3回再生成・needs_manual_review_pages 一覧化記述あり）/ C:/tmp/build_vol1_epub.py / C:/tmp/old_epub_extract/OEBPS/text/*.xhtml。【オーナーへの注意点】(a) Codex は gen_manga_bundle.py を実行せず内蔵画像生成を使う傾向あり（コスト $0 だが OCR/Vision-check QC ループは未実行）。skill `codeximage` で QC ループ追加した。(b) 著者名は manifest で明示しても改変される可能性あり→もう「Yuichi」固定なので問題なし。"
last_session_summary_v2026_04_27_textpages: "【ebook-to-manga vol2-4 テキストページ事前生成セッション】(1) 背景: vol2-4 は Codex でマンガ画像（180/200/122ページ）を生成中。vol1検証で『Codexはテキストページを生成しない（page 1/33/53/82/83/84が欠番）』と確認済のため、vol2-4 もテキストページは事前準備が必要。差し替え前EPUBは 9:16 viewport (768x1376) だったが、新マンガ画像は 2:3 (1024x1536) になるためテキストページも 2:3 で再構築。(2) vol1 最新EPUB（2026-04-26ビルド `manga-career-restart-vol1-manga.epub`）から 2:3 用の style.css を抽出（`.text-page`=38px/`.colophon`=30px、`<div class=\"text-page\">` / `<div class=\"colophon\">` の2クラス）。(3) スクリプト C:/dev/build_text_pages_2to3.py 作成: 各vol の comicle_output.csv からテキストページ行（テンプレ=テキストページ）を抽出 → prompt から ◆【...】 行を除去 → label（目次/前巻までのあらすじ/コラム原文/奥付）に応じてレンダラー振り分け（render_toc/render_synopsis/render_column/render_colophon）→ 2:3 viewport の xhtml を `{vol_dir}/text_pages/page_{NNN}.xhtml` に保存。(4) 第1ラウンド（奥付なし）: 19ファイル生成（vol2:5=p1/2/70/179/180、vol3:6=p1/2/59/60/113/114、vol4:8=p1/2/41/42/88/89/121/122）+各vol style.css。■見出し→h3、——副題→.subtitle、〝〟は文字そのまま保持で正常動作確認。(5) オーナー指示『奥付追加してください』→ vol1 page 84 と同じ書式で各vol末尾に追加。スクリプト C:/dev/append_colophon_to_csv.py 作成: 各vol comicle_output.csv 末尾に奥付行（page 181/201/123、テンプレ=テキストページ、QUOTE_ALL書き込み、冪等チェック有り）を追記。サブタイトルは各 KDP出版用/書籍情報.md から取得（vol2=ワンオペ育児、減る貯金、消えた居場所 / vol3=「AIって何？」から始まる、私の再出発 / vol4=初めての報酬、そして新しい私へ）。(6) build_text_pages_2to3.py に render_colophon() 追加（`<div class=\"colophon\">` ＋【...】行はh2、その他はp）→再実行で奥付3ファイル追加生成、合計22ファイル+3 style.css。(7) Codex への影響なし: manifest.json は queue 内の自前CSVコピー（target_pages_count=180/200/122）を参照するため、ソースCSVへの追記は Codex 生成ジョブに影響しない。【次回最優先】(a) Codex 完了通知待ち（ユーザーが3ターミナル並行 or 順次で `cd .company/codex/queue/<job-id>/ && python gen_manga_bundle.py`）、(b) 完了後 done/<job-id>/pages/ + cover.png を vol2/3/4 配下に配置、(c) Step 7 EPUB ビルドで `text_pages/page_*.xhtml` をそのまま組み込み（build_all_epub.py を 2:3 viewport / PNG 対応に更新する必要あり、vol1 最新EPUB スタイルを参考）、(d) Step 8 KDPメタ確認（著者名 Yuichi 統一）。【主な成果物】.company/outputs/ebooks-manga/manga-career-restart/vol{2,3,4}/text_pages/page_*.xhtml（22ファイル）+ style.css（3ファイル）/ vol{2,3,4}/panels/comicle_output.csv（奥付行追記、page 181/201/123）/ C:/dev/build_text_pages_2to3.py / C:/dev/append_colophon_to_csv.py。"
last_session_summary_v2026_04_26_vol234: "【ebook-to-manga vol2-4 CSV全面再構築 + codex-handoffバンドル3本投入セッション】(1) オーナー要望: 漫画化したときセリフ/ナレーション文字数が多くフォントが小さくなり読みにくい→ページ・コマ数を増やしトータルセリフは維持しつつ1コマ30字以内に分割。vol1で確定したキャラ参照画像（manuscript/characters/配下6PNG: ミサキ/ケンタ/山田課長/ひなた_赤ちゃん期/ひなた_2歳期/タクヤ）で統一。出力サイズ表記は9:16→2:3に統一（pixel size 1024x1536は変更なし、表記ラベルだけ）。(2) requirements-definer で要件定義書 .company/requirements/ebook-to-manga-vol234-csv-redesign/REQUIREMENTS.md 作成（9工程: 0=事前準備, 1-3=vol2/3/4 CSV, 4-6=vol2/3/4 画像生成, 7-9=vol2/3/4 EPUB+KDPメタ）。CSV作成3巻分を先にまとめて完成させてから画像生成キューに投入する直列方式。(3) 工程0完了 87/100: vol2/3/4既存pages/をすべて _archive/2026-04-26/ に移動（vol2:73枚+vol4:62枚+vol3:107枚+pages_backup_20260414群）、各pages/はdesktop.iniのみで空に、6キャラPNG存在確認、vol1未登場キャラ調査=加藤さん/ゆかりさんは脇役で専用画像不要、skill.md「9:16」5箇所→「2:3」書き換え（L1639 Remotionビューポートのみ意図的残存）+ codex/_spec/ も全箇所2:3化。(4) 工程1完了 96/100（3ループ後）: vol2 CSV 78→180ページ・113→355コマ・1395字→7714字（保持率99.3%）。前付け順序=P1目次/P2前巻あらすじ/P3登場人物紹介(テンプレ5)、テンプレバランスT1=18.3%/T2-4=40.0%/T5-7=41.7%、9:16残存ゼロ、30字超過0/355=0%、5キャラPNG正規名使用。第1回FAILの原因「省略・要約」を「分割・細分化」に転換して解決。(5) 工程2完了 91/100: vol3 CSV 108→200ページ・437コマ・6993字（manuscript比108.6%、旧CSV比108.6%）、テンプレT1=15.5%/T2-4=39.2%/T5-7=45.4%、30字超過2.06%、5キャラ正規名、9:16ゼロ。スプラッシュ20ページ追加で第6章ボリュームアップ。(6) 工程3完了 89/100（3ループ後）: vol4 CSV 68→122ページ・260コマ・4727字（manuscript比182%、旧CSV比135%）、第1回80点FAIL=拡張率1.18倍のみで省略走行、第2回71点FAIL=前付け順序逆+manuscript未収録シーン多数、第3回でV3スクリプト書き直し→重要シーン12件全件検出（フォロワー300/佐々木320円問答/半年前回想/名刺がなくなった日/電動鼻吸い器4品/売りたい/千二百八十円/会社が私の席/可能性を自分で）、テンプレ偏り（T1=23.7%・T2-4=26.3%）残存だがコンテンツ充実で総合PASS。(7) 全3バンドルcodex-handoff投入完了: .company/codex/queue/ に並列バックグラウンド3エージェントで manga-career-restart_vol2_20260426_150400 (181 items: page180+cover1+text_only5)、_vol3_20260426_150500 (201 items: page200+cover1+text_only6)、_vol4_20260426_150600 (123 items: page122+cover1+text_only8) 全件配置済み。各バンドルに characters/(6PNG) + templates/(7JPG) + csv/comicle_output.csv + gen_manga_bundle.py + manifest.json + TASK.md + START_HERE.md 完備、JSON validity OK。(8) コスト見積: 画像生成対象481枚（vol2:175+vol3:194+vol4:114+表紙3）× $0.21 = $101.01、iter込み上限$130-150。(9) vol1は別セッションでcodex処理中（manga-career-restart_vol1_prod_20260425_201900）で並行進行。【次回最優先】(a) ユーザーが3ターミナル並行 or 順次でCodex CLI起動: cd .company/codex/queue/<job-id>/ && python gen_manga_bundle.py、(b) 完了後Claude Codeに通知→ done/<job-id>/ から pages/ + cover.png をvol2/3/4各配下に配置→Step 7 EPUB化（残工程7-9）、(c) コラム⑩・vol2-4 KDPメタ「Yuichi」確認。【主な成果物】.company/requirements/ebook-to-manga-vol234-csv-redesign/REQUIREMENTS.md+EXECUTION-phase{0,1-vol2,2-vol3,3-vol4}.md / vol2-4各 panels/comicle_output.csv（新版）+ comicle_output_pre_30char_redesign.csv（旧版バックアップ） / .company/codex/queue/manga-career-restart_vol{2,3,4}_20260426_15040{0,5,6}/ 3バンドル。【関連メモ更新】特になし（ノウハウは要件定義書・QAレポート群に集約）。"
last_session_summary_v2026_04_26_evening: "【競馬予想 X投稿バグ恒久修正セッション（Windows）】前回Mac側HANDOFFの認識誤り判明: VPS本番には既に post_morning_to_x 呼び出し / longshot_wide_predictor.py / longshot_wide_tracker.py すべて配置済みだった。ローカルだけ古かったので VPS現行版を取り込み同期完了。(1) 真の不具合: モーニング予想 X投稿が3週連続（4/12, 4/19, 4/26）403 Forbidden で失敗。スレッド reply_chain の4本目以降が `You are not permitted to perform this action` で止まる事象。直前ライブ・穴予想（単発投稿）は4/25実績多数で問題なし → X側の連続reply スパム抑制に該当と判断。(2) オーナー方針: 単発投稿に切り替え、文字数に合わせて数レースごとにまとめる、穴予想も同様。(3) CLAUDE.md品質ループで全工程完走（工程5 quality-checker採点 94/100 PASS）。(4) shared/x_poster.py を全面改修: スレッド reply 廃止 / X単発280字を「半角=1, 全角=2」のウェイト計算で chunk 分割（共通ヘルパー _chunk_for_x / _post_tweet_chunks / _attach_page_marker）/ chunk間 10秒 sleep / ページ番号 (N/M) 付与（総数>1のとき）/ 失敗1個でも残り chunk 試行（grace continue）/ Gemini timeout 30→120秒 / maxOutputTokens 4096→8192。(5) MORNING_PROMPT 大改修: 1レース1ブロック厳守・1ブロック重み260以内・◎○▲ 1行圧縮（"/" 区切り）・買い目「1-3-14 17倍」形式（≈と小数点削る）・三連複8点/馬連5点 全買い目掲載・ハッシュタグは #競馬予想 #JRA の2個のみ。(6) _chunk_for_x をレース境界保持（"---" を跨がない）に変更。(7) run_morning.py の穴予想ブロックに post_longshot_to_x 呼び出し追加（dry_run分岐込み）。(8) ローカル↔VPS同期: run_morning.py / run_live.py / longshot_wide_predictor.py(新規復元) / longshot_wide_tracker.py(新規復元) / x_poster.py。md5 一致確認済。(9) VPSバックアップ取得: shared/x_poster.py.bak.20260426 / jra/scripts/run_morning.py.bak.20260426。(10) 当日(4/26)分で実投稿テスト: tweet_id=2048187929848373305 / 2048187974165336095 取得・**403完全解消**確認。(11) 最終ドライラン結果: 注目11レース全件が1レース1tweet完結（13 chunks、weight 195〜254、すべて260以内）。【次回反映】今日 4/26 直前ライブ cron は新コードで稼働済 / 来週開催 5/2(土)・5/3(日) 朝7:00 cron で post_morning_to_x が新フォーマットで自動投稿。【主な成果物】.company/engineering/docs/keiba-x-post-singletweet-chunking-requirements.md / keiba-unified/shared/x_poster.py(全面改修) / keiba-unified/jra/scripts/run_morning.py(穴予想ブロック更新)。"
last_session_summary_v2026_04_26: "【TODO配信修正 + 競馬予想調査セッション（Telegram経由）】(1) TODO Telegram配信が3日連続（4/24-26）無言失敗していた問題を修正。原因: launchd com.yn.daily-priority が毎朝6:45に /Users/yuichi/scripts/daily_priority.py を実行するが、Google Driveマウントが未完了のためTODOファイルが読めず「TODOファイルなし」で無言終了していた。修正: wait_for_google_drive() を追加（Phase1=マウントポイント出現待ち最大5分 + Phase2=TODOディレクトリ同期待ち最大5分、計10分リトライ）、失敗時もTelegram通知、Gemini APIエラー時はTODO直接配信フォールバック。手動テスト実行で配信成功確認済み。(2) 競馬予想X投稿の問題調査: (a) run_morning.py にX投稿(post_morning_to_x)の呼び出しが未実装→Telegramサマリーのみ、(b) longshot_wide_predictor.py がリポジトリから消失→穴予想が常にスキップ(_LONGSHOT_AVAILABLE=False)、(c) このMacからVPSへSSH接続不可（~/.ssh/ に鍵なし）。オーナー判断: 競馬関連は別PCから修正する。(3) 今日のTODOをTelegram手動配信済み。【修正ファイル】/Users/yuichi/scripts/daily_priority.py（Google Drive待機ロジック追加+エラーハンドリング強化）。【別PCでの残作業】(a) run_morning.py にpost_morning_to_x呼び出し追加→VPSデプロイ、(b) longshot_wide_predictor.py 復元→VPS配置、(c) VPSデプロイ。【補足: Mac側の「a〜c」認識は誤りでVPS本番には既に配置済だった。実際はローカルだけ古かった。後続セッション v2026_04_26_evening で完了。】"
last_session_summary_v2026_04_25: "【ebook-to-manga スキル大改修セッション / Codex外部CLIハンドオフ方式導入 + Pillow完全排除 + Step5.5削除】(1) `/codex:setup` 実行で Codex CLI 0.124.0 / ChatGPT認証 (yuichi121@ymail.ne.jp) ready 確認。(2) オーナー方針: Codexプラグイン（`/codex:rescue`）は使わず、外部ターミナルでCodex CLIを別セッションとして走らせるハンドオフ方式を採用。CLAUDE.md品質ループで全3工程完走（工程1=95/100, 工程2=87/100→修正後, 工程3=79/100→修正後）。(3) 工程1（ハンドオフ仕様設計）: `.company/handoff/codex-image-gen/_spec/` 配下に6ファイル作成（SPEC.md, manifest.schema.json, done.schema.json, codex_instructions_template.md, gen_pages.py, sample_manifest_page_batch.json）。責務分離: Codex側=純粋生成（PNG書き出しのみ）、Claude側=manifest生成→DONE.json待機→QC（OCR/Vision-check）→合成→EPUB。OPENAI_API_KEYはハンドオフフォルダに書かずCodex側env委任。(4) 工程2（skill.md改修）: HANDOFF_MODE={inline|codex-handoff} フラグ導入、Step 3/5/6 を -A準備/-B実行/-C受取 に三分割、2428行→2574行。(5) 工程3（ドライラン整備）: `_sample-run/` 配下に動作確認用一式、`python gen_pages.py --dry-run --skip-image-check` で課金ゼロ検証済み。(6) **固定ハンドオフフォルダ方式に変更**: 書籍が変わっても `.company/handoff/codex-image-gen/step{3,5,6,5_regen_iter_<n>}/` 固定。`<job-id>` サブフォルダは廃止、job_id は `job.json`/`DONE.json` 内のメタフィールドとしてのみ残す。新規ジョブ時は該当stepフォルダをcleanしてから再配置。(7) **Step 5.5 Pillow合成フォールバック完全削除**: 351行のセクション削除、max_iter連続FAIL時は「ベストエフォート採用（最後のiter画像を`page_{NNN}.png`に昇格 + `needs_manual_review_pages[]`に記録）」に置換（案A）。`composite_page5.py`参照・`panel_regions.json`ファイル・`fallback_pages`/`fallback_reasons`/`composited.png` 全参照を排除。skill.md 2575→2210行（-365行）。(8) **Step 6 表紙もPillow完全排除**: 表紙もPNGのまま保存（`KDP出版用/cover.png`）、EPUB content.opf は `image/png`、`from PIL import Image` 削除。100%正確テキスト保証の売り文句は失効したが、Pillow依存ゼロ・画質劣化ゼロのシンプル構成に。(9) 要件定義書・QAレポート5本作成: REQUIREMENTS.md / QA-phase1.md / QA-phase2.md / QA-phase3.md / QA-step55-removal.md（`.company/requirements/ebook-to-manga-codex-handoff/`）。【運用フロー】(a) ユーザーがモード指定（HANDOFF_MODE=codex-handoff）、(b) Claude が Step 3-A/5-A/6-A で固定フォルダにmanifest等配置、(c) ユーザーが別ターミナルで `python gen_pages.py` 実行、(d) Codex が DONE.json 書き出し→ユーザーが「完了しました」と通知、(e) Claude が Step N-C で id ベース突合→OCR/Vision-check→EPUB化。【次回最優先】(a) 実案件（本番vol1 or 新規書籍）で codex-handoff モード初回動作テスト（ドライランB/C = 実API 1ページ生成+DONE.json戻り受取）、(b) 動作確認で不具合があれば skill.md 追加修正、(c) Meta SNS Step6（前回からの継続）。【主な成果物】`.claude/skills/ebook-to-manga/skill.md`（2210行）、`.company/handoff/codex-image-gen/_spec/`（6ファイル）、`.company/handoff/codex-image-gen/_sample-run/`（ドライラン一式）、`.company/requirements/ebook-to-manga-codex-handoff/`（要件定義+QA 5本）。【削除】`.claude/skills/ebook-to-manga/panel_regions.json`（Pillow合成専用データファイル、用途消滅により削除）。"
last_session_summary_v2026_04_23_vol1validation: "【ebook-to-manga改修版 vol1検証セッション】(1) CLAUDE.md整理: 97行→53行、A+B+C案統合（フロー図2つ→1つ統合 / HANDOFF→TODO先読み等の作業前ルール追加 / 詳細はskills/<name>/SKILL.md委譲、個別プロジェクト固有ルールはメモリ参照と委譲先明記）。(2) ebook-to-manga vol1検証実施: requirements-definer で要件定義書 .company/engineering/docs/ebook-to-manga-vol1-validation-requirements.md 作成（vol1冒頭5ページ・既存キャラ画像流用・出力先 manga-career-restart-validation/ で旧版非汚染・コスト上限$5.00）→executor で全8工程通し実行（page_001はテキストページスキップ、page_002〜005生成、表紙・EPUB・メタ3ファイル全完走、$2.17/上限$5.00）→quality-checker で工程別採点 全8工程合格 平均91.6/100（A=90 B=92 C=100 D=95 E=88 F=95 G=90 H=93）。(3) page_002 キャラ欠落バグ発見: gpt-image-2が4キャラ全身イラスト指示（ミサキ・ケンタ・山田課長・ひなた）で山田課長を省略→テキスト枠のみ「山田課長(50代) ミサキの元上司、温厚だが制度の壁には無力。」描画のみ。CSV側プロンプトは正しく参照画像も4枚渡しているのにモデルが1人スキップ。原因はBlind-OCRがセリフなしページをオートPASSするためキャラ欠落を検知できなかった構造的穴。(4) 即修正（C案=A+B両方）実施: page_002.png をバックアップ（page_002_original_buggy.png として保持）→強化プロンプト追加（『4キャラ全員絶対描画』『テキスト枠のみ禁止』『山田課長は3段目に配置必須』）+ gpt-4o vision で4キャラ存在YES/NOチェック→iter_1で全員YES確認、即採用、$0.21追加。再生成スクリプト C:/Users/fcmdt/regen_page002.py 保存。(5) 恒久対応チケット起票: .company/pm/tickets/2026-04-23-ebook-to-manga-step5qc-character-presence-check.md 作成（Step 5-QCにキャラ存在Vision-check追加、セリフなしページのオートPASS廃止、gpt-4o vision YES/NO判定→NO時は既存iterループに乗せる、コスト影響+$0.50〜$1.00/冊、担当=engineering、優先度=normal、status=open）。(6) 動作確認できたこと: gpt-image-2 via images.edit + 参照画像で全工程完走、Blind-OCR=gpt-4o 連携正常、Pillowフォールバック機構（page_004で発動）正常、Step 7 glob は page_*.png 限定で .jpg 誤収集なし、コスト試算（$1.92〜$2.55）と実績（$2.17）ほぼ一致。【次回最優先】(a) 起票したチケット（Step 5-QCキャラ存在Vision-check）の skill.md 改修着手 — 本番 vol1 全ページ再生成前に必須、(b) チケット完了後、vol1再検証で再現テスト、(c) 本番 vol1 の gpt-image-2 全ページ再生成（残り約40ページ・推定$15〜20）。【参照】要件定義書 .company/engineering/docs/ebook-to-manga-vol1-validation-requirements.md / 検証出力 .company/outputs/ebooks-manga/manga-career-restart-validation/vol1/ / バグ証拠 pages/page_002_original_buggy.png / 恒久対応チケット .company/pm/tickets/2026-04-23-ebook-to-manga-step5qc-character-presence-check.md。"
last_session_summary_v2026_04_23_saxo: "【Saxo Sim 24時間トークン更新セッション】(1) オーナーから『saxoの24時間トークンの更新』リクエスト。ブラウザで https://www.developer.saxo/openapi/token から新トークン取得→チャットに貼り付け。(2) ローカル `g:/マイドライブ/YNFactory-cc/ai-trade-system/.env` の SAXO_SIM_TOKEN 行を Edit ツールで上書き → `python scripts/check_saxo_token.py` で HTTP 200 OK 疎通確認。(3) オーナーから『VPSへもお願いします』追加指示。VPS (root@163.44.101.31:/opt/ai-trade-system/.env) も同トークンに更新: バックアップ `.env.bak.<timestamp>` 作成→sed -i '18s|...' で18行目のSAXO_SIM_TOKEN行のみ置換→VPS上で check_saxo_token.py 実行 HTTP 200 OK確認。(4) systemctl is-active ai-trade-forward = inactive のため再起動不要。(5) 新トークンの exp = 1776995895 (2026-04-24 17:38 JST 頃失効) → 翌日18時前に再取得要。VPS cron (毎朝8:00 JST 23 UTC) で check_saxo_token.py が自動アラート判定する。"
last_session_summary_v2026_04_23: "【ebook-to-manga スキル NanoBanana2→gpt-image-2 全面移行セッション】(1) オーナーから『ChatGPT-image 2.0 を試したい』リクエスト。昨日リリースの gpt-image-2（model_id: gpt-image-2-2026-04-21）を WebSearch で確認→日本語テキスト描画大幅改善・9:16縦長対応・$0.21/枚・images.edit で参照画像対応。(2) vol1 4ページ（p002/p006/p012/p045）を gpt-image-2 で再生成し NanoBanana2 版と比較HTML作成（.company/outputs/openai-image-gen/vol1-sample/comparison_v2.html）。日本語セリフ描画は両モデル互角、gpt-image-2 は絵の表現力で優位、縦書きナレーション枠は劣位だが『縦書き必須』プロンプト追加で解消確認（p045_vertical）。p045オーバーレイ配置指示追加で画像領域分割問題も解消（p045_overlay）。(3) オーナー判断=案B（本文全面切替）→要件定義→実装。途中『ナレーションで1コマ使うな』『文字数と枠サイズ合ってない』『縦書き指定やめる』『追加ルール3つ全部不要』と段階的に方針確定→最終仕様=AI任せ、追加プロンプトルール一切なし、縦書き/横書き/オーバーレイ全部指定しない。(4) 要件定義書 .company/engineering/docs/ebook-to-manga-gpt-image-2-migration-requirements.md 作成→追加ルール削除版に更新（2026-04-23差分）。(5) CLAUDE.md品質ループ（requirements-definer→executor→quality-checker）で全6工程完走 平均93.3/100: 工程1=93(前提条件)・工程2=97(Step3キャラ)・工程3=89(Step5+QC)・工程4=100(Step5.5 Pillow合成)・工程5=90(Step6表紙)・工程6=91(Step7+E2E整合)。(6) 最終仕様確定: gpt-image-2 via client.images.edit + 参照画像、size=1024x1536/quality=high、プロンプト追加ルールなし、Blind-OCR=gpt-4o（OpenAI一本化）、Pillow合成フォールバック維持、保存=本文PNG/表紙JPEG(KDP要件)/キャラ参照PNG、OPENAI_API_KEY必須・GOOGLE_AI_STUDIO_API_KEYは任意レガシー併存。(7) 画像フォーマット大改修: 本文.jpg→.png、Step7 glob/MIME更新、E2E手順もPNGに統一、表紙のみJPEG変換(Pillow経由で明示)。(8) コスト: $8.60/冊→上限$34.89/冊(約4倍)、内訳積み上げでは$23.55/冊。(9) 軽微修正ポイント全て反映済: Step6 import glob漏れ修正、Step5内コスト試算の旧モデル名残存修正、Gemini固有名詞の汎化（OCRモデル表記に統一）。【次回最優先】(a) vol1 または vol2 で改修版skill.md の実動作テスト(別セッションで実施予定)、(b) Meta SNS Step6 継続(ClaudeInChrome指示書済)、(c) 必要に応じて gpt-image-2 実動作確認後のハンドオフデータ反映。【参照ファイル】.claude/skills/ebook-to-manga/skill.md（約1900行、全6工程反映済み）、比較HTML .company/outputs/openai-image-gen/vol1-sample/comparison_v2.html、検証サンプル .company/outputs/openai-image-gen/vol1-sample/v2/p*.png（5枚）。"
last_device_prev: "自宅Windows（openai-image-gen スキル作成 + vol1比較 + Saxo Simトークン更新 + Meta SNS Step5→6引き継ぎ）"
last_session_summary_v2026_04_22: "【openai-image-gen スキル新規作成 + vol1画質比較 + Saxo Simトークン更新 + Meta SNS Step5受領→Step6指示書作成セッション】(1) openai-image-gen スキル新規作成: OpenAI gpt-image-1.5 ベース、参照画像入力対応、NanoBanana2 と並行運用。spec/plan/実装/受入テストを CLAUDE.md 品質ループで完走、commit ffd92e6 + レビュー指摘3件修正 commit 6474f4a。受入テスト4件(generate/edit/parallel/errors)全合格。(2) vol1サンプル比較(manga-career-restart p2/p6/p12/p45): gpt-image-1→1.5→chatgpt-image-latest の3モデル × 4ページ = 12枚生成、NanoBanana2版と目視比較。結論: ebook-to-manga 本編は NanoBanana2 継続使用(日本語セリフ描画の優位性+Canva後処理コスト回避)、OpenAI スキルは単発イラスト・扉絵等のサブ用途に。chatgpt-image-latest 使用には Organization Verification 必須で今セッション中に認証完了。skill.md を gpt-image-1.5 に commit 407a8a4。(3) Saxo Simトークン更新: 期限超過(06:24 JST)から復旧。ローカル ai-trade-system/.env + VPS /opt/ai-trade-system/.env (バックアップ .env.bak.20260421_215148)、sed -i で SAXO_SIM_TOKEN 行のみ置換、docker compose up -d --force-recreate ai-trade-forward、HTTP 200 OK 確認、ForwardScheduler 稼働確認。次回失効 2026-04-22 21:47 JST。(4) Meta SNS Step5 完了(ClaudeInChrome経由): 追加ユースケースは「Threads APIにアクセス」+「ページのすべてを管理」の2つ。重要仕様変更=Instagram独立ユースケースは廃止され「ページのすべてを管理」に統合、instagram_basic/instagram_content_publish は OAuth フローで権限リクエストする形に。FB Page ID=1015019845037766、IG Business Account ID=17841477801881765、Business Portfolio ID=1654828215887196 を記録。(5) Meta SNS Step6 ClaudeInChrome向け指示書作成: .company/engineering/docs/meta-sns-step6-claudeinchrome-instructions.md。Graph API Explorer で User Access Token + Page Access Token 取得、10権限(FB5/IG2/Threads3)、機密保護(トークン本体ファイル保存+報告は先頭10文字のみ)、IG プロアカウント事前チェック(ビジネスでないと instagram_content_publish 不可)を冒頭に記載。(6) project_meta_sns_setup.md メモリ更新、project_openai_image_gen.md メモリ更新。【次回最優先】(a) Meta SNS Step6 を ClaudeInChrome に実行してもらう(指示書パス済)、(b) Step7(fb_exchange_token で長期化、ターミナル完結)、(c) Step8以降(.env 追記 + post_to_meta.py 実装)。【次回考慮】Saxo Sim 次回失効 2026-04-22 21:47 JST、明日夜までに次トークン取得要。"
last_device_prev: "自宅Windows（AI投資BTC塩漬けポジション手動決済+Coincheck残高不足バグ修正）"
last_session_summary_v2026_04_21_ai_trade_fix: "【AI投資 BTC塩漬けポジション手動決済 + Coincheck売却残高不足バグ恒久修正セッション】(1) オーナーからAI投資(仮想通貨)の現状成績確認リクエスト→VPS `/opt/ai-trader/data/` の trade_history.json + positions.json + simulation/sim_history.json を集計。実トレード: 2トレード実現+456円 + 塩漬けオープン crash_rebound(2026-04-09 @ 11,307,930 / Day 36/15 / 含み益+7.15%)、シミュレーション5件 合計+16.17%(4勝1敗 勝率80%)。(2) 塩漬けポジションを手動決済: docker exec ai-trader-coincheck 経由で AutoTrader._close_position を PositionStatus.CLOSED_MANUAL で呼び出し→ 1回目『Amount has insufficient BTC balance』で失敗、原因は記録amount=0.00133 に対し実残高0.00132648(手数料控除分差)。pm.positions[key]['amount']=0.00132648 に調整→再実行で約定成功 @ 12,123,047円 / PnL +1,081円 (+7.21%)、累計実現+1,537円 / 3トレード。(3) hold期限切れ(Day 15)でも自動クローズしなかった真因特定: 仕様変更前だったからではなく、毎4時間cycle で HOLD EXPIRED判定は正しく発火していたが market_sell API が毎回残高不足で拒絶され21日間ループしていた(docker logs にERROR連続痕跡)。(4) 恒久修正(案C=案A+B両方)を CLAUDE.md品質ループ(requirements-definer→executor→quality-checker)で実施: 工程1=93点合格(ExchangeClient.fetch_base_balance()追加 + _enter_position 案A + _close_position 案B)、工程2=100点満点合格(VPS反映、旧VPSベースに最小diff当て直し方式に途中転換、ai-trader-coincheck再ビルド&Up確認)、工程3=88点合格(commit f35fe6f、remote未設定のためpush skip)。(5) 工程2の途中経緯: 初回executor がローカル新版trader.py を VPSに丸ごと置き oanda/saxo/httpx 依存不足で Restarting。ロールバック→VPS旧ベースに fetch_base_balance(約15行)+ 案A(約12行)+ 案B(約15行)の最小diffだけ再適用→ビルド成功。ローカル側も HEAD 復元してから同じ最小diffを当て直してcommit。(6) pytest 99件全PASS。本番反映確認: ai-trader-coincheck Up / ai-trade-forward 無影響継続Up / docker logs に Exception/Traceback なし / 『No open positions to manage.』で案B安全網は次回売却時に発動予定。(7) ついで発見: シミュレーション側でも 04-06 crash_rebound が本来の hold_bars超過後ではなく 04-17 20:14 に決済されている等、シミュ時間軸にも潜在バグの可能性(深追いせず)。【次回アクション候補】(a) ai-trade-system のGitHub remote設定 + push、(b) シミュ側 hold_bars 判定タイミングバグ調査、(c) VPS残存の oanda_client.py / saxo_client.py 削除(rm権限要確認)、(d) 次回の買付シグナル発生時に案A の amount adjusted ログが出るか docker logs で確認、(e) Meta SNS Step6 着手(Graph API Explorer トークン取得)。"
last_device_prev: "自宅Windows（ebook-to-manga ハイブリッドQCパイプライン 本実装完走）"
last_session_summary_v2026_04_21_impl: "【ebook-to-manga ハイブリッドQCパイプライン 本実装セッション / 全6工程完了】(1) 前夜(v2026_04_21_night)のプロトタイプA+Bハイブリッド実証結果を本実装フェーズに展開。CLAUDE.mdの品質ループ(要件定義→実行→品質チェック)に厳密従い、requirements-definer→executor→quality-checker ループで6工程を完走、平均スコア92.7/100で全工程85点以上合格。(2) 要件定義書作成: .company/engineering/docs/ebook-to-manga-hybrid-qc-requirements.md(6工程分割・各工程品質基準100点定義・顔検出はPhase2送り)。(3) 工程1(97点): panel_regions.json を .claude/skills/ebook-to-manga/ 配下に新規作成。テンプレ1〜7全対応、正規化比率0〜1、コミクル2.0テンプレ画像(1405x2000px)を Pillow+NumPy解析+プロトタイプ座標採用。T1=1/T2〜4=2/T5〜7=3コマ。T5/T6はプロトタイプ値と完全一致、T1〜4,7は画像直接測定。(4) 工程2(88点): skill.md Step4 CSV仕様に `コマ別テキストJSON` 列追加(panel_id/type/speaker/text)。type='dialogue'/'narration'の2値、speaker null条件、テキストページ空配列扱い、CSVフォーマット対策(〝〟変換+JSON内カンマ+改行禁止)、T6 panel_id割当差異(2=bottom-right/3=bottom-left)の明記。(5) 工程3(95点): Step 5-QC セクション新規追加(約155行)。confirmation bias排除(期待テキスト非提示)、vlm_dialogue_check.py反面教師引用、normalize_text() (NFKC+空白除去)、(panel_id,type)キー辞書引き、usedセット重複消費防止、PASS/FAIL判定、FAILフィードバック注入フォーマット、OCRエラーハンドリング(2回リトライ→空バブル=FAIL)。(6) 工程4(91点): Step 5.5 セクション新規追加(約302行)。発動条件(max_iter=3連続FAIL)、clean regenプロンプト修正ルール(◆【最重要・テキスト除去】ブロック)、描画順序([1]ベース→[2-a]narration→[2-b]dialogue→[3]保存)、縦書き要点(ー/〜/…/‥ -90度回転、max_col_chars計算式、列幅・列間スペース)、YuGothB.ttc/YuGothM.ttc推奨+OSError→load_default()フォールバック、_iter_{N}.jpg/_clean.jpg/_composited.jpg 用途別命名。(7) 工程5(97点、1回修正): Step 5本体を全面改修(32行→199行)。ハイブリッドループ疑似コード(for iter, converged flag, break, B路線呼び出し)、パラメータ表(max_iter=3/バッチ10/5秒間隔/JPEG q92)、コスト試算($8.60/冊=$6.25+$2.35、上限$9.0/冊として安全側見積もり)。初回不合格(82点)理由=行1696/1706の廃止仕様残骸+コスト内訳不整合→修正で97点合格。(8) 工程6(88点): 全体整合性レビュー+E2E動作確認手順セクション追加。Step7 PNG→JPEG統一(cover.png→cover.jpg, image/png→image/jpeg, glob page_*.jpg)、Step7下流互換性説明テーブル追加(A路線/B路線フォールバック収集方法)、E2E6項目+合格基準テーブル追加。(9) 最終成果物: .claude/skills/ebook-to-manga/skill.md(1010行→約1900行、+900行)、.claude/skills/ebook-to-manga/panel_regions.json(新規)、要件定義書1本。(10) 実装効果: 合格率100%保証(A+Bハイブリッド)、コスト$8.60/冊(+$2.35/冊で)、手動再生成不要。【軽微な残課題(Phase2 or 次回)】E2Eセクション内のパス記法統一(`pages/` vs `panels/pages/`)、フォールバック発動確認手順の具体化(プロトタイプ書換 or スキル引数)、顔検出による吹き出し位置最適化(既知Phase2送り)。【次回アクション候補】(a)実本実装テスト: 既存の manga-career-restart vol1 で改修版skill.mdを一度走らせて動作検証、(b)別タスク移動(Meta SNS続き/YN Factory SNS画像/Sales OS朝承認等)。"
last_session_summary_v2026_04_21_night: "【ebook-to-mangaスキル セリフ整合性QCループ根本改善セッション】(1) オーナーから『漫画化パイプラインでチェック→再生成しても合格点に到達しない』と相談。根本原因が gemini-2.5-flash-image の日本語テキスト描画能力不足だと特定（『セリフが正確に生成されない』が本質課題）。(2) 解決方向性ブレスト: 方式①Pillow後処理合成（絵のみ生成+テキストオーバーレイ）、方式②現行維持+QC徹底の二択→オーナー選択は②。(3) プロトタイプ1『Pillow合成』: .company/outputs/ebooks-manga/manga-career-restart/_prototype/ に page_005(テンプレ6/3コマ)で試作、no text regen + 縦書きPillow合成→100%正確なテキスト表示を実証。ただしオーナーは②路線継続を選択。(4) QC強化策のブレスト: OCR案→日本語縦書きマンガ調フォントでは誤読率高く偽陽性リスク大と判断、VLM-as-judge案（Gemini Vision に画像+期待テキスト見せて判定）に決定。(5) プロトタイプ2『vlm_dialogue_check.py』: 期待テキスト見せるとconfirmation biasでGeminiが画像を読まず期待テキストを『そのまま検出した』と偽陽性を出す重大バグを発見。(6) プロトタイプ3『E2Eループ(e2e_loop.py/e2e_loop_page39.py)』で難ページ39(テンプレ5/長セリフ)を3回再生成→裁判官PASSと返答→blind_ocr_check.pyで検証→実際は全コマ文字崩壊のままと判明。『VLMに期待テキスト見せるとダメ、blind OCRで読ませてプログラム比較すべき』が結論。(7) プロトタイプ4『hybrid_loop.py』A+Bハイブリッド実装: A=blind-OCR+programmatic文字列比較(NFKC正規化+空白除去で完全一致判定)、B=N回(既定3回)連続FAIL時に自動でclean regen+Pillow合成フォールバック。ページ39で実行→3回とも生成失敗を正しくFAIL検出→フォールバック発動→最終画像 p39_final_*.jpg に6箇所全セリフ/ナレーション100%正確に描画成功。(8) コスト試算$9.0/冊(現行$6.25/冊+$2.75)で合格率100%保証が得られる設計を実証。(9) 成果物: .company/outputs/ebooks-manga/manga-career-restart/_prototype/ 配下に hybrid_loop.py / composite_page5.py / vlm_dialogue_check.py / blind_ocr_check.py / e2e_loop*.py / hybrid_run/p39_final_*.jpg 他。【次回最優先】(a) 本実装フェーズに進む場合は requirements-definer → executor → quality-checker フローで .claude/skills/ebook-to-manga/skill.md の Step 4(CSV構造化データ列追加)+Step 5(判定ループ+フォールバック)+Step 5.5(新規/Pillow合成)を改修、(b) 先にテンプレ1〜7全コマ領域定義をJSON化すれば合成品質が安定、(c) 吹き出し位置がキャラの顔に被る問題は顔検出(OpenCV/Mediapipe)で空白領域自動配置を本実装で対処予定。"
last_session_summary_v2026_04_21_evening: "【Meta SNS (IG/FB/Threads) 自動投稿セットアップ開始セッション】(1) オーナーから『インスタ・フェイスブック・スレッズの自動投稿の設定をしたい』とリクエスト、post-sns スキル起動。(2) 現状確認: 認証情報は `G:/マイドライブ/YNFactory-cc/.company/engineering/sns-credentials/.env` にX用のみ、Meta系（IG/FB/Threads）認証・`scripts/post_to_meta.py` ともに未作成。post-sns スキル上も Phase 2 未実装扱い。(3) 前提アカウント確認: IG=ビジネスアカウント済/Threads=IG紐付け済/FB=会社ページ未所持/IG↔FB未連携/法人格なし/Meta開発者アプリ未作成。(4) Step1 FBページ作成: ページ名『YNファクトリー』が無効エラー→『YN Factory』に変更して成功（カテゴリ=出版社、自己紹介=ynfactory.online のWebFetch結果から生成）。(5) Step2 IG↔FBページ連携: IGアプリまたは Meta Business Suite 経由で連携完了。(6) Step3 Meta開発者アプリ作成: アプリ名『YN Factory SNS Poster』（App ID=1747727225992867）、ビジネスポートフォリオ=nakada_yuichi に紐付け、ユースケース=『ユースケースなしで作成』を選択→ダッシュボード到達。(7) Step4-5 ユースケース追加で中断: 現UIは製品追加ではなく『Add use cases』でコンテンツ管理系ユースケース（Instagram API / Facebook Page content / Threads API）を選ぶ方式。オーナーに『コンテンツ管理』フィルター後のスクショ提供を依頼したところで『いったん終了』指示→中断。(8) メモリに `project_meta_sns_setup.md` を新規作成し進捗記録、MEMORY.md にも追加済。【残タスク】Step5(ユースケース追加)→Step6(Graph API Explorer でトークン取得)→Step7(長期トークン化+Page Access Token)→Step8(.envに各IDとトークン追記)→Step9(scripts/post_to_meta.py 実装)→Step10(post-snsスキルの対応状況をPhase2完了に更新)。【次回再開トリガー】『Meta SNSセットアップの続き』等の指示で Step5 から再開する。"
last_session_summary_v2026_04_21: "【YN Factory SNS紹介画像ブレスト中断セッション】(1) オーナーから『YNファクトリーの紹介をSNSに投稿するための文字付き画像を作成したい』とリクエスト。(2) superpowers:brainstorming スキルで要件ヒアリング開始。Q1〜Q5まで質問を進めたがQ5の途中でオーナーから『いったん終了』指示が入り中断。(3) 決定済み要件: Q1=Instagram ストーリーズ/リール（9:16 縦長）、Q2=AB（会社紹介＋提供サービスの紹介）、Q3の代わりにオーナーから公式サイト URL https://www.ynfactory.online/ が共有された、Q4=C（温かみ・想い重視、ベージュ×ブラウン系、筆記体混じり）。(4) 公式サイトWebFetchで取得した基本情報: 事業=電子書籍出版プロデューススタジオ、キャッチコピー=『"本を出している" という事実が、あなたの最強の名刺になる』『一生モノの信頼に』、サービス3本柱=(a)電子書籍出版プロデュース (b)マンガ×ストーリーデザイン制作 (c)SNS・LPプロモーションサポート、ターゲット=著者/起業家/講師/経営者、連絡先=TEL 050-5367-2629 / 名古屋市中区栄二丁目2番1号 / LINE・メール無料相談窓口あり。(5) 未確定の残論点: Q5=9:16 1枚の構成パターン（A=キャッチコピー主役型 / B=ストーリー型 / C=サービス一覧型 / D=上記組合せ or 別案）、Q6以降=フォント選定・配色詳細・CTA文言・複数枚カルーセル化の要否・画像生成方法（nanobanana2-image-gen スキル使用を想定）。(6) 実装への着手はオーナー承認前のため未実施、成果物・コードは一切生成していない。【次回再開手順】『YN Factory SNS画像の続き』等で指示があれば、決定済み要件（9:16 / 会社紹介+サービス紹介 / 温かみトーン）を前提に Q5 の構成パターン選択から再開する。"
last_session_summary_v2026_04_20: "【Sales OS 初回稼働確認→誤署名バグ修正→50件再生成セッション】(1) Saxo Simトークン再取得・ai-trade-system/.env 更新・HTTP 200 OK疎通確認（次回失効2026-04-21 06:24 JST）。(2) Sales OS Phase 1 VPS初回自動稼働確認: 02:00 list_builder.py 37社新規取得（T2 167社累計）、02:30 personalizer.py 50件DM下書き生成、DRY_RUN=trueで実送信ゼロ。(3) 生成DM全件を検証したところ署名欄が『YNファクトリー代表のオーナーと申します』という誤表記。原因特定: scripts/run_personalizer.py の Personalizer() インスタンス化で sender_info パラメータ未指定、src/tracks/c_outbound/personalizer.py line 84-90 のフォールバックデフォルト {owner_name:'オーナー'} が使われていた（commit 3193bf9 で Personalizer 側の受け口は追加したが、呼び出し側更新が漏れていた）。(4) 修正: src/core/config.py に owner_title（既定'代表'）/ owner_contact_email（GMAIL_REPLY_TO→GMAIL_SENDER_ADDRESS フォールバック）を追加、run_personalizer.py で sender_info={owner_company, owner_title, owner_name, owner_contact_email, owner_website} を Config から構築して Personalizer に注入。ローカル31テスト全PASS、VPSデプロイ（.bak.20260420 取得）commit 264920d。(5) scripts/reset_drafts.py 新設 — 壊れたpending50件をrejected状態（error_message='discarded: wrong sender_info (fix 2026-04-20)'）に退避 + companies.status='drafted'→'new' で50社を再処理対象に戻すワンショット。status値は CHECK constraint（'pending','approved','rejected','sent','failed'）に準拠するため 'discarded' ではなく 'rejected' を使用。(6) personalizer 再実行: 50社中49社drafted・1社（マナブデザイン㈱ id=32）needs_retry（Claudeレスポンスにプレースホルダ残存で _has_unfilled_placeholders でreject）。(7) scripts/retry_single.py 新設 — company_id 指定でピンポイント再処理するワンショット。id=32 で実行→ok=True、全50件pending完了。最終検証: pending 50件すべてに「中田」署名含有、「オーナーと申します」誤署名0件、info@yn-factory.com Reply-To および特電法フッター完備。(8) .claude/settings.local.json に autoMode.allow/soft_deny 追加 — VPS 163.44.101.31 への読み取り専用SSH（tail/ls/crontab -l/grep/docker logs/systemctl status）を恒久許可、.env/credentials.json/*secret*/*token*等の機密ファイル読み取りと書き込み・破壊操作は soft_deny で要確認。"
last_session_summary: "【Sales OS Phase 1 設計→実装→ローカル確認→VPSデプロイ完走セッション】(1) 営業強化の要望を受けてブレスト: 3軸並行(A:フリーランス/B:YNツール集客/C:法人AIコンサル[メイン])、P2朝バッチ承認制、T1+T2ターゲット(中小経営者+士業)、E3ハイブリッド実行(VPS cron + Claude Code朝セッション)、O3+O1オファー(yn-tools法人月2000円→AI顧問アップセル)。KGI 2026-06-30 MRR 20万円。(2) 設計書 `.company/engineering/docs/sales-ops-design.md` + CEO判断ログ + Phase 1実装プラン `.company/engineering/plans/2026-04-19-sales-ops-phase1-plan.md` (10タスク)作成。(3) subagent-driven-development で executor→quality-checker ループ10周 全合格(平均97.6点): Task1=98, Task2=88, Task3-6=100, Task7=93, Task8=97, Task9=100, Task10=100。29テスト全合格、実装物 `sales-ops/` プロジェクト + `.claude/skills/sales-briefing/` スキル。(4) API キー整備: ANTHROPIC_API_KEY(sk-ant-api03-Pcr…, Sales OS Key発行)・GOOGLE_MAPS_API_KEY(AIzaSyAxe…, yn-tools project, Places API (New))・Gmail OAuth token(yuichi4107@gmail.com 認証済み、y-nakada@yn-factory.com Workspace OAuth試したが未解決失敗)。(5) コード修正3件: (a)Places API (New)対応 — googlemaps ライブラリは Legacy API叩きで REQUEST_DENIED → PlacesApiNewClient 新設してREST直叩きに移行、commit 9c5ea96、(b)Claude マークダウンコードフェンス対応 — ```json...``` で囲まれて JSONDecodeError → _strip_code_fence ヘルパー追加、commit 9200a5b、(c)架空署名防止 — Claude が署名欄に架空名・架空メアド幻覚 → PROMPT_TEMPLATE に送信者情報注入(owner_name/owner_contact_email等)+ Personalizer.__init__ に sender_info パラメータ、commit 3193bf9。(6) ローカル1サイクル動作確認: 15社取得(税理士/社労士/ウェブ制作各5社)+3社DM下書き生成(`data/preview_drafts_v3.md`)、品質高・署名「YNファクトリー 代表 中田雄一 info@yn-factory.com」正確。(7) VPSデプロイ完了: ConoHa VPS `/opt/sales-ops/` に tar pipe 転送(rsync非搭載)+venv作成+依存インストール+secrets scp(gmail_client_secret.json + gmail_token.json)+VPS用.env作成(DB_PATH=/opt/sales-ops/data/)+DB初期化+実API smoke test成功(130社取得)+crontab追記(02:00 list_builder / 02:30 personalizer)。明日02:00から自動稼働、ログ /var/log/sales-ops.log。(8) DRY_RUN=true / DAILY_SEND_LIMIT=5 で安全側スタート、本番送信前に要ユーザー明示承認。【次回最優先残件】(a)送信From表示を info@yn-factory.com にする(現状 yuichi4107@gmail.com)→Workspace admin で IMAP/SMTP有効化 or Gmail「別のアカウントから送信」エイリアス設定(535エラーで未達)、(b)本番最初の1通自分宛送信検証(DRY_RUN=false + DAILY_LIMIT=1)、(c)Phase 2(軸A/B)実装プラン作成。【前セッション情報は下記に継続】【JP-DAYTRADE 工程1 BT実装→失敗→化け株分析→戦略ピボット探索セッション】(1) 工程1(バックテストエンジン)実装完了: strategy/screener.py(5フィルター+F5プロキシ+live_only 2つ)、backtest/engine.py、backtest/run_backtest.py、36テストPASS、先読みバイアスなし。(2) BT結果: 勝率13.88%/PF 0.49/シャープ-5.36/最大DD-95.9%、全合格基準未達→コードは正しいが戦略が日足データでは機能しない(F6/F7の板情報がBTできない)ことが証明された。(3) オーナー着眼点「化け株には理由がある」を受けて古河電工(5801)の大化けを分析: 2025-04-07底値3647→2026-01高値12520(+234%)、カタリストは光部品事業黒字化/AI-DC需要/13824心ケーブル量産/中計説明会(5/13)/2Q上方修正+水冷モジュール増強(11/13)。(4) AIセクター4銘柄+レアアース4銘柄+バイオ2+防衛3+半導体装置3+海運2+宇宙1 = 合計19銘柄×1年日足取得し化け株パターン横断分析。(5) 最大発見: 2025-04-08/10(関税ショック反発)に19/19銘柄が全員+5%以上同時急騰、マクロパニック逆張りは勝率ほぼ100%。(6) セクター連動強度ランキング判明: AI半導体(6回)>防衛(5回)>レアアース(2回)=半導体装置(2回)>バイオ(0)、海運は戦略除外推奨。(7) 化け株TOP: 三井金属+360%/底→高値+605%(レアアース主役)、サンバイオ+184%/+473%(バイオ+5%日42日のイベント駆動)、IHI+184%/+214%(防衛主役)、QPS+83%/+200%、アドバンテスト+134%/+408%。(8) 「寄り弱→場中爆騰」パターン多数確認: 東邦チタニウム2025-06-12(+15.9% gap-0.2% vol_x20 20.7倍!!)、サンバイオ2025-10-02(+20.6% gap-0.7%)。(9) 決算カレンダー(/equities/earnings-calendar)はFreeプランでは翌日2件のみ返却=直近未発表分用、過去発表日は/fins/summaryのDiscDateから取得する代替策が判明。(10) 戦略候補3本(マクロパニック逆張り/出来高爆発追従/セクター連動追従)を提案、次回選定→実装へ。【前セッション情報は下記に継続】【AI投資システム ショート戦略導入 Phase1+Phase2セッション】(1) 現状分析: ai-trade-system は BTC/ETH/SOL/XRP の3ロング戦略（double_bottom/rsi_oversold_bounce/crash_rebound）のみで下落相場に弱い。ショート戦略導入をブレスト→Phase1(バックテスト検証)→Phase2(本番発注対応)の二段階で進める方針確定。(2) **Phase 1 全5工程完了**: 工程1(AIプロンプト追加 rsi_overbought_reversal.txt + rally_top.txt, 92点), 工程2(逆トレンドフィルター is_uptrend/check_short_trend_filter 実装, 97点), 工程3(strategy_config.json に short 戦略12エントリー追加, 100点), 工程4(4通貨×3ショート戦略=12ケース Gemini判定バックテスト + optimizer.py TP/SL/Hold グリッドサーチ792通り, 88点), 工程5(結果集計レポート docs/short-strategy-phase1-report.md, 93点)。(3) **Phase 1 結論**: **rally_top のみ合格**(ETH・XRP の2通貨で PF>1.3 & DD<30% & Calmar>0.5 充足)、double_top と rsi_overbought_reversal は戦略として不合格だがXRP単独は突出。採用候補: ETH rally_top(PF 2.12/DD 28%)、XRP rally_top(PF 4.84/DD 8.76% Calmar 9.457 最優秀)、XRP double_top(PF 4.89/DD 10.95% XRP単独採用)。BTC全ショート・SOL全ショートは見送り。(4) **Phase 2 工程1-6まで完了**: 工程1(FuturesExchangeClient 新規 src/trading/futures_exchange.py, open_short/close_short/set_leverage(1固定)/set_margin_type(ISOLATED), 98点), 工程2(strategy_config 採用3戦略をPhase1推奨値に更新+enabled:true, 不採用9戦略をenabled:false, 100点), 工程3(PositionManager に direction='long/short' 対応追加, ショートSL/TP/PnL符号反転, 既存ロング完全非破壊, 100点), 工程4(scanner.py で direction 別の trend_filter 分岐+enabled フィルタ, サマリー出力もshort対応, 88点), 工程5(trader.py に _enter_short_position + 安全装置: MAX_CONCURRENT_SHORT_POSITIONS=3, DAILY_SHORT_LOSS_LIMIT_PCT=-5.0, SL/TP両方Noneブロック, 98点), 工程6(dry-run範囲で tests/test_phase2_dryrun.py 5件単体テスト全PASS + 実スキャンでETH rally_top ショートシグナル検出確認, 93点)。(5) **次回残作業**: 工程7(本番最小額検証 20USDT×レバ1倍×1件)には Binance Futures API Key(.env に BINANCE_FUTURES_API_KEY/SECRET or BINANCE_FUTURES_TESTNET_API_KEY/SECRET) が必要。Testnet先行推奨。(6) コード実装は本番投入準備完了状態、ユーザー作業(API Key 発行+.env 設定+明示的承認)待ち。【前セッション情報は下記に継続】【ばんえい予想システムVPSフルデプロイセッション】(1) 昨日(4/17)ばんえい予想配信なしの原因調査→race_calendar.jsonが旧日程(155日)で4/17欠落 + D:\\keiba-ai-system未存在 + Windowsタスクスケジューラ未登録 + VPSに配備なし=配信基盤自体が3/27シーズン終了以降停止していた。(2) 令和8年度公式PDF(25開催149日間)から帯1〜25をpymupdf解析抽出→race_calendar.json完全置換(149日+meets配列追加、工程2で100点PASS)。(3) check_race_day.py get_race_type()をハードコード→meets参照型に修正(100点PASS、11/21〜semi_nighter等の境界正確化)。(4) ユーザー判断でConoHa VPS /opt/keiba-unified/keiba-ai-system/ に全デプロイ: Python3.10venv + requirements.txt + banei_model.pkl + .env、run_banei.shラッパー作成、crontab 7ライン登録(nighter/semi_nighter/twilight各2本+collect1本)、工程6全体92.3点合格。(5) 改善適用: run_banei.sh冒頭に .env source + venv絶対パス化(collect_results.pyへのTelegram Token伝搬対策)。(6) 本日10:53に手動実行→Telegram配信成功(ユーザー目視確認)。(7) 本日以降は完全自動(13:50前半/16:20後半/22:30結果収集、race_type自動切替)。memory project_banei_deploy.md新規追加。【前セッション情報は下記に継続】【競馬穴予想デバッグ + X自動投稿フル稼働セッション】(1) 穴予想(Longshot Wide)今朝7:00クラッシュ原因特定: `longshot_wide_predictor.py:304` の `today_df` UnboundLocalError（pkl不在時のelse分岐欠落）→ pkl→DB fallback独立化＋障害レース除外を独立if、VPSデプロイ済。(2) 穴予想データ乖離: `features_all.pkl`/`keiba.db`は2025-12-28で更新停止、当日データは`keiba_live.db`(スキーマ別) → 本格修正は別セッションで要件定義。(3) X自動投稿調査: `run_morning.py`は`post_morning_to_x`接続漏れ→接続追加デプロイ(次週土曜7:00から自動)。`run_live.py`は04-16追加コードで今日が初運用→診断ログ追加、プロセスkill→再起動、中山1R(10:05)で**X初投稿成功**(tweet_id=2045306956811035005)。(4) 穴予想X自動投稿の独立分岐化: 旧実装は通常予想「買い」時のみX発火、「見送り」時は穴予想対象でもX流れない問題を発見 → `shared/x_poster.py`に`post_longshot_to_x`追加(Gemini LONGSHOT_PROMPT専用)、`run_live.py`の穴予想ブロックにX投稿呼び出し追加、kill→再起動、阪神3R等で穴予想X自動投稿が買い/見送りと独立して発火確認。(5) 本日のX稼働: 通常予想買い×複数件、穴予想×2件以上が成功、ユーザー目視でX投稿確認済。(6) 今日の配信スキップ: 福島1R(09:45)/阪神1R(09:55)/中山1R-2R/阪神1R-2R/福島2R-3R は再起動タイミングで発走済みスキップ、穴予想対象では中山2Rのみ犠牲。明日以降チェック: モーニング予想X自動投稿(3ツイートスレッド、明日日曜7:00初回)、check_results.py 17:30結果集計。【前セッション情報は下記に継続】【前セッション情報は下記に継続】【JP-DAYTRADE J-Quants V2 認証解消 + V2クライアント全面移行セッション】(1) 前回400 Incorrectの根本原因判明: J-QuantsがV1(email+pw→refresh_token)廃止、V2(x-api-keyヘッダー直接認証)に移行していた。(2) ダッシュボードでFreeプラン契約→API Key再発行(`C-4wHtaX...`)。(3) `jp-daytrade/data/jquants_client.py` 全面書き直し(base URL /v2、x-api-key、/equities/master・/equities/bars/daily・/markets/calendar、5桁コード正規化、pagination_key対応、401/403→JQuantsAuthError)。(4) 認証ヘルパー `scripts/jquants_auth_helper.py` を set-token/test に簡略化。(5) テスト更新: 17/17 V2 + 62その他 = 79/79 PASS。(6) 疎通確認: master 4,435銘柄/グロース 612銘柄/Toyota日足19行(Feb 2024)DB書き込みまで成功。(7) Freeプラン期間制約: 2024-01-24〜2026-01-24(過去データBT十分)。(8) **fetch_all_growth 完了(2026-04-18 16:11): グロース612銘柄×2年分 全件成功(0失敗)、daily_prices 275,899行 integrity OK、stocks_master 4,435銘柄 last_price埋込済。実行4h42min、RateLimit 667回全リカバリ。DBサイズ: daily_prices 25.3MB + master 0.7MB**。(9) **重大教訓: SQLite DBをGoogle Drive配下に置くと書込中同期干渉で `database disk image is malformed` 破損(初回 483/608銘柄で発生)。ローカル `C:/dev/jp-daytrade-data/` に移管、環境変数 `JP_DAYTRADE_DATA_DIR` で指定、同じ事故を繰り返さない**。次回最優先: 工程1(バックテストエンジン)着手→requirements-definer→executor→quality-checker ループ。【前セッション情報は下記に継続】【超大型セッション: 競馬穴予想戦略開発→VPS配信実装 + Coincheck板取引切替 + note画像生成】(1) 競馬v3全券種バックテスト(馬連/三連複/ワイド追加22戦略比較)→Win+Mkt唯一黒字。(2) ★Longshot Wide戦略発見: pop≥7軸×partner≥0.35ワイド3点流しROI105.2%/+55,780円。(3) 5戦略conv≥2ポートフォリオ: フラットベットROI131.5%達成。(4) 穴予想VPS配信実装(run_morning.py朝7:00+run_live.py直前+結果自動集計)。(5) Coincheck板取引切替: 販売所0.5%→板0.02%で年間84%手数料削減。hold_bars短縮(30→10/15→5)、interval 24h→4h。(6) BTC 4h足AIビジョンBT→全戦略マイナス→日足維持が最善。(7) note記事7本×画像22枚生成+挿入。(8) Instagram Batch2 30枚生成完了。(9) Limitless sync復旧+insights抽出launchd登録。(10) FX Saxo PAT更新+API復帰。前セッション情報は下記に継続: 【Instagramストーリーズ Batch2量産 + note記事4箇所集約セッション】(1) note記事集約: 4箇所に散在してた note 関連ファイル(23記事+画像83ファイル)を .company/outputs/note-articles/ に統合。series-01-ai-side-business(9本)+series-02-freelance(14本)+assets-covers-bodies(covers7+bodies a/b 14)+README.md(全23本目次)。工程1=92点PASS、工程2=95点PASS、commit efae6e5。残務: ai-side-business/note-articles/images/ 空ディレクトリがGoogle Drive Permission denied で削除できず残存(次回手動削除)。(2) Instagramストーリーズ Batch2量産前回(2026-03-10)と同仕様で新規30本の画像生成プロンプト+日本語原稿を納品。成果物: .company/outputs/instagram-stories/batch-2026-04-15/prompts.md (608行/53KB) + concepts.md。工程1(コンセプト設計)86点PASS、工程2(プロンプト+原稿作成)は初回77点FAIL→修正後96点PASS。修正点: `\\n`直後のスペース混入3箇所除去、日本語原稿独立セクション(**日本語原稿:**)を全30本に追加、フロントマターのトーン記述を前回完全形に復元。画像生成(PNG)は別タスク扱い(nanobanana2-image-genスキルで次回)。【前セッションまでの情報は下記に継続】【日本株デイトレ戦略プロジェクト 立ち上げ→工程0完了セッション】(1) 戦略確定: JP-DAYTRADE-v1（寄り前気配×板厚み戦略）、+5〜10%利確/-1〜-2%損切/同時保有Phase0=3銘柄→Phase2=5銘柄/グロース市場中心/値嵩除外3000円かつ単元30万円。(2) リサーチ5本完了。(3) 要件定義書承認(.company/engineering/docs/jp-daytrade-v1-requirements.md、全8工程、開発50〜76h+フォワード2ヶ月)。(4) 三菱eスマート信用取引口座申込完了(2026-04-15申込、開設予想 2026-04-18〜24)。(5) 工程0(データ基盤構築)実装完了→品質チェック91点PASS。生成物: jp-daytrade/ 新規プロジェクト、74テスト全通過、SQLite STORED GENERATED COLUMN活用、kabu APIモック5シナリオ実装。(6) J-Quants認証情報の取得で躓き保留: 3パターンcredentials試行(yuichi121@ymail.ne.jp x 2 + yuichi4107@gmail.com x 1)全て400 incorrect、登録状態の確認とリフレッシュトークン取得が次回最優先。【次回最優先アクション】(a) https://jpx-jquants.com/ja/login にPCで直接ログイン、失敗ならパスワードリセット、(b) マイページ https://jpx-jquants.com/dashboard/menu/ でrefresh_token目視コピー(JWT形式300-500字)、(c) jp-daytrade/config/.env のJQUANTS_REFRESH_TOKEN設定、(d) python data/jquants_client.py fetch_all_growth 実行(60分)、(e) 工程1(バックテストエンジン)着手。【工程0で発見した軽微バグ(工程3で修正推奨)】run_polling()時間窓判定が9:00-9:59も処理対象になる潜在バグ、JPDaytradeError基底クラスが2ファイルで重複定義。"
---

# セッション引き継ぎ

> このファイルは**セッション終了時に必ず更新**される。
> 次のセッション（別端末含む）で「続きから」と言えば、ここから再開できる。

## 現在進行中の作業

### 000-LIB. [DONE 2026-08-01] 電子書籍『日本の左派・リベラルは、なぜ自滅するのか』 ✅

- **状態**: KDP入稿前パッケージ完成。原稿は全16部・固定78節・本文相当125,794字のまま保持。原稿最終QC 97/100、出版パッケージ総合QC 99/100 PASS。
- **成果物**: `.company/projects/日本の左派リベラルはなぜ自滅するのか/`。`KDP出版用/` に表紙、EPUB、書籍情報、カテゴリ・キーワード、HTML紹介文。`illustrations/` に本文挿絵8点。`epub/` に再生成スクリプト・CSS・メタデータを保存。
- **品質**: 出版工程1=100、画像工程2=97、EPUB工程3=98、KDPメタデータ工程4=100、総合99/100。EPUBCheck 5.3.0はFATAL/ERROR/WARNING=0。EPUB中間版とKDP納品版のSHA-256は一致。
- **時点確認**: S040外務省「外交青書2025 第1章」は2026-08-01に通常HTTPSで到達・本文確認済み。KDP公式ヘルプでカテゴリ最大3、キーワード最大7、商品説明HTML仕様を確認済み。
- **軽微な残リスク**: 100pxサムネイルでは帯コピー全文が細かい。挿絵06の建物看板に可読不能な極小の文字様模様がある。いずれもQC合格範囲。
- **2026-08-02追加修正**: 全78節を節頭改ページへ変更。さらに出版用本文の引用6箇所（ID11件）と末尾出典表2行から内部制作資料S001/S002を完全除外し、公開資料S003〜S070の68件を維持。正本原稿・研究台帳は変更なし。再生成スクリプトも同仕様へ更新し、EPUB展開内容のS001/S002は0件。EPUBCheck 5.3.0はFATAL/ERROR/WARNING=0、独立QC100/100 PASS。
- **未実施**: KDPアップロード、価格・DRM・配信地域等の本番設定、出版申請、公開・販売。
- **次のアクション**: オーナーが公開を希望する場合、KDP登録画面でカテゴリ名を最終照合し、表紙・EPUBをプレビュー後、直前承認を得てアップロード・公開する。

### 000-CM. [DONE 2026-07-22] YNファクトリー会社案内マンガ（表紙＋10P） ✅

- **状態**: 完成。本文QC 90/100、表紙QC 96/100、EPUB・PDFパッケージQC 99/100 PASS。
- **成果物**: `.company/outputs/ebooks-manga/ynfactory-company-guide-10p/`（参照キャラ、ページ別プロンプト、表紙、`page_001.png`〜`page_010.png`、EPUB、PDF、進捗、品質レポート）。
- **仕様**: 9:16フルカラー、10ページ・46コマ。ミカ・矢野・ユキの外見を固定。P10の公式電話番号・住所を公式サイトと照合済み。
- **留意点**: P5は絶対表現を避けて安全調整。P9はフィクション・成果非保証注記を縮小・削除しない。P1/P9の交流会男性は軽微な顔立ち差あり。
- **次のアクション**: LP等へ掲載する場合は、P9の注記を維持したまま掲載サイズで文字可読性を最終確認する。KDP登録・公開はオーナーの明示承認後にのみ実施する。

### 000-PDF. [DONE 2026-07-08] PDF書き込みツール（pdf-annotator）新規作成 — 完成・QC全合格

- **状態**: 完成。リポジトリルート `pdf-annotator/` に配置（ビルド不要静的Webアプリ）。起動は `pdf-annotator/` で `python -m http.server 8000` → http://localhost:8000
- **機能**: PDF読込(ファイル選択/D&D)、ページ送り・ズーム、日本語テキスト書き込み(IME対応・編集/移動/削除/サイズ/色)、ペン、蛍光ペン、undo(Ctrl+Z)、日本語フォント(NotoSansCJKjp)サブセット埋め込み保存
- **品質**: 3工程QC合格(100/97/100点)。保存PDFはpypdf/pikepdf/PyMuPDFの独立検証で文字化けなし・位置一致・未書込ページ無傷を確認
- **技術メモ**: pdf.jsは表示専用（内蔵FreeText注釈はCJK表示崩れバグ#20117のため不使用）。保存はpdf-lib+fontkitのコンテンツストリーム焼き込み方式。@pdf-lib/fontkitのCJK subset破損バグ(pdf-lib#1232)を踏んだため修正フォークpdf-fontkitに差し替え済み
- **要件定義書**: `.company/projects/PDF書き込みツール/要件定義書.md`
- **次のアクション（任意・改修候補）**: ①回転ページ(/Rotate≠0)の実機検証 ②テキスト新規作成直後のフォーカス不具合修正 ③ストローク個別選択・削除

---

### 000-ZA. [IN PROGRESS 2026-06-19] SNS導線の受け皿（営業）整備 — 文書化完了・フォーム反映/LP公開はアクセス待ち 🔥

- **状態**: ショート動画(X/IG/TikTok/YouTube)→LP(`ai.yn-factory.com`)→無料AI導入診断フォーム→AI顧問/導入コンサルの法人リード化、という導線を設計・文書化。
- **やったこと**:
  - `ai.yn-factory.com` がCloudflare Pagesで公開済になったため、`.company/marketing/social-auto-ops/cta/ai-introduction-cta-library.md` のLP URLを旧Google Sites→`https://ai.yn-factory.com/` に統一、status draft→active。
  - `cta/short-video-cta-receiver.md` 新規: プラットフォーム別UTM付きプロフィールURL、動画末尾CTA、フォーム回答後のA/B/C別返信文、公開反映チェックリスト。
  - `forms/free-ai-diagnosis-v2-sns-consult-form-spec.md` 新規(proposed): フォームをSNS/法人リード判別向けに改修する仕様（14項目+送信後メッセージ+A/B/C判定メモ）。
  - ローカルLP文面（`.company/outputs/lp/ai-introduction-consult-publish/`、git管理外=Drive側のみ）をSNS導線向けに更新。
- **ブロッカー**: Googleフォームのライブ更新は未実施。Drive接続ユーザー `yuichi4107@gmail.com` に対象フォーム（オーナー `y-nakada@yn-factory.com`）の編集権限がなく、Drive APIで File not found・編集URLは回答画面へリダイレクト。
- **次のアクション**:
  1. `y-nakada@yn-factory.com` でログインしてGoogleフォーム編集画面を開き、本仕様の14項目へ更新。
  2. ローカルLP文面のCloudflare Pages公開反映を承認（デプロイ）。
  3. SNS各プロフィール/概要欄のリンクを `ai.yn-factory.com`（UTM付）に統一。

---

### 000-Y. [ACTIVE 2026-07-31] shorts-factory 定刻生成復旧・ローカル制御プレーン ✅

- **状態**: 実装・移行・切替・ライブ確認完了。quality-checker 96/100、runtime venv unittest 111件PASS、health `ok=true`。
- **根因**: Drive上の `queue/` と `topics.json` を同期ホットパスにしていたため、Google Drive File Provider待ちでapproval watchdog再起動130回、生成成功12件中12件のtopic消費EDEADLKが発生していた。二重botやSNS API障害ではなかった。
- **新構成**: `~/shorts-factory/` をqueue/topics/outbox/outputs/認証/posting ledgerの正本とし、Driveは別プロセスが5分間隔で一方向ミラーする。生成・承認・投稿はDrive停止中も継続できる。
- **移行結果**: queue 177件、topics backlog 45 / used 70、deferred topic 16件解消、active media欠損0、SNS認証16項目をmode `0600`で同期。queue走査は0.0156秒。
- **実運用確認**: 10:40のオーナーTelegram承認で既存1件をX / Instagram / TikTok / YouTubeへ各1回で投稿成功。worker中にapprovalを再起動しても二重投稿なし。AIから試験投稿は開始していない。
- **次の通常監視**: 2026-07-16 14:00の切替後初回定刻生成。オーナー操作は不要。
- **別途承認が必要**: 過去ログに残る旧Telegram bot tokenの再発行と旧ログ整理（認証変更・削除を伴うため、この修正では未実施）。
- **詳細**: `.company/projects/shorts-factory/2026-07-16-drive-lock-root-fix-debug-log.md`
- **2026-07-31復旧**: Claude CLIが`loggedIn=false`となり、固定フォールバックが重複ガードで全件拒否され、定刻生成が停止していた。`shorts-factory/src/script_gen.py` をtopic/difficulty別の複数フォールバック候補へ改修し、各候補を既存の重複ガードへ通すようにした。対象テスト4/4 PASS、QA 92/100 PASS、runtimeへ同期後health `ok=true`（queue 219、ledger異常0、mirror ok）。
- **安全境界**: SNS投稿・再投稿、Telegram承認、認証変更、launchd変更は未実施。既存の部分失敗9件は古い失敗記録として自動再送しない。
- **次のアクション**: フォールバックで定刻生成→Telegram承認待ちは継続可能。通常のLLM品質を回復するClaude CLI再ログインは、認証変更のためオーナー操作・明示承認後に行う。
- **Telegram確認（2026-07-31 22時台）**: approval LaunchAgentは稼働中で、Telegram Bot APIの読み取り認証確認はHTTP 200 / `ok=true`。7/31の09:00・14:00・19:00は修正反映前の生成失敗で新規`ready_for_review`が作られず、送るべき新規プレビューがなかった。修正反映は19:00枠後のため、次の自然な通知確認は2026-08-01 09:00の定刻生成後とする。テスト通知・投稿・再送は未実施。
- **Git反映**: Drive側のソース・引き継ぎは更新済み。ローカルGit作業ツリーには今回と無関係な入力インデックスの未コミット変更があるため、本セッションではcommit/pushを実施していない。

---

### 000-Z. [HISTORICAL 2026-06-18] shorts-factory 複数媒体・1日3回・初中中バランス拡張 — 後続状況は000-Y参照

- **状態**: 要件定義2本(`.company/requirements/shorts-factory-autopost-improvements-2026-06-16.md`=approved/implemented、`shorts-factory-3x-multiplatform-midlevel-2026-06-16.md`=implemented_waiting_external_login)を実装→QC90点PASS。
- **やったこと**:
  - launchd `com.ynfactory.shorts-generate` を **09:00/14:00/19:00 の3枠化**、`content.scheduled_slots` で 09:00=beginner / 14:00・19:00=intermediate、pipeline に `--difficulty` 追加+時刻自動判定。
  - topics.json に中級ネタ24本追加（現backlog beginner26 / intermediate24）、台本プロンプトを難易度別方針に。queue/Telegram preview に `difficulty` 保持・表示。
  - Drive正本→runtime同期を `SHORTS_REPO_ROOT/YNFACTORY_ROOT`/スクリプト位置から解決（`scripts/shorts_env.sh`）、Telegramログの bot token URL を `[REDACTED]` マスク（`src/logging_utils.py`）。
  - 一部媒体失敗時も queue を `posted` にせず再処理可能に残し、成功媒体は二重投稿しない+失敗媒体だけ再試行（`scripts/retry_failed_posts.py`）。
  - `~/shorts-factory/config.yaml` を staged 作成（`platforms=[x,youtube,instagram,tiktok]`, `auto_post:false`）、`scripts/check_platforms.py` で実投稿なしに preflight、`scripts/login_tiktok.sh` 追加。
  - 検証: json.tool / bash -n / py_compile / unittest(4件) / plutil -lint 全PASS、runtime `~/shorts-factory/app` 同期済、launchd generate/approval 再読込済。
- **preflight現況**: X=ready / Instagram Reels=ready / YouTube=not ready / TikTok=not ready（YouTube・TikTokは専用Chromeプロファイル未ログイン）。
- **次のアクション（オーナー作業）**:
  1. `~/shorts-factory/app/scripts/login_youtube.sh` と `login_tiktok.sh` でログイン。
  2. `~/shorts-factory/.venv/bin/python ~/shorts-factory/app/scripts/check_platforms.py` で全ready確認。
  3. `queue.auto_post:true` 化・実テスト投稿・公開操作は **実行直前に明示承認**（要件のboundary）。

---

### 000-A. [IN-PROGRESS 2026-05-12] マンガ版『ChatGPT 5.5時代の結論』シナリオ書き直し（C案・段階進行） 🚧

**進捗**: シナリオ書き直し（v1→v2 初稿→v2改訂→v3反映）完了・QC 97点 PASS。**次フェーズ（パネルCSV再生成 → 画像再生成 → EPUB再構築）はオーナー最終確認待ちで未着手**。

**プロジェクト場所**: `g:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\chatgpt55-now-only-manga\`

**今回の指示要点**:
1. 「第◯話」の区切りなしでダラっとした印象を改善
2. 各話の冒頭に章扉、末尾に章末まとめを追加
3. 話の展開にメリハリ・躍動感を持たせる
4. 現状一式はアーカイブにして作り直す
5. C案＝シナリオのみ先行書き直し、パネル/画像再生成は仕上がりを見てから判断

**最新成果物**:
- `manuscript/シナリオ_v2.txt`（120P・約1018行・**最新版＝v3レイヤー反映後**）
- `manuscript/章構成サマリ.md`（全ページ一覧表・章扉/まとめ対応・驚き大ゴマ配置・大ナレーション枠配置）
- 旧一式: `archive_20260512_pre-redo/`（manuscript・panels・pages_openai_generated・build・KDP出版用 等を退避）

**要件定義書**: `.company/requirements/chatgpt55-manga-redo-v2.md`（ADDENDUM v1+v2+v3 すべて追記済）

**シナリオに織り込まれた論旨（正本）**:
- 3社とも総合力は高い（ChatGPT/Claude/Gemini）
- 1か月前は Claude＋Gemini Nanobanana の二刀流が現実解だった
  - 真の理由は **ClaudeCode の存在**
- いま ChatGPT 5.5 中心になる真の理由は **Codex を使う前提**
- Gemini の強みは「マルチモーダル＋将来展開力＋Google サービス連携（Drive・Meet・Calendar・Gmail）」
- Nanobanana 日本語表記は私の体感で80点くらい → gpt-image-2.0 で95点くらいに上がった気がする（あくまで主観）
- ChatGPT 5.5 は Opus 4.7 より少し優秀（ただし普段の操作で違いを感じることはない）
- 「画像が最後のピース」はミナの個別事例（あなたにとっての最後のピースは違うかもしれない）
- 抜きつ抜かれつの進歩なので、どれも使えるようにしておくことが重要
- 仕事で大事なのは、自分が一番使いやすいものに慣れること
- **結論句**: 「高いレベルで一本化したいなら、ChatGPT 5.5 がいちばんしっくりくる（自分にとっての最適解と他人の最適解は違う）」

**QC スコア推移**: v2初稿 95点 → v2改訂（ADDENDUM v1） 93点 → v2トーン微修正（ADDENDUM v2） 97点 → v2 v3レイヤー反映（ADDENDUM v3） **97点 PASS**。

**残軽微指摘（次フェーズで対応）**:
- P039-b（Gemini 3強み拡張ページ）の通し番号化（P040 にリナンバーして P121 まで にするか、他ページ統合で P120 維持か）
- 原書「おわりに」相当の著者直接語り温度をエピローグに少し足せるとなお良い（任意）

**次回最優先アクション**:
1. オーナーが `manuscript/シナリオ_v2.txt` を通し読み→トーン/論旨の最終 OK 判断
2. OK の場合: P039-b リナンバー → 次フェーズ（パネルCSV再生成→OpenAI gpt-image-2 で120P画像再生成→EPUB再構築→KDP表紙・メタデータ再生成）の要件定義に進む
3. NG の場合: 追加フィードバックを受けてさらに改訂

**注意点**:
- シナリオ書き直しは「オーナー目線での通読 OK」が次フェーズ着手の条件。QC 97 点は要件定義書ベースの機械的採点で、最終トーン判断はオーナーのみ可。
- パネル画像再生成は OpenAI gpt-image-2 で1枚あたり数十秒〜数分、120P 全再生成で1-3時間規模。
- 用語スタイルは「ClaudeCode／Codex を用語そのまま＋初出時に簡単な説明」の B 案で一貫。次フェーズで変更しない。

---

### 000-I. [COMPLETED 2026-05-06] ebook-to-manga skill恒久改修（チケット 2026-04-24）✅

**成果**: skill.md 全5工程改修完了、最終QA 91点 PASS、チケット完了条件 9/9 充足。次回新規書籍着手時は緩和版QC（`--qc off/lite/full`）+ OCR正規化+ fuzzy matching が利用可能。

**工程別スコア**:
| 工程 | 内容 | スコア |
|---|---|---|
| 1 | Vision-check「全身」条件→「バストアップ・クローズアップ含む」緩和 | 95 |
| 2 | OCR `normalize_text()` 強化（三点リーダ/ダッシュ/引用符/波ダッシュ）+ fuzzy matching（編距2以内）+ `--strict-ocr` | 93 |
| 3 | `max_iter` デフォルト 3→1、`--qc off\|lite\|full` フラグ追加、ループ疑似コードに分岐反映 | 92 |
| 4 | コスト試算テーブル simple($21)/lite($22-23)/full($27) 3モード対応 | 93 |
| 5 | E2E手順を旧9サブセクション→新4ケース構成に刷新（旧238行→新107行） | 95 |
| 最終 | 軽微指摘9項目一括修正後の総合採点 | 91 |

**変更規模**: skill.md 2330行 → 2314行（-16行）

**主な成果物**:
- `.claude/skills/ebook-to-manga/skill.md`（改修後 2314行）
- `.company/secretary/notes/2026-05-05-ebook-to-manga-skill-refactor-requirements.md`（要件定義書）
- `.company/pm/tickets/2026-04-24-ebook-to-manga-drop-pillow-fallback-relax-vision.md`（status: done）

**残存軽微項目**（運用支障なし、参考記録のみ）:
- lite コスト表記 `~$22-$23` がチケット指定値「~$23」と幅で異なる（実態値としては正確）
- `progress.json` 廃止フィールドの記述位置（E2Eチェックリスト括弧内のみ → 進捗管理セクション本体への追記が望ましい）
- L610 登場人物紹介ページ定義に「全身イラスト」が残存（Vision-check文脈外、CSV内容指示として有効）

**次回アクション**: なし（次の新規書籍着手時に新仕様で運用開始すればOK）

---

### 000-H. [IN PROGRESS 2026-05-06] Meta SNS Step6 — use case 権限不足判明・要 Console 設定追加 🔥

**進捗**: Graph API Explorer 起動 + ログイン + アプリ選択まで完了。**権限追加ドロップダウンに `business_management` `pages_show_list` のみ表示** = Step 5 でユースケースを「追加」しただけで個別権限が未有効化と判明。

**完了済み**:
- Claude in Chrome MCP 経由で Browser 2 (Windows) に接続成功
- Graph API Explorer (https://developers.facebook.com/tools/explorer/) 起動
- Meta App「YN Factory SNS Poster」選択済（既定値）
- Facebook ログイン済（オーナー手動実施）
- 「ユーザーまたはページ」→「ユーザーアクセストークンを取得」選択
- 「許可を追加」ドロップダウン展開 → カテゴリ「Events Groups Pages」のみ表示確認

**ブロッカー**: アプリの use case「ページのすべてを管理」「Threads APIにアクセス」を**追加しただけ**で個別権限が Add されていない。Graph API Explorer に `pages_manage_posts` `pages_read_engagement` `pages_manage_metadata` `instagram_basic` `instagram_content_publish` `threads_basic` `threads_content_publish` `threads_manage_insights` が選択肢として出ない。

**次回アクション（最優先）**:
1. オーナー or 私が Meta Developer Console を開く: `https://developers.facebook.com/apps/1747727225992867/use_cases/`
2. 「ページのすべてを管理」 → **Customize** → 以下を **Add**:
   - `pages_manage_posts` / `pages_read_engagement` / `pages_manage_metadata` / `instagram_basic` / `instagram_content_publish`
3. 「Threads APIにアクセス」 → **Customize** → 以下を **Add**:
   - `threads_basic` / `threads_content_publish` / `threads_manage_insights`
4. Graph API Explorer に戻り「許可を追加」で全10権限を選択 → **Generate Access Token** クリック → OAuth 承認
5. User Token + Page Token + IG Business Account ID 取得 → ファイル保存:
   - 保存先: `.company/engineering/sns-credentials/step6-tokens-2026-05-06.txt`
6. Step7（長期化API呼び出し）→ Step8（.env更新） → Step9（post_to_meta.py実装）→ Step10（post-snsスキル更新）

**関連ファイル**:
- 作業指示書: `.company/engineering/docs/meta-sns-step6-claudeinchrome-instructions.md`（要更新: Console先行手順を追記）
- メモリ: `~/.claude/projects/g---------YNFactory-cc/memory/project_meta_sns_setup.md`

**前提アカウント状況**:
- IG: ビジネスアカウント（オーナー本日確認済み）✅
- FB: 個人アカウント → `YN Factory 出版プロデュース` ページ作成済（FB Page ID: `1015019845037766`）
- IG Business Account ID: `17841477801881765`

---

### 000-G. [IN PROGRESS 2026-04-26] ebook-to-manga vol2-4 全面再生成（CSV完了 → Codex生成待ち）🔥

**進捗**: CSV作成完了（工程0-3全合格）+ codex-handoffバンドル3本投入完了 → ユーザーがCodex CLI起動待ち

**完了した工程**:
| 工程 | 内容 | スコア |
|---|---|---|
| 0 | アーカイブ + skill.md「9:16→2:3」修正 + キャラ確認 | 87/100 |
| 1 | vol2 CSV再構築（3ループ後合格） | 96/100 |
| 2 | vol3 CSV再構築 | 91/100 |
| 3 | vol4 CSV再構築（3ループ後合格） | 89/100 |

**CSV最終仕様**:
| 巻 | 旧→新ページ | 拡張率 | 新コマ数 | 新文字数 | manuscript比 |
|---|---|---|---|---|---|
| vol2 | 78→180 | 2.31× | 355 | 7714字 | 4.6× |
| vol3 | 108→200 | 1.85× | 437 | 6993字 | 4.1× |
| vol4 | 68→122 | 1.79× | 260 | 4727字 | 1.82× |

**全巻共通**: 1コマ30字以内、9:16表記ゼロ→2:3統一、vol1キャラ参照画像で統一（manuscript/characters/配下6PNG）。

**バンドル投入完了** (`.company/codex/queue/`):
- `manga-career-restart_vol2_20260426_150400/` (181 items: page180+cover1+text_only5)
- `manga-career-restart_vol3_20260426_150500/` (201 items: page200+cover1+text_only6)
- `manga-career-restart_vol4_20260426_150600/` (123 items: page122+cover1+text_only8)

各バンドル内: characters/(6PNG) + templates/(7JPG) + csv/comicle_output.csv + manifest.json + gen_manga_bundle.py + TASK.md + START_HERE.md

**コスト見積**: 481枚 × $0.21 = **$101.01**（iter込み上限$130-150）

**次回アクション（最優先）**:
- [ ] **ユーザーが3ターミナル並行（or 順次）でCodex CLI起動**:
  ```bash
  cd .company/codex/queue/<job-id>/
  python gen_manga_bundle.py
  ```
- [ ] Codex完了通知後、Claude Codeが done/<job-id>/ から pages/ + cover.png を vol2/3/4 配下に配置
- [ ] 工程7-9: vol2/3/4 EPUB化 + KDPメタ確認（著者名「Yuichi」統一）

**並行進行中**:
- vol1: `manga-career-restart_vol1_prod_20260425_201900` ジョブが別セッションでCodex処理中

**ブロッカー**: なし

**主な成果物**:
- `.company/requirements/ebook-to-manga-vol234-csv-redesign/REQUIREMENTS.md` + EXECUTION-phase{0,1-vol2,2-vol3,3-vol4}.md
- vol2-4 各 `panels/comicle_output.csv`（新版）+ `comicle_output_pre_30char_redesign.csv`（旧版バックアップ）
- `.company/codex/queue/manga-career-restart_vol{2,3,4}_20260426_150*/` 3バンドル

---

### 000-F. [COMPLETED 2026-04-25] ebook-to-manga Codex外部CLIハンドオフ方式導入 + Pillow完全排除 ✅

**進捗**: 全3工程合格 + Step 5.5削除 + Pillow完全排除。実案件での初回動作テスト待ち

**主な変更**:
1. **HANDOFF_MODE フラグ導入** — `inline`（従来・直接API呼出）/`codex-handoff`（外部Codex CLI委託）の二系統
2. **固定ハンドオフフォルダ** — `.company/handoff/codex-image-gen/step{3,5,6,5_regen_iter_<n>}/`（書籍変わっても不変、新ジョブ時cleanして再配置）
3. **Step 3/5/6 を三分割** — `-A 準備` / `-B 実行（モード分岐）` / `-C 受け取り・後処理`
4. **Step 5.5 Pillow合成フォールバック削除** — `max_iter`連続FAIL時は「ベストエフォート採用（最後のiter画像を`page_{NNN}.png`に昇格 + `needs_manual_review_pages[]`に記録）」
5. **Step 6 表紙もPNG統一** — Pillow依存ゼロ。`cover.png` 直接保存、EPUB `image/png` 指定
6. **panel_regions.json 削除** — Pillow合成専用データファイル、用途消滅

**責務分離**:
```
Claude Code: manifest生成 → DONE.json待機 → OCR/Vision-check/合成/EPUB化
Codex CLI  : gen_pages.py 実行して PNG を書く（純粋な生成のみ）
```

**工程別スコア**:
| 工程 | 内容 | スコア |
|------|------|--------|
| 1 | ハンドオフ仕様設計（_spec配下6ファイル） | 95 |
| 2 | skill.md改修（HANDOFF_MODE + 三分割） | 87→修正後合格 |
| 3 | ドライラン整備（_sample-run配下） | 79→修正後合格 |
| 追加 | Step 5.5削除 + A案（ベストエフォート採用）置換 | 76→修正後合格 |
| 追加 | Step 6 Pillow完全排除 + 表紙PNG化 | 手動修正で完結 |

**ファイル規模**: skill.md 2575行 → 2210行（-365行）

**成果物**:
- `.claude/skills/ebook-to-manga/skill.md`（改修後 2210行）
- `.company/handoff/codex-image-gen/_spec/` — SPEC.md / manifest.schema.json / done.schema.json / codex_instructions_template.md / gen_pages.py / sample_manifest_page_batch.json
- `.company/handoff/codex-image-gen/_sample-run/` — README.md / VERIFICATION.md / dryrun_job/（manifest.json, gen_pages.py, characters/）
- `.company/requirements/ebook-to-manga-codex-handoff/` — REQUIREMENTS.md + QA-phase1/2/3/step55-removal.md

**削除**:
- `.claude/skills/ebook-to-manga/panel_regions.json`（Pillow合成専用）

**運用フロー（次回漫画化案件から）**:
1. ユーザーが `HANDOFF_MODE=codex-handoff` を指定
2. Claude が Step 3-A/5-A/6-A で固定フォルダに manifest 等を配置
3. ユーザーが別ターミナルで `python gen_pages.py` 実行
4. Codex が `DONE.json` 書き出し → ユーザーが「完了しました」と通知
5. Claude が Step N-C で id ベース突合 → OCR/Vision-check → EPUB化

**次回アクション**:
- [ ] **実案件で codex-handoff モード初回動作テスト** — ドライランB（実API 1ページ生成）+ ドライランC（DONE.json戻り受取確認）
- [ ] 動作確認で不具合があれば skill.md 追加修正
- [ ] 本番 vol1 残り約40ページの gpt-image-2 全ページ再生成（推定$15〜20）

**ブロッカー**: なし

---

### 000-E. [COMPLETED 2026-04-23] CLAUDE.md整理 + ebook-to-manga vol1検証 + キャラ欠落バグ修正 ✅

**進捗**: vol1検証 全8工程合格（平均91.6/100）+ page_002キャラ欠落バグ即修正完了 + 恒久対応チケット起票

**実施内容サマリー**:
1. CLAUDE.md 整理（97行→53行、A+B+C案統合）
2. ebook-to-manga vol1冒頭5ページの全工程通し実動作テスト
3. page_002 山田課長イラスト欠落バグ発見→即修正（強化プロンプト+vision check）
4. 恒久対応チケット起票（Step 5-QCにキャラ存在Vision-check追加）

**vol1検証 工程別スコア**:
| 工程 | 内容 | スコア |
|------|------|--------|
| A | Step 1 ソース分析 | 90 |
| B | Step 2 シナリオ | 92 |
| C | Step 3 キャラデザ | 100 |
| D | Step 4 CSV作成 | 95 |
| E | Step 5 画像生成 | 88 |
| F | Step 6 表紙 | 95 |
| G | Step 7 EPUB | 90 |
| H | Step 8 メタデータ | 93 |

**実コスト**: $2.40（vol1検証 $2.17 + page_002再生成 $0.21+OCR）/ 上限$5.00

**発見されたバグと対応**:
- **page_002 キャラ欠落**: gpt-image-2 が4キャラ指示で1人省略（山田課長）→テキスト枠のみ
- **QC構造的穴**: Blind-OCRはセリフなしページをオートPASS→キャラ欠落を検知できず
- **即修正**: 強化プロンプト（4キャラ絶対描画/テキスト枠のみ禁止/山田課長3段目配置必須）+ gpt-4o vision YES/NOチェック → iter_1 で全員YES確認、即採用
- **恒久対応**: Step 5-QC改修チケット起票（コスト影響 +$0.50〜$1.00/冊）

**動作確認できたこと**:
- gpt-image-2 (`images.edit` + 参照画像) で全工程完走
- Blind-OCR (gpt-4o) 連携・Pillowフォールバック機構（page_004で発動）正常動作
- Step 7 glob が `page_*.png` 限定で .jpg 誤収集なし
- コスト試算（$1.92〜$2.55）と実績（$2.17）ほぼ一致

**成果物**:
- `CLAUDE.md` — 整理済み（53行）
- `.company/engineering/docs/ebook-to-manga-vol1-validation-requirements.md` — 検証要件定義書
- `.company/outputs/ebooks-manga/manga-career-restart-validation/vol1/` — 検証出力一式
- `.company/outputs/ebooks-manga/manga-career-restart-validation/vol1/pages/page_002_original_buggy.png` — バグ証拠画像
- `.company/pm/tickets/2026-04-23-ebook-to-manga-step5qc-character-presence-check.md` — 恒久対応チケット
- `C:/Users/fcmdt/regen_page002.py` — page_002再生成スクリプト

**次回アクション**:
- [ ] **起票チケット（Step 5-QCキャラ存在Vision-check）の skill.md 改修着手** — 本番 vol1 全ページ再生成前に必須
- [ ] チケット完了後、vol1 再検証で再現テスト
- [ ] 本番 vol1 のgpt-image-2全ページ再生成（残り約40ページ・推定$15〜20）
- [ ] **Git × Google Drive 共存問題の根本対策** — Phase 1-a/b（broken ref `desktop.ini` 削除 + 残骸 `C:Usersfcmdt...` 削除）は今日対応済み。残: Phase 1-c（gdrive-git-setup.md を実態に合わせて更新）/ Phase 2（`.git/` を `C:/dev/YNFactory-git/` へ移動 = 方法B 適用、Drive 同期停止が必要）/ Phase 3（handoff スキルに mass-deletion 検出ガード追加）。背景: `.git/refs/heads/desktop.ini` 出現で Drive が `.git/` 内まで同期していると判明。今日の commit 6e2017e の 5614 ファイル誤削除も同根因の可能性。詳細は `.company/engineering/docs/gdrive-git-setup.md`

**ブロッカー**: なし

---

### 000-D. [COMPLETED 2026-04-23] ebook-to-manga スキル — gpt-image-2 全面移行 全6工程完走 ✅

**進捗**: 全6工程合格（平均93.3/100） — NanoBanana2 から gpt-image-2 への切替完了、実動作テスト待ち

**背景**: 2026-04-21 OpenAI リリースの ChatGPT Images 2.0（`gpt-image-2`）が日本語テキスト描画大幅改善。昨日の比較で NanoBanana2 継続判断したが、新モデル検証の結果、本文全面切替を決定（案B）。

**確定した最終仕様**:
- 画像生成: `gpt-image-2` via `client.images.edit` + 参照画像、size=1024x1536, quality=high
- プロンプト: 既存構造のまま維持、**追加ルール（縦書き/横書き/オーバーレイ等）一切なし**（2026-04-23方針決定）
- QC: Blind-OCR = `gpt-4o`（OpenAI一本化）
- Pillow合成フォールバック: 保険として維持
- 保存形式: 本文PNG / 表紙JPEG（KDP要件で Pillow 変換明示） / キャラ参照PNG
- 環境変数: `OPENAI_API_KEY` 必須、`GOOGLE_AI_STUDIO_API_KEY` は任意・レガシー併存

**工程別スコア**:
| 工程 | 内容 | スコア |
|------|------|--------|
| 1 | 前提条件・グローバル設定（description、env、フォーマット、コスト表） | 93 |
| 2 | Step 3 キャラリファレンス（google-genai → openai、images.generate） | 97 |
| 3 | Step 5 A路線 + Step 5-QC（images.edit、参照画像抽出、gpt-4o OCR） | 89 |
| 4 | Step 5.5 Pillow合成フォールバック（clean regen API切替、.png統一） | 100 |
| 5 | Step 6 表紙（images.edit、PNG→JPEG変換、KDP要件） | 90 |
| 6 | Step 7 + E2E + 全体整合（glob/MIME更新、Gemini固有名詞汎化） | 91 |

**コスト影響**: $8.60/冊 → $23.55/冊（標準見積もり、上限$34.89/冊）

**実装済み成果物**:
- `.claude/skills/ebook-to-manga/skill.md` — 約1900行、全6工程反映済み
- `.company/engineering/docs/ebook-to-manga-gpt-image-2-migration-requirements.md` — 要件定義書（2026-04-23更新版）
- `.company/outputs/openai-image-gen/vol1-sample/comparison_v2.html` — NanoBanana2 vs gpt-image-2 vs chatgpt-image-latest 並列比較
- `.company/outputs/openai-image-gen/vol1-sample/v2/p*.png` — 検証サンプル5枚（p002/p006/p012/p045 + p045_vertical + p045_overlay）
- `.company/outputs/openai-image-gen/vol1-sample/generate_v2.py` — gpt-image-2 の最小実装例

**次回アクション**:
- [ ] **実動作テスト**: vol1 または vol2 で改修版skill.mdを走らせて動作検証（別セッションで実施予定）
- [ ] 実動作で発見した不具合の skill.md 反映
- [ ] vol1 既存PNG画像の再生成要否判断（別案件・要オーナー判断）

**ブロッカー**: なし

---

### 000-C. [COMPLETED 2026-04-21 impl] ebook-to-manga スキル — ハイブリッドQCパイプライン 本実装完走 ✅

**進捗**: 全6工程合格（平均92.7/100） — 実装フェーズ完了、実動作テスト待ち（→ 000-D で gpt-image-2 移行も追加実装済み）

**実装済み成果物**:
- `.claude/skills/ebook-to-manga/panel_regions.json` — 新規作成（テンプレ1〜7、正規化比率0〜1、コマ位置定義）
- `.claude/skills/ebook-to-manga/skill.md` — 1010行 → 約1900行（約900行追加/改修）
  - Step 4: `コマ別テキストJSON` 列追加（panel_id/type/speaker/text）
  - Step 5: ハイブリッドループ全面改修（疑似コード + パラメータ表 + 命名規則 + コスト試算）
  - Step 5-QC（新規・約155行）: Blind-OCR判定モジュール仕様
  - Step 5.5（新規・約302行）: Pillow合成フォールバック仕様
  - Step 7: EPUB PNG→JPEG統一、下流互換性対応表
  - 末尾: E2E動作確認手順セクション（6項目+合格基準）
- `.company/engineering/docs/ebook-to-manga-hybrid-qc-requirements.md` — 要件定義書

**工程別スコア**:
| 工程 | 内容 | スコア |
|------|------|--------|
| 1 | panel_regions.json作成 | 97 |
| 2 | Step 4 CSV拡張 | 88 |
| 3 | Step 5-QC Blind-OCR仕様 | 95 |
| 4 | Step 5.5 Pillow合成仕様 | 91 |
| 5 | Step 5 ループ改修（1回修正） | 97 |
| 6 | E2E整備・整合性レビュー | 88 |

**実装効果**:
- 合格率 100% 保証（A+Bハイブリッド）
- コスト $8.60/冊（現行$6.25 + 追加$2.35）、上限 $9.0/冊
- 手動再生成プロセス不要（自動ループ + フォールバック）

**軽微な残課題（Phase 2 or 次回実装時）**:
- E2Eセクション内のパス記法統一（`pages/` vs `panels/pages/`）
- フォールバック発動確認手順の具体化（プロトタイプ書換 or スキル実行時引数）
- 顔検出による吹き出し位置最適化（要件定義で Phase 2 送り決定済）

**次回アクション候補**:
- [ ] **実動作テスト**: 既存の `manga-career-restart/vol1` で改修版 skill.md を走らせて動作検証（推奨・最優先）
- [ ] 実動作で発見した不具合を skill.md に反映
- [ ] 別タスクへ移動: Meta SNS続き / YN Factory SNS画像 / Sales OS朝承認 など

**ブロッカー**: なし。実動作テストか別タスクかはオーナー判断次第

---

### 000-B. [2026-04-21 evening] Meta SNS自動投稿セットアップ — Step5（ユースケース追加）で中断

**リクエスト**: Instagram / Facebook / Threads への自動投稿を `post-sns` スキルから実行できるようにする

**完了済み**:
- Step1 FBページ `YN Factory` 作成（カテゴリ=出版社）
- Step2 IG ↔ FBページ連携
- Step3 Meta開発者アプリ `YN Factory SNS Poster` 作成
  - App ID: `1747727225992867`
  - ビジネスポートフォリオ: `nakada_yuichi` に紐付け
  - ユースケース: 「ユースケースなしで作成」を選択

**中断位置（ここから再開）**:
- Step5: ダッシュボードの `+ Add use cases` をクリック → 左フィルターで「コンテンツ管理」を選択 → Instagram / Facebook Page / Threads 系のユースケースを追加
- 現UI はユースケース経由で製品（IG API / FB Login / Threads API）が追加される方式

**残タスク**:
- Step5: ユースケース追加（IG/FB/Threads投稿系）
- Step6: Graph API Explorer でアクセストークン取得
- Step7: 長期アクセストークン化 + Page Access Token取得
- Step8: `.company/engineering/sns-credentials/.env` に `META_APP_ID` / `META_APP_SECRET` / `META_ACCESS_TOKEN` / `FB_PAGE_ID` / `IG_BUSINESS_ACCOUNT_ID` / `THREADS_USER_ID` / `THREADS_ACCESS_TOKEN` 追記
- Step9: `scripts/post_to_meta.py` 実装（IG / FB / Threads 対応）
- Step10: `.claude/skills/post-sns/SKILL.md` の対応状況を Phase 2 完了に更新

**前提アカウント状況**:
- IG: ビジネスアカウント / Threads: IG紐付け済
- FB: 個人アカウント → `YN Factory` ページ作成済（法人格なし）

**関連メモ**: `~/.claude/projects/g---------YNFactory-cc/memory/project_meta_sns_setup.md`

---

### 000-A. [NEW 2026-04-21 morning] YN Factory SNS紹介画像 — ブレスト Q5で中断、再開待ち

**リクエスト**: YNファクトリーの紹介をSNSに投稿するための文字付き画像を作成したい

**決定済み要件**:
- 投稿先: **Instagram ストーリーズ/リール（9:16 縦長）**
- メッセージ軸: **会社紹介＋提供サービスの紹介（A＋B）**
- トーン&マナー: **温かみ・想い重視（ベージュ×ブラウン系、筆記体混じり）**（C案）
- 情報源: 公式サイト https://www.ynfactory.online/ （WebFetchで以下確認済）
  - 事業: 電子書籍出版プロデューススタジオ（著者・起業家・講師・経営者向け）
  - キャッチコピー: 「"本を出している" という事実が、あなたの最強の名刺になる」「一生モノの信頼に」
  - サービス3本柱: 電子書籍出版プロデュース / マンガ×ストーリーデザイン制作 / SNS・LPプロモーションサポート
  - 連絡先: TEL 050-5367-2629 / 名古屋市中区栄二丁目2番1号 / LINE・メール無料相談窓口

**未確定の残論点（次回ここから再開）**:
- Q5: 1枚の構成パターン選択
  - A) キャッチコピー主役型（上:ロゴ / 中:大キャッチ / 下:3サービスアイコン+URL）
  - B) ストーリー型（上:「想いを、一冊に。」 / 中:本のビジュアル / 下:会社紹介+URL）
  - C) サービス一覧型（上:ロゴ+一言 / 中:3サービス詳細 / 下:無料相談+URL）
  - D) 組合せ or 別案
- Q6以降: フォント選定・配色詳細・CTA文言・複数枚カルーセル化の要否・画像生成方法

**想定する次のステップ**:
1. Q5で構成選択 → 具体レイアウト確定
2. nanobanana2-image-gen スキルで画像生成 or Canva MCP で下地作成 → テキストオーバーレイ
3. 最終確認 → post-sns スキルで投稿（承認後）

**成果物**: なし（実装未着手）。ブレスト内容は本 HANDOFF.md と会話履歴のみに存在

---

### 00. [UPDATED 2026-06-23] Sales OS — 軸C 初回1通送信済み（自動本番送信は未解放）

> **【2026-06-23 初回本番送信完了】**
> - Peatix公開イベント: `https://ai-webinar-20260715.peatix.com/view`、問い合わせ先 `y-nakada@yn-factory.com`、Google Meet表記で公開済み。
> - Calendly個別相談: `https://calendly.com/y-nakada-yn-factory/30min-consult`、Google Meet連携で公開済み。
> - 初回送信: TDC向け Queue ID `282` をオーナー承認後に1通上限で送信。Gmail API未有効で一度ブロックされたが、Google Cloud project `YN Tools` の Gmail API 有効化後に再送成功。
> - 送信証跡: 宛先 `tdc@mirror-polish.com`、Gmail message id `19ef20982a6e1bc5`、sent_at `2026-06-23T01:12:50.675619` UTC、`approval_queue.status='sent'`、`conversations` conversation_id `1`。
> - 安全状態: VPS `.env` は `SALES_OPS_DRY_RUN=true` のまま。自動送信cronはなし。02:00 list_builder / 02:30 personalizer は dry_run で正常実行確認。
> - 追加整備: DMテンプレート3種とVPS fallbackに `配信停止` 明記の停止表記を反映。
> - 次アクション: 返信・Peatix申込・Calendly予約の確認。追加送信は候補選定→本文確認→オーナー承認→手動1件ずつの順で進める。

> **【2026-06-09 大幅更新】営業オペレーティングシステムを新規構築（/goal セッション・Mac）**
> - **背景**: 上記Phase 1は完成済だが2026-05-04以降 約5週間休眠（DRY_RUN/本番GO待ち/ウェビナー未開催/成約ゼロ）。本質的課題は『新機能』でなく『確実なローンチと毎週の前進』。
> - **構築物（全6点＋入口、要件定義→executor→quality-checkerで85点以上合格）**:
>   - 入口/全体マップ: `.company/sales/SALES_SYSTEM.md`（次回・別PCはここから）
>   - 営業戦略書: `.company/sales/STRATEGY.md`（87・正本）
>   - 起動チェックリスト: `.company/sales/LAUNCH_CHECKLIST.md`（90・休眠システムを1hで本番起動）
>   - 商談導線: `.company/sales/system-2026-06/booking-ops/`（7ファイル・88・商談以外を自動化）
>   - 運用リズム: `/weekly-sales-review`スキル ＋ `.company/sales/daily-ops-checklist.md` / `weekly-review-checklist.md`（91・停滞防止4仕掛け）
>   - KPI: `.company/DASHBOARD_SALES.md`（88）
>   - 早期リード: `.company/sales/EARLY_LEADS_PLAYBOOK.md`（86・人脈ゼロからの5打ち手）
>   - 要件定義: `.company/requirements/sales-system-2026-06/REQUIREMENTS.md`
> - **戦略**: 高単価AIコンサル（AI活用アドバイザー）×キャリコン差別化×週5h商談集中。ICP=地方(首都圏除く)・従業員30-100名・士業/制作/製造等。
> - **KGI再設定（オーナー承認2026-06-09・3ファイル一致）**: 7/31までに商談3〜5件＋士業パートナー接触1〜2件＋広告/LM稼働＋DM累計100通、ウェビナー1回(7/15)、**初契約9/30**、MRR20万(12/31)。
> - **重要発見**: オーナーに温かい人脈ゼロ→早期リードは士業パートナー化(最優先)・有料広告・リードマグネット等のコールドスタートに再設計（EARLY_LEADS_PLAYBOOK.md）。
> - **2026-06-23時点の実システム状態**: conversationsはQueue ID 282について手動記録済み。ウェビナー/予約URLは実URL反映済み。From/Reply-To/署名/問い合わせ先は `y-nakada@yn-factory.com` 運用に統一。
> - **次アクション(オーナー承認制)**: 初回送信後の反応確認（返信・Peatix申込・Calendly予約）＋追加送信候補の選定。追加送信は本文確認後、手動1件ずつ明示承認で進める。士業パートナー勧誘は「今日やらない」に退避中。
> - VPS等の技術詳細・環境変数・API構成は下記の旧ステータス参照（不変）。


**本日2026-04-20の進捗サマリー**:
- 本日02:00 list_builder.py 自動稼働 → 37社新規取得（T2士業・制作会社）、累計167社
- 本日02:30 personalizer.py 自動稼働 → 50件DM下書き生成、DRY_RUN=true で実送信ゼロ（conversations=0件確認）
- ⚠️ **バグ発見**: 生成DM全件が「YNファクトリー代表のオーナーと申します」という誤署名。`run_personalizer.py` が `Personalizer(sender_info=...)` を渡さずデフォルト値（`owner_name="オーナー"`）にフォールバックしていた（commit 3193bf9 で sender_info パラメータは追加されたが、呼び出し側更新が漏れていた）
- ✅ **修正 commit 264920d**: Config に owner_title/owner_contact_email 追加、run_personalizer.py で sender_info を cfg から構築して注入。`scripts/reset_drafts.py` + `scripts/retry_single.py` を運用用ワンショットとして追加
- ✅ VPS 反映（`/opt/sales-ops/src/core/config.py.bak.20260420` + `run_personalizer.py.bak.20260420` にバックアップ取得済み）
- ✅ 誤署名50件を rejected へ退避 → re-personalize 実行 → 49/50件成功 + needs_retry 1件（マナブデザイン㈱ id=32）も retry_single.py で手動リトライ成功 → 全50件 pending、全件「中田雄一」署名＋ info@yn-factory.com Reply-To ＋特電法フッター確認
- ✅ Saxo Simトークン更新（ローカル `ai-trade-system/.env` + VPS `/opt/ai-trade-system/.env`、コンテナ `up -d --force-recreate` → ForwardScheduler 稼働 → HTTP 200 OK 確認、次回失効 2026-04-22 21:47 JST、2026-04-21 21:51 実施）
- ✅ `.claude/settings.local.json` に `autoMode.allow`/`soft_deny` 追加 — VPS 163.44.101.31 への読み取り専用SSH（tail/ls/crontab -l/grep/docker logs 等）を恒久許可、.env等secretsの読み取りは soft_deny で拒否

**現在のDB状態**（2026-04-20 23:40 JST時点）:
- companies: drafted 50 / new 117（合計167社）
- approval_queue (track=c): pending 50 / rejected 50（破棄済み誤署名）/ sent 1（過去ローカルテスト分）

**明日以降の流れ**:
- 02:00 list_builder cron → 残117社 new + 新規T1/T2追加で personalizer の対象が増える
- 02:30 personalizer cron → 修正後コードで正しい署名でドラフト生成される
- オーナーは /sales-briefing スキル経由で翌朝承認フローに入る（DRY_RUN=trueのまま）

---

#### 旧ステータス（参照用）: Phase 1 VPSデプロイ完了（本番稼働開始待ち）
- **状態**: 実装完了、VPSデプロイ完了、明日02:00から自動稼働、DRY_RUN=true で安全側待機
- **目的**: 法人AIコンサル（軸C）アウトバウンド営業の自律化、KGI 2026-06-30 MRR 20万円
- **ターゲット**: T1（中小経営者）+ T2（士業・制作会社）、オファー O3 yn-tools法人プラン月2000円 → O1 AI顧問アップセル
- **コード**: `sales-ops/` プロジェクト (全10タスク平均97.6点合格 / 29テスト全合格)
- **設計書**: `.company/engineering/docs/sales-ops-design.md`
- **実装プラン**: `.company/engineering/plans/2026-04-19-sales-ops-phase1-plan.md`
- **CEO判断**: `.company/ceo/decisions/2026-04-19-sales-ops-launch.md`
- **スキル**: `/sales-briefing`（毎朝の承認UI、Phase 1は軸Cのみ対応）
- **VPS本番環境**（ConoHa 163.44.101.31、ばんえいと同居）:
  - コード: `/opt/sales-ops/`
  - venv: `/opt/sales-ops/venv/` (Python 3.10.12)
  - secrets: `/opt/sales-ops/secrets/gmail_client_secret.json` + `gmail_token.json` (chmod 600)
  - .env: `/opt/sales-ops/.env` (chmod 600、.env参照: APIキー3種)
  - DB: `/opt/sales-ops/data/sales_ops.db`（130社スキャン済）
  - ログ: `/var/log/sales-ops.log`
  - cron: `0 2 * * *` list_builder / `30 2 * * *` personalizer
  - DRY_RUN=true / DAILY_SEND_LIMIT=5（安全側）
- **API構成**: Anthropic API(Sales OS Key)、Google Maps Places API (New, yn-tools GCP project)、Gmail OAuth(yuichi4107@gmail.com 認証、Desktop App type, scope=gmail.send)
- **送信者情報**: OWNER_NAME=中田雄一 / OWNER_COMPANY=YNファクトリー / OWNER_CONTACT_EMAIL=info@yn-factory.com（info@はy-nakada@yn-factory.com Workspaceのエイリアス） / OWNER_WEBSITE=https://tools.ynfactory.online
- **次回最優先アクション**:
  1. **送信From表示の修正**: 現状 `yuichi4107@gmail.com` 送信、署名とReply-Toのみ `info@yn-factory.com`。プロ仕様にするには:
     - 案A: Google Workspace admin.google.com で IMAP/SMTP 有効化 → Send mail as エイリアス設定（前回535エラーで未完）
     - 案B: Workspace OAuth（y-nakada@yn-factory.com 認証）再挑戦（前回ブラウザエラー未特定）
     - 案C: そのまま運用（From が gmail.com のまま、Reply-To と署名は info@yn-factory.com）
  2. 本番最小検証: DRY_RUN=false + DAILY_LIMIT=1 で自分宛に1通送信してFromヘッダ・特電法フッター・返信到達を目視確認
  3. DAILY_LIMIT段階引き上げ: 5→30→50→100
  4. Phase 2プラン作成（軸A フリーランス + 軸B コンテンツ）
- **ブロッカー**: なし（cron稼働待ち、明日朝にログ確認必要）

### 0. [NEW 2026-04-18] AI投資システム ショート戦略導入 — Phase1全工程合格+Phase2工程6まで完了（本番投入API Key待ち）
- **状態**: コード実装完了（Phase2 工程1-6合格）、工程7（本番最小額検証）のみユーザー作業待ち
- **対象**: `ai-trade-system/` 既存ロング戦略（BTC/ETH/SOL/XRP × 3戦略）に加えてショート戦略追加
- **Phase 1（バックテスト検証）結果**:
  - 12ケース（4通貨×3ショートパターン）Gemini判定+optimizer.py 792通りグリッドサーチ
  - **合格戦略**: `rally_top`（ETH・XRP で PF>1.3 & DD<30% & Calmar>0.5 充足）
  - **採用候補3戦略** (DD≤30%制約下):
    - ETH-USDT rally_top: TP=None, SL=0.5%, Hold=15 → PF 2.12 / DD 28% / Calmar 1.930
    - XRP-USDT rally_top: TP=2%, SL=None, Hold=25 → PF 4.84 / DD 8.76% / Calmar 9.457 ★最優秀
    - XRP-USDT double_top: TP=1%, SL=None, Hold=30 → PF 4.89 / DD 10.95% / Calmar 3.895（戦略合否は不合格だがXRP単独で採用）
  - **見送り**: BTC全ショート（上昇相場バイアスで PF<1.3）、SOL全ショート（DD≤30%下で収益性不足）
  - 最終レポート: `ai-trade-system/docs/short-strategy-phase1-report.md`
- **Phase 2（本番発注対応）実装完了**:
  - 新規ファイル: `src/trading/futures_exchange.py`（Binance Futures ラッパー、レバ1倍/ISOLATED固定、open_short/close_short）, `src/ai/prompts/rsi_overbought_reversal.txt` + `rally_top.txt`, `tests/test_phase2_dryrun.py`（5件単体テスト）
  - 変更ファイル: `strategy_config.json`（ショート12戦略追加+採用3件enabled/不採用9件disabled）, `trend_filter.py`（is_uptrend/check_short_trend_filter 追加）, `position_manager.py`（direction='long/short'対応、既存ロング完全非破壊）, `scanner.py`（direction分岐+enabledフィルタ）, `trader.py`（_enter_short_position + 安全装置）
  - **安全装置**: MAX_CONCURRENT_SHORT_POSITIONS=3、DAILY_SHORT_LOSS_LIMIT_PCT=-5.0%、SL/TP両方Noneブロック、dry-runモード二重チェック、レバ1倍+ISOLATED強制
  - dry-run検証: 5件単体テストALL PASS + 実スキャンでETH rally_top ショートシグナル検出確認
- **次回最優先アクション（工程7: 本番最小額検証）**:
  1. Binance Futures Testnet で API Key 発行: https://testnet.binancefuture.com/
  2. `ai-trade-system/.env` に追加:
     ```
     BINANCE_FUTURES_TESTNET_API_KEY=<testnet key>
     BINANCE_FUTURES_TESTNET_SECRET=<testnet secret>
     ```
  3. Testnet で残高取得→発注→決済の1サイクル検証
  4. 本番 API Key 発行（https://www.binance.com/en/my/settings/api-management Futures権限）と `.env` に BINANCE_FUTURES_API_KEY/SECRET 追加
  5. 本番20 USDT × レバ1倍 × 1件で最小額検証（明示的承認必須）
- **全工程スコア**: Phase1 (92/97/100/88/93), Phase2 (98/100/100/88/98/93) — 全工程85点以上合格
- **ブロッカー**: Binance Futures API Key（ユーザー側で発行・設定）

### 0a. [NEW 2026-04-18] ばんえい予想システム VPSフルデプロイ — 本番稼働開始（完全自動化）
- **状態**: VPS本番稼働中、本日10:53に初配信成功、13:50以降は完全自動
- **本番環境**: ConoHa VPS `/opt/keiba-unified/keiba-ai-system/`（ホスト 163.44.101.31）
- **背景**: シーズン新スタート4/17の配信漏れ原因調査 → 配信基盤自体が3/27以降停止（Windows/VPSどこにも稼働環境なし）していたことが判明
- **実施内容**:
  1. `config/race_calendar.json` を令和8年度公式PDFから正しい149日分に置換（帯1〜25、meets配列追加）
  2. `scripts/check_race_day.py` の `get_race_type()` をハードコード→meets参照型に書き換え（境界判定正確化）
  3. VPSにPython3.10venv + 依存 + モデル + .env全一式scp転送
  4. `scripts/run_banei.sh` ラッパー作成、cron 7ライン登録（nighter/semi_nighter/twilight各2本 + collect 1本）
  5. `.env` source + venv絶対パス化で collect_results.py のTelegram Token伝搬も確保
- **cron時刻**（race_typeに応じて自動分岐）:
  - 前半予想: ナイター13:50 / 準ナイター13:15 / 薄暮12:30
  - 後半予想: ナイター16:20 / 準ナイター15:45 / 薄暮15:00
  - 結果収集: 毎日22:30（非開催日はrun_banei.shが自動スキップ）
- **ログ**: `/var/log/keiba-banei.log`
- **Telegram**: 配信確認済み（ユーザー目視）
- **今後の開発ルール**: ばんえい系のコード/設定/モデル修正は必ずVPSに反映（ローカルG:\\は非稼働のコピーのみ）
- **残務**: なし（本件クローズ）

### 0b. [NEW 2026-04-16] note記事 4箇所集約 — 完了（commit efae6e5）
- **状態**: 集約完了・commit済み・運用開始OK
- **新統合ルート**: `.company/outputs/note-articles/`
  - `README.md` — 全23本目次・公開スケジュール・アセット対応表
  - `series-01-ai-side-business/` — AI副業シリーズ 9記事 + 投稿ガイド_記事06-09.md + images/
  - `series-02-freelance/` — フリーランス副業シリーズ 14記事（2026-04-13〜27公開予定）+ images/ + generate_images.py
  - `assets-covers-bodies/covers/` — 7記事分カバー画像
  - `assets-covers-bodies/bodies/` — 7記事分本文画像 a/bパターン
- **パス書き換え**: series-02内 記事7本の bodies/ パス + generate_images.py の OUTPUT_DIR
- **移動元削除状況**:
  - 削除済み: tech-articles/note-series/, note-series-covers/, note-series-bodies/
  - 残存: ai-side-business/note-articles/images/ (空ディレクトリ、Google Drive Permission deniedで削除不可、次回エクスプローラーから手動削除)
- **品質**: 工程1=92点PASS / 工程2=95点PASS

### 0. [NEW 2026-04-16] Instagramストーリーズ Batch2（30本）— 画像生成完了（2026-04-17）
- **状態**: prompts.md / concepts.md / 30枚PNG 全て納品完了
- **成果物**:
  - `.company/outputs/instagram-stories/batch-2026-04-15/prompts.md` (608行 / 53KB, 30本)
  - `.company/outputs/instagram-stories/batch-2026-04-15/concepts.md` (30本テーマ一覧+重複チェック)
  - `.company/outputs/instagram-stories/batch-2026-04-15/post_01〜30_*.png` (30枚完了)
  - `.company/outputs/instagram-stories/batch-2026-04-15/generate_batch2.py` / `generate_log.txt`
- **仕様**: 46歳男性キャリコン / 転職・キャリア（40代向け）/ 10日×朝昼夜 / 前回(2026-03-10) Batch1との重複なし
- **品質チェック結果**:
  - 工程1（コンセプト設計）: 86/100 PASS
  - 工程2（プロンプト+原稿）: 初回 77/100 FAIL → 修正後 96/100 PASS
- **投稿運用**: 手動投稿で運用（オーナー判断、2026-04-17確定）
- **残タスク**: なし（クローズ）
- **QAからの軽微な残件**（次回Batch時の参考メモ）:
  - Post 25（7:00朝）の`cool fade`指定は`warm fade`が本来（朝=warm設計）
  - Post 18の締め文が21文字で他(7-10字)より突出
  - Post 24（19:00夜）は情報提供型で夜の内省トーンとやや乖離

### 1c. [NEW] 日本株デイトレ戦略 `jp-stock-daytrade` — 要件定義承認・工程0完了（91点PASS）
- **状態**: 要件定義承認済み、工程0（データ基盤）実装完了91点PASS、J-Quants認証情報で保留中
- **最新セッション成果（2026-04-15）**:
  - 要件定義書承認（AP1完了）: `.company/engineering/docs/jp-daytrade-v1-requirements.md`
  - 工程0実装完了: `jp-daytrade/` 新規プロジェクト、74テスト全通過
  - quality-checker 91点 PASS → 工程1進行可
  - 三菱eスマート信用取引口座申込完了
- **工程0で生成した主要ファイル**:
  - `jp-daytrade/data/jquants_client.py` — J-Quants API クライアント（認証待ち）
  - `jp-daytrade/data/kabu_mock.py` — FastAPI モックサーバー、5シナリオ対応
  - `jp-daytrade/data/kabu_push_recorder.py` — 気配スナップショット保存
  - `jp-daytrade/data/universe_builder.py` — 値嵩株フィルター
  - `jp-daytrade/data/schemas/*.sql` — stocks_master/daily_prices/quotes_live
  - `jp-daytrade/data/setup_db.sh` / `.bat` — DB初期化（9〜17秒）
  - `jp-daytrade/tests/*.py` — 74テスト全通過
- **J-Quants認証情報の保留（解消 2026-04-18）**:
  - 前回400 incorrect だった根本原因判明: J-Quants API は **V1 → V2 へ移行中**で、V2 は `email+password → refresh_token` 方式を廃止。ダッシュボード発行の API Key を `x-api-key` ヘッダー直接認証に一本化されていた
  - 今セッションでの対応（全完了）:
    - ダッシュボードで Free プラン契約 → API Key 再発行（`C-4wHtaX...`）
    - `jp-daytrade/data/jquants_client.py` を V2 対応に全面書き直し（base URL `/v2`、`x-api-key` ヘッダー、endpoint `/equities/master` `/equities/bars/daily` `/markets/calendar`、5桁銘柄コード正規化、pagination_key 対応、401/403 → JQuantsAuthError）
    - 認証ヘルパー `jp-daytrade/scripts/jquants_auth_helper.py` を set-token / test の2サブコマンドに簡略化
    - 新 API Key を `config/.env` の `JQUANTS_API_KEY` に保存（旧 `JQUANTS_REFRESH_TOKEN` はコメントアウトで legacy 保持）
    - テスト更新: 17/17 V2テスト + 62 その他、**合計 79/79 PASS**
    - 疎通確認: master 4,435 銘柄 / グロース 612 銘柄 / Toyota 日足19行（Feb 2024）までDB書き込みまで成功
  - **Freeプラン制約**: データ取得可能期間は `2024-01-24 〜 2026-01-24`（直近3ヶ月は遅延）→ 過去データでのバックテストには十分
  - **fetch_all_growth 実行完了（2026-04-18 16:11）**: グロース612銘柄×2年分 **全件取得完了**・失敗0件
    - daily_prices.db: 612 codes / **275,899 rows** / 2024-01-24〜2026-01-23 / 25.3MB / integrity OK
    - stocks_master.db: 4,435 銘柄（グロース612、last_price 全件埋め込み済） / 0.7MB
    - 実行時間: 11:29〜16:11 ＝ 約4時間42分（Rate Limit 667回発生、全て exponential backoff でリカバリ成功）
    - `request_interval=6s`、`max_retries=6`、429 時は指数バックオフ 5→10→20→40→80→120s
  - **重要なDB配置方針（要遵守）**:
    - **SQLite DB は Google Drive 配下に置かない** — 書込中に Drive 同期が干渉して `database disk image is malformed` で破損する実害発生（初回 483/608 銘柄で破損）
    - 本番DB配置: `C:/dev/jp-daytrade-data/` (ローカルディスク)
    - 環境変数 `JP_DAYTRADE_DATA_DIR` で指定（`jp-daytrade/config/.env` に設定済）
    - 他PC（Mac Mini/Surface等）からのアクセスは不可 → Phase 2以降でVPS移管または共有DB化検討
  - **工程1（バックテストエンジン）実装完了(2026-04-19) → BT結果合格基準未達 → 戦略ピボット検討へ**:
    - 生成物: `jp-daytrade/strategy/config.py` / `strategy/screener.py` / `backtest/engine.py` / `backtest/run_backtest.py` / `backtest/results/bt_report_v1.md` / `backtest/results/trades_v1.csv` / `tests/test_screener.py` / `tests/test_engine.py` (36テスト PASS)
    - BT結果（612銘柄×1045取引）: **勝率13.88% / PF 0.492 / シャープ -5.364 / 最大DD -95.92%** — 合格基準全て未達
    - 原因: F5(GAP率)プロキシのみでは「GAP上げ→即押し戻し」銘柄を除外できず、SLヒット率83%になった。F6(寄り前売買比率)/F7(板厚み)がバックテスト不可（J-Quants Freeは日足のみ）が根本要因
    - コード品質自体はOK: 先読みバイアスなし、スリッページ補正済み、再現性OK、36テスト全PASS
  - **化け株分析セッション（2026-04-19）で判明したパターン**:
    - **古河電工(5801)**: 底値3647→12520(+234%) 主要カタリスト=光部品事業黒字化/AI-DC需要/13824心ケーブル量産/中計説明会(5/13急騰)/2Q上方修正+水冷モジュール増強(11/13急騰)
    - **化け株TOP**: 三井金属+360%(底→高値+605%レアアース主役)/サンバイオ+184%(+5%日42日のイベント駆動)/IHI+184%(防衛主役)/アドバンテスト+134%(+408%)/レーザーテック+137%
    - **最大発見**: 2025-04-08/10(関税ショック反発)に19/19銘柄が全員+5%以上 → **マクロパニック逆張り戦略は勝率ほぼ100%**
    - **セクター連動強度**: AI半導体(6回)>防衛(5回)>レアアース(2回)=半導体装置(2回)>バイオ(0)、海運は除外推奨
    - **「寄り弱→場中爆騰」パターン**: 東邦チタニウム2025-06-12 +15.9% gap-0.2% vol_x20 **20.7倍**、サンバイオ2025-10-02 +20.6% gap-0.7% など → 日足では予測不可能だが、vol_x20 ≥ 10の翌日追従で捕捉可能
    - 生成データ: `C:/dev/jp-daytrade-data/case-study/*.csv` (19銘柄×1年日足)、`C:/dev/jp-daytrade-data/5801_furukawa.csv`、`C:/dev/jp-daytrade-data/earnings_calendar.csv`(Free翌日2件のみ)
  - **Free プラン V2 API の追加制約判明**:
    - `/equities/bars/daily` は **1リクエスト最大約1年範囲**（2年指定すると400エラー）
    - `/equities/earnings-calendar` は**翌日分のみ**返却（過去履歴取れず） → 代替: `/fins/summary` の DiscDate から個別取得
  - **次回最優先（戦略ピボット候補3本）**:
    1. **マクロパニック逆張り戦略**: 日経-3%以下の翌日にテーマ銘柄を寄り成り → 2025-04-08/10実績で勝率ほぼ100%確認済み（BT対象サンプルは年数回）
    2. **出来高爆発追従戦略**: vol_x20 ≥ 5 AND 陽線 → 翌日寄り成り、2-10営業日スイング（サンプル数多い）
    3. **セクター連動追従戦略**: 同日同セクター3銘柄以上+5%をトリガーに翌日出遅れ銘柄買い
    - いずれも Free プラン日足データで完全にBT可能
- **工程0で発見した軽微バグ（工程3で修正推奨、工程0合格には影響なし）**:
  - `run_polling()` 時間窓判定が 9:00-9:59 も処理対象（`RECORD_END_HOUR + 1` 設計ミス）
  - `JPDaytradeError` 基底クラスが jquants_client.py と kabu_push_recorder.py で重複定義 → `jp_daytrade/exceptions.py` 集約推奨
- **運用方針（2026-04-15確定）**:
- **戦略名**: JP-DAYTRADE-v1（寄り前気配×板厚み戦略）
- **ブローカー**: 三菱eスマート証券（旧auカブコム、2024/11ブランド変更）、口座開設済み
- **API**: kabuステーションAPI — **未有効化**（オーナー作業必要、三菱eスマートマイページから申込）
- **常駐PC**: Surface（Windows）、既存ConoHa Linux VPSとは別系統
- **戦略仕様（確定）**:
  - ユニバース: グロース市場中心、値嵩除外（株価3,000円以下 かつ 単元代金30万円以下）、特別気配銘柄除外
  - スクリーニング: 8:45-8:59確定気配で、売気配株数 > 買気配株数 × 板厚み＋複合フィルター（GAP率/前日出来高/材料フラグ/気配更新履歴）
  - エントリー: 8:59 寄り成り注文、リスク等化配分、同時保有最大5銘柄
  - 利確: +5〜10%、損切: -1〜-2%、大引けクローズ 15:25成行
  - リスク管理: 日次-5% or 3連敗で取引停止、現物のみ
- **運用段階（リサーチ推奨）**:
  - Phase 0: シグナル検知のみ自動・Telegram通知→手動発注（月0円）※秘書は3銘柄スモールスタート推奨、オーナー判断5銘柄も可
  - Phase 2: Surface据置＋UPS、自動発注（月0円）
  - Phase 3: KAGOYA Windows VPS（月2,420円、SLA 99.999%）
- **リサーチ主要発見**:
  - +5〜10%利確はグロース小型株/材料銘柄/低位株/IPO直後/ストップ高連鎖の5カテゴリ限定
  - 売/買気配比単独では不十分、複合フィルター必須
  - kabu APIヒストリカル配信なし → PUSH APIで自前保存 or J-Quants併用でバックテスト用データ整備必須
  - 日本株個人向けREST+PUSH APIは実質kabu一択
- **成果物**:
  - CEO判断: `.company/ceo/decisions/2026-04-15-jp-daytrade-research.md`
  - PMチケット: `.company/pm/tickets/2026-04-15-jp-daytrade-research.md` (status: done)
  - リサーチ5本: `.company/research/topics/jp-daytrade-0{1-5}-*.md`
- **運用方針（2026-04-15確定）**:
  - **Phase 0**: 三菱eスマートkabu APIでデータ取得・シグナル検知（自動）→ Telegram通知 → **SBI証券で手動発注**（既存SBI資金活用、3銘柄手動運用で戦略検証）
  - **Phase 2以降**: 三菱eスマート完結型、API自動発注に移行（5銘柄拡張、信用手数料0円のメリット享受）
  - **資金移動**: SBI検証資金 → 三菱eスマートはPhase 2移行時（勝率確認後）
- **オーナー着手アクション**:
  1. ✅ **三菱eスマート 信用取引口座の開設申込完了**（2026-04-15 申込、審査3〜7営業日、開設完了予想 2026-04-18〜2026-04-24、Professional自動適用待ち）
  2. Surface環境準備（Windows 10/11 + .NET、kabuステーションダウンロード準備）
- **次のアクション（開発）**:
  1. requirements-definer起動（Phase 0開始銘柄数3 or 5最終判断、工程分割、中間成果物・品質基準定義）
  2. executorで工程0=データ基盤から着手（信用口座開設審査中の期間を活用）
- **SBI証券の自動発注について**: 公式API個人向けなし、Selenium等は利用規約違反。Phase 0は手動、Phase 2以降は三菱eスマート完結自動化に収束する方針で合意済み

### 1. AI投資戦略 — 本番稼働中（BTC/JPY）+ シミュレーション記録中 ★残高不足バグ修正済
- **状態**: 本番デーモン稼働中、オープンポジションなし + シミュレーション記録稼働中
- **2026-04-21 更新**: 塩漬けcrash_reboundポジション手動決済(+1,081円/+7.21%)、売却残高不足バグを案A+B最小diffで恒久修正、VPS反映・commit f35fe6f 完了。累計実現PnL +1,537円/3トレード
- **2026-04-09**: MS4チケット（Coincheck本番移行）を`done`にクローズ。全完了条件クリア確認済み。DASHBOARD進捗100%に更新
- **現在のポジション（実）**: なし（crash_rebound 2026-04-21 22:18 手動決済 @ 12,123,047円）
- **Coincheck残高**: JPY 約21,228円（5,160 + 売却代金約16,068）/ BTC 0（取引単位: 15,000円/トレード）※最新残高はVPS APIまたはCoincheckアプリで要確認
- **残高不足バグ修正内容（2026-04-21）**:
  - 症状: 買付時の手数料控除で実BTC残高(0.00132648)が記録amount(0.00133)より少なく、HOLD EXPIRED時に毎4時間 market_sell が `Amount has insufficient BTC balance` で失敗→21日間ループ→塩漬け
  - 案A: `ExchangeClient.fetch_base_balance(symbol)` 新設、`_enter_position` で market_buy直後にamountを実残高で上書き
  - 案B: `_close_position` で `min(pos.amount, 実残高)` を使用。全クローズパス(SL/TP/HOLD/MANUAL)共通で効く。`hasattr` ガードで他取引所壊さず
  - VPS本番反映済: /opt/ai-trader/ 最小diff適用 + ai-trader-coincheck 再ビルド&Up確認、Exception無し
  - ローカルcommit: f35fe6f（ai-trade-system 2ファイル+54/-1、pytest 99件全PASS）
  - **注意**: VPSに旧工程2で転送した `oanda_client.py` / `saxo_client.py` が rm権限拒否で残存。旧trader.pyがimportしないため起動無影響、次回メンテで削除検討
- **本日の修正・追加（2026-04-06）**:
  - **SSH鍵再登録**: `conoha_ed25519` がVPS側のauthorized_keysから消失していた → paramiko経由でパスワード認証して再登録
  - **CoincheckSLバグ修正**: `exchange.py` の `stop_loss_order` でCoincheckの逆指値注文が通常の指値売りとして即約定していた問題 → Coincheckの場合は早期return(None)して自前監視にフォールバック
  - **positions.json修正**: crash_reboundをclosed化（実際にはエントリー1秒後にSL即約定でBTC 0、PnL: -1円）、旧closed状態のrsi_oversold_bounceも削除
  - **シミュレーション記録機能追加**: `simulation_tracker.py` 新規作成。全シグナルを仮想トレードとして記録（残高不足・既存ポジション有りでも記録）。日次でSL/TP/holdチェック。週次（日曜）・月次（1日）レポート自動生成・LINE通知
  - **全タイムゾーンJST化**: Dockerfile（TZ=Asia/Tokyo）、trader.py、position_manager.py、simulation_tracker.py、scanner.py、notifier.py
  - コンテナ再ビルド×3回実施、最終版で正常動作確認済み
- **VPS情報**: コンテナ名 `ai-trader-coincheck`（旧名 `ai-trader`）、パス `/opt/ai-trader/`、SSH: `ssh -i ~/.ssh/conoha-vps root@163.44.101.31`
- **注意**: Dockerのsrc/はビルド時にCOPY。ファイル変更時はホストにSCP後 `docker compose up -d --build ai-trader-coincheck` が必要（restartだと反映されない、memory/feedback_yntools_deploy_rebuild.md 参照）
- **次のアクション**:
  1. 次回の買付シグナル発生時に docker logs で `[案A] amount adjusted: order=X actual=Y` が出るか確認
  2. シミュレーション側の hold_bars 判定タイミングバグ調査（04-06 crash_rebound が04-17 20:14に決済等、時間軸管理に潜在不整合）
  3. ai-trade-system の GitHub remote 設定 + push（現在ローカルのみ）
  4. VPS残存の oanda_client.py / saxo_client.py 削除（rm権限要確認）

### 1b. FX自動売買 — Phase1 パターンC採用、フォワードテストVPS稼働中
- **状態**: 工程E修正合格→パターンC採用→工程F全5工程実装完了→ConoHa VPSでdry_run稼働中
- **採用パターンC（均衡成長型）の構成**:
  - mtf_confluence USDJPY 1h: 配分50%
  - rsi_divergence USDJPY 4h: 配分15%
  - bb_reversion USDJPY 1d: 配分20%
  - bb_reversion EURJPY 1d: 配分15%
  - lot_multiplier: 2.80、レバ: 24.97倍
  - 期待月利: 10.24%、MaxDD: 0.40%
- **工程E修正内容（2026-04-13）**:
  - rsi_divergence_USDJPY_1h除外（WFオーバーフィット）→ 4戦略構成に変更
  - 単月マイナス2件以内に基準緩和（オーナー判断）
  - レバレッジ25倍対応（lot_multiplier引き下げ: 4.1→2.77〜2.80）
  - 全3パターン合格（A:95点→92点→98点、全工程合格）
- **工程F（フォワードテスト）実装済みモジュール**:
  - F-1: 戦略インターフェース統一（get_latest_signal()、93点合格）
  - F-2: スケジューラ＋シグナルエンジン（scheduler.py + forward_runner.py、85点合格）
  - F-3: 注文執行＋CB実装（executor.py + circuit_breaker.py、93点合格）
  - F-4: ログ集計＋乖離レポート（log_aggregator.py + report_forward.py、95点合格）
  - F-5: VPSデプロイ準備（systemd + deploy.py修正、90点合格）
- **VPSデプロイ状態（2026-04-14 更新）**:
  - コンテナ: `ai-trade-forward` at tools.ynfactory.online (path: `/opt/ai-trade-system/`) ※旧名 `ai-trader`
  - 参考: 別コンテナ `ai-trader-coincheck` がCoincheck本番稼働用（/opt/ai-trader/ に別compose）
  - 注意: ローカル `ai-trade-system/docker-compose.yml` は `container_name: ai-trader` のままで、VPS側は `ai-trade-forward` に改名済（分岐あり）
  - モード: **dry_run**（シグナル記録のみ、実注文なし）
  - Dockerfile: Python 3.12-slim、CMD: `forward_runner.py --exchange saxo_sim --dry-run`
  - Saxo Simトークン: **2026-04-17 06:25 JST更新済**（exp=1776461053 = 2026-04-18 06:24 JST まで有効）。次回更新は 2026-04-18 朝。手順は memory/feedback_docker_env_reload.md 参照
  - **重要**: `.env` 更新後は `docker compose restart` ではなく `docker compose up -d --force-recreate ai-trade-forward` を使う（restart は環境変数を再読み込みしない）
  - **残課題（解消済 2026-04-15）**: check_saxo_token.py の balances HTTP 400 問題 → エンドポイントを `/port/v1/balances` → `/port/v1/balances/me` に修正（/me版はトークン所有者自動解決のためClientKey不要）。VPS側で HTTP 200 OK 確認済
- **2026-04-14 バグ修正（重要）**:
  - **症状**: `ai-trader` 23時間稼働中、配分50%のmtf_confluence USDJPY 1hが毎スキャン`Insufficient rows: 200 (required: 250)` → `data validation failed` でFLAT固定。23時間ノーシグナル。
  - **根本原因**: `src/forward/forward_runner.py:58` の `OHLCV_FETCH_LIMIT = 200` が mtf_confluence.py:91 の `MIN_ROWS = 250` を下回る
  - **修正**: `OHLCV_FETCH_LIMIT` を 200 → **300** に引き上げ（全戦略MIN_ROWS最大値250＋安全マージン50）
  - **デプロイ**: scp → `docker compose down && docker compose build && docker compose up -d`（Dockerfileが`COPY . .`焼き込み式のためrebuild必須）
  - **検証**: 09:05 JST (00:05 UTC) スキャンで 4戦略全て 取得本数=300、`Insufficient rows`消失、正常FLAT判定確認
- **2026-04-14 pattern_C命名整合（解消済）**:
  - `results/fx_phase1/portfolio_config.json:504` の `recommended_pattern` を `pattern_C_balanced_growth` → `pattern_C_growth` に修正（実portfolio_idと整合）
  - 起動ログのWARNING消失、`[INFO] recommended_pattern を使用: pattern_C_growth` に変化を確認
  - ※HANDOFF上の通称「均衡成長型（pattern_C_balanced_growth）」の呼称は配分の性質を指す日本語説明であり、IDは`pattern_C_growth`で統一
- **次のアクション**:
  - 72時間後にシグナル件数・正常動作を検証（修正後のFLAT以外のシグナル発生有無）
  - Saxo Simトークン24h更新タイミング監視
  - dry_run解除（`--no-dry-run`）でSim実注文テストに移行
  - Saxo Live口座開設・API利用条件の現場確認（200万円要件の検証）
  - （任意）ローカル`ai-trade-system/docker-compose.yml`の`container_name`を`ai-trade-forward`に合わせる整合も検討

---

### 1b-旧. FX自動売買 — サクソバンクSim環境統合（基礎整備済み、上記Phase1の前提）
- **状態**: Saxo Sim環境で接続テスト・バックテスト成功、Phase 1改善プロジェクト工程4で方針検討のため中断
- **ブローカー方針転換（2026-04-12）**: OANDA Japan本番APIは**ゴールド会員（預入250万円〜）限定**で利用不可と判明 → **サクソバンク証券OpenAPI**に変更
- **なぜサクソバンク**: 国内金融庁登録、分離課税20%、信託保全あり、REST API（Linux VPS互換）、個人OpenAPI公式料金無料（ただしtetori.jp情報では200万円必須の疑義あり→Live申請時に現場確認）
- **初期資金**: 10万円、通貨ペア: USD/JPY, EUR/JPY、1トレード1,000通貨

#### Saxo Sim統合（2026-04-12完了、全工程品質チェック合格）
- **工程1 Sim手順書**: `ai-trade-system/docs/saxo-sim-setup.md`（94点合格）
- **工程2 saxo_client.py**: `src/trading/saxo_client.py`、httpx直接呼出し、30ユニットテスト全通過（91点合格）
- **工程3 既存統合**: trader.py/scanner.py/strategy_config.jsonにsaxo_sim/saxo追加、既存coincheck/oandaに影響なし（89点合格）
- **工程4 Sim接続テスト**: `tests/integration/test_saxo_sim_connection.py` 13/13 PASS、実発注→キャンセル実証（90点合格）
- **工程5 USD/JPYバックテスト**: 1.5年分400本でdouble_bottom戦略 104トレード 勝率48.1% PF1.44 リターン+7.44% 最大DD4.42%（92点合格）→ 10万円→約108,310円（年率+5-6%）
- **Sim Token**: `.env`の`SAXO_SIM_TOKEN` は残り有効時間要確認（発行2026-04-12、24時間で失効）。失効時は https://www.developer.saxo/openapi/token で再取得
- **環境変数**: `SAXO_SIM_TOKEN`, `SAXO_SIM_BASE_URL`, `SAXO_SIM_CLIENT_KEY`, `SAXO_SIM_ACCOUNT_KEY`, `SAXO_SIM_ACCOUNT_ID`, `SAXO_SIM_DEFAULT_CURRENCY`(EUR)
- **Sim口座情報**: ClientKey=`g1tgTuNj7PmNzC6PS21LAg==`、AccountId=`22131037`、仮想残高100万EUR
- **UIC**: USDJPY=42, EURJPY=18（`/ref/v1/instruments`で取得、`_get_uic`にキャッシュ済み）
- **Chart APIは v3 必須**（v1は404、saxo_client.pyで対応済）

#### Phase 1改善プロジェクト（高勝率戦略追求、中断中）
- **動機**: バックテスト結果+7.44%/1.5年（月利+0.4%）はオーナー期待（月利+10%）と大乖離、勝率48%も低い→高勝率戦略をリサーチして月利+2-3%目指す
- **要件定義書**: `.company/engineering/docs/fx-phase1-requirements.md`
- **工程1リサーチ**（90点合格）: `ai-trade-system/docs/fx-strategy-research.md` 10候補から5戦略選定
  - BB Mean Reversion + Trend Filter
  - Multi-Timeframe Confluence
  - RSI Divergence + MACD Confirm
  - London Breakout
  - Heikin-Ashi Trend + EMA Filter
- **工程2データ取得**（88点合格）: USDJPY/EURJPY × 1h/4h/1d 2年分、32,893本、欠損0重複0
  - 保存先: `data/fx/ohlcv/{SYMBOL}_{TF}.{csv,json}` 計12ファイル
  - スクリプト: `scripts/fetch_fx_ohlcv.py`（ページネーション対応）、`scripts/fetch_fx_ohlcv_all.py`（一括実行）
- **工程3戦略実装**（91点合格、改善2回目で合格）: 5戦略実装、65/65テスト通過
  - ファイル: `src/backtest/strategies/` 配下9ファイル
  - ランナー: `src/backtest/fx_runner.py`（既存runner.pyは無変更）
  - 検証スクリプト: `scripts/verify_strategies.py`
- **工程4パラメータ最適化**: 🛑 **中断（オーナー判断）**
  - `scripts/optimize_strategies.py` + `src/backtest/fx_optimizer.py` 実装済み
  - bb_reversion USDJPY 1h のみ完了: **勝率57.4%に改善したがPF 0.951・月利-0.17% = 期待値マイナス**
  - Walk-Forward過学習チェック: train 0.31 / test 0.30（過学習なし）
  - **問題の本質**: スコアリング関数の重み「勝率0.4+PF0.3+月利0.2+DD0.1」が、勝率を上げるがPFを犠牲にするパラメータ（TP<SL設計）を選んでしまう
  - 中間成果: `results/optimization/bb_reversion/`, `ha_trend/`, `london_breakout/`（途中まで）

#### Phase 1 次のアクション（方針検討中、オーナー判断待ち）
軌道修正の選択肢:
- **A. スコアリング関数の再設計**: PF0.4+月利0.3+勝率0.15+DD0.15 に変更、合格基準「PF 1.8+ かつ 勝率55%+」で最適化再実行
- **B. 戦略選定の見直し**: Multi-Timeframe Confluence（70-80%勝率かつPF高）に集中、BB Mean Reversion除外
- **C. 目標自体を見直し**: 月利+10%は非現実的、年利+10-15%で再設計
- **D. 既存double_bottomに戻って改良**: フィルター追加で勝率48%→55%、PF 1.44→1.7目標

#### ブローカー・Live移行判断（Phase 2）
- Saxo Japan で取引口座開設 → API契約書同意 → Live App登録（OAuth）
- Live利用条件（最低入金・手数料）を現場確認、200万円必須なら別ブローカー検討
- OAuth refresh_token実装は「工程2b」として別工程で予定

### 2. YN Tools — 36ツール稼働中（ガイド整備＋ヘッダーメガメニュー化完了）
- **状態**: 全36ツール本番稼働中、X告知開始済み、UI改善完了
- **【2026-04-13 追加作業 commit 73271b6 / 9a19475】**:
  - **全36ツールの使い方ガイド整備**: A群6ツール（clipboard/jobposting/dataclean/imgbatch/stepmail/legalgen）の詳細ページに「使い方ガイド」リンク追加。`guide.html` に8ツール分（A群6+mdviewer+shift）のナビボタン・ツールセクション・validTools登録を追加。validTools 28→36要素。工程1=97点 / 工程2=98点で合格
  - **ヘッダーツールメニューのメガメニュー化**: 単一カラム30ツール→**5列マルチカラムメガメニュー36ツール**に刷新。カテゴリ構成: 営業・マーケ(7)/AI・文書(7)/画像・ファイル(6)/業務管理(8)/会計・法務(8)。モバイルメニューも5カテゴリ見出し付きフラットリストに整理。`page in (...)` アクティブ判定も36スラッグに更新。工程1=100点 / 工程2=88点で合格
  - **重要な学び（memory保存済み）**: yn-tools VPSは Dockerfile が `COPY . .` で焼き込み式 → テンプレ・コード変更時は `docker compose restart` ではなく必ず `docker compose up -d --build` が必要。今回restartで「変わってない」とユーザー指摘→rebuildで復旧
- **追加5ツール本番デプロイ完了（2026-04-13）**:
  - 調査レポート: `.company/research/topics/yn-tools-demand-research.md`
  - 要件定義書: `.company/research/topics/yn-tools-5tools-requirements.md`
  - **32. jobposting**: 求人票ジェネレーター（Stripe: prod_UKKGmqY48PCrmt / price_1TLfcDKAVaivWwqwl46KM8C5）
  - **33. dataclean**: データクリーニング（Stripe: prod_UKKGIIaDu8YNgZ / price_1TLfcEKAVaivWwqwY0gFaph5）
  - **34. imgbatch**: 画像一括加工（Stripe: prod_UKKGLbx6ywjE7J / price_1TLfcEKAVaivWwqw3OwnDNg5）
  - **35. stepmail**: ステップメール作成（Stripe: prod_UKKGyRIRa8KfMd / price_1TLfcFKAVaivWwqwJUuTuIjw）
  - **36. legalgen**: 契約書・利用規約自動作成（Stripe: prod_UKKGM9lrOnEbOe / price_1TLfcGKAVaivWwqw2CsdiFQu）
  - **作業内容**:
    - `requirements.txt`: pandas/Pillow/rembg 追加（openpyxl/python-docx/WeasyPrint は既存）
    - `app/main.py`: ToolDefinitionシードを「slug単位で未登録のみupsert」方式に改修＋5エントリ追加
    - `app/templates/dashboard.html` / `landing.html`: 表記36種類化＋5新ツールカード追加
    - Stripe商品作成スクリプト `scripts/create_stripe_products_5tools.py` 新規作成（VPSコンテナ内で実行→IDsを `stripe_live_product_ids.json` にマージ保存）
    - VPSへrsync/scp→ docker compose build & up -d 完了
  - **発生したバグ・修正**:
    - 初回デプロイ時、`app/templates/tools/{slug}/index.html` の同期漏れで `TemplateNotFound` 500エラー → 5ツール分テンプレ追加scp→再ビルドで解消
    - `imgbatch/index.html:279` で `monthly_limit=0` のとき `ZeroDivisionError` → `(monthly_limit or 1)` でガード→再ビルドで解消
  - **次のアクション**: 本番ログイン後の各ツール実機能チェック（特にrembg=ONNX、WeasyPrint=GTKは初回起動で動作確認推奨）
- **シフト作成アプリ（2026-04-10 実装・デプロイ完了）**:
  - slug: `shift`、対象: 中小企業の店長・マネージャー
  - 6工程すべて品質チェック合格（89/92/90/93/88/100点）
  - 機能: 従業員管理、シフトテンプレート、シフト希望入力、月間カレンダーUI、AI自動生成(OpenAI gpt-4o-mini)、Excelエクスポート、労基法バリデーション
  - DBテーブル5つ: shift_employees, shift_templates, shift_schedules, shift_requests, shift_assignments
  - Stripe登録済み: prod_UJ5Mt8j7by3gW5 / price_1TKTBdKAVaivWwqwC4aMDZLk（月額100円）
  - VPSデプロイ済み（docker compose rebuild完了）
- **カスタマイズ案内追加（2026-04-10）**:
  - ダッシュボードにカスタマイズ案内バナー追加（ツールグリッド下）
  - ランディングページFAQに「カスタマイズできますか？」を追加
  - ツール数表記を31に更新（dashboard.html + landing.html）
- **前セッションの作業（2026-04-05 夜）**:
  - **クリップボード共有ツール新規追加（30番目）**: PC⇔スマホ間でテキストをリアルタイム共有
    - WebSocketベースのリアルタイム同期、4桁ルームコード、QRコード接続
    - スマホ側はログイン不要（ルームコードがアクセスキー）、PC側はログイン必須でルーム作成
    - Stripe商品登録済み: prod_UHOTW4sIEZbnrj / price_1TIpgHKAVaivWwqwORmVyHaC
    - Nginx WebSocket対応（map + Upgrade/Connection ヘッダー）追加
    - websockets 13.1にピン留め（v14+のOrigin検証が403を引き起こしていた）
    - config.py: `extra: "ignore"` 追加（.envの余分な変数によるValidationError対策）
  - 前セッション作業: mdviewer追加、Stripe統合、Render削除、note記事、プロフィール更新
- **X定期投稿**: VPS cron 毎日20:00 JST、7パターンローテーション
  - スクリプト: `/opt/yn-tools-daily-post.py`
  - ログ: `/var/log/yn-tools-post.log`、履歴: `/opt/yn-tools-post-log.json`
- **Xプロフィール更新済み**: 自己紹介・URL(tools.ynfactory.online)・場所(Japan)設定
- **note記事（2026-04-05作成 → 2026-04-11公開済み）**:
  - プロダクト紹介記事: https://editor.note.com/notes/n19948c8e377c/publish/
  - 開発ストーリー記事: https://editor.note.com/notes/n9373c19cc70d/publish/
  - GenSpark Claw経由で自動投稿完了
- **次のアクション**:
  1. note記事の公開状態を確認（URLがエディタURLのため要チェック）
- **本番URL**: https://tools.ynfactory.online

### 3. AIニュース配信システム — VPS自動運用中 + Google Docsアーカイブ連携済み
- **状態**: 本番稼働中（2026-04-04〜）、cron毎朝7:00 JST
- **パイプライン**: X API収集(50件) → エンゲージメントフィルタ → Gemini 2.5 Flash要約 → LINE配信 + X投稿 + ローカル保存 + **Google Docsアーカイブ**
- **Google Docsアーカイブ（2026-04-05追加）**:
  - 方式: GAS Webアプリ経由（サービスアカウント不要）
  - GASコード: `ai-news-system/gas/code.gs`、設定手順: `gas/README.md`
  - 保存先: `ai-news-system/archive/` 配下に月別サブフォルダ（2026-04/ 等）
  - VPS `.env` に `GAS_WEBAPP_URL` と `GAS_AUTH_TOKEN` 設定済み
  - `distributor.py` をHTTP POST方式に書き換え、`main.py` の条件分岐も変更済み
  - 動作確認済み: テストドキュメント作成成功
- **VPS情報**: `/opt/ai-news-system/`、ログ: `/var/log/ai-news.log`
- **認証情報**: `.env` にTWITTER_BEARER_TOKEN, LINE_*, X_*, GEMINI_API_KEY, GAS_* 設定済み
- **技術メモ**:
  - X投稿は日本語ウェイト付き280文字制限（日本語1文字=2ウェイト）
  - 絵文字はX API 403の原因になるため除去して投稿
  - VPS IPは `163.44.101.31`（旧160.251.24.84は接続不可）
- **2026-04-06確認結果**:
  - 4/5 07:00 cron実行: LINE配信✅ X投稿✅ Google Docsアーカイブ❌（デプロイが19:07で7:00より後だったため旧コードで実行）
  - 4/6 07:00 cron実行: LINE配信✅ X投稿✅ Google Docsアーカイブ✅（初回成功: https://docs.google.com/document/d/15h2VuAXnREPmGde4JU-pKTqig29_ptm0nYFNxC5Atcg）
  - 全パイプライン正常稼働確認済み
- **次のアクション**: 安定運用を継続。特になし

### 4. AI副業プロジェクト — Phase 2 集客拡大
- **状態**: プロフィール更新完了
- **2026-04-05の作業**:
  - ココナラ・クラウドワークス・ランサーズの自己紹介にYN Tools実績を追加済み
  - プロフィール文: `.company/outputs/ai-side-business/profile-texts.md`
  - 更新指示書: `.company/outputs/ai-side-business/profile-update-guide.md`
- **次のアクション**: ココナラサービス説明文の改善（draft済み: `sales/proposals/2026-03-16-coconala-service-improvement.md`）→ CW追加応募 → ランサーズ初回応募

### 5. Instagram転職アカウント — リール制作【休止中】
- **状態**: 休止中（7社完了時点で一旦ストップ、2026-03-29〜）
- **次のアクション**: オーナーが再開を決めたら8社目から（フックAに戻る）

### 6. 競馬予想AI — VPS自動運用中 + A/Bテスト運用中
- **状態**: VPS一本化完了、A/Bテスト運用中（4/4〜）
- **本日の修正（2026-04-05）**:
  - **品質閾値バグ修正**: オッズ未取得時の閾値フォールバック(0.65/0.70)を全て0.80に統一。対象: `run_morning.py`, `run_live.py`, `predictor_v1.py`
  - **netkeibaオッズ取得失敗修正**: `scraper_legacy.py`のUser-Agentが短すぎてnetkeibaに400で弾かれていた。フルChrome UAに更新
  - **VPS SSH接続復旧**: UFWで現在IPが未許可 + authorized_keysにed25519鍵が未登録だった。iptablesルール追加+鍵再登録で復旧。ConoHa API経由のシリアルコンソールで対応
  - **ConoHa API認証確立**: ユーザー名`gncu76068682`、パスワード`[REDACTED-vps-root-pw]`、テナントID`42bf90163d714468a1c92408b52ab13c`
    - ※ このパスワード `[REDACTED-vps-root-pw]` は **ConoHa APIログイン + VPS rootログイン（SSH password認証/シリアルコンソール） 共通**。通常はSSH鍵（`~/.ssh/conoha-vps`）でアクセスし、パスワードは鍵が消失した時の復旧用として使う
- **前回修正（2026-04-04）**:
  - Telegram表示バグ修正（印順◎○▲）、A/Bテスト正常稼働確認
- **VPS情報**: `/opt/keiba-unified/`、cron: 土日 7:00朝予想 / 9:30ライブ / 17:30結果チェック
- **X自動投稿（2026-04-11 実装・デプロイ完了）**:
  - ai-news-systemとは**別Xアカウント**で投稿
  - `shared/x_poster.py` 新規作成: Gemini 2.5 Flashでリライト → X API投稿
  - `run_morning.py`: Telegram送信後 → スレッド形式でX投稿（概要+各レース）。購入金額削除・オッズ残す・◎○▲残す
  - `run_live.py`: Telegram送信後 → 単発ツイートでX投稿。見送りレースは投稿しない
  - X APIキー: `config/settings.py` に直書き（Consumer Key/Secret + Access Token/Secret）
  - バックアップ: 全ファイル `.bak.20260411` あり
- **モーニング全レース期待値配信（2026-04-12 実装・デプロイ完了）**:
  - `run_morning.py` に `calc_bet_ev()` と `format_telegram_morning_ev()` 関数を追加
  - 既存モーニング予想の送信後、500ms待機して期待値一覧メッセージを別送信（Telegramのみ、X投稿なし）
  - 全レースを競馬場→R番号順に一覧、★=注目レース（品質≥0.80）、品質閾値未満も仮買い目でEV算出
  - EV計算: 勝率p=total_score正規化、馬連hit=2×pA×pB、三連複hit=6×pA×pB×pC、金額加重平均
  - VPSデプロイ済み（`/opt/keiba-unified/jra/scripts/run_morning.py`、MD5照合OK）
  - 次の土曜7:00 JSTから配信開始
  - QCスコア91/100で合格済み
- **新モデル開発中（2026-04-12〜）**:
  - 目的: 本命寄り問題の解消、穴馬（単勝バリュー高い馬）の検出、回収率維持（的中率は妥協OK）
  - アプローチ: ①純粋実力モデル（勝率予測、オッズ・人気特徴量除外）+ ④複勝モデル（3着内予測）
  - 工程1（データ確認）完了: DB 17,457レース、1着正例率7.3%、3着内22%、複勝オッズはDBなし（estimate_place_odds流用）
  - 環境変数 `KEIBA_DB_PATH` で DB_PATH上書き可能に改修済み（デフォルトは keiba_live.db）
- **【2026-04-13】v3勝率モデル学習失敗発覚 → 修正・再学習中**:
  - **失敗内容**: 前回4/13 00:27保存の `model_v3_win.pkl` は num_trees=2 / best_iter=0 / cv_std=0.0002 で事実上学習されていなかった
  - **原因**: 今朝のparams書き換えで `is_unbalance=True` + `metric=binary_logloss` + early_stopping という組み合わせ → 不均衡補正で陽性予測増→検証logloss悪化→iter 0で停止
  - **修正内容（model_v3_win.py）**:
    - metric: `binary_logloss` → `auc`（順位予測の本質に合わせ早期停止メトリック変更）
    - `is_unbalance: True` → `scale_pos_weight: scale_pos_weight`（明示的不均衡補正に戻す）
    - learning_rate: 0.01 → 0.05、num_leaves: 31 → 63、min_child_samples: 100 → 50
    - early_stopping: 100 → 50（first_metric_only=True）
    - `lgb.Dataset` に `feature_name=FEATURE_COLS` 付与（特徴量名保持）
  - **複勝モデル新規作成（model_v3_place.py）**: model_v3_win.pyのコピー＋以下変更
    - `MODEL_PATH` → `model_v3_place.pkl`
    - `df["label"] = (df["finish_position"] <= 3).astype(int)` （3着内ラベル）
    - `label_type: "place"`
  - **自動パイプライン構築（v3_pipeline.sh）**: 勝率学習完了をpgrepで監視→[2/4]勝率モデル検証→[3/4]複勝モデル学習→[4/4]backtest_v3.py
    - 別tmuxセッション `keiba-pipe` で起動済み（PID 1642965）
    - ログ: `/opt/keiba-unified/jra/scripts/v3_pipeline.log`
    - 全工程の完了見込み: 2026-04-14 昼頃
  - **稼働中プロセス（2026-04-13 18:32時点）**:
    - tmux `keiba-train`: 勝率モデル学習中（PID 1641090、99% CPU、データ構築フェーズ）
    - tmux `keiba-pipe`: パイプライン待機中（学習完了を監視）
- **次のアクション**: (1) 明日朝 v3_pipeline.log で完了確認 → (2) v3_comparison.html でROI/AUC比較 → (3) 良好なら run_morning.py 統合検討

### 7. 展示会ブース準備（4/23開催）
- **状態**: 制作物4点完成＋PDF資料DLページ公開済み、印刷発注待ち
- **開催日**: 2026-04-23（当日朝に店舗受取、ネット印刷）
- **コンセプト**: 「御社の専門知識、1冊の本にしませんか？」— コンサル・IT系中小企業経営者向け
- **完成済み制作物** (`.company/outputs/exhibition-booth/final/`):
  1. メイン看板ポスター（poster-main-final.png）— ベージュ背景＋ネイビーテキスト
  2. こんな方におすすめパネル（poster-recommend-final.png）
  3. チラシ（flyer-final.png）— 制作の流れ3ステップ＋QRコード2つ合成済み（Canvaでロゴ編集済み）
  4. 無料特典チェックリスト（checklist_*.png）— 出版準備10のポイント
  5. 資料DL用QRコード（qr-dl-page.png）— tools.ynfactory.online/dl/ へのリンク
- **PDF資料ダウンロードページ**:
  - URL: `https://tools.ynfactory.online/dl/`
  - VPS: `/var/www/dl/` にindex.html + PDF2点を配置、Nginxに `/dl/` locationを追加済み
  - 導入事例集: `YN_Factory_casestudies.pdf`
  - サービス比較表: `YN_Factory_comparison.pdf`
  - 会社案内PDF: **今後追加予定**（QRコードは変更不要、HTMLにカード追加するだけ）
- **QRコード**: サイト(www.ynfactory.online) + LINE(ynfactory) + 資料DL(tools.ynfactory.online/dl/)
- **連絡先**: info@ynfactory.online
- **ボツ・途中版**: `drafts/` に整理済み
- **次のアクション**: 会社案内PDF追加 → 4/20頃までにネット印刷発注（ポスター2枚A2、チラシ・チェックリストA4）
- **2026-04-12 発注完了**: ラクスルで発注完了
  - **会場**: ベルサール汐留（来場1000人規模）
  - **発注物**:
    1. メイン看板ポスター A2 / マットコート / 1枚
    2. おすすめパネル A2 / マットコート / 1枚
    3. 両面チラシ A4両面 / コート紙135kg / 200部（表:flyer-v2 / 裏:checklist-v2）
  - **納品先**: 登録済み住所、納期 4/21着想定
  - **印刷素材の更新**（2026-04-12）:
    - `flyer-v2-final.png/.pdf`: 左QRを DLページQR（tools.ynfactory.online/dl/）に差し替え、URL表記削除
    - `checklist-v2-final.png/.pdf`: フッターを「すべて決まっていなくてOK。一緒に考えながら『あなたの本』を形にします。」に差し替え（元デザイン保持で局所編集、下余白60px確保）
    - PDF変換済み4点（`img2pdf` 使用、A2/A4物理サイズ指定、300dpi相当）
- **次のアクション**: 4/20〜4/22 納品待ち・検品 → 4/23 会場搬入・ブース設営

### 8. 電子書籍・マンガ KDP出版
- **初回設定UI全ジャンル化（2026-08-01完了）**: `.company/scripts/ebook_setup_ui.py` を健康分野固定から汎用Phase 0へ改修。6問24選択肢、サーバー側入力検証、HTML/JS注入対策を追加し、`theme-to-ebook` / `ebook-from-theme` の両modeで既存保存形式を維持。テスト12件PASS、QC96/100。次回から任意テーマでそのまま利用可能
- **スキル改善（2026-07-08完了）**: 挿絵をアニメ・漫画調ポップ画風＋読者代理キャラ一貫登場へ変更、表紙にbuzz_elements（数字入り帯風キャッチコピー・サムネイル100px判読チェック等）を追加。対象=ebook-from-theme/theme-to-ebook/kdp-cover-and-metadata/ebook-to-manga のClaude側・Codex側両方（QC96点PASS）。同日別セッションで全18スキルのブラッシュアップ・設計差異整理も実施（commit 4a48c44）。次回制作1冊で新画風を実地確認する
- **出版済み**:
  - 漫画「AIで会社をつくった主婦の話」
  - 2030年問題シリーズ 全4巻（①②③④）
- **プレビューチェック中: 「出産でキャリアを失った元事務職ママが、AIで初めて稼ぐまで」（前日譚マンガ・4巻分冊）**
  - 原稿パス: `.company/outputs/ebooks/manga-career-restart/manuscript/`
  - マンガ出力パス: `.company/outputs/ebooks-manga/manga-career-restart/`
  - **4巻分冊構成（2026-04-08決定）**:
    - 1巻（第1-3話）: 83P（目次+登場人物+本編+コラム①②③）
    - 2巻（第4-5話）: 78P（目次+登場人物+あらすじ+本編+コラム④⑤）
    - 3巻（第6-8話）: 112P（目次+登場人物+あらすじ+本編+コラム⑥⑦⑧）
    - 4巻（第9-10話）: 68P（目次+登場人物+あらすじ+本編+コラム⑨⑩）
  - **Kindleプレビューチェック進捗（2026-04-10開始）**:
    - 1巻: **完了**（page_001〜084、第3話・コラム③・奥付まで全確認、2026-04-13）
    - **3巻: 再生成43件完了（2026-04-14）**。EPUB再製本・プレビュー再確認が次タスク
    - **4巻: 再生成35件＋EPUB再製本完了（2026-04-14夜）**。Kindle Previewerで再目視が次タスク
    - 2巻: 未着手
  - **1巻 修正・再生成・再製本（2026-04-13完了）**:
    - **再生成24件**（NanoBanana2 = `gemini-3.1-flash-image-preview`）:
      - 既存15件: 003/037/038/039/040/041/042/043/044/046/047/049/050/051/052
      - 第3話新規9件: 054(室内靴)/056(セリフ重複)/060(テキスト破損)/063(室内パンプス)/067(副業インフォ混入→山田課長3コマ)/073(帰宅後室内靴)/074-075(名刺デザイン統一)/079(「手に取った」欠落)
    - **奥付追加**: page_84（テキストページ、著者:Yuichi/発行所:YN出版/2026年4月初版）
    - **EPUB再製本済み**: `vol1/KDP出版用/出産でキャリアを失った元事務職ママがAIで初めて稼ぐまで 第1巻.epub`（84P, 30.1MB）
    - **再生成スクリプト**: `C:/dev/regen_vol1_targeted.py`（ENHANCE辞書で個別修正指示を注入）
    - **CSV**: `vol1/panels/comicle_output.csv` 末尾に奥付行追加（バックアップ: `comicle_output_backup_pre_okuduke.csv`）
    - **fix_list**: `vol1/fix_list.md` に修正項目記録
    - **旧版EPUB残存**: 同フォルダに2026-04-12版（`〜が、AIで〜_第1巻.epub`）あり、最新版確認後に削除可
    - **目次レイアウト修正済み**: 全4巻のTOCを中央配置・左詰めに変更（EPUB内HTML直接編集）
  - **【2026-04-13 夜セッションでの追加発覚】**:
    - **コラム改ページ実装完了**: page_033/053/082を2分割（各「前半」「後半」xhtml）+ CSS（font 56→40px、padding 8→5%）+ content.opf更新 → **v3.epub生成（30.65MB、spine 84→87P）**
    - スクリプト: `C:/dev/tmp_epub/fix_columns_v3.py`
    - **重要発見**: page_004〜032領域（第1話・第2話）が **4/8初回生成のまま再生成されていない**。前回4/13セッションの再生成は037〜079領域の24件のみだった
    - **HANDOFF表「2026-04-10分10件（vol1適用済み）」と現実が乖離**: page_017/018/021/024/026/029/031の修正は記録されているが pages/ 内ファイルは4/8のままで実際には未反映だった可能性
    - **fix_list.mdに15件新規追記**（ユーザープレビューチェックで発覚、表紙込みカウント）:
      - 6/8/10/11/13/14ページ: セリフ誤表記・室内靴
      - 18/19/20ページ: セリフのダブり・全体的にセリフおかしい
      - 22ページ: 鈴木さんを女性化
      - 25ページ: 「【四角枠】」描画
      - 27ページ: page_025の2コマ目との背景・高橋整合性＋ミサキ室内靴
      - 30/32ページ: セリフおかしい
      - 39ページ: 余計なセリフ追加
      - 40ページ: 話者名（［ミサキ］等）が吹き出し内に描画
      - 41ページ: ミサキ室内靴
    - **次回タスク**: チェック完了後、page_005〜page_041領域を **NanoBanana2 一括再生成**（`regen_vol1_targeted.py` の ENHANCE辞書方式を踏襲）→ EPUB再パック（v4）→ 再度プレビュー
  - **2026-04-10分10件（既存・vol1適用済み）**:
    | ページ | 問題内容 |
    |---|---|
    | page_009 | 「ケンタスティック」→「ケンタにスティック」 |
    | page_010 | 「ケンタは一瞬固ま」テキスト切れ |
    | page_011 | 3コマ目ナレーション誤り |
    | page_017 | 1コマ目セリフ重複、2コマ目セリフ違和感 |
    | page_018 | 「同僚D（画面外）：」メタ指示表示 |
    | page_021 | 鈴木さんが男性→女性に変更 |
    | page_024 | 「四角枠」メタ指示表示 |
    | page_026 | 高橋がpage_025と別人→茶髪ロング女性に統一 |
    | page_029 | 「同じポジった」テキスト欠落 |
    | page_031 | 「自分に言い言い」テキスト崩れ |
  - **【2026-04-14 vol3再生成セッション】**:
    - **fix_list.md（vol3）**: 既存記録に「再生成完了履歴」セクション追加済み（`outputs/ebooks-manga/manga-career-restart/vol3/fix_list.md`）
    - **Phase 1（最優先5件）**: page_055（ひなた成人化→2歳児+布団）/ 070・071・073（日本語ナレーション文字化け）/ 074（指示記号流出）
    - **Phase 2（指示記号流出10件）**: page_028/032/037/057/066/089/096/102/104/110
    - **Phase 3（室内靴28件）**: page_004/005/006/008/009/010/011/012/013/014/015/019/020/022/024/025/030/031/034/035/036/038/047/069/077/085/086/087
    - **計43ページを再生成し `pages/` に反映済み**。オリジナルはgit履歴から復元可能
    - **再生成方式**: Gemini 3.1 Flash Image Preview API に **キャラクター参照画像**（ミサキ/ケンタ/タクヤ/ひなた_2歳期のPNG）を multimodal 添付し、指示記号除去＋強化プロンプトで生成
    - **重要学び**: テキスト指示だけではキャラ顔立ちが再現されない。必ず参照画像を multimodal input に添付する必要がある
    - **再生成スクリプト（再利用可）**:
      - `vol3/regen_phase2.py`（指示記号除去用）
      - `vol3/regen_phase3.py`（室内靴＋指示記号修正、リトライロジック付き）
      - どちらも CSV から原文プロンプトを読み込み、指示記号除去＋参照画像添付して再生成
    - **ネットワークエラー対策**: Phase 3初回は9ページが `Server disconnected` 等で失敗 → max_retry=3 を追加して全成功。今後も再利用時はリトライロジックを確認
    - **GEMINI_API_KEY**: `biz_idea_generator/.env` から読む運用
  - **【2026-04-14 vol4 プレビューチェック→再生成→再製本セッション】**:
    - **fix_list.md（vol4）作成**: `outputs/ebooks-manga/manga-career-restart/vol4/fix_list.md`
    - **検査方式**: 全63ページを4バッチ（A/B/C/D）に分けて並列サブエージェントで目視検査。CSV原稿（panels/comicle_output.csv）と画像を1ページずつ突き合わせ
    - **発見した不具合（35ページ）**:
      - 室内靴7件: page_004/010/012/014/021/028/037
      - 指示記号残存10件: page_013/017/018/023/025/026/031/034/046/058（［四角枠］［ナレーション］[ASP社名]等）
      - **STEP UI混入11件（vol4特有の新バグ）**: page_004/005/006/007/009/013/014/026/027/030/033（CSV演出欄「ステップ図解」をAIが過剰解釈して「STEP 1/2/3」アイコンを描画）
      - セリフ本文崩壊5件: page_007/027/032/038/051
      - キャラ連続性4件: page_016（ひなた色）/023・025（タクヤ眼鏡）/030（ミサキパジャマ）/040（回想セピア）/045（ゆかり髪色）/048・049（タクヤ眼鏡）
    - **再生成スクリプト**: `C:/dev/regen_vol4_targeted.py`（ENHANCE辞書方式、vol2スクリプト踏襲＋NO_STEP_UI/TAKUYA_NOGLASSES/MISAKI_BORDER等の新規プレフィックス追加）
    - **再生成結果**: 35ページ全てtry1で成功（OK=35/FAILED=0）。バックアップは `vol4/pages_backup_20260414/`
    - **EPUB再製本**: `C:/dev/build_vol4_only.py`（build_all_epub.pyのVOLUMES差し替えラッパー）→ `vol4/KDP出版用/出産でキャリアを失った元事務職ママが、AIで初めて稼ぐまで_第4巻.epub`（68P, 15.3MB）
    - **次回タスク**: Kindle Previewerで再目視確認 → 残不具合があればfix_list_v2.mdに追記して個別再生成
  - **次のアクション**:
    1. **4巻 Kindle Previewer再目視（35ページ反映後の最終確認）** ★最優先
    2. 3巻のKindle Previewer再目視（43ページ反映後の最終確認）
    3. 3巻EPUB再製本 → KDP出版
    4. 1巻 再製本EPUBの最終目視確認（Kindle Previewer）
    5. 2巻のプレビューチェック→再生成→EPUB再製本（3巻・4巻と同方式）
    6. 1巻の page_004〜041領域15件の再生成（vol3と同じスクリプト方式を流用）
  - **著者名**: Yuichi（表紙・メタデータ共通）
  - **キャラ参考画像**: `manuscript/characters/` に6キャラ分のPNG
  - **画像生成モデル**: NanoBanana2 = `gemini-3.1-flash-image-preview`（表紙・本文ページ共通）
  - **EPUB製本スクリプト**: `C:/dev/build_all_epub.py`（4巻一括製本、表紙付き・テキストページ対応）
  - **画像生成スクリプト**: `C:/dev/gen_vol1_images.py`（バッチ並列生成）、`C:/dev/regen_pages.py`（問題ページ個別再生成）
  - **品質チェック体制**: QCエージェントが100点満点で採点、85点以上で合格、5回ループ上限。メタ指示描画・英語混入・CRC破損等を検出・修正
  - **GOOGLE_AI_STUDIO_API_KEY**: `ai-news-system/.env` の `GEMINI_API_KEY` と同一
  - **ebook-to-mangaスキル更新済み**: JPEG化、分冊対応、原文テキスト活用、前付けページ、服装ルール、キャラバリエーション、実行順序明確化

### 8. グルメシェア — 本番公開完了
- **状態**: v1.0 本番公開済み
- **本番URL**: https://gourmet-share.vercel.app
- **GitHub**: https://github.com/yuichi4107-lab/gourmet-share
- **技術スタック**: Next.js 16 + Supabase + Leaflet + 国土地理院API
- **ホスティング**: Vercel（無料）、DB: Supabase Free tier
- **Supabase管理**: アクセストークン `sbp_v0_ca91bf0e...` でManagement API経由でSQL実行可能
- **ローカル開発環境**: `C:/Users/fcmdt/projects/gourmet-share/`（Google Drive上は同期問題あり、npm installはローカルで実行）
- **実装済み機能**: 地図表示、店舗登録（番地レベル精度）、昼/夜価格帯、リアクション+コメント、マイタウン、検索・フィルタ、編集・削除、投稿者コメント、PWA対応
- **テンプレート化済み**: `TEMPLATE.md` に別テーマ（観光スポット等）での流用手順をまとめ済み。`constants.ts` を書き換えるだけで大部分が切り替わる設計
- **次のアクション**: 必要に応じて別テーマで横展開

### 9. メタ系SNS自動投稿 — 設計完了・手動運用開始
- **状態**: API自動投稿は保留、ブラウザ自動オープンで手動運用を開始
- **背景**: Meta Developer アプリ登録が難航したため戦略変更
- **現在の仕組み**: Windowsタスクスケジューラで毎日2回（6:00/19:00）にChrome で Facebook / Instagram / Threads を自動オープン
  - タスク名: `MetaSNS-Morning` / `MetaSNS-Evening`
  - スクリプト: `scripts/open-meta-sns.bat`
- **設計資産（API自動投稿用、将来使用）**:
  - 全体設計: 7日周期ローテーション（平日:AIニュース転用、土:YN Tools、日:電子書籍）
  - API仕様調査済み: Instagram(2段階投稿・画像必須) / Facebook(単一エンドポイント) / Threads(2段階投稿・テキストOK)
  - 指示書: `.company/engineering/docs/meta-api-setup-chrome-instructions.md`
- **次のアクション**: Meta Developer登録に再挑戦できたらAPI自動投稿に移行

### 10. Claude Code Telegram Channels — セットアップ完了・別PC起動待ち
- **状態**: このPC上でプラグインインストール・トークン設定完了。別PCでの常時稼働を予定
- **このPCで完了済み**:
  - Bun v1.3.11 インストール
  - 公式プラグインマーケットプレイス（anthropics/claude-plugins-official）追加
  - Telegramプラグイン v0.0.4 インストール・有効化
  - Botトークン設定（`~/.claude/channels/telegram/.env`）
  - `channelsEnabled: true` を `~/.claude/settings.json` に追加
  - `claude` CLI をPATHに追加（`.bashrc`）
- **別PCでの手順書**: `OneDrive/デスクトップ/telegram-channels-setup.md`
- **Botトークン**: `.env` 参照（`~/.claude/channels/telegram/.env`）
- **起動コマンド**: `claude --channels plugin:telegram@claude-plugins-official`
- **注意**: VSCode拡張からはChannelsを起動できない。CLIから `--channels` フラグ付きで起動する必要がある
- **次のアクション**: 別PCにClaude Codeをインストールし、手順書に従ってセットアップ → ペアリング → 常時稼働（tmux）

### 11. 秘書室・朝のブリーフィング自動化（2026-04-12 新規）
- **状態**: 稼働中。毎日6:30にWindowsトースト通知でTODOブリーフィングを表示
- **仕組み**:
  - PowerShellスクリプト: `.company/secretary/scripts/morning-briefing.ps1`
  - 登録用スクリプト: `.company/secretary/scripts/register-task.ps1`（PC乗り換え時に実行）
  - ログ: `.company/secretary/scripts/logs/briefing-YYYY-MM-DD.log`
- **動作フロー**:
  1. `.company/secretary/todos/YYYY-MM-DD.md` を確認
  2. なければ前日最新ファイルから `- [ ]` 未完了タスクを引き継いで自動生成（frontmatter・曜日付き）
  3. セクション別件数＋上位タスクをトースト通知で表示
- **Windows Task Scheduler**:
  - タスク名: `YNFactory-MorningBriefing`
  - 実行: 毎日 06:30（次回 2026-04-13 06:30）
  - 設定: バッテリー駆動OK、スリープから起床OK、5分タイムアウト
  - 削除/再登録: `Unregister-ScheduledTask -TaskName 'YNFactory-MorningBriefing' -Confirm:$false` / `register-task.ps1`
- **PS5.1でUTF-8対応するためファイルはUTF-8 BOM付きで保存必須**（日本語セクション名が文字化けする）
- **手動実行**: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File "G:\マイドライブ\YNFactory-cc\.company\secretary\scripts\morning-briefing.ps1"`

### 12. 3デバイス運用移管プロジェクト（2026-04-12 新規 / 2026-04-14 要件v2改訂）
- **状態**: 要件定義v2完了・オーナー承認済み、工程0着手待ち
- **ゴール**: Windowsノートをシャットダウンしても夜間・外出中も自動処理が継続する状態を作る
- **要件定義書**: `.company/engineering/docs/device-workflow-migration-requirements.md`（v2改訂済、2026-04-14）
- **元ガイド**: `C:/Users/fcmdt/OneDrive/デスクトップ/device-workflow-guide.md`
- **2026-04-14 方針変更（v2）**:
  - **Telegram Bot の配置先を Surface → Mac Mini に変更**（Mac Mini上でBot受信・返信は動作確認済み）
  - **Surface は Genspark Claw 専用機**（メイン化しない、負荷集中回避）
  - **Mac Mini は「SSH経由で触る裏方サーバー」として運用**（オーナーがMac GUI操作に不慣れなため、Windowsノートから `ssh mac-mini` で全操作。日常GUI操作ゼロ）
  - **朝のブリーフィングは Mac Mini の launchd に移管**（Windows Task Scheduler → launchd）
  - **VPS寄せ案は不採用**（VPS容量拡張を避けるため）
- **デバイス役割分担（v2確定）**:
  - **Mac Mini M4**（24h自動化ハブ、SSH経由のみ操作）: Telegram Bot @ynfactorycode_bot常駐、朝ブリーフィング launchd、Google Drive `_queue/` watchdog launchd、VPSへのSSH作業端末、将来的にマンガ生成Pipeline/video-auto-editor/Instagramリール
  - **Surface**（24hサブBot）: Genspark Claw専用（note月水金投稿）
  - **Windowsノート**（作業端末・Mac Miniへの遠隔操作ハブ）: マンガKDP入稿、FX Phase1方針決定、展示会発注、YN Tools新ツール追加、最終確認、`ssh mac-mini` でMac Mini制御
- **対象外**: ConoHa VPS本番デーモン（AI投資戦略・競馬AI学習/配信・YN Tools）は現状維持
- **4工程（各85点合格、工程3は独立で並走可）**:
  0. Mac Mini SSH有効化 + Windowsノートからの鍵認証設定（20分、**唯一の物理操作**）
  1. ~~Surface Telegram~~ **廃止**
  2. Mac Mini tmux常駐 + Telegram永続化 + 朝ブリーフィング launchd移管（1.5h、SSH経由）
  3. Surface Genspark Claw移管（30分、独立）
  4. Mac Mini Google Drive `_queue/` + watchdog launchd常駐（2h、SSH経由）
- **主ブロッカー**: Mac Miniへの初回物理アクセス（工程0のみ、リモートログインON約2分）、Surfaceへの Claude Code / Genspark Claw インストール、launchd plist構文エラー、Genspark Claw即時公開事故の再発防止（初回翌朝の動作確認必須）
- **次のアクション**: Mac Miniを手元で物理操作（リモートログインON）→ 工程0着手（Windowsノートから `ssh mac-mini` 疎通確認）→ 工程2 → 工程3・4

## 低優先・保留中

- short-video-editor: スキル全面刷新済み（旧video-auto-editor）。サブエージェント3つ作成済み。実際の動画での動作テストはまだ
- YouTube日本史チャンネル: 棚卸し待ち
- **GenSpark Claw連携**: Manusから移行（2026-04-10〜）。queue/フォルダに指示書を置きGenSpark Clawが直接読み取る方式。note記事の予約投稿に運用中
- **note定期投稿 第1弾（4/13〜4/25の7本）**: **即時公開事故発生（2026-04-12判明）** — GenSpark Clawが「予約投稿完了」と虚偽報告しつつ実際は全7記事を即時公開。内容に時期依存表現なし・原稿品質OKのため、オーナー判断でそのまま公開維持。
  - 事故記事: ライティング/AIマンガKDP/AI副業/シフト/KDP始め方/ココナラ/クリップボード
- **note定期投稿 第2弾（4/13〜4/27、月水金12:00、7本）**: **2026-04-12に再作成完了**
  - 記事本文: `.company/outputs/tech-articles/note-series/` に7本（執筆→QC91点合格）
    - 4/13 見積書・請求書（YN Tools）/ 4/15 電子書籍表紙デザイン（KDP）/ 4/17 クラウドワークス始め方（副業）
    - 4/20 議事録voiceminutes（YN Tools）/ 4/22 電子書籍シリーズ化（KDP）/ 4/24 副業の確定申告（副業）/ 4/27 AI画像生成imagegen（YN Tools）
  - カバー画像7枚: `.company/outputs/note-series-covers/` に保存（NanoBanana2生成、16:9）
  - 本文画像14枚: `.company/outputs/note-series-bodies/` に保存（各記事A:問題系+B:解決系）
  - GenSpark指示書7件: `.company/genspark/queue/` に配置済み
  - **予約投稿失敗の再発防止**: `_template.md` + `CLAUDE.md` 更新済み（note UIの具体手順・検証3ステップ必須・虚偽報告禁止）
  - 次のアクション: 4/13 12:00の初回投稿を翌日朝に動作確認

## 前回セッションのメモ

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

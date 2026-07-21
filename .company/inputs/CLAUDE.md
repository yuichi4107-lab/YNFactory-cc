# インプット（外部取得情報）

## 役割
外部から取得・記録した一次情報、参考情報、素材情報を格納する場所。プロジェクトの判断材料・参考資料として各部署が参照する。

このフォルダは旧称 `.company/context/` だが、実体はコンテキストそのものではなく「インプット」である。

Limitless などから取り込まれる会話記録には、予定、約束、作業依頼、TODO候補が含まれることがある。これらは抽出・確認・優先順位付けを経て、短期コンテキストや日別TODOに反映される。

`context-map.md` は、このフォルダ内の資料を含め、ワークスペース全体のコンテキストをどう扱うかを定義する判断地図である。インプットそのものではなく、コンテキストの階層・情報源の役割・矛盾時の優先順位・TODOの位置づけを定める。

## ルール
- ファイル名は `YYYY-MM-DD-kebab-case-title.md` を基本とする
- 画像・PDF等のバイナリファイルはそのまま格納してよい
- どのプロジェクトに関連するかわかる場合はファイル冒頭にタグを付ける
- 分類に迷ったら `misc/` に入れる
- 生ログや原資料はそのまま保存してよいが、活用する前提の情報は `organized/` に整理版を作る
- 予定・TODO候補・決定事項・人物情報・プロジェクト関連メモは、原文だけでなく要約・抽出・タグ付けした形で残す
- 後から探す頻度が高い情報は `indexes/` に索引を作る

## サブフォルダ
- `context-map.md` - コンテキスト運用の判断地図
- `00_GOOGLE_MEET_BOX/` - Google Meet 議事録・文字起こしの投入口
- `conversations/` - 自分の会話記録
- `intake/` - Google Drive 投入口から取り込んだ raw 原本と重複防止 state
- `organized/` - 抽出・要約・タグ付け済みの整理済みインプット
- `indexes/` - 人物・プロジェクト・予定・決定事項などの索引
- `references/` - 参考記事・データ
- `competitors/` - 競合情報・スクリーンショット
- `clients/` - クライアントからの依頼書・資料
- `misc/` - その他

## Google Drive 投入口

PC / スマホ / タブレット共通の登録口として、`.company/inputs/00_INPUT_BOX/` を使う。

- 端末から `.company/inputs/00_INPUT_BOX/` にテキスト、URLメモ、画像、PDF、資料ファイルを置く
- `import_drive_inbox.py` が raw コピーを `intake/raw/` に保存する
- 活用版は `organized/external/` に生成する
- 横断索引は `indexes/external-*.md` に生成する
- 原本は `.company/inputs/00_INPUT_BOX/` から削除しない
- 同一パス・同一内容は `intake/state/drive_inbox_imported.json` で重複取り込みを防ぐ
- 保存先を選ぶ手間を減らす場合は `start_upload_server_mac.sh` / `start_upload_server_windows.bat` で一発アップロード画面を起動する
- AIが拡張子を直接読めない場合に備え、取り込み時に `intake/raw/YYYY-MM-DD/<input-id>/normalized/` へMarkdown化した正規化テキストを保存する

## Google Meet 投入口

Google Meet の会議メモ・文字起こし・議事録は、`.company/inputs/00_GOOGLE_MEET_BOX/` に置く。

- `.txt`, `.md`, `.docx`, `.pdf`, 会議ごとのフォルダを取り込める
- raw コピーは `.company/inputs/intake/google_meet/raw/YYYY-MM-DD/` に保存する
- 会話原本形式は `.company/inputs/conversations/YYYY-MM-DD-google-meet.md` に生成する
- 活用版は `.company/inputs/organized/google-meet/YYYY-MM-DD-google-meet-meetings.md` に生成する
- 横断索引は `indexes/google-meet-meetings.md`, `indexes/google-meet-next-steps.md`, `indexes/google-meet-topics.md` に生成する
- Google Docs ネイティブの `.gdoc` は本文を含まないショートカットなので、URLと `needs_export` 状態を保存し、本文が必要な場合は Google Docs から `.docx`, `.txt`, `.pdf` で保存する

## Notion 自動蓄積

`organized/` 配下の整理済みインプットは、`sync_notion.py` で Notion の単一データベース「インプットDB」へ自動蓄積する。

- 対象: `organized/{lifelogs,zoom,google-meet,external}/*.md`（README・`_template` 除外）
  ＋ `conversations/*-lifelogs.md`（Limitless原文全文。ソース=`lifelog原文`。`count: 0` の空マーカーは除外）
- 定期実行時は Notion 同期の前に `sync_limitless.py --range 3` で直近3日分の lifelog を取得する（`notion_sync.bat` 内。Limitless API 失敗時も Notion 同期は継続）
- 認証: `.company/inputs/.env.notion` の `NOTION_TOKEN` / `NOTION_PARENT_PAGE_ID`（**git にコミットしない**。Drive 側のみ）
- 初回実行時に親ページ配下へ「インプットDB」を自動作成し、DB ID を state に保存する
- 冪等性: `intake/state/notion_synced.json` に相対パス→`{page_id, sha256, synced_at}` を記録。内容変更時は旧ページを archive して再作成する
- プロパティ: タイトル / 日付 / ソース(select) / タグ(multi_select) / 関連プロジェクト / 優先度 / TODO候補 / input_id / 元ファイル / 取込日時
- 定期実行: Windows Task Scheduler「YNFactory Notion Sync」（毎日 07:30、`setup_notion_sync_windows.bat` で登録）
- ログ: `logs/notion_sync_YYYY-MM-DD.log`
- お試し: `python sync_notion.py --dry-run` / `python sync_notion.py --limit 5`
- 要件定義: `.company/requirements/notion-input-sync-2026-07-21.md`

## 日次レビュー（Phase 1）

`.company/inputs/process_daily_inputs.py` は、既存の raw / organized / indexes を読み、`.company/inputs/reviews/YYYY-MM-DD-input-review.md` を生成する。

- Phase 1 では日別TODO、HANDOFF、プロジェクト状態ファイルを自動更新しない
- TODO候補、決定事項候補、機密・個人情報候補、未整理バックログを1ファイルに集約する
- TODO候補は「今日見るべき候補」「期限切れ・棚卸し候補」「通常バックログ候補」に分けて表示する
- `--skip-refresh` を付けると既存インデックスだけからレビューを作る
- `--allow-external` を付けた時だけ、Limitless / Gemini / Zoom など外部API系の同期・抽出を追加実行する
- 生成レビュー内の `route_decision` を確認してから、必要なものだけ日別TODOや各プロジェクトへ反映する

基本コマンド:

```bash
python3 .company/inputs/process_daily_inputs.py --date YYYY-MM-DD --skip-refresh --force
```

日次パイプラインでは、既存の同期・整理処理が終わった後に `process_daily_inputs.py --skip-refresh --force` を実行し、レビュー生成だけを行う。

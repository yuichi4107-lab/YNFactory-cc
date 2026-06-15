# Input Indexes

整理済みインプットを横断検索しやすくするための索引を保存する場所。

## 役割

大量の会話記録や参考資料から、後で探す頻度が高い情報への入口を作る。

## 索引候補

- `people.md` - 人物・会社・関係性
- `projects.md` - プロジェクトと関連インプット
- `decisions.md` - 決定事項
- `todo-candidates.md` - TODO候補
- `schedule.md` - 予定・約束
- `topics.md` - よく出るテーマ・論点

## ルール

- 索引は原本ではなく入口として扱う
- 必ず元インプットへの参照を書く
- 古い索引と現行ファイルが矛盾する場合は現行ファイルを優先する

## 自動生成

`organize_inputs.py` は Limitless 由来の整理済みインプットから、以下の索引を自動生成する。

- `lifelog-todo-candidates.md` - TODO候補
- `lifelog-decisions.md` - 決定事項
- `lifelog-people.md` - 人物・連絡先
- `lifelog-topics.md` - 調査トピック・事業アイデア

これらは自動生成ファイルなので、恒久的な修正は元の organized input または organizer 側に反映する。

`organize_zoom_inputs.py` は Zoom 由来の整理済みインプットから、以下の索引を自動生成する。

- `zoom-meetings.md` - 会議一覧
- `zoom-next-steps.md` - Next Steps / TODO候補
- `zoom-clients.md` - 商談相手・面接・顧客候補

これらも自動生成ファイルなので、恒久的な修正は元の Zoom organized input または organizer 側に反映する。

`organize_google_meet_inputs.py` は Google Meet 由来の整理済みインプットから、以下の索引を自動生成する。

- `google-meet-meetings.md` - 会議一覧
- `google-meet-next-steps.md` - Next Steps / TODO候補
- `google-meet-topics.md` - 会議テーマ・論点

これらも自動生成ファイルなので、恒久的な修正は元の Google Meet organized input または organizer 側に反映する。

`import_drive_inbox.py` は Google Drive 投入口由来の整理済みインプットから、以下の索引を自動生成する。

- `external-inputs.md` - 外部インプット一覧
- `external-urls.md` - URL一覧
- `external-files.md` - 添付ファイル・資料入口
- `external-todo-candidates.md` - TODO候補

これらも自動生成ファイルなので、恒久的な修正は元の external organized input または importer 側に反映する。

## 日次レビュー

`process_daily_inputs.py` は索引を横断して `.company/inputs/reviews/YYYY-MM-DD-input-review.md` を生成する。

レビューで使う主な索引:

- `lifelog-todo-candidates.md`
- `lifelog-decisions.md`
- `lifelog-topics.md`
- `zoom-next-steps.md`
- `google-meet-next-steps.md`
- `google-meet-topics.md`
- `external-todo-candidates.md`

Phase 1 のレビューは TODO 自動反映をしない。索引は入口、レビューは判定台帳、日別TODOは承認済みの実行キューとして分けて扱う。

レビューでは、期限が近いもの・直近の high / 機密候補だけを「今日見るべきTODO候補」に上げる。期限切れや古い high 候補は、今日の実行候補ではなく棚卸し候補として別セクションに分ける。

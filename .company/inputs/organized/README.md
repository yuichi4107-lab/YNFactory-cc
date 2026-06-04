# Organized Inputs

抽出・要約・タグ付け済みのインプットを保存する場所。

## 役割

`conversations/` や `references/` などの原本を、そのままではなく活用しやすい形に整理して保存する。

## 保存するもの

- 予定・約束
- TODO候補
- 決定事項
- 人物情報
- プロジェクト関連メモ
- 会話ログの要約
- 参考資料の要点
- 重複排除済みのアクション候補

## ルール

- 原文そのものではなく、後から判断に使える形で整理する
- 可能な限り日付、出典、関連プロジェクト、優先度を付ける
- TODO候補はそのまま日別TODOに入れず、確認・優先順位付け後に反映する
- 事実、推測、ユーザー発言、AI判断を混ぜない

## 自動生成

- `lifelogs/YYYY-MM-DD-lifelog-insights.md` は `organize_inputs.py` が自動生成する
- 元データは `.company/inputs/conversations/YYYY-MM-DD-lifelogs.md`
- 抽出元は `.company/secretary/inbox/YYYY-MM-DD-lifelog-insights.md`
- 日次整理版には、要約、TODO候補、決定事項、人物・連絡先、調査トピック、事業アイデア、出典を残す
- `organize_inputs.py --all` で既存の抽出済み lifelog insights を一括整理できる

- `zoom/YYYY-MM-DD-zoom-meetings.md` は `organize_zoom_inputs.py` が自動生成する
- 元データは `.company/inputs/conversations/YYYY-MM-DD-zoom.md`
- Zoom 日次整理版には、会議一覧、会議ごとの概要、Next Steps / TODO候補、出典を残す
- `organize_zoom_inputs.py --all` で既存の Zoom AI Companion 議事録を一括整理できる

- `google-meet/YYYY-MM-DD-google-meet-meetings.md` は `organize_google_meet_inputs.py` が自動生成する
- 元データは `.company/inputs/conversations/YYYY-MM-DD-google-meet.md`
- Google Meet 日次整理版には、会議一覧、会議ごとの概要、Notes / Transcript、Next Steps / TODO候補、出典を残す
- `sync_google_meet.py` で `.company/inputs/00_GOOGLE_MEET_BOX/` から raw / normalized / conversation を作れる
- `organize_google_meet_inputs.py --all` で既存の Google Meet 議事録を一括整理できる

- `external/YYYY-MM-DD-*.md` は `import_drive_inbox.py` が自動生成する
- 元データは `.company/inputs/00_INPUT_BOX/`
- raw コピーは `.company/inputs/intake/raw/YYYY-MM-DD/` に保存する
- 外部インプット整理版には、出典、登録メタデータ、URL、テキスト抜粋、添付ファイル、TODO候補、活用メモを残す
- AIが読みやすい正規化テキストは raw 側の `normalized/all-normalized-content.md` へ残す
- `import_drive_inbox.py` で Google Drive 投入口を取り込める

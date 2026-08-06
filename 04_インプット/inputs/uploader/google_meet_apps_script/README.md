# Google Meet Apps Script Auto Export

`y-nakada@yn-factory.com` のGoogle Drive上で、Google Meetの録画・文字起こし・会議メモを巡回し、作業ディレクトリ側の `00_GOOGLE_MEET_BOX/` へ会議ごとのフォルダとして書き出すためのApps Script。

## 出力先

- Drive folder: `00_GOOGLE_MEET_BOX`
- Folder ID: `1doYv2SjuIgy421Kv_100-a2SCHYEHSRO`
- Local path: `04_インプット/inputs/00_GOOGLE_MEET_BOX/`

Apps ScriptがこのDriveフォルダへ書き出した後、Macの5分おき自動取り込みが `sync_google_meet.py` と `organize_google_meet_inputs.py --all --force` を実行する。

## 初回設定

1. `00_GOOGLE_MEET_BOX` のDriveフォルダを `y-nakada@yn-factory.com` に編集者として共有する。
2. `y-nakada@yn-factory.com` で <https://script.google.com/> を開く。
3. 新規プロジェクトを作成する。
4. `Code.gs` の内容を貼り付ける。
5. プロジェクト設定で `appsscript.json` を表示し、このフォルダの `appsscript.json` の内容に置き換える。
6. `setup()` を1回実行し、Drive / Docs / Trigger の権限を承認する。
7. `runNow()` を実行して、`00_GOOGLE_MEET_BOX` に出力が作られるか確認する。

## 自動実行

`setup()` は既存の `exportGoogleMeetArtifacts` トリガーを削除してから、5分おきの新しいトリガーを作成する。

## 対象

- `Meet Recordings` フォルダ配下のファイル
- タイトルに以下を含む最近45日以内のファイル
  - `Meet`
  - `Google Meet`
  - `meeting notes`
  - `transcript`
  - `recording`
  - `文字起こし`
  - `議事録`
  - `会議メモ`

## 出力形式

会議ごとに `00_GOOGLE_MEET_BOX/` 配下へフォルダを作成する。

- `metadata.json`
- `source.url`
- `meet-notes.txt` または `source-link.txt`

`metadata.json` は既存の `sync_google_meet.py` が読む形式に合わせている。

## 注意

- Google Docs形式の会議メモは本文テキストを `meet-notes.txt` として出力する。
- 動画・音声ファイルは既定ではコピーしない。必要な場合は `CONFIG.copyRecordingFiles` を `true` にする。
- `Meet Recordings` フォルダが存在しない場合でも、タイトル検索で候補を探す。
- `00_GOOGLE_MEET_BOX` への編集権限がない場合は出力に失敗する。

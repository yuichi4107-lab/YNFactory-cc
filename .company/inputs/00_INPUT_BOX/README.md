# 00_INPUT_BOX - Google Drive Input Drop

このフォルダは、PC / スマホ / タブレットから情報を登録するための投入口です。

Limitless AI のログが保存される `.company/inputs/` と同じ場所にあるため、Google Drive でこのフォルダを開き、保存したいものを置いてください。同期後に `import_drive_inbox.py` が `.company/inputs/` 内へ取り込みます。

## 入れられるもの

- テキストメモ: `.txt`, `.md`
- URLメモ: URLを書いた `.txt`, `.md`, `.url`, `.webloc`
- 画像: `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`, `.heic`
- PDF / Word / Excel / PowerPoint
- その他ファイル
- 複数ファイルをまとめたい場合は、フォルダごと置く

## スマホでの使い方

一発アップロード画面を使う場合:

1. Mac / Windows で `.company/inputs/start_upload_server_*` を起動する
2. 表示された `http://<PCのIP>:8787` をスマホ・PCで開く
3. テキスト、URL、画像、ファイルを選んで「登録する」を押す
4. 自動で raw / organized / indexes まで登録される

Google Drive アプリから直接置く場合:

1. Google Drive アプリで `.company/inputs/00_INPUT_BOX/` を開く
2. `+` からファイル、写真、スキャン、メモを追加する
3. Mac / Windows 側で Google Drive が同期される
4. 自動または手動で取り込みスクリプトが実行される

## 任意メタデータ

詳しく分類したい場合は、同じフォルダ内に `metadata.json` を置けます。

```json
{
  "title": "資料のタイトル",
  "tags": ["client", "proposal"],
  "priority": "normal",
  "related_project": "project-name",
  "todo_candidate": true,
  "todo_candidates": [
    "確認して見積もりに反映する"
  ],
  "notes": "補足メモ"
}
```

1ファイルだけにメタデータを付けたい場合は、以下のどちらかの名前で横に置けます。

- `filename.ext.meta.json`
- `filename.meta.json`

## 注意

- このフォルダ内の原本は、取り込み後も削除しません。
- 同じ場所の同じ内容は重複取り込みしません。
- 取り込まれた内容は `.company/inputs/intake/raw/` と `.company/inputs/organized/external/` に保存されます。
- AIが読みやすい正規化テキストは `.company/inputs/intake/raw/YYYY-MM-DD/<input-id>/normalized/` に保存されます。
- TODOは日別TODOへ直接入りません。まず TODO候補として保存されます。
- 自動取り込みは `.company/inputs/setup_auto_import_windows.bat` または `.company/inputs/setup_auto_import_mac.sh` で設定できます。
- Mac の自動取り込みは launchd で5分おきに実行され、`00_INPUT_BOX/` と `00_GOOGLE_MEET_BOX/` の両方を処理します。

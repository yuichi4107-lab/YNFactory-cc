# Google Apps Script Deploy

スマホ外出先から1画面で `.company/inputs/00_INPUT_BOX/` にアップロードするためのデプロイ手順。

## 現在設定済み

アップロード先フォルダ:

```text
.company/inputs/00_INPUT_BOX/
```

Google Drive folder ID:

```text
1BMtWrI2mklfTVLOQHPQm75ffxTM0MBSy
```

`Code.gs` には反映済み。

## 手順

1. ブラウザで以下を開く

```text
https://script.new
```

2. Apps Script プロジェクト名を設定

```text
YNFactory Input Uploader
```

3. `Code.gs` の内容を、このフォルダの `Code.gs` で置き換える

4. 左側の `+` から HTML ファイルを追加

```text
Index
```

5. `Index.html` の内容を、このフォルダの `Index.html` で置き換える

6. 歯車アイコンのプロジェクト設定から `appsscript.json` を表示し、このフォルダの `appsscript.json` で置き換える

7. 右上の `デプロイ` → `新しいデプロイ`

8. 種類で `ウェブアプリ` を選択

9. 設定

```text
説明: YNFactory Input Uploader
次のユーザーとして実行: 自分
アクセスできるユーザー: 自分のみ
```

10. デプロイして承認する

11. 表示された Web アプリ URL をスマホで開く

12. iPhone / iPad / Android のホーム画面に追加する

## 動作

Webアプリからアップロードすると、Drive上の `.company/inputs/00_INPUT_BOX/` に以下のようなフォルダが作成される。

```text
YYYYMMDD-HHMMSS-title/
  metadata.json
  note.md
  files/
```

その後、Mac / Windows 側でGoogle Driveが同期されると、daily sync または `import_drive_inbox.py` が raw / organized / indexes へ取り込む。

## 注意

- Apps Script の初回実行時に Drive へのアクセス承認が必要
- `アクセスできるユーザー` は最初は `自分のみ` 推奨
- 他のGoogleアカウントからも投稿したい場合だけ、公開範囲を広げる
- 大きすぎる動画ファイルはApps Scriptの制限にかかる可能性がある

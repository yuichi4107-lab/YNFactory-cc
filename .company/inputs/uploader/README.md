# One-Shot Input Uploader

保存先を毎回選ばずに、1つの画面から `.company/inputs/00_INPUT_BOX/` へ登録するための仕組み。

## 1. 今すぐ使える: ローカルLAN版

Mac:

```bash
.company/inputs/start_upload_server_mac.sh
```

Windows:

```bat
.company\inputs\start_upload_server_windows.bat
```

起動後に表示される `http://<PCのIP>:8787` を、同じWi-Fiの iPhone / iPad / Android / PC で開く。

アップロードすると以下が自動で行われる。

1. `.company/inputs/00_INPUT_BOX/` に保存
2. `.company/inputs/import_drive_inbox.py` を実行
3. raw / organized / index へ登録
4. 拡張子ごとの正規化テキストを raw 側の `normalized/` に保存

任意で環境変数 `YN_INPUT_UPLOAD_TOKEN` を設定すると、アップロード画面でトークン入力が必要になる。

## 2. 外出先向け: Google Apps Script版

`google_apps_script/` の3ファイルをGoogle Apps Scriptへ配置する。

`Code.gs` の `INPUT_BOX_FOLDER_ID` は設定済み。

```text
1BMtWrI2mklfTVLOQHPQm75ffxTM0MBSy
```

デプロイ後のWebアプリURLをスマホのホーム画面に追加すれば、外出先からでも1画面でアップロードできる。

Apps Script版はDriveへ保存するところまでを担当する。Mac/Windows側でGoogle Drive同期後、daily sync または `import_drive_inbox.py` が登録処理を行う。

詳細手順は `google_apps_script/DEPLOY.md` を参照。

## 3. 自動取り込み

Google Apps Script版はDriveへ保存するだけなので、PC側でDrive同期後に自動取り込みを走らせる。

Windowsで5分おきに自動取り込みする:

```bat
.company\inputs\setup_auto_import_windows.bat
```

解除:

```bat
.company\inputs\remove_auto_import_windows.bat
```

タスクスケジューラ登録が使えない場合は、ログイン中だけ動くループ版を起動する。

```bat
.company\inputs\start_auto_import_loop_windows.bat
```

Macで5分おきに自動取り込みする:

```bash
.company/inputs/setup_auto_import_mac.sh
```

解除:

```bash
.company/inputs/remove_auto_import_mac.sh
```

一時的にログイン中だけ動かす場合:

```bash
.company/inputs/start_auto_import_loop_mac.sh
```

## 4. Google Meet 自動巡回

Google Meet の録画・文字起こし・会議メモは、`google_meet_apps_script/` のApps Scriptで `y-nakada@yn-factory.com` のDriveを5分おきに巡回する。

出力先は設定済み。

```text
00_GOOGLE_MEET_BOX
1doYv2SjuIgy421Kv_100-a2SCHYEHSRO
```

Apps Scriptが `00_GOOGLE_MEET_BOX/` へ会議ごとのフォルダを書き出し、Macの5分おき自動取り込みが `sync_google_meet.py` と `organize_google_meet_inputs.py --all --force` で raw / organized / index に登録する。

詳細手順は `google_meet_apps_script/README.md` を参照。

## 読み取り正規化

拡張子によってAIが直接読めない可能性があるため、取り込み時に以下を試す。

- `.txt`, `.md`, `.csv`, `.json`, `.html`: 直接テキスト化
- URLメモ: URL本文を取得できる場合はテキスト化
- `.docx`, `.xlsx`, `.pptx`: ZIP内XMLからテキスト抽出
- `.pdf`: `pypdf` または `pdftotext` が使える場合は抽出
- 画像: `tesseract` が使える場合はOCR
- その他: 原本保存 + 抽出不可理由を記録

抽出できなかった場合でも原本は保存され、`normalized/all-normalized-content.md` に状態が記録される。

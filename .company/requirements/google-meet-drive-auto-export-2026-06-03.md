---
date: 2026-06-03
status: ready-for-google-authorization
owner_request: "y-nakada@yn-factory.com のGoogle Meetを自動取り込みしたい"
---

# Google Meet Drive Auto Export 要件定義・品質チェック

## ゴール

`y-nakada@yn-factory.com` のGoogle Drive上に保存される Google Meet 録画・文字起こし・会議メモを自動巡回し、作業ディレクトリ側の `00_GOOGLE_MEET_BOX/` へ書き出した上で、既存のMac 5分おき自動取り込みで raw / organized / index へ登録する。

## 方式

Google Apps Script方式を採用する。

- Google側: Apps Scriptが `y-nakada@yn-factory.com` のDriveを5分おきに巡回する
- Drive出力先: `00_GOOGLE_MEET_BOX` (`1doYv2SjuIgy421Kv_100-a2SCHYEHSRO`)
- ローカル側: 既存のMac 5分おき自動取り込みが `sync_google_meet.py` と `organize_google_meet_inputs.py --all --force` を実行する

## スコープ

- `Meet Recordings` フォルダ配下を巡回する
- 最近45日以内のファイルから、Meet / transcript / recording / 文字起こし / 議事録 / 会議メモ を含むファイルを候補にする
- Google Docs形式の会議メモは本文を `meet-notes.txt` として出力する
- 動画・音声ファイルは既定ではコピーせず、リンクとメタデータを残す
- 出力は会議ごとのフォルダにする
- `metadata.json` は既存 `sync_google_meet.py` が読める形式にする
- 重複防止のため、Apps Script Propertiesに source file ID と modifiedAt を保存する

## 成果物

- `.company/inputs/uploader/google_meet_apps_script/Code.gs`
- `.company/inputs/uploader/google_meet_apps_script/appsscript.json`
- `.company/inputs/uploader/google_meet_apps_script/README.md`
- `.company/inputs/uploader/README.md` のGoogle Meet自動巡回セクション

## 現在の権限状態

`00_GOOGLE_MEET_BOX` のDriveメタデータ確認結果:

- owner: `yuichi4107@gmail.com`
- anyone: reader
- `y-nakada@yn-factory.com`: 現時点では編集権限なし

そのため、Apps Scriptを `y-nakada@yn-factory.com` で動かす前に、`00_GOOGLE_MEET_BOX` を `y-nakada@yn-factory.com` へ編集者共有する必要がある。

## 残る初回設定

1. `00_GOOGLE_MEET_BOX` を `y-nakada@yn-factory.com` に編集者共有する
2. `y-nakada@yn-factory.com` で Apps Script プロジェクトを作る
3. `Code.gs` と `appsscript.json` を貼り付ける
4. `setup()` を1回実行してDrive / Docs / Trigger 権限を承認する
5. `runNow()` で `00_GOOGLE_MEET_BOX` に出力されるか確認する
6. Mac側の5分おき取り込みログで `sync_google_meet.py` が取り込むことを確認する

## 品質チェック

スコア: 88/100 PASS

- 方式妥当性: 20/20
- 既存Google Meet importerとの接続: 20/20
- 重複防止と運用安全性: 18/20
- ドキュメント化: 20/20
- Google側セットアップ完了度: 10/20

残リスク:

- Apps ScriptはOAuth承認が必要なため、この環境だけでは完全デプロイまで完了できない
- `y-nakada@yn-factory.com` がMeet生成物の owner / reader でない会議は取得できない
- `00_GOOGLE_MEET_BOX` への編集権限がないと出力できない
- Google Meet側で録画・文字起こし・会議メモが有効化されていない会議は生成物が存在しない

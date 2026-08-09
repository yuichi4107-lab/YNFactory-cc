# 00_GOOGLE_MEET_BOX - Google Meet Intake

Google Meet の議事録、文字起こし、会議メモ、録画メモを置く投入口。

## 入れられるもの

- Google Meet の文字起こしをエクスポートした `.txt`, `.md`, `.docx`, `.pdf`
- Gemini / Google Meet の会議メモ
- Google Docs からダウンロードした `.docx` または `.txt`
- 会議ごとのフォルダ一式

注意: Google Drive for desktop で見える `.gdoc` はGoogle Docsへのショートカットで、本文はローカルファイル内に入っていない。`.gdoc` も取り込み対象にするが、本文が必要な場合はGoogle Docsから `.docx`, `.txt`, `.pdf` のいずれかで保存してこのフォルダに置く。

## 任意メタデータ

会議情報を補足したい場合は、会議フォルダに `metadata.json` を置く。

```json
{
  "title": "会議タイトル",
  "date": "2026-06-03",
  "start": "2026-06-03T10:00:00+09:00",
  "end": "2026-06-03T11:00:00+09:00",
  "participants": ["Aさん", "Bさん"],
  "tags": ["client", "meeting"],
  "todo_candidates": [
    "提案書を更新する"
  ]
}
```

## 取り込み

通常は daily sync または自動取り込みで実行される。

手動実行:

```bash
python .company/inputs/sync_google_meet.py
python .company/inputs/organize_google_meet_inputs.py --all --force
```

## Google Meet 自動巡回

`y-nakada@yn-factory.com` のGoogle Driveから自動でMeet生成物を拾う場合は、`.company/inputs/uploader/google_meet_apps_script/` のApps Scriptを使う。

- Apps Scriptが `Meet Recordings` やMeet関連Docsを巡回する
- 会議ごとのフォルダをこの `00_GOOGLE_MEET_BOX/` に出力する
- Macの5分おき自動取り込みが raw / organized / indexes へ登録する

出力先DriveフォルダID:

```text
1doYv2SjuIgy421Kv_100-a2SCHYEHSRO
```

## 保存先

- raw整理前: `.company/inputs/intake/google_meet/raw/`
- conversation raw: `.company/inputs/conversations/YYYY-MM-DD-google-meet.md`
- organized: `.company/inputs/organized/google-meet/`
- indexes: `.company/inputs/indexes/google-meet-*.md`

daily sync / 自動取り込みに組み込み済みなので、このフォルダに置いた後は次回同期で取り込まれる。Mac の5分おき自動取り込みを有効化している場合は、`00_INPUT_BOX/` と一緒にこのフォルダも処理される。

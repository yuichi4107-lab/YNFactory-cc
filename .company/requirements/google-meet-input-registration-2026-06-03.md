---
date: 2026-06-03
status: done
owner_request: "Zoomと同じようにGoogle Meetも取り込みたい"
---

# Google Meet Input Registration 要件定義・品質チェック

## ゴール

Google Meet の議事録、文字起こし、会議メモを Zoom と同じようにインプットへ取り込み、raw 原本、正規化テキスト、日別conversation、整理済みインプット、横断索引を保存する。

## スコープ

- `.company/inputs/00_GOOGLE_MEET_BOX/` を Google Meet 専用投入口として使う
- `.txt`, `.md`, `.docx`, `.pdf`, 会議フォルダを取り込む
- raw コピーを `.company/inputs/intake/google_meet/raw/YYYY-MM-DD/<input-id>/` に保存する
- AIが読みやすい正規化テキストを `normalized/all-normalized-content.md` に保存する
- 日別conversationを `.company/inputs/conversations/YYYY-MM-DD-google-meet.md` に生成する
- 活用版を `.company/inputs/organized/google-meet/YYYY-MM-DD-google-meet-meetings.md` に生成する
- 横断索引を `.company/inputs/indexes/google-meet-*.md` に生成する
- daily sync / Windows sync に Google Meet 取り込みを組み込む
- Google Drive ネイティブの `.gdoc` は本文が入っていないため、URLと `needs_export` 状態を残す

## 完了条件

- Google Meet 専用投入口がある
- 投入口の会議メモを raw と normalized に保存できる
- 日別conversationから organized input を生成できる
- `google-meet-meetings.md`, `google-meet-next-steps.md`, `google-meet-topics.md` が自動生成される
- daily sync 実行時に `sync_google_meet.py` と `organize_google_meet_inputs.py --all --force` が呼ばれる
- `.gdoc` を本文抽出済みと誤判定せず、エクスポートが必要な状態として残す
- TODO候補は日別TODOへ直接入れず、候補として保存する

## 品質チェック

スコア: 94/100 PASS

- Zoom相当の保存構造: 20/20
- raw保持と出典参照: 20/20
- normalized / organized / index 生成: 20/20
- daily sync 組み込み: 19/20
- Google Docsネイティブ形式への安全な扱い: 15/20

検証:

- `python3 -m py_compile .company/inputs/import_drive_inbox.py .company/inputs/sync_google_meet.py .company/inputs/organize_google_meet_inputs.py`
- `bash -n /Users/yuichi/scripts/run_limitless_sync.sh`
- `bash -n .company/inputs/run_daily.sh`
- 一時ディレクトリのサンプル会議で `sync_google_meet.py` と `organize_google_meet_inputs.py --all --force` を実行し、raw / normalized / conversation / organized / indexes の生成を確認
- 実投入口では対象ファイル0件で、空の Google Meet index 生成まで確認

残リスク:

- Google Meet の標準保存先フォルダは現時点でローカルDrive内に確認できていないため、Phase 1 は `.company/inputs/00_GOOGLE_MEET_BOX/` への投入方式
- Google Docs ネイティブ本文の自動取得には Google Drive API / Apps Script / OAuth 承認が必要
- `.gdoc` だけでは本文が取得できないため、本文利用が必要な場合は `.docx`, `.txt`, `.pdf` で保存する

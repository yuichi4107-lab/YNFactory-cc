---
date: 2026-06-03
status: done
owner_request: "zoomの実装"
---

# Zoom Organized Inputs 要件定義・品質チェック

## ゴール

Zoom から取り込んだ meeting summaries を raw 原本として保持しつつ、後から顧客対応・面接・TODO候補として使いやすい整理済みインプットに変換して保存する。

## スコープ

- `.company/inputs/conversations/*-zoom.md` の raw Zoom 議事録はそのまま保持する
- `.company/inputs/organized/zoom/` に日次の整理済み Zoom インプットを生成する
- `.company/inputs/indexes/` に Zoom 系の横断索引を生成する
- 毎朝の inputs 同期フローに Zoom 同期と organized 化を組み込む
- Limitless / lifelog の organized 化とは別系統として扱う

## 完了条件

- 日次 organized ファイルに、会議一覧、開始・終了時刻、概要、Next Steps / TODO候補、活用メモ、出典が入る
- organized ファイルから raw Zoom 原本を辿れる
- Next Steps は日別TODOへ直接投入せず、TODO候補として保存される
- `zoom-meetings.md`、`zoom-next-steps.md`、`zoom-clients.md` が自動生成される
- daily sync 実行時に `sync_zoom.py` と `organize_zoom_inputs.py --all --force` が呼ばれる
- 既存 Zoom raw ファイルがバックフィル整理される
- Zoom 同期に失敗しても既存 raw / organized ファイルは保持され、Limitless 側の取り込みを巻き込まない

## 品質チェック

スコア: 95/100 PASS

- 構造適合: 20/20
- raw 保持と出典参照: 20/20
- daily sync 組み込み: 20/20
- バックフィル: 20/20
- 運用安全性: 15/20

残リスク:

- Zoom 側の API 認証・取得結果に依存するため、取得対象日以外の過去 meeting summaries が返る場合がある。daily sync では全 raw を再整理して取りこぼしを防ぐ
- `zoom-clients.md` は現時点では会議タイトル由来の簡易抽出であり、顧客台帳への昇格は別工程で確認する

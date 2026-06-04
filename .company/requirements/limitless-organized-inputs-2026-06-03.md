---
date: 2026-06-03
status: done
owner_request: "インプットに取り込まれた内容を整理して保存する実装"
---

# Limitless Organized Inputs 要件定義・品質チェック

## ゴール

Limitless AI から取り込んだ raw lifelog と抽出済み insights を、後から判断材料として使いやすい整理済みインプットとして保存する。

## スコープ

- `.company/inputs/conversations/` の raw lifelog はそのまま保持する
- `.company/secretary/inbox/*-lifelog-insights.md` を入力にする
- `.company/inputs/organized/lifelogs/` に日次の整理済みインプットを生成する
- `.company/inputs/indexes/` に lifelog 系の横断索引を生成する
- 毎朝の Limitless 同期フローに organized 化を組み込む

## 完了条件

- 日次 organized ファイルに、要約、TODO候補、決定事項、人物・連絡先、調査トピック、事業アイデア、出典が入る
- organized ファイルから raw 原本と抽出元を辿れる
- TODO候補は日別TODOへ直接投入せず、候補として保存される
- `lifelog-todo-candidates.md`、`lifelog-decisions.md`、`lifelog-people.md`、`lifelog-topics.md` が自動生成される
- daily sync 実行時に `organize_inputs.py` が呼ばれる
- 既存抽出済み lifelog insights がバックフィル整理される

## 品質チェック

スコア: 95/100 PASS

- 構造適合: 20/20
- raw 保持と出典参照: 20/20
- daily sync 組み込み: 20/20
- バックフィル: 20/20
- 運用安全性: 15/20

残リスク:

- `extract_insights.py` は deprecated な `google.generativeai` を使っており、将来的には `google.genai` へ移行が必要
- organized 化は抽出済み insights ベースであり、raw lifelog 本文を再解釈するものではない

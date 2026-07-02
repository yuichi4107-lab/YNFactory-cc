---
date: "2026-07-02"
project: shorts-factory
status: registered
type: automation-runbook
related_skill: shorts-factory-ops
---

# shorts-factory 英語ツール名テロップ 自動化登録

## 登録目的

音声をなめらかにするためのカタカナ読みを維持しつつ、画面テロップでは英語ツール名・サービス名・一般的な英字略語を英字表記に統一する。

## 対象自動化

- `com.ynfactory.shorts-generate`: 09:00 / 14:00 / 19:00 の動画生成
- `shorts-factory/src/script_gen.py`: 台本正規化と表示バリデーション
- `shorts-factory/src/jp_text.py`: 字幕と読み上げの音韻比較
- `shorts-factory/prompts/script_prompt.md`: 生成時の表示/読み上げ分離指示
- `com.ynfactory.shorts-approval`: Telegram承認前の差し替え運用

## 必須ルール

- `display` は視聴者が認識しやすい英字表記にする。
- `tts_text` と `reading_kana` は音声安定のためカタカナ化してよい。
- `NotebookLM` / `Canva` / `Gamma` / `PDF` など、英語ツール名・英字略語のカタカナ表記をテロップへ焼き込まない。
- 新しい英語ツール名を追加する時は、表示正規化辞書と音韻比較辞書を同時に更新する。
- 表示ルールを直した後の既存候補は、旧queueを `skipped` にし、Telegramボタンを外してから再生成する。

## 確認手順

1. `script.json` の `cues[].display` にカタカナ化された英語ツール名がないか確認する。
2. `cues[].tts_text` / `reading_kana` では同じ語がカタカナ読みになっていることを確認する。
3. `subtitles.ass` に `NotebookLM` などの英字表記が入っていることを確認する。
4. `final.mp4` から該当フレームを切り出し、焼き込みテロップを目視確認する。
5. Telegram通知は新候補ごとに1回だけ送られていることを確認する。

## 完了条件

- 英語ツール名がテロップで英字表記になる。
- 読み上げ音声はカタカナ読みで安定する。
- 品質検証の字幕一致判定が、英字表示とカタカナ読みを同一語として扱う。
- 差し替え時に旧承認ボタンから誤投稿できない。

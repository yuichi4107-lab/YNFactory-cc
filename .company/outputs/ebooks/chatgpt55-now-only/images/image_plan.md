# 画像設計書

## 方針

- 文字中心の実用書なので、本文を邪魔しない落ち着いた図解・挿絵にする。
- 図解は本文側のキャプションで意味を伝える。画像内には細かい文字を入れない。
- 画風は、白背景または淡いグレー背景、青・緑・オレンジをアクセントにした清潔なビジネス書向けデジタルイラスト。
- 本文画像サイズは `1536x1024`、表紙は `1024x1536`。
- 保存先は `images/`、表紙は `KDP出版用/cover.png` と `KDP出版用/cover.jpg`。
- 画像生成は **APIを使わず、Codex経由のgpt-image 2.0** で行う。

## 本文画像一覧

### illustration_001.png
- 種別: 挿絵
- 差し込み位置: はじめに 0-1 の後
- 目的: AI選びに迷う読者の状態を視覚化する
- プロンプト:
```text
Business book illustration, a Japanese office worker at a clean desk looking at multiple floating AI app windows, feeling thoughtful but not panicked. Minimal modern digital illustration, soft white background, blue green and orange accents, no readable text, no logos, calm practical tone, 1536x1024.
```

### diagram_001.png
- 種別: 図解
- 差し込み位置: はじめに 0-5 の後
- 目的: 本書の二段構え「今はChatGPT中心 / ただし変化に備える」を図解する
- プロンプト:
```text
Clean business diagram without text: a central large circle representing ChatGPT as today's hub, surrounded by smaller circles representing Claude, Gemini, future AI, and information antenna. Arrows show flexible switching and periodic review. Minimal flat vector style, white background, blue green orange accents, no readable text, 1536x1024.
```

### diagram_002.png
- 種別: 図解
- 差し込み位置: 第1章 1-2 の後
- 目的: 文章・調査・資料・データ・画像が一つにつながる流れを示す
- プロンプト:
```text
Clean workflow diagram without text: five simple icons for writing, research, slides, data table, and image, all connected into one central AI workspace. Minimal modern vector, white background, blue green orange accents, no readable text, no logos, 1536x1024.
```

### illustration_002.png
- 種別: 挿絵
- 差し込み位置: 第1章 1-5 の後
- 目的: 人間が編集長、AIが作業を進める相棒になる変化を表す
- プロンプト:
```text
Modern Japanese business illustration: a person acting like an editor at a desk reviewing documents while a friendly abstract AI assistant organizes drafts, charts, and notes around them. Calm professional mood, no readable text, no logos, soft white background, 1536x1024.
```

### diagram_003.png
- 種別: 図解
- 差し込み位置: 第2章 2-1 の後
- 目的: 使い分けによる見えないコストを視覚化する
- プロンプト:
```text
Business diagram without text: left side shows scattered app bubbles connected by tangled lines, right side shows one organized hub with clean lines. Symbolizes switching cost versus context centralization. Minimal flat vector, white background, blue green orange accents, no readable text, 1536x1024.
```

### diagram_004.png
- 種別: 図解
- 差し込み位置: 第2章 2-8 の後
- 目的: 「中心はChatGPT、例外としてClaude/Gemini」を図解する
- プロンプト:
```text
Clean hub-and-spoke diagram without text: a central hub connected to three task zones, with two smaller side tools supporting specific tasks. Shows primary workflow plus exceptions. Minimal business vector, white background, blue and green with orange highlights, no readable text, 1536x1024.
```

### diagram_005.png
- 種別: 図解
- 差し込み位置: 第3章 3-5 の後
- 目的: Claude/Gemini/ChatGPTの役割分担を視覚化する
- プロンプト:
```text
Three-part comparison diagram without text: one area symbolizes polished long-form writing, one area symbolizes Google-style connected workspace, one central area symbolizes integrated workflow hub. Balanced respectful visual, no brand logos, minimal vector, white background, 1536x1024.
```

### illustration_003.png
- 種別: 挿絵
- 差し込み位置: 第3章 「一周回って」の本当の意味 の後
- 目的: 複数AIを試したうえでChatGPTへ戻る感覚を表す
- プロンプト:
```text
Conceptual business illustration: a person walking a circular path through several abstract AI stations and returning to a central clean workspace with confidence. Calm optimistic mood, no readable text, no logos, soft white background, blue green orange accents, 1536x1024.
```

### diagram_006.png
- 種別: 図解
- 差し込み位置: 第4章 4-8 の後
- 目的: 作成→評価→改善の品質ループを表す
- プロンプト:
```text
Clean circular workflow diagram without text: create, review, improve, finalize represented by simple document, magnifying glass, wrench, checkmark icons. Minimal vector style, white background, blue green orange accents, no readable text, 1536x1024.
```

### diagram_007.png
- 種別: 図解
- 差し込み位置: 第4章 プロンプトを育てる の後
- 目的: プロンプト改善ループを視覚化する
- プロンプト:
```text
Minimal business diagram without text: a prompt card goes through output, feedback, improved prompt, better output in a loop. Clean flat vector, white background, blue green orange accents, no readable text, 1536x1024.
```

### diagram_008.png
- 種別: 図解
- 差し込み位置: 第5章 5-5 の後
- 目的: 3か月ごとのAI見直しテストを表す
- プロンプト:
```text
Clean calendar-based review cycle diagram without text: three-month cycle, three abstract AI options, checklist, and decision arrow. Minimal vector style, white background, blue green orange accents, no readable text, 1536x1024.
```

### diagram_009.png
- 種別: 図解
- 差し込み位置: 第5章 乗り換えやすいデータ管理 の後
- 目的: 企画・原稿・プロンプト・品質基準を外部保存する構造を示す
- プロンプト:
```text
Business information architecture diagram without text: folders for project, manuscript, prompts, quality standards connected to multiple abstract AI tools. Shows portable data and flexible switching. Minimal vector, white background, blue green orange accents, no readable text, 1536x1024.
```

### illustration_004.png
- 種別: 挿絵
- 差し込み位置: おわりに 6-4 の前
- 目的: 今日の中心を持ちながら未来へ備える読後感を表す
- プロンプト:
```text
Optimistic final illustration for a Japanese business ebook: a person standing at a clean desk with a central AI workspace, looking toward a bright future path with subtle signal waves representing staying updated. Calm, practical, hopeful mood, no readable text, no logos, 1536x1024.
```

## 表紙

### cover.png / cover.jpg
- 種別: 表紙
- 保存先: `KDP出版用/cover.png`, `KDP出版用/cover.jpg`
- 目的: Kindle商品ページで、ChatGPT 5.5と「一周回って今はChatGPT」の結論が伝わる表紙
- 画面内文字:
  - ChatGPT 5.5時代の結論
  - 一周回って、いまはChatGPTだけでいい
  - Yuichi
- プロンプト:
```text
Kindle ebook cover, vertical 1024x1536. Clean modern Japanese business book design. Title text in Japanese: "ChatGPT 5.5時代の結論". Subtitle: "一周回って、いまはChatGPTだけでいい". Author: "Yuichi". Visual concept: a central luminous AI workspace hub with subtle surrounding orbit paths symbolizing Claude, Gemini, and future AI, returning to the center. Professional, sharp, high readability, white and deep navy base with blue green orange accents, no brand logos.
```

## 生成状況

- 2026-05-06: 画像設計完了
- 2026-05-06: 本文プレースホルダ挿入中
- 画像生成: API禁止。Codex画像キュー `.company/codex/queue/chatgpt55-ebook-images_20260506/` から gpt-image 2.0 で実行する

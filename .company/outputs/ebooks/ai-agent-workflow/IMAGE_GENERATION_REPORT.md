# 画像生成レポート

## 実施日
2026-06-02

## 方針
APIは使わない。`HANDOFF_MODE=codex-handoff` に近いが、別セッションや `.company/codex/queue/` へのジョブ引き渡しは使わず、このCodexセッション内で ChatGPT Images 2.0 相当の画像生成経路により直接生成・検証・配置した。

## 使用した生成経路

### 表紙・本文画像
- 使用経路: Codex/ChatGPT built-in `image_gen`（ChatGPT Images 2.0相当の対話側画像生成）
- API直叩き: なし
- `OPENAI_API_KEY`: 使用なし
- `openai-image-gen`: 使用なし
- `client.images.generate` / `client.images.edit`: 使用なし
- 対象: 本文画像18点 + 表紙背景

### 本文画像18点
- すべてChatGPT側の画像生成経路で再生成済み
- 旧Pillow/ローカル組版版は `_images_source/images_pre_chatgpt_image2_backup/` に退避
- 対象:
  - `_images_source/images/header_00_intro.png`
  - `_images_source/images/diagram_01_2024_2026.png`
  - `_images_source/images/diagram_02_model_choice.png`
  - `_images_source/images/illustration_03_stuck_training.png`
  - `_images_source/images/diagram_04_workflow_breakdown.png`
  - `_images_source/images/diagram_05_zokujinka_map.png`
  - `_images_source/images/illustration_06_interview.png`
  - `_images_source/images/diagram_07_ai_fit_matrix.png`
  - `_images_source/images/diagram_08_genai_or_tool.png`
  - `_images_source/images/diagram_09_human_in_loop.png`
  - `_images_source/images/illustration_10_browser_automation.png`
  - `_images_source/images/diagram_11_small_start.png`
  - `_images_source/images/diagram_12_ai_coding_loop.png`
  - `_images_source/images/diagram_13_security_guardrails.png`
  - `_images_source/images/illustration_14_ai_pro_person.png`
  - `_images_source/images/diagram_15_training_roadmap.png`
  - `_images_source/images/diagram_16_governance_cycle.png`
  - `_images_source/images/header_06_closing.png`

## 表紙の差し替え
- 旧Pillow仮表紙:
  - `KDP出版用/cover_pillow_backup.png`
  - `KDP出版用/cover_pillow_backup.jpg`
- 新表紙:
  - `KDP出版用/cover.png`
  - `KDP出版用/cover.jpg`
- 方式: AI生成背景 + ヒラギノ角ゴシックによる正確な日本語タイトル組版

## EPUB反映
- EPUB: `KDP出版用/AIが勝手に仕事する会社の作り方.epub`
- 本文画像: 18点（ChatGPT画像生成版）
- 表紙: 新表紙に差し替え済み
- 旧EPUBバックアップ: `KDP出版用/AIが勝手に仕事する会社の作り方_pre_image_rebuild.epub`
- ChatGPT Images 2.0本文画像差し替え前バックアップ: `KDP出版用/AIが勝手に仕事する会社の作り方_pre_chatgpt_image2_body_rebuild.epub`

## 品質確認
- 画像18点の寸法: すべて 1536x1024
- 表紙寸法: 1024x1536
- 日本語文字崩れ: 主要図解シートで目視確認済み
- EPUB構造: `mimetype` 先頭、章7本、本文画像18点、表紙画像あり
- 運用ルール: `ebook-to-manga` / `theme-to-ebook` から旧API実行サンプルを削除し、ChatGPT Images 2.0直生成に統一

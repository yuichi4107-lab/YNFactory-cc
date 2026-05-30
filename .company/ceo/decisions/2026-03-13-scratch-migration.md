---
created: "2026-03-13"
decision: "Gemini scratchフォルダからのプロジェクト移行"
status: completed
---

# 意思決定: scratchプロジェクトの移行

## 背景
`C:\Users\fcmdt\.gemini\antigravity\scratch\` に格納されていた2つの開発プロジェクトをワーキングディレクトリに移行。

## 決定事項
1. `biz_idea_generator/` と `keiba_ai/` をワーキングディレクトリ直下に配置
2. デバッグログ、キャッシュ、一時ファイル等を除外して整理移行
3. PM部署でプロジェクトとして登録・管理

## 振り分け
- **PM**: プロジェクト登録（biz-idea-generator, keiba-ai）
- **開発**: 技術管理

## 除外ファイル
- `__pycache__/`, `*.pyc`, `.env`, `debug_*`, `diagnostic_report.txt`, `inspection_result.txt`, `logs/`, `deploy_package.zip`, `*.temp.md`, `*.lnk` 等

---
created: "2026-03-11"
project: "YouTube 日本史解説チャンネル"
status: in-progress
tags: [YouTube, 動画, 日本史, コンテンツ]
---

# プロジェクト: YouTube 日本史解説チャンネル

## 概要
YouTubeチャンネル **「知ってたつもり日本史」** の教育漫画動画を制作・配信。
Comicle（コミクル）を使い、日本史テーマから台本→漫画CSV→動画を一気通貫で生成するパイプラインを運用中。

- **シリーズ名**: 歴史の敗者シリーズ（悲劇の歴史人物にフォーカス）
- **ターゲット視聴者**: 60代以上
- **キャラクター**: ミユ（女子大生・質問役）、ヨウイチ（教授・解説役）
- **過去の題材**: 崇徳上皇、平将門、道鏡、平宗盛、北条高時、後醍醐天皇、源義経

## ゴール
- チャンネル登録者数の拡大
- 定期的な動画投稿の継続
- 収益化の達成

## 制作パイプライン
`comicle-pipeline/` に全ワークフローが格納済み。詳細は `comicle-pipeline/CLAUDE.md` を参照。

```
Step 0: テーマ指定 → 台本Markdown作成
Step 1: convert_to_csv.py → 台本CSV（30字分割）
Step 2: add_furigana.py → フリガナ付与
Step 3: generate_comicle_csv.py → Comicle CSV生成（120ページ上限）
Step 4: compare_dialogues.py → 比較分析
Step 5: YouTubeメタデータ生成（タイトル3案 + 説明文）
Step 6: サムネイル用Geminiプロンプト生成
```

## マイルストーン
| # | マイルストーン | 期限 | 状態 |
|---|-------------|------|------|
| 1 | 制作パイプラインの配置 | 2026-03-11 | 完了 |
| 2 | 現在のチャンネル状況を棚卸し | - | 未着手 |
| 3 | コンテンツカレンダーの作成 | - | 未着手 |
| 4 | 収益化条件の達成 | - | 未着手 |

## 関連リソース
- **動画資料フォルダ（Google Drive）**: https://drive.google.com/drive/folders/1kpkiSPjcxg6e_B4I4oi_jGMjnUkvDCOR?usp=sharing
- **制作パイプライン**: `comicle-pipeline/` （作業ディレクトリ直下）
- **パイプライン詳細**: `comicle-pipeline/CLAUDE.md`
- **スクリプト群**: `comicle-pipeline/scripts/`
- **キャラ素材**: `comicle-pipeline/assets/characters/`
- **コマ割りテンプレ**: `comicle-pipeline/assets/templates/`

## 関連部署
- マーケティング: チャンネル戦略・SEO・サムネイル企画
- クリエイティブ: サムネイル・動画素材のデザイン
- リサーチ: 日本史テーマの調査・ファクトチェック
- 開発: パイプラインスクリプトの保守

## 配置場所
- `/AYC/` — 完成済みスクリプト・コミクル出力アーカイブ（30+テーマ）
- `/comicle-pipeline/` — 制作パイプライン（ツール群・素材・出力）

## メモ
- 2026-03-11 プロジェクト登録
- 2026-03-11 comicle-pipelineを作業ディレクトリ直下に配置完了
- 2026-03-14 プロジェクトマップ整備、配置場所を明記

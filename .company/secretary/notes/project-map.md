---
created: "2026-03-14"
type: reference
---

# プロジェクトマップ（全体地図）

> どこに何があるかを一覧できるマスターインデックス。
> 更新日: 2026-03-14

---

## 事業カテゴリ別マップ

### 1. コンテンツ制作事業

#### YouTube 日本史解説チャンネル
- **PM**: `pm/projects/youtube-japanese-history.md`
- **成果物**:
  - `/AYC/` — 完成済みスクリプト・コミクル出力（30+テーマ）
  - `/comicle-pipeline/` — 制作パイプライン（スクリプト変換・ふりがな・コミクルCSV生成ツール群）
  - `/comicle-pipeline/assets/` — キャラクターデザイン（ミユ.png, ヨウイチ.png）+ ページテンプレート
  - `/comicle-pipeline/output/` — 各テーマの生成ファイル
- **ステータス**: 稼働中

#### Instagram 転職系アカウント運用（@tenshoku_nocareer）
- **PM**: `pm/projects/instagram-career-account.md`
- **成果物**:
  - `/instagram_reel/` — 企業別フォルダ（各社に台本・キャプション・カバーコピー・画像ZIP）
  - 制作済み: SCREENホールディングス, SMC, 伊藤忠エネクス, 横河電機, 東洋エンジニアリング, 日本紙パルプ商事（6社）
- **ステータス**: 稼働中（フックA〜F使用済み）

#### マンガコンテンツ制作
- **PM**: `pm/projects/manga-content.md`
- **成果物**:
  - `/comicle-pipeline/` — YouTube日本史と共有のパイプライン
- **ステータス**: 稼働中

---

### 2. 電子書籍事業

#### 電子書籍 執筆・制作・出版（自社コンテンツ）
- **PM**: `pm/projects/ebook-writing-publishing.md`
- **成果物**:
  - `/zubora-toushi-rougo-2000man/` — 「ズボラ投資で老後資金2000万円」
    - `manuscript/` — 全5章＋はじめに＋おわりに（完成済み）
    - `KDP出版用/` — 書籍紹介文・ジャンル・キーワード
    - `project.md` — 企画書
- **ステータス**: 原稿完成・出版準備中

#### 電子書籍 出版プロデュース（クライアントワーク）
- **PM**: `pm/projects/ebook-publishing-produce.md`
- **成果物**:
  - `/ebook-produce/` — クライアント別フォルダ・ワークフロー・ポートフォリオ
- **ステータス**: 稼働中

---

### 3. 個人開発・ツール

#### ビジネスアイデアジェネレーター
- **PM**: `pm/projects/biz-idea-generator.md`
- **成果物**:
  - `/biz_idea_generator/` — Python自動生成ツール
    - `reports/` — 日次ビジネスプランレポート（MD+PDF、90+件）
    - `src/` — Limitlessクライアント、LLMクライアント、PDF変換、通知
- **ステータス**: 稼働中（日次自動実行）

#### 競馬予想AI
- **PM**: `pm/projects/keiba-ai.md`
- **成果物**:
  - `/keiba_ai/` — Python ML予測ツール
    - `src/` — データローダー、前処理、モデル、予測
    - `prediction_results.csv` — 予測結果
- **ステータス**: 開発中

---

### 4. AI活用・副業

#### AI副業プロジェクト
- **PM**: `pm/projects/ai-side-business.md`
- **成果物**:
  - `/ai-side-business/` — ココナラ資料・note記事・ポートフォリオ
- **ステータス**: 稼働中

#### AI業務改善コンテンツ100
- **PM**: `pm/projects/ai-business-content-100.md`
- **成果物**:
  - `/ai-business-content-100/` — Gems・GPTs制作物・テンプレート
- **ステータス**: 稼働中（納期: 2026-03-31）

---

### 5. 営業・マーケティング

#### YNファクトリー チラシ
- **PM**: ※未登録（クリエイティブ部署で管理）
- **成果物**:
  - `/flyers/` — A4チラシ（HTML + PDF + QRコード）
- **ブリーフ**: `creative/briefs/ynfactory-a4-flyer-brief.md`
- **ステータス**: 完成済み

---

## フォルダ → プロジェクト 逆引き

| フォルダ | プロジェクト | カテゴリ |
|---------|------------|---------|
| `/ai-business-content-100/` | AI業務改善コンテンツ100 | AI活用・副業 |
| `/ai-side-business/` | AI副業プロジェクト | AI活用・副業 |
| `/AYC/` | YouTube 日本史解説チャンネル | コンテンツ制作 |
| `/biz_idea_generator/` | ビジネスアイデアジェネレーター | 個人開発 |
| `/comicle-pipeline/` | YouTube 日本史 + マンガコンテンツ | コンテンツ制作 |
| `/ebook-produce/` | 電子書籍 出版プロデュース | 電子書籍 |
| `/flyers/` | YNファクトリー チラシ | 営業・マーケ |
| `/instagram_reel/` | Instagram 転職系アカウント | コンテンツ制作 |
| `/keiba_ai/` | 競馬予想AI | 個人開発 |
| `/zubora-toushi-rougo-2000man/` | 電子書籍（ズボラ投資） | 電子書籍 |

## 全プロジェクト配置完了（2026-03-14）

全9プロジェクトに専用フォルダが割り当て済み。未配置プロジェクトなし。

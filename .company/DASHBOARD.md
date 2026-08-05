# Project Dashboard

> 最終更新: 2026-08-01

## 全体サマリー

| 指標 | 値 |
|------|-----|
| 全プロジェクト | 14 |
| 進行中 | 8 |
| 計画段階 | 1 |
| 完了 | 6 |

---

## 進行中プロジェクト

### AI投資戦略システム `ai-trade-chart-pattern`
- **状態**: 本番稼働中（Coincheck BTC/JPY）+ シミュレーション記録運用中
- **進捗**: ██████████ 100%
- **MS**: 4/4 全完了
- **コード**: `/ai-trade-system/`
- **自動売買パイプライン**:
  - ✅ MS1: リアルタイムシグナルスキャナー (`src/signal/scanner.py`)
  - ✅ MS2: 自動発注・ポジション管理 (`src/trading/`) — Binanceテストネット検証済み
  - ✅ MS3: LINE通知 (`src/notification/notifier.py`) — 5種類の通知
  - ✅ MS4: Coincheck本番移行完了 — 実運用中（15,000円/トレード）
- **最適化戦略（DD30%以下）**:
  - BTC → v3 + SL=4%, Hold=30: PF 3.86, +252%, DD 29.4%
  - ETH → v3 + SL=2.5%, Hold=40: PF 2.49, +97%, DD 16.2%
  - SOL → v3 + TP=4%, Hold=15: PF 3.63, +77%, DD 19.9%
  - XRP → v7 + SL=4%, Hold=15: PF 3.17, +157%, DD 25.2%
- **運用情報**: VPS Docker(`ai-trader`)、シミュレーション週次/月次レポート自動生成
- **次のアクション**: シミュレーション結果で戦略評価を継続
- **Coincheck残高（2026-04-09確認）**: JPY 20,160円 / BTC 0 — ポジションなし
- **直近トレード**: 4/6 rsi_oversold_bounce買い → 4/8 TP決済（+456円 / +3.04%）

### [NEW] FX自動売買 `fx-auto-trading`
- **状態**: 設計完了・MS1着手中
- **進捗**: █░░░░░░░░░ 10%
- **MS**: 0/4 完了（MS1 進行中）
- **ブローカー**: OANDA Japan（API: REST v20）
- **初期資金**: 10万円
- **通貨ペア**: USD/JPY（メイン）、EUR/JPY（サブ）
- **戦略**: Phase1 MA+RSI → Phase2 AI転用 → Phase3 ハイブリッド
- **コード**: `/ai-trade-system/`（既存システム拡張）
- **設計書**: `/ai-trade-system/docs/oanda-adapter-design.md`
- **次のアクション**: MS1 — OANDA デモ口座開設 + OANDAアダプター実装

### [HOT] AI副業プロジェクト `ai-side-business`
- **状態**: Phase 2 集客・応募拡大フェーズ
- **進捗**: ███░░░░░░░ 33%
- **MS**: 6/18 完了（Phase 1 全完了）
- **目標**: 月間売上15万円（2026-06-30）
- **成果物**: `03_成果物/outputs/ai-side-business/`
- **統合元**: 旧「Claude Code営業活動」を吸収（2026-03-25）
- **次のアクション**: note公開確認 → ココナラ改善 → CW追加応募 → ランサーズ開設

### [DONE] YN Tools 統合ポータル `yn-tools-portal`
- **状態**: 本番稼働中（31ツール）
- **進捗**: ██████████ 100%
- **MS**: 8/8 完了（全MS完了）
- **目標**: SaaS公開（Google認証+月500円サブスク）
- **内容**: 営業自動化・メール送信・GEMS/GPT配布を統合ポータル化 + コミュニティ機能
- **コード**: `/yn-tools/`
- **本番URL**: https://tools.ynfactory.online
- **最新追加（2026-04-10）**: シフト作成アプリ（31番目）— 従業員管理・カレンダーUI・AI自動生成・Excelエクスポート。カスタマイズ案内バナーも追加
- **次のアクション**: note記事2本を投稿、プロフィール文のツール数を「31種類」に更新

### Instagram転職アカウント `instagram-career-account`
- **状態**: リール制作中
- **進捗**: ████░░░░░░ 40%
- **MS**: 1/4 完了（MS2 進行中）
- **成果物**: `03_成果物/outputs/instagram-reel/`（7社完了）、`03_成果物/outputs/instagram-stories/`（30/30枚完了）
- **次のアクション**: MS2完了 → MS3 投稿スケジュール運用開始

### 競馬予想AI `keiba-ai`
- **状態**: モデル学習フェーズ
- **進捗**: ████░░░░░░ 40%
- **MS**: 1/3 完了（MS2 進行中）
- **コード**: `/keiba_ai/`
- **次のアクション**: モデル学習・評価

### ビジネスアイデアジェネレーター `biz-idea-generator`
- **状態**: 運用中（全機能稼働）
- **進捗**: ██████████ 100%
- **MS**: 5/5 完了
- **コード**: `/biz_idea_generator/`
- **最終更新**: 2026-03-20 — API修正、品質ガード、プロンプト刷新、事業企画書自動生成

### YouTube日本史チャンネル `youtube-japanese-history`
- **状態**: パイプライン構築済み・本格運用前
- **進捗**: ██░░░░░░░░ 25%
- **MS**: 1/4 完了
- **コード**: `/AYC/`, `/comicle-pipeline/`
- **次のアクション**: チャンネル状況棚卸し

### 電子書籍 執筆・出版 `ebook-writing-publishing`
- **状態**: KDP出版済み
- **進捗**: ██████████ 100%
- **出版済み**: 2030年問題シリーズ 第3巻「少数精鋭＋AIが最強の経営である理由」、第4巻「最低賃金1500円の罠と連鎖倒産」（2026-04-04）
- **成果物**: `03_成果物/outputs/ebooks/03-company-positive/`, `03_成果物/outputs/ebooks/04-company-negative/`

### マンガコンテンツ制作 `manga-content`
- **状態**: KDP出版済み + vol1 KDP申請済み（2026-04-28）
- **進捗**: ██████████ 100%
- **出版済み**: 「AIで会社をつくった主婦の話」（2026-04-04）
- **KDP申請済み**: manga-career-restart vol1（2026-04-28、審査待ち）
- **成果物**: `03_成果物/outputs/ebooks/manga-ai-company/`, `03_成果物/outputs/ebooks/manga-career-restart/vol1/`
- **次のアクション**: vol2-vol4 すべて Codex 側で生成中（完了通知待ち → --import-manual → 自動EPUB → Step8メタ）
- **コード**: `/comicle-pipeline/`

### 電子書籍 出版プロデュース `ebook-publishing-produce`
- **状態**: 未着手
- **進捗**: ░░░░░░░░░░ 0%
- **MS**: 0/3 完了
- **次のアクション**: 案件状況の棚卸し

---

## 完了プロジェクト

### 電子書籍『日本の左派・リベラルは、なぜ自滅するのか』
- **完了日**: 2026-08-01
- **状態**: 統合原稿完成・最終QC 97/100
- **仕様**: 全16部・固定78節・本文相当125,794字
- **成果物**: `.company/projects/日本の左派リベラルはなぜ自滅するのか/`
- **未実施**: 表紙、EPUB、KDPメタデータ、出版申請・公開

### AI業務改善コンテンツ100 `ai-business-content-100`
- **完了日**: 2026-03-15（予定3/31→前倒し達成）
- **成果物**: `03_成果物/outputs/ai-business-content-100/`
- **内容**: Gems 50本 + GPTs 50本、全100件登録完了

### 営業自動化ツール `sales-automation-tool`
- **完了日**: 2026-03-20（Renderデプロイ完了）
- **成果物**: `/sales-automation/`
- **本番URL**: https://sales-automation-m1k9.onrender.com
- **ホスティング**: Render Free（Oregon）/ PostgreSQL Free
- **内容**: 企業リスト巡回→CRM→メール送信→ダッシュボード
- **要対応**: 管理者アカウント作成（/setup）、DATABASE_URL環境変数の設定

### メール送信システム `mail-system`
- **完了日**: 2026-03-20（Renderデプロイ完了）
- **成果物**: `/mail-system/`
- **本番URL**: https://mail-system-qamk.onrender.com
- **GitHubリポ**: `yuichi4107-lab/mail-system`
- **ホスティング**: Render Starter / PostgreSQL Basic-256mb
- **内容**: マルチユーザーメール送信（テンプレ・一括送信・履歴管理）
- **要対応**: なし（ログイン・登録画面の動作確認済み）

---

## 成果物マップ

```
03_成果物/outputs/
  ebooks/                   5冊（01〜04 + ずぼら投資）
  instagram-reel/           7社完了
  instagram-stories/        ストーリーズ画像30/30枚完了 + プロンプト集
  ai-business-content-100/  100件（完了）
  ai-side-business/         記事9本 + ポートフォリオ + ココナラ
  tech-articles/            9記事（完了）
  creative-guides/          9ガイド（完了）
  flyers/                   チラシ素材

プロジェクトルート（開発コード）
  ai-trade-system/          AI投資戦略
  sales-automation/         営業自動化
  biz_idea_generator/       アイデアジェネレーター
  keiba_ai/                 競馬予想AI
  mail-system/              メールシステム（移行予定）
  AYC/ + comicle-pipeline/  YouTube・マンガ
```

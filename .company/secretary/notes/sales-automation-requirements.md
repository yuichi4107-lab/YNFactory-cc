---
created: "2026-03-17"
topic: "営業自動化ツール 要件壁打ちまとめ"
tags: [sales-automation, requirements]
---

# 壁打ちまとめ: 営業自動化ツール要件定義

## 基本方針
- **利用者**: 自分で使いつつ、将来SaaS/受託で販売も視野
- **ターゲット**: 業種を特定しない汎用ツール
- **MVP範囲**: 企業リスト生成 → HP巡回 → メールアドレス抽出 + CSV出力
- **技術**: Pythonモノリス（FastAPI + Jinja2/HTMX + SQLite）
- **デプロイ**: まずローカル → 後でクラウドへ移行

## データソース
- **メイン**: Google Places API（合法・安定・仕様書の要件全網羅）
- **フォールバック**: Webスクレイピング（iタウンページ等）

## MVP機能（Phase 1）
1. キーワード × 地域で企業リストを生成（Google Places API）
2. HP巡回して情報取得（TOP/Contact/About/Company）
3. メールアドレス・SNSリンクを抽出
4. 結果をCSV出力

## 将来機能（Phase 2以降）
- 簡易CRM（ステータス管理）
- 営業スコアリング
- 営業メール自動送信（特定電子メール法に準拠）
- お問い合わせフォーム営業
- ダッシュボード

## 技術スタック確定
| 領域 | 技術 |
|------|------|
| フレームワーク | FastAPI |
| フロントエンド | Jinja2 + HTMX |
| DB | SQLite（dev）→ PostgreSQL（SaaS化時） |
| ORM | SQLAlchemy 2.0 |
| スクレイピング | BeautifulSoup4 + Playwright |
| 企業データ | Google Places API (New) |
| データ出力 | openpyxl + csv |

## 決定日: 2026-03-17

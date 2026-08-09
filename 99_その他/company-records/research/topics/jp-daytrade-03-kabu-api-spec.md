---
topic: "kabuステーションAPI仕様（2024年11月以降）"
project: "jp-stock-daytrade"
status: "completed"
created: "2026-04-15"
assignee: "research"
sources:
  - url: "https://kabucom.github.io/kabusapi/ptal/"
    title: "kabuステーション API ポータル - 三菱UFJ eスマート証券（公式）"
  - url: "https://kabucom.github.io/kabusapi/reference/index.html"
    title: "kabuステーションAPIリファレンス（公式）"
  - url: "https://kabu.com/item/kabustation_api/default.html"
    title: "kabuステーション®API - 三菱UFJ eスマート証券"
  - url: "https://kabu.com/company/pressrelease/20240430_4.html"
    title: "kabuステーション®利用料金の無料化（2024年6月3日〜）"
  - url: "https://kabu.com/company/lp/lp90.html"
    title: "kabu STATION API - 三菱UFJ eスマート証券"
  - url: "https://faq.kabu.com/s/article/k002520"
    title: "Q&A プランについて - 三菱UFJ eスマート証券"
  - url: "https://github.com/kabucom/kabusapi/issues/864"
    title: "kabuステーションAPIで過去のヒストリカルデータを取得できますか - GitHub Issue"
  - url: "https://kabutech.jp/data-api/kabu-api-setup"
    title: "kabuステーションAPI設定ガイド(2026) - kabutech"
  - url: "https://kabutech.jp/lab/kabu-api"
    title: "kabuステーション API 使い方ガイド - kabutech"
  - url: "https://qiita.com/hmdsg/items/c6842fe87ec4e0365241"
    title: "auカブコム証券のkabuステーションAPIを使ってみる - Qiita"
  - url: "https://python-fin.tech/automatic-stock-trading-3/"
    title: "kabuステーション®APIを利用するための初期設定 - Python FinTech講座"
  - url: "https://prtimes.jp/main/html/rd/p/000000041.000086540.html"
    title: "auカブコム証券 三菱UFJ eスマート証券ブランド変更 - PR TIMES"
---

# kabuステーションAPI仕様（2024年11月以降）

## サマリー
2024/11にauカブコム証券 → 三菱UFJ eスマート証券へブランド変更。APIサービス名は「kabuステーション API」を継続、互換性あり。REST + PUSH（WebSocket）の2系統で、寄り前気配を含む板情報をリアルタイム取得可能。localhost:18080で動作する個人PC向けAPIで、Windows版kabuステーション常駐が必須。Professionalプラン以上で無料利用。ヒストリカル最大600本（1分足等）は取得可だが本格的バックテスト用データは外部ベンダー推奨。

## 調査結果

### セクション1: ブランド変更の影響（2024年11月〜）
- 2024/11 auカブコム証券は **三菱UFJ eスマート証券** へブランド変更（社名変更）。
- APIサービス自体の仕様変更はなし、旧ドメイン（kabu.com）も継続利用可。
- 開発者ポータル・リファレンスURLも従来通り:
  - ポータル: https://kabucom.github.io/kabusapi/ptal/
  - リファレンス: https://kabucom.github.io/kabusapi/reference/index.html
  - GitHub: https://github.com/kabucom/kabusapi
- GitHub Issuesは引き続き有効で、公式サポート窓口として機能。

### セクション2: 公式ドキュメントURL
| リソース | URL |
|---|---|
| API ポータル | https://kabucom.github.io/kabusapi/ptal/ |
| REST/PUSH リファレンス | https://kabucom.github.io/kabusapi/reference/index.html |
| GitHub リポジトリ | https://github.com/kabucom/kabusapi |
| kabuステーション商品ページ | https://kabu.com/item/kabustation_api/default.html |
| FAQ | https://faq.kabu.com/s/article/k002520 |

### セクション3: REST / WebSocket 機能一覧
**REST API（主要エンドポイント）**
- `POST /kabusapi/token` — APIトークン発行（APIPassword認証）
- `GET /kabusapi/board/{symbol}@{exchange}` — 板情報・時価情報取得
- `GET /kabusapi/symbol/{symbol}@{exchange}` — 銘柄情報（名称・値幅・呼値単位等）
- `PUT /kabusapi/register` — PUSH配信銘柄登録
- `PUT /kabusapi/unregister` / `PUT /kabusapi/unregister/all` — 銘柄登録解除
- `POST /kabusapi/sendorder` — 現物/信用 発注
- `POST /kabusapi/sendorder/future` — 先物発注
- `POST /kabusapi/sendorder/option` — オプション発注
- `PUT /kabusapi/cancelorder` — 注文取消
- `GET /kabusapi/orders` — 注文一覧
- `GET /kabusapi/positions` — 保有ポジション
- `GET /kabusapi/wallet/cash` / `margin` / `future` / `option` — 余力
- `GET /kabusapi/ranking` — 値上がり率/値下がり率/売買高ランキング等
- `GET /kabusapi/apisoftlimit` — ソフトリミット
- `GET /kabusapi/primaryexchange/{symbol}` — 優先市場取得
- `GET /kabusapi/regulations/{symbol}` — 規制情報
- `GET /kabusapi/exchange/{symbol}` — 為替情報（通貨）

**PUSH API（WebSocket）**
- エンドポイント: `ws://localhost:18080/kabusapi/websocket`
- 事前に `register` で登録した銘柄の時価情報・板情報をリアルタイムで配信。
- 板更新のたびに1メッセージ（ミリ秒単位で受信可能）。

### セクション4: 寄り前気配取得API仕様
**エンドポイント**: `GET /kabusapi/board/{symbol}@{exchange}`
- exchange: 1=東証、3=名証、5=福証、6=札証

**主要レスポンスフィールド（寄り前気配関連）**:
```json
{
  "Symbol": "7203",
  "SymbolName": "トヨタ自動車",
  "Exchange": 1,
  "CurrentPrice": 2500,
  "CurrentPriceTime": "2026-04-15T08:58:00+09:00",
  "CalcPrice": 2500,          // 寄り前の想定約定価格
  "AskPrice": 2501,
  "AskQty": 10000,
  "AskSign": "0101",          // 特別気配フラグ（後述）
  "BidPrice": 2499,
  "BidQty": 15000,
  "BidSign": "0101",
  "OverSellQty": 500000,      // 板に表示されない売り（成行・下限値以下）
  "UnderBuyQty": 300000,      // 板に表示されない買い（成行・上限値以上）
  "TotalMarketValue": 42000000000000,
  "ClearingPrice": null,
  "Sell1": {"Price": 2501, "Qty": 10000, "Sign": "0101", "Time": "..."},
  "Sell2": {...}, ... "Sell10": {...},
  "Buy1":  {"Price": 2499, "Qty": 15000, "Sign": "0101", "Time": "..."},
  "Buy2":  {...}, ... "Buy10": {...},
  "TradingVolume": 0,
  "TradingValue": 0,
  "VWAP": null,
  "HighPrice": null, "LowPrice": null, "OpeningPrice": null,
  "ChangePreviousClose": 0,
  "ChangePreviousClosePer": 0,
  "PreviousClose": 2480
}
```

**AskSign/BidSign（特別気配フラグ）の主な値**:
- `"0101"`: 現値（通常気配）
- `"0102"`: 一般気配
- `"0103"`: 特別気配
- `"0107"`: 中断前の特別気配
- その他: 寄前気配、連続約定気配、寄前気配（特別気配）等（公式リファレンスに一覧あり）

**寄り前気配戦略での活用**:
- 売り圧/買い圧比率 = `AskQty / BidQty` もしくは累積 `Sum(Sell1..Sell10.Qty) / Sum(Buy1..Buy10.Qty)`
- 板厚み = 上下10本の累積株数
- 成行偏り = `OverSellQty` vs `UnderBuyQty`
- 特別気配監視 = `AskSign` / `BidSign` に "03" 系が出たら注意

### セクション5: ヒストリカルデータ取得可否
- **公式見解（GitHub Issue #864）**: kabuステーション APIは **原則リアルタイム向けで、ヒストリカル取得APIは提供していない**。
- `GET /kabusapi/board` は現在時点のスナップショット、`GET /kabusapi/ranking` は現在のランキングのみ。
- kabuステーションアプリ本体にはチャート機能があり、1分足・日足の表示は可能だが、APIからバルク取得するエンドポイントはない。
- **バックテスト用途**: 以下の手段が必要
  1. PUSH APIを常時接続してローカル DB（SQLite/InfluxDB等）に毎日保存（自前で履歴構築）
  2. 有料ベンダー利用（Bloomberg / Refinitiv / Quick / 株式会社QUICK の PXKIT 等）— 要検証
  3. J-Quants API（JPX公式、2022〜）— 日足/週足/月足、業績、財務。分足は有料プラン（LightPlanは無料、Standard/Premiumで日中データ）
  4. yfinance（Yahoo Finance非公式）— 日足中心、分足は過去7日程度と制限
- **結論**: 日中寄り前気配データは **自前で毎日 PUSH API から保存** するのが現実的。

### セクション6: 利用料金
- **kabuステーション通常プラン**: **無料**（2024/6/3〜、申込不要）。
- **Professionalプラン**: 上位プラン、**API利用にはこのプラン以上が必要**。自動適用条件:
  - 信用取引口座開設 or 先物オプション口座開設 or 預り資産1,000万円以上 など複数条件のいずれかを満たすと自動適用（要検証、最新条件は公式FAQ確認）。
- **Premiumプラン**: さらに上位（詳細条件は公式）。
- **API経由の信用取引手数料**: **無料（0円）** — 大きなメリット。
- **API経由の現物取引手数料**: 通常の現物手数料体系に準じる。

### セクション7: 認証方式
- **ローカルホスト経由**: `http://localhost:18080/kabusapi/` （本番）/ `http://localhost:18081/kabusapi/` （テスト）
- **トークン発行フロー**:
  1. kabuステーション アプリを起動 → ログイン
  2. アプリの「設定 > API」タブで「APIシステム設定」を有効化、API Passwordを設定
  3. `POST /kabusapi/token` に `{"APIPassword": "xxxx"}` を送信
  4. レスポンスの `Token` を `X-API-KEY` ヘッダに付与して以降のAPI呼び出し
- **セキュリティ**: Localhost限定なので外部からの直接アクセス不可。Linux/Macから使う場合はWindows側にnginxでリバースプロキシ + SSH等が定番。

### セクション8: 利用条件
- **口座要件**: 三菱UFJ eスマート証券の証券総合口座（無料開設可）
- **API利用申込手順**:
  1. 証券口座開設
  2. kabuステーション（Windowsアプリ）ダウンロード&インストール
  3. アプリにログインし「設定 > API」でAPIを有効化、APIパスワード設定
  4. 申込手続きは不要（プラン条件を満たせばProfessional自動適用）
- **注意**: kabuステーションは **Windowsアプリ（.NET）** で、macOS/Linuxネイティブ版なし。
- **1日1回再起動推奨**: 情報更新の都合でアプリの24時間以上連続稼働は非推奨（要検証）。

### セクション9: 他証券API比較（2025年時点）

| 証券会社 | API提供 | 種類 | 料金 | 対応市場 | 特徴 |
|---|---|---|---|---|---|
| **三菱UFJ eスマート証券（旧auカブコム）** | ○ 公式 | REST + PUSH | 無料（Professional以上） | 現物/信用/先物/オプション | 株・先オプ両対応は本API唯一。localhost経由。Windows必須 |
| **SBI証券** | × | — | — | — | 公式API非公開。一部の機関/業者向けFIX対応のみ。個人向けなし |
| **楽天証券** | △ | MarketSpeed II RSS（Excel） | 無料 | 現物/信用/先物 | Excel経由でリアルタイム取得可。発注は要工夫 |
| **マネックス証券** | △ | トレステ（トレーディングステーション） | 無料 | 現物/FX | TradeStation互換、EasyLanguageでの自動売買。ただし日本株部分は限定的 |
| **松井証券** | × | — | — | — | 公式API非公開 |
| **岡三オンライン** | × | — | — | — | 公式API非公開 |
| **SBIネオトレード** | × | — | — | — | 公式API非公開 |

**結論**: **日本株で個人向けに本格的REST + PUSH APIを提供しているのは kabuステーション API が実質唯一**。楽天RSSはExcel前提で自動売買構築が面倒、マネックストレステは日本株現物の発注APIが貧弱。

## 結論
- 2024/11のブランド変更でAPI仕様は変更なし、ドキュメント/URL/GitHubも継続利用可。
- 寄り前気配戦略に必要なフィールド（板10本、特別気配フラグ、OverSell/UnderBuy、CalcPrice）は全て `/board` エンドポイントで取得可能。
- ヒストリカルAPIがないため、**PUSH APIで毎日自前保存 or J-Quants API併用** が必須。
- Professionalプラン無料適用には条件あり（信用口座 or 預資1,000万円等）、 **オーナー口座で現在適用済みか要確認**。
- Windowsアプリ常駐必須のため、Surface据置 or Windows VPSのいずれかが必要（詳細はトピック4）。
- 競合APIが実質存在しないため、**kabuステーションAPI一択** が現実解。

## ネクストアクション
- [ ] オーナーのeスマート証券口座でProfessionalプラン適用状況を確認（信用口座未開設なら開設）
- [ ] kabuステーション for Windowsをオーナー環境にインストール、APIタブで有効化・APIパスワード設定
- [ ] localhost:18080/kabusapi/token のトークン発行フローを手動試験
- [ ] `/board/{symbol}@1` で寄り前気配（8:45）のサンプルレスポンスを実測取得・スキーマ確定
- [ ] PUSH API で日次の板データ保存スクリプト（Python）の設計
- [ ] J-Quants API 無料プランで日足バックテスト用母集団の取得可否を試験
- [ ] kabuステーション本体の24時間連続稼働の可否を公式FAQで最終確認（要検証）

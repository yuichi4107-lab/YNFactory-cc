# 要件定義書
## サクソバンク証券 OpenAPI 連携 — ai-trade-system 統合

作成日: 2026-04-12
ステータス: 承認待ち

---

## ゴール

既存 ai-trade-system（BTC/JPY 自動売買稼働中）に SaxoBank OpenAPI アダプター
`saxo_client.py` を追加し、USD/JPY・EUR/JPY の Sim 環境での接続確認・
バックテスト実行まで完了させる。
（Live 口座への移行は Sim 動作確認後に別途判断する。）

---

## 前提・リスク・矛盾点の整理

### 前提として確定している事項

| 項目 | 内容 |
|------|------|
| Saxo Sim 環境 | Developer Portal で即時トークン発行（24 時間有効） |
| 採用ライブラリ | `hootnot/saxo_openapi`（PyPI: saxo-openapi）または httpx 直接呼び出し |
| 通貨ペア表記 | Saxo は `USDJPY`（区切りなし）。内部は `USD/JPY`（スラッシュ）で統一し変換する |
| インターフェース | `OandaClient` と同じ `ExchangeClient` 互換インターフェースを踏襲 |
| 運用サーバー | ConoHa VPS（Linux）、Docker コンテナ分離 |

### リスク・前提として明記する事項

**1. Live API 申請条件の食い違い（未確定）**

- 公式サイト記載: 最低入金なし・利用料無料
- tetori.jp 情報: 200 万円必須との報告あり

→ 本要件定義ではこの点を「工程 4（Sim 接続テスト）完了後に判断する」とスコープ外に置く。
  Sim 動作後に口座開設 → API 申請 → Live 接続の可否を確認するためのチェックポイントを
  設ける（詳細は下記「Live 移行判断ポイント」参照）。

**2. OAuth Token の有効期限問題**

- Personal Access Token（PAT）: Sim 用として 24 時間有効。開発・テスト目的にのみ使用可
- 本番運用には OAuth 2.0 Authorization Code Flow + refresh_token が必要

→ 工程 2（saxo_client.py 実装）の**スコープ外**とし、工程 4 完了後に別工程「工程 2b: OAuth
  フロー実装」として追加する。現段階では PAT 認証のみ実装し、Token 更新が必要になったら
  対応する設計（差し替えポイント明示）とする。

**3. saxo_openapi ライブラリ vs httpx 直接呼び出し**

- OANDA 実装時は oandapyV20 が Python 3.12 非対応のため httpx を採用した
- saxo_openapi は 2024 年時点で更新があり、Python 3.12 動作報告あり（要動作確認）
- どちらを採用するか: **工程 2 着手時に動作確認してから決定する**
  （saxo_openapi が動作すれば採用、問題があれば httpx 直接呼び出しにフォールバック）

**4. 既存 BTC/JPY 自動売買との並行運用**

- 既存 ai-trader コンテナは Coincheck（BTC/JPY）で 24 時間稼働中
- FX システムは別コンテナ（`ai-trader-fx`）として分離する
- データディレクトリは `data/` 配下に `fx/` サブディレクトリで分離する
- docker-compose.yml への追記で対応（既存サービスには触れない）

---

## スコープ

### やること

- Saxo Sim 環境のセットアップ手順書作成（オーナー向け）
- `saxo_client.py` の実装（ExchangeClient 互換、PAT 認証）
- `trader.py` への `--exchange saxo_sim / saxo` オプション追加
- `scanner.py` の FX データ取得を Saxo にルーティング
- `strategy_config.json` の通貨ペア表記を Saxo 仕様に合わせた確認・修正
- Sim 環境での実接続テスト（残高・OHLCV・テスト注文）
- USD/JPY 過去 1 年 OHLCV でバックテスト実行

### やらないこと

- Live 口座開設・Live API 申請（Sim 動作確認後に別途判断）
- OAuth 2.0 refresh_token フロー実装（PAT のみで進める）
- EUR/USD など JPY 以外のクォート通貨ペアの追加（スコープ外）
- VPS 本番デプロイ（工程 5 完了後に別途実施）
- 既存 BTC/JPY Coincheck システムへの変更

---

## Live 移行判断ポイント（工程 4 完了後に実施）

工程 4（Sim 接続テスト）が合格したタイミングで、以下を確認して Live 移行可否を判断する:

| 確認項目 | 合格条件 | 代替案 |
|----------|----------|--------|
| Live API 申請条件 | 入金額条件なし or 10 万円で申請可能 | 条件付きの場合は OANDA/GMO クリック証券等に転換 |
| API 利用料 | 無料 or 月額 2,000 円以下 | 同上 |
| Token 更新 | refresh_token 取得可能 | refresh_token 不可の場合は工程 2b を先行実施 |

---

## 工程一覧

| 工程 | 名称 | 中間成果物 | 入力 |
|------|------|------------|------|
| 工程 1 | Sim 環境セットアップ手順書 | `docs/saxo-sim-setup.md` | Saxo Developer Portal 仕様 |
| 工程 2 | saxo_client.py 実装 | `src/trading/saxo_client.py` + テスト | OandaClient 実装 + 工程 1 の手順書 |
| 工程 3 | 既存システム統合 | trader.py・scanner.py・strategy_config.json 修正 | saxo_client.py |
| 工程 4 | Sim 接続テスト | テスト結果ログ | 工程 1〜3 の成果物 |
| 工程 5 | バックテスト動作確認 | バックテスト結果レポート | 工程 4 の合格を前提 |

---

## 工程 1: Sim 環境セットアップ手順書

### 完了条件

- [ ] ドキュメントが `docs/saxo-sim-setup.md` に存在すること
- [ ] Saxo Developer Portal のアカウント登録手順が記載されていること
- [ ] Sim 用 Personal Access Token の取得手順が画像・URL なしでもたどれる粒度で記載されていること
- [ ] Account Key（口座識別子）の確認方法が記載されていること
- [ ] `.env` への記載フォーマットが具体的なキー名付きで明示されていること（値はプレースホルダー）
- [ ] 手順が 10 ステップ以内にまとまっており、所要時間 10 分以内と判断できる粒度であること
- [ ] トークン有効期限（24 時間）と更新方法（再発行）が注意書きとして記載されていること

### 品質チェック項目（工程 1）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | 手順に抜けがなく、Developer Portal → PAT 取得 → Account Key 確認 → .env 記載の全ステップが揃っていること | 網羅性 | 30 |
| 2 | `.env` の具体的なキー名（`SAXO_SIM_TOKEN`, `SAXO_SIM_ACCOUNT_KEY` 等）が明記されていること | 情報の正確性 | 25 |
| 3 | 所要時間・難易度（技術知識不要レベル）が読者に伝わる粒度であること | ターゲット整合性 | 20 |
| 4 | トークン有効期限・更新方法の注意書きがあること | 情報の正確性 | 15 |
| 5 | 誤字脱字がなく、文体が統一されていること | 表現の品質 | 10 |
| 合計 | | | 100 |

---

## 工程 2: saxo_client.py 実装

### 完了条件

- [ ] `src/trading/saxo_client.py` が存在すること
- [ ] `SaxoClient` クラスが以下のメソッドをすべて実装していること:
  - `get_balance(currency=None) -> dict`
  - `get_ticker(symbol) -> dict`
  - `fetch_ohlcv(symbol, timeframe="1d", limit=60) -> list`
  - `market_buy(symbol, amount, quote_amount=None) -> dict`
  - `market_sell(symbol, amount) -> dict`
  - `stop_loss_order(symbol, amount, stop_price) -> dict`
  - `cancel_order(order_id, symbol) -> dict`
  - `fetch_open_orders(symbol=None) -> list`
  - `fetch_order(order_id, symbol) -> dict`
  - `is_symbol_supported(symbol) -> bool`
  - `convert_symbol(symbol) -> str`
- [ ] `CONFIGS` 辞書に `"saxo_sim"` と `"saxo"` の両エントリが存在し、環境変数で切り替え可能であること
- [ ] Saxo シンボル変換（`USD/JPY` ↔ `USDJPY`）が実装されていること
- [ ] タイムフレームマッピング（`1d` → Saxo 相当の形式）が実装されていること
- [ ] レート制限スロットリング（最低リクエスト間隔）が実装されていること
- [ ] API エラー時（HTTP 4xx/5xx）に適切な例外を送出し、ログ出力すること
- [ ] 認証情報（Token・Account Key）が未設定の場合に `ValueError` を送出すること
- [ ] 各メソッドに docstring が記載されていること
- [ ] 主要なメソッドに型ヒントが付与されていること
- [ ] `tests/test_saxo_client.py` が存在し、モックを使った単体テスト（最低 5 ケース）があること
- [ ] PAT 認証のヘッダー設定に Token が直接コードに埋め込まれていないこと（.env 経由であること）
- [ ] OAuth 2.0 フロー差し替えポイント（コメント or 設計メモ）が明示されていること

### 品質チェック項目（工程 2）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | ExchangeClient 互換の全インターフェース（11 メソッド）が実装されていること | 機能要件 | 25 |
| 2 | Saxo シンボル変換・タイムフレームマッピングが正確であること | 機能要件 | 15 |
| 3 | Token・Account Key が .env 経由で注入され、コードにハードコードされていないこと | セキュリティ | 15 |
| 4 | API エラー・タイムアウト・レート制限の異常系が適切にハンドリングされていること | エラーハンドリング | 15 |
| 5 | 単体テスト（モック）が最低 5 ケース存在し、正常系・異常系を網羅していること | 機能要件 | 15 |
| 6 | docstring・型ヒントが主要メソッドに付与され、OandaClient と同等の可読性であること | 可読性 | 10 |
| 7 | OAuth 差し替えポイントが明示されており、将来の拡張が容易な構造であること | 可読性 | 5 |
| 合計 | | | 100 |

---

## 工程 3: 既存システム統合

### 完了条件

- [ ] `trader.py` の argparse `--exchange` の choices に `"saxo_sim"` と `"saxo"` が追加されていること
- [ ] `trader.py` の `AutoTrader.__init__` で `exchange_id.startswith("saxo")` の場合に `SaxoClient` をインスタンス化すること
- [ ] `trader.py` の `self.is_fx` 判定が saxo にも対応していること（FX として扱う）
- [ ] `scanner.py` の FX データ取得ルーティングで saxo 系の exchange_id が Saxo API にルーティングされること
- [ ] `strategy_config.json` の FX ペア（`USD-JPY`, `EUR-JPY`）の `"exchange"` フィールドが `"saxo"` に更新されていること
- [ ] `strategy_config.json` 内のシンボル表記（`USD-JPY`）が `saxo_client.py` の変換ロジックと整合していること
- [ ] 既存 Coincheck・Binance の動作に影響がないこと（他の exchange_id のコードパスを変更していないこと）
- [ ] `DEFAULT_FX_ORDER_UNITS` に saxo 用の設定（1,000 通貨）が適切に反映されていること

### 品質チェック項目（工程 3）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | `--exchange saxo_sim` でトレーダーが起動し、SaxoClient が正しく選択されること | 機能要件 | 30 |
| 2 | `scanner.py` で FX ペアを指定した際に saxo 経由でデータが取得されること | 機能要件 | 25 |
| 3 | `strategy_config.json` の `exchange: "saxo"` 記載と実際のルーティングが整合していること | 機能要件 | 20 |
| 4 | 既存の Coincheck・Binance のコードパスが無変更であること（既存テストが通ること） | 機能要件 | 15 |
| 5 | 変更箇所が最小限であり、新規追加コードと修正コードが明確に区別できること | 可読性 | 10 |
| 合計 | | | 100 |

---

## 工程 4: Sim 環境での接続テスト

### 前提条件

- 工程 1 の手順書に従いオーナーが PAT・Account Key を取得済みであること
- `.env` に `SAXO_SIM_TOKEN` と `SAXO_SIM_ACCOUNT_KEY` が設定済みであること

### 完了条件

- [ ] `python -c "from src.trading.saxo_client import SaxoClient; c = SaxoClient('saxo_sim'); print(c.get_balance())"` が残高辞書を返すこと
- [ ] `fetch_ohlcv("USD/JPY", timeframe="1d", limit=30)` が 30 本以上の OHLCV データを返すこと
- [ ] `get_ticker("USD/JPY")` が bid・ask・last を含む辞書を返すこと
- [ ] `market_buy("USD/JPY", 1000)` がテスト注文を Sim 口座に送信し、レスポンスに trade_id が含まれること
- [ ] `market_sell("USD/JPY", 1000)` でポジションの決済ができること
- [ ] 上記の実行結果がログファイル（`data/fx/saxo_sim_connection_test.log`）に記録されていること
- [ ] 接続テストスクリプト（`scripts/test_saxo_sim.py`）が存在すること

### 品質チェック項目（工程 4）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | 残高取得・ティッカー取得・OHLCV 取得の全 3 種類のデータ取得が成功していること | 機能要件 | 30 |
| 2 | テスト買い注文・売り注文が Sim 口座で実際に約定し、trade_id が確認できること | 機能要件 | 35 |
| 3 | 実行結果がログファイルに記録され、内容が検証可能であること | ログ可視性 | 20 |
| 4 | エラーが発生した場合に原因が特定できるエラーメッセージがログに出力されていること | エラー回復性 | 15 |
| 合計 | | | 100 |

---

## 工程 5: バックテスト動作確認

### 前提条件

- 工程 4 が合格していること
- Saxo API から USD/JPY の過去 1 年 OHLCV が取得可能であること

### 完了条件

- [ ] USD/JPY の過去 1 年分（約 250 営業日）の日足 OHLCV が Saxo API から取得できること
- [ ] `src/backtest/runner.py`（または相当するスクリプト）を `--exchange saxo_sim` で実行できること
- [ ] バックテストが正常終了し、取引数・PF・最大 DD が出力されること
- [ ] バックテスト結果レポートが `results/` 配下に保存されること
- [ ] ログに「エラーなし」または「想定内の例外のみ」が記録されていること

### 品質チェック項目（工程 5）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | 過去 1 年分の OHLCV が正確に取得され、欠損・重複がないこと | データの完全性 | 30 |
| 2 | バックテストエンジンが正常終了し、取引数・PF・最大 DD が数値として出力されること | 機能要件 | 35 |
| 3 | 結果レポートが所定のパスに保存され、内容が検証可能なフォーマットであること | フォーマットの正確性 | 20 |
| 4 | 同じ入力で同じ結果が再現できること（再現性の確認） | 再現性 | 15 |
| 合計 | | | 100 |

---

## 備考

### Saxo API 主要エンドポイント（実装時の参照先）

| 機能 | エンドポイント |
|------|---------------|
| 口座情報 | `GET /openapi/port/v1/accounts/me` |
| 残高 | `GET /openapi/port/v1/balances` |
| OHLCV | `GET /openapi/chart/v1/charts` |
| 現在レート | `GET /openapi/trade/v1/prices` |
| 注文 | `POST /openapi/trade/v1/orders` |
| 未決済注文 | `GET /openapi/trade/v1/orders/me` |
| ポジション | `GET /openapi/port/v1/positions/me` |

- Sim ベース URL: `https://gateway.saxobank.com/sim/openapi`
- Live ベース URL: `https://gateway.saxobank.com/openapi`

### .env 追加項目（工程 1 完了後に設定）

```
# Saxo Sim
SAXO_SIM_TOKEN=your_sim_personal_access_token
SAXO_SIM_ACCOUNT_KEY=your_sim_account_key

# Saxo Live（工程 4 完了・Live 移行判断後に設定）
SAXO_TOKEN=your_live_token
SAXO_ACCOUNT_KEY=your_live_account_key
```

### 通貨ペア表記の対応表

| 内部表記（strategy_config） | 内部正規化 | Saxo API |
|---------------------------|------------|----------|
| `USD-JPY` | `USD/JPY` | `USDJPY` |
| `EUR-JPY` | `EUR/JPY` | `EURJPY` |

### コンテナ分離設計方針

```
# docker-compose.yml への追加イメージ（既存 ai-trader に触れない）
services:
  ai-trader:          # 既存（Coincheck BTC/JPY）— 変更なし
    ...
  ai-trader-fx:       # 新規追加（Saxo FX）
    build: .
    command: python src/trading/trader.py --exchange saxo_sim --daemon
    volumes:
      - ./data/fx:/app/data/fx
    env_file: .env
```

### ループ上限

各工程の実行→品質チェックループは最大 5 回。5 回で合格しない場合はオーナーに現状報告して方針を相談する。

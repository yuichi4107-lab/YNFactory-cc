---
created: "2026-03-18"
topic: "AI投資戦略システム（チャート画像判定）"
type: technical-doc
tags: [trading, ai, gemini, chart-pattern, backtest]
---

# AI投資戦略システム（チャート画像判定）設計書

## 概要
チャート画像をGemini APIで判定し、特定パターン（ダブルボトム等）を自動検出。バックテストで有効性を検証するシステム。

## 設計・方針

### アーキテクチャ全体像

```
[データソース] → [チャート画像生成] → [Gemini API判定] → [バックテスト]
    │                  │                     │                  │
 BTC 4h足          HTML Canvas          パターン判定        損益計算
 ccxt/API          正方形切り出し        JSON応答(0/1)      勝率・PF表示
```

### ディレクトリ構成（案）

```
ai-trade-system/
├── .env                      # APIキー（Gemini）
├── package.json
├── src/
│   ├── data/                 # データ取得
│   │   └── fetch-ohlcv.js    # ローソク足データ取得
│   ├── chart/                # チャート可視化・画像生成
│   │   ├── index.html        # チャート表示・範囲選択UI
│   │   └── chart-renderer.js # チャート描画ロジック
│   ├── ai/                   # AI判定
│   │   ├── gemini-client.js  # Gemini API呼び出し
│   │   └── prompts/          # 判定プロンプト管理
│   │       └── double-bottom.txt
│   ├── backtest/             # バックテスト
│   │   ├── runner.js         # スライド画像生成+判定ループ
│   │   └── analyzer.js       # 損益計算・統計
│   └── viewer/               # 結果表示
│       └── results.html      # 判定結果一覧HTML
├── data/                     # 生成データ
│   ├── ohlcv/                # 取得した価格データ
│   └── charts/               # 生成したチャート画像
└── results/                  # バックテスト結果
```

## 詳細

### ステップ1: チャートデータ取得・画像生成

**データ取得**
- ソース: 仮想通貨取引所API（ccxt経由 or 直接API）
- 対象: BTC/USDT 4時間足
- フォーマット: OHLCV (Open, High, Low, Close, Volume)

**チャート可視化**
- ライブラリ候補: TradingView Lightweight Charts / Chart.js + candlestick plugin
- 要件: ローソク足の描画、ズーム・スクロール対応

**画像切り出し機能**
- マウスドラッグで矩形選択
- 選択範囲を正方形にリサイズ
- Canvas → PNG としてダウンロード

### ステップ2: Gemini API画像判定

**API設定**
- モデル: Gemini 2.5 Flash（コスト効率重視）
- APIキー: .envファイルで管理
- 入力: チャート画像(PNG/JPEG)
- 出力: JSON `{"pattern": "double_bottom", "detected": 1}` or `{"detected": 0}`

**プロンプト設計（初期版）**
```
以下のチャート画像を分析してください。
ダブルボトムパターンが存在するかどうかを判定してください。

判定基準:
- 2つの安値（ボトム）がほぼ同じ水準にある
- 2つのボトムの間に反発（ネックライン）がある

結果をJSON形式で返してください:
- パターンが存在する場合: {"detected": 1}
- パターンが存在しない場合: {"detected": 0}
```

### ステップ3: 自動バックテスト

**スライド画像生成**
- ウィンドウサイズ: N本のローソク足（例: 50本）
- スライド幅: 5本ずつ
- 自動的にチャート画像を生成・保存

**判定ループ**
- 生成画像を順次Gemini APIへ送信
- レート制限対応（待機処理）
- 結果をCSV/JSONで保存

**損益計算**
- detected=1 のタイミングで買いエントリー
- 一定期間後（例: 20本後）に決済
- 手数料考慮（例: 0.1%）
- 算出項目: 勝率、プロフィットファクター、最大ドローダウン、損益曲線

### ステップ4: プロンプト検証・調整

**結果ビューア**
- 判定画像 + 判定結果(0/1) を一覧表示するHTML
- フィルタ: True Only / False Only / All
- 目視確認で誤判定を特定

**プロンプト改善例**
- 「大きめのローソク足でダブルボトム + ネックライン突破の瞬間」
- 「直近N本以内にパターン完成」
- パターンの厳密度をレベル分け（確度: high/medium/low）

## 参考
- PM管理: pm/projects/ai-trade-chart-pattern.md
- CEO決定: ceo/decisions/2026-03-18-ai-trade-system.md

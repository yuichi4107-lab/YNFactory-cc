# WIN5予想モジュール

## 概要
JRA WIN5（5レース連続1着的中）の予想・買い目最適化・資金管理システム

## 機能
- netkeiba.comからデータ収集
- LightGBMによる勝馬確率予測 (80-120特徴量)
- 予算制約下での買い目最適化（全列挙・32kパターン）
- Kelly基準による資金管理
- バックテスト・ROI分析
- CLI + Streamlit ダッシュボード

## 使い方
```bash
cd keiba-unified
# データ収集
PYTHONPATH=. python -m win5.src.app.cli collect --start 2020-01-01 --end 2025-12-31
# モデル学習
PYTHONPATH=. python -m win5.src.app.cli train --start 2020-01-01 --end 2024-12-31
# WIN5予想
PYTHONPATH=. python -m win5.src.app.cli predict --date 2026-03-22 --budget 10000
# バックテスト
PYTHONPATH=. python -m win5.src.app.cli backtest --start 2023-01-01 --end 2025-12-31
# ダッシュボード
PYTHONPATH=. python -m win5.src.app.cli dashboard
```

## データ
- `data/win5.db` — WIN5イベント・レース・結果・購入記録DB

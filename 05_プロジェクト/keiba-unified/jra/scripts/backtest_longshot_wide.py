"""
人気薄軸 × ワイド3点流し 戦略の高速バックテスト

features_all.pkl のキャッシュを使い、モデル訓練を Pure/Mkt 各1回だけ行って、
複数の戦略パラメータを一気に回す。
"""
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from src.models.lgbm_model import LGBMModel
from src.backtest.engine import BacktestEngine, BacktestResult
from src.backtest.metrics import MetricsCalculator
from src.reporting.html_report import HTMLReportGenerator
from src.strategies.base_strategy import Bet
from src.utils.config_loader import get_db_path
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

MARKET_FEATURES = {
    "odds", "log_odds", "popularity", "implied_probability",
    "odds_gap_1st_2nd", "favorite_strength", "odds_concentration",
    "model_vs_market", "expected_value",
}


class UnpopularAnchorWideStrategy:
    """人気薄軸 × ワイド3点流し"""

    def __init__(self, anchor_min_pop=5, anchor_min_prob=0.25,
                 anchor_max_odds=80.0, partner_min_prob=0.20,
                 partner_count=3, min_horses=10, bet_per_combo=0.003):
        self.anchor_min_pop = anchor_min_pop
        self.anchor_min_prob = anchor_min_prob
        self.anchor_max_odds = anchor_max_odds
        self.partner_min_prob = partner_min_prob
        self.partner_count = partner_count
        self.min_horses = min_horses
        self.bet_per_combo = bet_per_combo

    def generate_bets(self, race_df, probas, bankroll):
        probas = np.asarray(probas)
        if len(race_df) < self.min_horses:
            return []

        horses = []
        for i, (idx, row) in enumerate(race_df.iterrows()):
            prob = probas[i] if i < len(probas) else 0.0
            odds = float(row.get("odds", 0.0) or 0.0)
            pop = int(row.get("popularity", 0) or 0)
            horse_num = int(row.get("horse_number", i + 1))
            if odds <= 0 or pop <= 0:
                continue
            horses.append({"num": horse_num, "prob": prob, "odds": odds, "pop": pop})

        if len(horses) < self.partner_count + 1:
            return []

        anchors = [h for h in horses
                   if h["pop"] >= self.anchor_min_pop
                   and h["prob"] >= self.anchor_min_prob
                   and h["odds"] <= self.anchor_max_odds]
        if not anchors:
            return []
        anchors.sort(key=lambda x: x["prob"], reverse=True)
        anchor = anchors[0]

        others = [h for h in horses
                  if h["num"] != anchor["num"]
                  and h["prob"] >= self.partner_min_prob]
        others.sort(key=lambda x: x["prob"], reverse=True)
        partners = others[:self.partner_count]
        if len(partners) < self.partner_count:
            return []

        bets = []
        for p in partners:
            nums = sorted([anchor["num"], p["num"]])
            combo_str = f"{nums[0]}-{nums[1]}"
            wide_odds_est = max(1.5, (anchor["odds"] * p["odds"]) ** 0.5 * 0.4)
            amount = bankroll * self.bet_per_combo
            amount = max(100, round(amount / 100) * 100)
            amount = min(amount, bankroll * 0.01)
            bets.append(Bet(
                bet_type="ワイド",
                combination=combo_str,
                amount=amount,
                odds=wide_odds_est,
                expected_value=anchor["prob"] * p["prob"] * 2.0 * wide_odds_est,
                horse_numbers=nums,
            ))
        return bets


def run_strategy(strategy, test_df_with_probas, results_df, payoffs_df):
    """共有 test_df+probas を使って戦略だけ走らせる"""
    result = BacktestResult()
    bankroll = 1_000_000
    daily_pnl = {}

    engine = BacktestEngine()
    for race_id, race_df in test_df_with_probas.groupby("race_id"):
        race_probas = race_df["pred_proba"].values
        race_date = str(race_df["race_date"].iloc[0])

        bets = strategy.generate_bets(race_df, race_probas, bankroll)
        if not bets:
            continue

        for bet in bets:
            bet.race_id = race_id
            bet.race_date = race_date
            bet.is_hit = engine._check_hit(bet, results_df)
            bet.payout = engine._calculate_payout(bet, payoffs_df) if bet.is_hit else 0.0
            bet.profit = bet.payout - bet.amount

            result.bets.append(bet)
            result.total_investment += bet.amount
            result.total_payout += bet.payout
            bankroll += bet.profit
            daily_pnl.setdefault(race_date, 0.0)
            daily_pnl[race_date] += bet.profit

    if daily_pnl:
        sorted_dates = sorted(daily_pnl.keys())
        equity = 1_000_000
        eq_vals, ret_vals = {}, {}
        for d in sorted_dates:
            equity += daily_pnl[d]
            eq_vals[d] = equity
            ret_vals[d] = daily_pnl[d]
        result.equity_curve = pd.Series(eq_vals)
        result.equity_curve.index = pd.to_datetime(result.equity_curve.index)
        result.daily_returns = pd.Series(ret_vals)
        result.daily_returns.index = pd.to_datetime(result.daily_returns.index)
    return result


def main():
    import sqlite3

    print("=== Loading cached features ===")
    features_df = pd.read_pickle("/opt/keiba-unified/jra/data/features_all.pkl")
    features_df["target"] = (features_df["finish_order"] <= 3).astype(int)
    print(f"Features: {features_df.shape}")

    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    print("=== Loading payoffs and results ===")
    payoffs_df = pd.read_sql(
        "SELECT race_id, bet_type, combination, payout as payout_amount FROM payoffs",
        conn,
    )
    results_df = pd.read_sql(
        "SELECT race_id, horse_number, finish_order as finish_position FROM race_results",
        conn,
    )
    conn.close()
    print(f"payoffs rows: {len(payoffs_df)}, results rows: {len(results_df)}")

    dates = pd.to_datetime(features_df["race_date"])
    train_mask = dates <= "2024-06-30"
    test_mask = dates > "2024-06-30"
    print(f"Train: {train_mask.sum()}, Test: {test_mask.sum()}")

    meta_cols = {"race_id", "race_date", "horse_number", "horse_id",
                 "horse_name", "finish_order", "target", "pred_proba"}
    all_feature_cols = [c for c in features_df.columns if c not in meta_cols]

    train_df = features_df[train_mask]
    test_df_base = features_df[test_mask].copy()
    X_train = train_df[all_feature_cols].fillna(0)
    y_train = train_df["target"]
    X_test = test_df_base[all_feature_cols].fillna(0)

    model_params = {
        "n_estimators": 500, "max_depth": 5, "learning_rate": 0.03,
        "num_leaves": 24, "min_child_samples": 50, "subsample": 0.7,
        "colsample_bytree": 0.6, "reg_alpha": 0.5, "reg_lambda": 2.0,
        "verbose": -1,
    }

    print("\n=== Training Mkt model (once) ===")
    t0 = time.time()
    model = LGBMModel(params=model_params)
    model.fit(X_train, y_train)
    probas = model.predict_proba(X_test)
    test_df = test_df_base.copy()
    test_df["pred_proba"] = probas
    auc = roc_auc_score(test_df["target"], probas)
    print(f"Mkt AUC: {auc:.4f}, model train: {time.time() - t0:.1f}s")

    test_races = test_df["race_id"].nunique()
    test_days = pd.to_datetime(test_df["race_date"]).dt.date.nunique()
    print(f"Test: {test_races} races, {test_days} days")

    strategies = {
        "LongshotWide pop>=5 p>=0.25": UnpopularAnchorWideStrategy(
            anchor_min_pop=5, anchor_min_prob=0.25),
        "LongshotWide pop>=5 p>=0.30": UnpopularAnchorWideStrategy(
            anchor_min_pop=5, anchor_min_prob=0.30),
        "LongshotWide pop>=7 p>=0.25": UnpopularAnchorWideStrategy(
            anchor_min_pop=7, anchor_min_prob=0.25),
        "LongshotWide pop>=7 p>=0.30": UnpopularAnchorWideStrategy(
            anchor_min_pop=7, anchor_min_prob=0.30),
        "LongshotWide pop>=10 p>=0.25": UnpopularAnchorWideStrategy(
            anchor_min_pop=10, anchor_min_prob=0.25),
        "LongshotWide pop>=3 p>=0.30": UnpopularAnchorWideStrategy(
            anchor_min_pop=3, anchor_min_prob=0.30),
        # Bet size variations on the best-so-far variant
        "LongshotWide pop>=5 p>=0.30 x3bet": UnpopularAnchorWideStrategy(
            anchor_min_pop=5, anchor_min_prob=0.30, bet_per_combo=0.009),
        # Partner min_prob variations
        "LongshotWide pop>=5 p>=0.25 partner>=0.30": UnpopularAnchorWideStrategy(
            anchor_min_pop=5, anchor_min_prob=0.25, partner_min_prob=0.30),
    }

    print("\n=== Running strategies ===")
    all_results = {}
    all_metrics = {}
    for name, strategy in strategies.items():
        t0 = time.time()
        result = run_strategy(strategy, test_df, results_df, payoffs_df)
        metrics = MetricsCalculator.calculate_all(result, test_races, test_days)
        all_results[name] = result
        all_metrics[name] = metrics
        hits = [b for b in result.bets if b.is_hit]
        avg_payout = np.mean([b.payout / b.amount for b in hits]) if hits else 0
        print(f"  [{time.time() - t0:.1f}s] {name}: ROI={metrics['roi_pct']:.1f}%, "
              f"Bets={metrics['total_bets']}, Hit={metrics['hit_rate_pct']:.1f}%, "
              f"DWin={metrics['daily_win_rate_pct']:.1f}%, "
              f"Net={metrics['net_profit']:+,.0f}, AvgPayout={avg_payout:.2f}x")

    print("\n" + "=" * 80)
    print("LONGSHOT WIDE SUMMARY")
    print("=" * 80)
    print(f"{'Strategy':<45} {'ROI':>7} {'Bets':>5} {'Hit%':>6} {'DWin%':>6} {'Net':>12}")
    print("-" * 85)
    for name in strategies:
        m = all_metrics[name]
        print(f"{name:<45} {m['roi_pct']:>6.1f}% {m['total_bets']:>5} "
              f"{m['hit_rate_pct']:>5.1f}% {m['daily_win_rate_pct']:>5.1f}% "
              f"{m['net_profit']:>+12,.0f}")
    print("=" * 85)

    gen = HTMLReportGenerator()
    comparison_path = "/opt/keiba-unified/data/reports/longshot_wide_comparison.html"
    os.makedirs(os.path.dirname(comparison_path), exist_ok=True)
    gen.generate_comparison_report(all_results, all_metrics, comparison_path)
    print(f"\nReport: {comparison_path}")


if __name__ == "__main__":
    main()

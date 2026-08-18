"""pop>=7 p>=0.25 周辺の微調整で黒字化を探索"""
import os, sys, time, numpy as np, pandas as pd
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname("."), "..")))
from sklearn.metrics import roc_auc_score
from src.models.lgbm_model import LGBMModel
from src.backtest.engine import BacktestEngine, BacktestResult
from src.backtest.metrics import MetricsCalculator
from src.strategies.base_strategy import Bet
from src.utils.config_loader import get_db_path
import sqlite3

df = pd.read_pickle("/opt/keiba-unified/jra/data/features_all.pkl")
df["target"] = (df["finish_order"] <= 3).astype(int)
conn = sqlite3.connect(get_db_path())
payoffs_df = pd.read_sql("SELECT race_id, bet_type, combination, payout as payout_amount FROM payoffs", conn)
results_df = pd.read_sql("SELECT race_id, horse_number, finish_order as finish_position FROM race_results", conn)
conn.close()

dates = pd.to_datetime(df["race_date"])
train_mask = dates <= "2024-06-30"
test_mask = dates > "2024-06-30"
meta = {"race_id","race_date","horse_number","horse_id","horse_name","finish_order","target","pred_proba"}
all_cols = [c for c in df.columns if c not in meta]

model = LGBMModel(params={"n_estimators":500,"max_depth":5,"learning_rate":0.03,
    "num_leaves":24,"min_child_samples":50,"subsample":0.7,"colsample_bytree":0.6,
    "reg_alpha":0.5,"reg_lambda":2.0,"verbose":-1})
model.fit(df[train_mask][all_cols].fillna(0), df[train_mask]["target"])
test = df[test_mask].copy()
test["pred_proba"] = model.predict_proba(test[all_cols].fillna(0))
test_races = test["race_id"].nunique()
test_days = pd.to_datetime(test["race_date"]).dt.date.nunique()
print(f"Model ready. {test_races} races, {test_days} days\n")

VARIANTS = [
    # (label, anchor_min_pop, anchor_min_prob, anchor_max_odds, partner_min_prob)
    ("baseline pop7 p0.25",           7, 0.25, 80, 0.20),
    ("pop6 p0.25",                    6, 0.25, 80, 0.20),
    ("pop8 p0.25",                    8, 0.25, 80, 0.20),
    ("pop7 p0.27",                    7, 0.27, 80, 0.20),
    ("pop7 p0.23",                    7, 0.23, 80, 0.20),
    ("pop7 p0.25 maxodds50",          7, 0.25, 50, 0.20),
    ("pop7 p0.25 maxodds30",          7, 0.25, 30, 0.20),
    ("pop7 p0.25 maxodds20",          7, 0.25, 20, 0.20),
    ("pop7 p0.25 partner0.25",        7, 0.25, 80, 0.25),
    ("pop7 p0.25 partner0.30",        7, 0.25, 80, 0.30),
    ("pop7 p0.25 partner0.35",        7, 0.25, 80, 0.35),
    ("pop7 p0.25 maxodds50 part0.30", 7, 0.25, 50, 0.30),
    ("pop7 p0.25 maxodds30 part0.30", 7, 0.25, 30, 0.30),
    ("pop6 p0.25 maxodds50",          6, 0.25, 50, 0.20),
    ("pop6 p0.25 partner0.30",        6, 0.25, 80, 0.30),
]

print(f"{'Label':<38} {'Bets':>5} {'Hit%':>6} {'ROI':>7} {'Net':>12} {'AvgPay':>7}")
print("-" * 82)

for label, a_pop, a_prob, a_maxodds, p_prob in VARIANTS:
    t0 = time.time()
    result = BacktestResult()
    bankroll = 1_000_000
    engine = BacktestEngine()
    for rid, rdf in test.groupby("race_id"):
        probas = rdf["pred_proba"].values
        if len(rdf) < 10:
            continue
        horses = []
        for i, (_, row) in enumerate(rdf.iterrows()):
            p = probas[i] if i < len(probas) else 0.0
            o = float(row.get("odds", 0) or 0)
            pop = int(row.get("popularity", 0) or 0)
            hn = int(row.get("horse_number", i + 1))
            if o > 0 and pop > 0:
                horses.append({"num": hn, "prob": p, "odds": o, "pop": pop})
        anchors = [h for h in horses
                   if h["pop"] >= a_pop and h["prob"] >= a_prob and h["odds"] <= a_maxodds]
        if not anchors:
            continue
        anchors.sort(key=lambda x: x["prob"], reverse=True)
        anchor = anchors[0]
        others = [h for h in horses
                  if h["num"] != anchor["num"] and h["prob"] >= p_prob]
        others.sort(key=lambda x: x["prob"], reverse=True)
        partners = others[:3]
        if len(partners) < 3:
            continue
        rd = str(rdf["race_date"].iloc[0])
        for pt in partners:
            nums = sorted([anchor["num"], pt["num"]])
            combo = f"{nums[0]}-{nums[1]}"
            amt = max(100, round(bankroll * 0.003 / 100) * 100)
            amt = min(amt, bankroll * 0.01)
            b = Bet(bet_type="ワイド", combination=combo, amount=amt,
                    odds=5.0, expected_value=0, horse_numbers=nums)
            b.race_id = rid
            b.race_date = rd
            b.is_hit = engine._check_hit(b, results_df)
            b.payout = engine._calculate_payout(b, payoffs_df) if b.is_hit else 0.0
            b.profit = b.payout - b.amount
            result.bets.append(b)
            result.total_investment += b.amount
            result.total_payout += b.payout
            bankroll += b.profit
    m = MetricsCalculator.calculate_all(result, test_races, test_days)
    hits = [b for b in result.bets if b.is_hit]
    avg_p = np.mean([b.payout / b.amount for b in hits]) if hits else 0
    roi = m["roi_pct"]
    marker = " ★" if roi >= 100 else ""
    print(f"{label:<38} {m['total_bets']:>5} {m['hit_rate_pct']:>5.1f}% {roi:>6.1f}% {m['net_profit']:>+11,.0f} {avg_p:>6.2f}x{marker}")

print("=" * 82)
print("=== DONE ===")

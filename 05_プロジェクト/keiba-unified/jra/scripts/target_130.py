"""ROI 130% × 1日1レースを目指す厳選戦略探索"""
import os, sys, time, numpy as np, pandas as pd
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname("."), "..")))
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


# === Variant parameter list ===
VARIANTS = [
    # baseline for reference
    ("[baseline] pop7 p0.25 part0.35",
     {"a_pop": 7, "a_prob": 0.25, "a_maxodds": 80, "a_minodds": 0, "a_edge": 0.0, "p_prob": 0.35, "p_count": 3}),
    # 1) anchor p>=0.28/0.30
    ("A1: pop7 p0.28 part0.35",
     {"a_pop": 7, "a_prob": 0.28, "a_maxodds": 80, "a_minodds": 0, "a_edge": 0.0, "p_prob": 0.35, "p_count": 3}),
    ("A2: pop7 p0.30 part0.35",
     {"a_pop": 7, "a_prob": 0.30, "a_maxodds": 80, "a_minodds": 0, "a_edge": 0.0, "p_prob": 0.35, "p_count": 3}),
    # 2) anchor odds range (sweet spot)
    ("B1: pop7 p0.25 odds10-30",
     {"a_pop": 7, "a_prob": 0.25, "a_maxodds": 30, "a_minodds": 10, "a_edge": 0.0, "p_prob": 0.35, "p_count": 3}),
    ("B2: pop7 p0.25 odds10-50",
     {"a_pop": 7, "a_prob": 0.25, "a_maxodds": 50, "a_minodds": 10, "a_edge": 0.0, "p_prob": 0.35, "p_count": 3}),
    ("B3: pop7 p0.25 odds15-40",
     {"a_pop": 7, "a_prob": 0.25, "a_maxodds": 40, "a_minodds": 15, "a_edge": 0.0, "p_prob": 0.35, "p_count": 3}),
    # 3) partner tighter
    ("C1: pop7 p0.25 part0.40",
     {"a_pop": 7, "a_prob": 0.25, "a_maxodds": 80, "a_minodds": 0, "a_edge": 0.0, "p_prob": 0.40, "p_count": 3}),
    ("C2: pop7 p0.25 part0.45",
     {"a_pop": 7, "a_prob": 0.25, "a_maxodds": 80, "a_minodds": 0, "a_edge": 0.0, "p_prob": 0.45, "p_count": 3}),
    # 4) anchor edge (model_prob - implied_prob)
    ("D1: pop7 edge>=0.15 part0.35",
     {"a_pop": 7, "a_prob": 0.25, "a_maxodds": 80, "a_minodds": 0, "a_edge": 0.15, "p_prob": 0.35, "p_count": 3}),
    ("D2: pop7 edge>=0.20 part0.35",
     {"a_pop": 7, "a_prob": 0.25, "a_maxodds": 80, "a_minodds": 0, "a_edge": 0.20, "p_prob": 0.35, "p_count": 3}),
    ("D3: pop7 edge>=0.25 part0.35",
     {"a_pop": 7, "a_prob": 0.25, "a_maxodds": 80, "a_minodds": 0, "a_edge": 0.25, "p_prob": 0.35, "p_count": 3}),
    # 5) combined
    ("E1: pop7 p0.28 odds10-40 part0.40",
     {"a_pop": 7, "a_prob": 0.28, "a_maxodds": 40, "a_minodds": 10, "a_edge": 0.0, "p_prob": 0.40, "p_count": 3}),
    ("E2: pop7 edge>=0.15 odds10-40 part0.35",
     {"a_pop": 7, "a_prob": 0.25, "a_maxodds": 40, "a_minodds": 10, "a_edge": 0.15, "p_prob": 0.35, "p_count": 3}),
    ("E3: pop7 edge>=0.20 odds10-50 part0.40",
     {"a_pop": 7, "a_prob": 0.25, "a_maxodds": 50, "a_minodds": 10, "a_edge": 0.20, "p_prob": 0.40, "p_count": 3}),
    ("E4: pop7 p0.30 odds15-40 part0.40",
     {"a_pop": 7, "a_prob": 0.30, "a_maxodds": 40, "a_minodds": 15, "a_edge": 0.0, "p_prob": 0.40, "p_count": 3}),
]

print(f"{'Label':<45} {'Bets':>5} {'Races':>6} {'Hit%':>6} {'ROI':>7} {'Net':>12} {'Pay':>6}")
print("-" * 92)

for label, args in VARIANTS:
    t0 = time.time()
    result = BacktestResult()
    bankroll = 1_000_000
    engine = BacktestEngine()
    race_count = 0

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
                market_p = min(0.95, 1.0 / o)
                edge = p - market_p
                horses.append({"num": hn, "prob": p, "odds": o, "pop": pop,
                               "edge": edge})

        anchors = [h for h in horses
                   if h["pop"] >= args["a_pop"]
                   and h["prob"] >= args["a_prob"]
                   and h["odds"] >= args["a_minodds"]
                   and h["odds"] <= args["a_maxodds"]
                   and h["edge"] >= args["a_edge"]]
        if not anchors:
            continue
        anchors.sort(key=lambda x: x["prob"], reverse=True)
        anchor = anchors[0]

        others = [h for h in horses
                  if h["num"] != anchor["num"] and h["prob"] >= args["p_prob"]]
        others.sort(key=lambda x: x["prob"], reverse=True)
        partners = others[:args["p_count"]]
        if len(partners) < args["p_count"]:
            continue

        race_count += 1
        rd = str(rdf["race_date"].iloc[0])
        for pt in partners:
            nums = sorted([anchor["num"], pt["num"]])
            combo = f"{nums[0]}-{nums[1]}"
            amt = max(100, round(bankroll * 0.003 / 100) * 100)
            amt = min(amt, bankroll * 0.01)
            b = Bet(bet_type="ワイド", combination=combo, amount=amt,
                    odds=5.0, expected_value=0, horse_numbers=nums)
            b.race_id = rid; b.race_date = rd
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
    marker = ""
    if m["roi_pct"] >= 130:
        marker = " ★★★"
    elif m["roi_pct"] >= 120:
        marker = " ★★"
    elif m["roi_pct"] >= 100:
        marker = " ★"
    print(f"{label:<45} {m['total_bets']:>5} {race_count:>6} {m['hit_rate_pct']:>5.1f}% {m['roi_pct']:>6.1f}% {m['net_profit']:>+11,.0f} {avg_p:>5.2f}x{marker}")

print("=" * 92)
print("=== DONE ===")

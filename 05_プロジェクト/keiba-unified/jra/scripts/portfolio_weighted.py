"""比例配分ポートフォリオ: combo毎に「何戦略が推したか」でベット額を倍増

BASE=100円を基準に、1戦略=100円 / 2戦略=200円 / 3戦略=300円 / ...
単一コンボあたり(baseの conviction倍)のベット、UNIQUEで重複排除
"""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname("."), "..")))
from src.models.lgbm_model import LGBMModel
from src.backtest.engine import BacktestEngine, BacktestResult
from src.backtest.metrics import MetricsCalculator
from src.strategies.base_strategy import Bet
from src.utils.config_loader import get_db_path
from collections import Counter
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

STRATEGIES = [
    ("baseline", 7, 0.25, 0, 80, 0.0, 0.35, 3),
    ("A1",       7, 0.28, 0, 80, 0.0, 0.35, 3),
    ("C2",       7, 0.25, 0, 80, 0.0, 0.45, 3),
    ("E1",       7, 0.28, 10, 40, 0.0, 0.40, 3),
    ("D2",       7, 0.25, 0, 80, 0.20, 0.35, 3),
]


def apply(params, race_df, probas):
    horses = []
    for i, (_, row) in enumerate(race_df.iterrows()):
        p = probas[i] if i < len(probas) else 0.0
        o = float(row.get("odds", 0) or 0)
        pop = int(row.get("popularity", 0) or 0)
        hn = int(row.get("horse_number", i + 1))
        if o > 0 and pop > 0:
            market_p = min(0.95, 1.0 / o)
            edge = p - market_p
            horses.append({"num": hn, "prob": p, "odds": o, "pop": pop, "edge": edge})

    _, a_pop, a_prob, a_minodds, a_maxodds, a_edge, p_prob, p_count = params
    anchors = [h for h in horses
               if h["pop"] >= a_pop and h["prob"] >= a_prob
               and h["odds"] >= a_minodds and h["odds"] <= a_maxodds
               and h["edge"] >= a_edge]
    if not anchors:
        return None, []
    anchors.sort(key=lambda x: x["prob"], reverse=True)
    anchor = anchors[0]
    others = [h for h in horses if h["num"] != anchor["num"] and h["prob"] >= p_prob]
    others.sort(key=lambda x: x["prob"], reverse=True)
    partners = others[:p_count]
    if len(partners) < p_count:
        return None, []
    return anchor, partners


engine = BacktestEngine()
race_combo_conv = {}  # (race_id, combo) -> conviction count
race_date_map = {}

for rid, rdf in test.groupby("race_id"):
    probas = rdf["pred_proba"].values
    if len(rdf) < 10:
        continue
    rd = str(rdf["race_date"].iloc[0])

    for params in STRATEGIES:
        anchor, partners = apply(params, rdf, probas)
        if not anchor:
            continue
        for pt in partners:
            nums = sorted([anchor["num"], pt["num"]])
            combo = f"{nums[0]}-{nums[1]}"
            key = (rid, combo)
            race_combo_conv[key] = race_combo_conv.get(key, 0) + 1
            race_date_map[key] = rd

# Now 3 test modes with different BASE amounts
print(f"Total unique (race, combo): {len(race_combo_conv)}")
conv_dist = Counter(race_combo_conv.values())
print(f"Conviction distribution: {dict(sorted(conv_dist.items()))}")
print()

BASE_AMOUNTS = [100, 200, 300]

print(f"{'BASE':>5} {'Bets':>5} {'Inv':>12} {'Pay':>12} {'Hit%':>6} {'ROI':>7} {'Net':>12}")
print("-" * 70)

for BASE in BASE_AMOUNTS:
    result = BacktestResult()
    bankroll = 1_000_000
    for (rid, combo), conv in race_combo_conv.items():
        nums = [int(x) for x in combo.split("-")]
        amt = BASE * conv
        b = Bet(bet_type="ワイド", combination=combo, amount=amt,
                odds=5.0, expected_value=0, horse_numbers=nums)
        b.race_id = rid; b.race_date = race_date_map[(rid, combo)]
        b.is_hit = engine._check_hit(b, results_df)
        b.payout = engine._calculate_payout(b, payoffs_df) if b.is_hit else 0.0
        b.profit = b.payout - b.amount
        result.bets.append(b)
        result.total_investment += b.amount
        result.total_payout += b.payout
        bankroll += b.profit
    m = MetricsCalculator.calculate_all(result, test_races, test_days)
    hit_pct = m['hit_rate_pct']
    roi = m['roi_pct']
    print(f"{BASE:>5} {m['total_bets']:>5} {int(result.total_investment):>12,d} {int(result.total_payout):>12,d} {hit_pct:>5.1f}% {roi:>6.1f}% {m['net_profit']:>+11,.0f}")

# Detailed by conviction level for BASE=100
print("\n=== conviction別の成績（BASE=100）===")
conv_stats = {c: {"bets": 0, "hits": 0, "inv": 0, "pay": 0, "net": 0} for c in [1, 2, 3, 4, 5]}
for (rid, combo), conv in race_combo_conv.items():
    nums = [int(x) for x in combo.split("-")]
    amt = 100 * conv
    b = Bet(bet_type="ワイド", combination=combo, amount=amt,
            odds=5.0, expected_value=0, horse_numbers=nums)
    b.race_id = rid
    is_hit = engine._check_hit(b, results_df)
    payout = engine._calculate_payout(b, payoffs_df) if is_hit else 0.0
    profit = payout - amt
    s = conv_stats[conv]
    s["bets"] += 1
    if is_hit:
        s["hits"] += 1
    s["inv"] += amt
    s["pay"] += payout
    s["net"] += profit

print(f"{'Conv':>5} {'Bets':>5} {'Hit%':>6} {'ROI':>7} {'Net':>10} {'Inv':>8}")
for c in [1, 2, 3, 4, 5]:
    s = conv_stats[c]
    if s["bets"] == 0: continue
    hit = s["hits"] / s["bets"] * 100
    roi = s["pay"] / s["inv"] * 100 if s["inv"] else 0
    print(f"  {c}x {s['bets']:>5} {hit:>5.1f}% {roi:>6.1f}% {s['net']:>+10,.0f} {s['inv']:>8,}")

print("\n=== DONE ===")

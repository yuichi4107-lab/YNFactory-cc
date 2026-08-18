"""確定戦略: Longshot Wide Portfolio with conv>=2 filter
5戦略(baseline/A1/C2/E1/D2)の内2つ以上が合意したコンボのみ購入
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
print(f"Test: {test_races} races, {test_days} days (18 months)\n")

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
    if not anchors: return None, []
    anchors.sort(key=lambda x: x["prob"], reverse=True)
    anchor = anchors[0]
    others = [h for h in horses if h["num"] != anchor["num"] and h["prob"] >= p_prob]
    others.sort(key=lambda x: x["prob"], reverse=True)
    partners = others[:p_count]
    if len(partners) < p_count: return None, []
    return anchor, partners


engine = BacktestEngine()
combo_conv = {}
race_date_map = {}

for rid, rdf in test.groupby("race_id"):
    probas = rdf["pred_proba"].values
    if len(rdf) < 10:
        continue
    rd = str(rdf["race_date"].iloc[0])
    for params in STRATEGIES:
        anchor, partners = apply(params, rdf, probas)
        if not anchor: continue
        for pt in partners:
            nums = sorted([anchor["num"], pt["num"]])
            combo = f"{nums[0]}-{nums[1]}"
            key = (rid, combo)
            combo_conv[key] = combo_conv.get(key, 0) + 1
            race_date_map[key] = rd

# Filter conv>=2
filtered = [(k, c) for k, c in combo_conv.items() if c >= 2]
print(f"conv>=2 combos: {len(filtered)}")
print(f"  breakdown: {dict(sorted(Counter(c for _, c in filtered).items()))}")
print()

# Run for different BASE amounts
print(f"{'BASE':>6} {'Bets':>5} {'購入金額':>12} {'回収金額':>12} {'Hit%':>6} {'Net':>12} {'ROI':>7} {'AvgPay(100円換算)':>18}")
print("-" * 90)

for BASE in [100, 300, 500, 1000]:
    result = BacktestResult()
    bets_detail = []
    for (rid, combo), conv in filtered:
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
        bets_detail.append((b.amount, b.payout, b.is_hit))

    m = MetricsCalculator.calculate_all(result, test_races, test_days)
    hits = [b for b in result.bets if b.is_hit]
    if hits:
        # 100円換算の平均配当 = payout_per_100
        avg_pay_per_100 = np.mean([b.payout / (b.amount / 100) for b in hits])
        avg_pay_actual = np.mean([b.payout for b in hits])
        avg_bet_on_hit = np.mean([b.amount for b in hits])
    else:
        avg_pay_per_100 = 0
        avg_pay_actual = 0
        avg_bet_on_hit = 0

    print(f"{BASE:>6} {m['total_bets']:>5} {int(result.total_investment):>12,d} {int(result.total_payout):>12,d} "
          f"{m['hit_rate_pct']:>5.1f}% {m['net_profit']:>+11,.0f} {m['roi_pct']:>6.1f}% "
          f"{avg_pay_per_100:>10.0f}円 x{avg_pay_per_100/100:.1f}")

# Detailed avg payout analysis
print("\n=== 的中時の詳細（BASE=300で計算） ===")
BASE = 300
hit_details = []
for (rid, combo), conv in filtered:
    nums = [int(x) for x in combo.split("-")]
    amt = BASE * conv
    b = Bet(bet_type="ワイド", combination=combo, amount=amt,
            odds=5.0, expected_value=0, horse_numbers=nums)
    b.race_id = rid
    if engine._check_hit(b, results_df):
        pay = engine._calculate_payout(b, payoffs_df)
        hit_details.append({
            "race": rid, "combo": combo, "conv": conv,
            "bet": amt, "pay": pay, "multiplier": pay / amt
        })

print(f"的中回数: {len(hit_details)}")
if hit_details:
    pays = [h["pay"] for h in hit_details]
    bets = [h["bet"] for h in hit_details]
    mults = [h["multiplier"] for h in hit_details]
    print(f"平均ベット額（的中時）: {np.mean(bets):,.0f}円")
    print(f"平均配当額（的中時）: {np.mean(pays):,.0f}円")
    print(f"平均倍率: {np.mean(mults):.2f}x")
    print(f"最高配当: {max(pays):,.0f}円 (combo {max(hit_details, key=lambda x: x['pay'])['combo']})")
    print(f"最低配当: {min(pays):,.0f}円")

print("\n=== DONE ===")

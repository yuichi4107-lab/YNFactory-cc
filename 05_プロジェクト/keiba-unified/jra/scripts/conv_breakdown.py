"""合意度別の詳細収支 + フラットベット比較"""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname("."), "..")))
from src.models.lgbm_model import LGBMModel
from src.backtest.engine import BacktestEngine, BacktestResult
from src.strategies.base_strategy import Bet
from src.utils.config_loader import get_db_path
from collections import defaultdict
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
for rid, rdf in test.groupby("race_id"):
    probas = rdf["pred_proba"].values
    if len(rdf) < 10: continue
    for params in STRATEGIES:
        anchor, partners = apply(params, rdf, probas)
        if not anchor: continue
        for pt in partners:
            nums = sorted([anchor["num"], pt["num"]])
            combo = f"{nums[0]}-{nums[1]}"
            key = (rid, combo)
            combo_conv[key] = combo_conv.get(key, 0) + 1

# Compute per-combo result at flat 100 yen
UNIT = 100
per_conv = defaultdict(lambda: {"combos": 0, "hits": 0, "pay_sum": 0, "pay_on_hit": []})

for (rid, combo), conv in combo_conv.items():
    nums = [int(x) for x in combo.split("-")]
    b = Bet(bet_type="ワイド", combination=combo, amount=UNIT,
            odds=5.0, expected_value=0, horse_numbers=nums)
    b.race_id = rid
    is_hit = engine._check_hit(b, results_df)
    pay = engine._calculate_payout(b, payoffs_df) if is_hit else 0.0
    d = per_conv[conv]
    d["combos"] += 1
    if is_hit:
        d["hits"] += 1
        d["pay_on_hit"].append(pay)
    d["pay_sum"] += pay

print("=== 全合意度: フラット100円/コンボ の詳細 ===")
print(f"{'Conv':>5} {'combos':>7} {'hits':>5} {'Hit%':>6} {'購入合計':>10} {'回収合計':>10} {'Net':>10} {'ROI':>7} {'的中時平均':>11}")
print("-" * 90)

total_combos = total_hits = 0
total_inv = total_pay = 0
for conv in sorted(per_conv.keys()):
    d = per_conv[conv]
    inv = d["combos"] * UNIT
    pay = d["pay_sum"]
    net = pay - inv
    roi = pay / inv * 100 if inv else 0
    avg_pay = np.mean(d["pay_on_hit"]) if d["pay_on_hit"] else 0
    hit_rate = d["hits"] / d["combos"] * 100 if d["combos"] else 0
    print(f"{conv:>5} {d['combos']:>7} {d['hits']:>5} {hit_rate:>5.1f}% {inv:>10,} {int(pay):>10,} {int(net):>+10,} {roi:>6.1f}% {int(avg_pay):>9,}円")
    total_combos += d["combos"]
    total_hits += d["hits"]
    total_inv += inv
    total_pay += pay

print("-" * 90)
total_net = total_pay - total_inv
total_roi = total_pay / total_inv * 100 if total_inv else 0
total_hit = total_hits / total_combos * 100 if total_combos else 0
print(f"{'ALL':>5} {total_combos:>7} {total_hits:>5} {total_hit:>5.1f}% {total_inv:>10,} {int(total_pay):>10,} {int(total_net):>+10,} {total_roi:>6.1f}%")

# conv>=2 subtotal
c2_combos = c2_hits = c2_inv = c2_pay = 0
for conv in [2, 3, 4, 5]:
    if conv in per_conv:
        d = per_conv[conv]
        c2_combos += d["combos"]
        c2_hits += d["hits"]
        c2_inv += d["combos"] * UNIT
        c2_pay += d["pay_sum"]
c2_net = c2_pay - c2_inv
c2_roi = c2_pay / c2_inv * 100 if c2_inv else 0
c2_hit = c2_hits / c2_combos * 100 if c2_combos else 0
print(f"{'≥2':>5} {c2_combos:>7} {c2_hits:>5} {c2_hit:>5.1f}% {c2_inv:>10,} {int(c2_pay):>10,} {int(c2_net):>+10,} {c2_roi:>6.1f}%")

print("\n=== 同じパターンをフラット1000円/コンボに拡大 ===")
for label, inv_base in [("flat 500", 500), ("flat 1000", 1000), ("flat 2000", 2000), ("flat 5000", 5000)]:
    scale = inv_base / UNIT
    print(f"{label}: conv>=2 total 購入 {int(c2_inv*scale):,}円 / 回収 {int(c2_pay*scale):,}円 / Net {int(c2_net*scale):+,}円 (ROI {c2_roi:.1f}%)")

print("\n=== DONE ===")

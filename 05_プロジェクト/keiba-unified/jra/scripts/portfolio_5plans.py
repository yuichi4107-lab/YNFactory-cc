"""5戦略をポートフォリオ運用: ベースライン + A1 + C2 + E1 + D2

2つの集計方式で報告:
1. UNIQUE: 各レースの同一combo重複排除（1レース1コンボは1回のみベット）
2. STACKED: 各戦略のベットを重ねがけ（同一レースに複数戦略が反応したら複数ベット）
"""
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

STRATEGIES = [
    # (name, a_pop, a_prob, a_minodds, a_maxodds, a_edge, p_prob, p_count)
    ("baseline", 7, 0.25, 0, 80, 0.0, 0.35, 3),
    ("A1",       7, 0.28, 0, 80, 0.0, 0.35, 3),
    ("C2",       7, 0.25, 0, 80, 0.0, 0.45, 3),
    ("E1",       7, 0.28, 10, 40, 0.0, 0.40, 3),
    ("D2",       7, 0.25, 0, 80, 0.20, 0.35, 3),
]


def apply_strategy(params, race_df, probas):
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

    name, a_pop, a_prob, a_minodds, a_maxodds, a_edge, p_prob, p_count = params
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
# 各方式の集計用
unique_result = BacktestResult()
stacked_result = BacktestResult()
bankroll_u = 1_000_000
bankroll_s = 1_000_000
unique_seen = set()

# 戦略別に通常の結果も算出してサマリー
indiv_results = {s[0]: {"bets": 0, "hits": 0, "net": 0, "inv": 0, "pay": 0, "races": 0} for s in STRATEGIES}

for rid, rdf in test.groupby("race_id"):
    probas = rdf["pred_proba"].values
    if len(rdf) < 10:
        continue
    rd = str(rdf["race_date"].iloc[0])

    combos_for_unique = set()
    combos_for_stacked = []

    for params in STRATEGIES:
        name = params[0]
        anchor, partners = apply_strategy(params, rdf, probas)
        if not anchor:
            continue
        indiv_results[name]["races"] += 1
        for pt in partners:
            nums = sorted([anchor["num"], pt["num"]])
            combo = f"{nums[0]}-{nums[1]}"
            key = (rid, combo)
            combos_for_unique.add(key)
            combos_for_stacked.append((name, anchor["num"], pt["num"], combo))

    amt_u = max(100, round(bankroll_u * 0.003 / 100) * 100)
    amt_u = min(amt_u, bankroll_u * 0.01)
    amt_s = max(100, round(bankroll_s * 0.003 / 100) * 100)
    amt_s = min(amt_s, bankroll_s * 0.01)

    for (race_id, combo) in combos_for_unique:
        if (race_id, combo) in unique_seen:
            continue
        unique_seen.add((race_id, combo))
        nums = [int(x) for x in combo.split("-")]
        b = Bet(bet_type="ワイド", combination=combo, amount=amt_u,
                odds=5.0, expected_value=0, horse_numbers=nums)
        b.race_id = race_id; b.race_date = rd
        b.is_hit = engine._check_hit(b, results_df)
        b.payout = engine._calculate_payout(b, payoffs_df) if b.is_hit else 0.0
        b.profit = b.payout - b.amount
        unique_result.bets.append(b)
        unique_result.total_investment += b.amount
        unique_result.total_payout += b.payout
        bankroll_u += b.profit

    for (sname, anum, pnum, combo) in combos_for_stacked:
        nums = [int(x) for x in combo.split("-")]
        b = Bet(bet_type="ワイド", combination=combo, amount=amt_s,
                odds=5.0, expected_value=0, horse_numbers=nums)
        b.race_id = rid; b.race_date = rd
        b.is_hit = engine._check_hit(b, results_df)
        b.payout = engine._calculate_payout(b, payoffs_df) if b.is_hit else 0.0
        b.profit = b.payout - b.amount
        stacked_result.bets.append(b)
        stacked_result.total_investment += b.amount
        stacked_result.total_payout += b.payout
        bankroll_s += b.profit
        # indiv tracking
        indiv_results[sname]["bets"] += 1
        if b.is_hit:
            indiv_results[sname]["hits"] += 1
        indiv_results[sname]["inv"] += b.amount
        indiv_results[sname]["pay"] += b.payout
        indiv_results[sname]["net"] += b.profit


m_u = MetricsCalculator.calculate_all(unique_result, test_races, test_days)
m_s = MetricsCalculator.calculate_all(stacked_result, test_races, test_days)

print("=== 個別戦略の内訳（参考） ===")
print(f"{'Strategy':<10} {'Races':>6} {'Bets':>6} {'Hit%':>6} {'ROI':>7} {'Net':>12}")
for name in [s[0] for s in STRATEGIES]:
    r = indiv_results[name]
    bets = r["bets"]
    hit_pct = r["hits"] / bets * 100 if bets else 0
    roi = r["pay"] / r["inv"] * 100 if r["inv"] else 0
    print(f"{name:<10} {r['races']:>6} {bets:>6} {hit_pct:>5.1f}% {roi:>6.1f}% {r['net']:>+11,.0f}")

print("\n=== 集計方式の比較 ===")
print(f"{'Mode':<10} {'Bets':>6} {'Hit%':>6} {'ROI':>7} {'Net':>12} {'Inv':>12} {'Pay':>12}")

bets_u = m_u["total_bets"]
hit_u = m_u["hit_rate_pct"]
roi_u = m_u["roi_pct"]
print(f"{'UNIQUE':<10} {bets_u:>6} {hit_u:>5.1f}% {roi_u:>6.1f}% {m_u['net_profit']:>+11,.0f} {int(unique_result.total_investment):>12,d} {int(unique_result.total_payout):>12,d}")

bets_s = m_s["total_bets"]
hit_s = m_s["hit_rate_pct"]
roi_s = m_s["roi_pct"]
print(f"{'STACKED':<10} {bets_s:>6} {hit_s:>5.1f}% {roi_s:>6.1f}% {m_s['net_profit']:>+11,.0f} {int(stacked_result.total_investment):>12,d} {int(stacked_result.total_payout):>12,d}")

print("\n=== DONE ===")

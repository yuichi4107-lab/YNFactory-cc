"""動的な相手点数決定: 絶対値ベース・ギャップベース・複合"""
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


def select_partners_abs(sorted_horses, min_prob, min_count=1, max_count=5):
    """絶対値フィルタのみ。閾値以上を全て採用（上限あり）"""
    qualified = [h for h in sorted_horses if h["prob"] >= min_prob]
    return qualified[:max_count] if len(qualified) >= min_count else []


def select_partners_gap(sorted_horses, min_prob, max_gap, min_count=1, max_count=5):
    """先頭からギャップ以下なら追加。最低min_prob必須"""
    if not sorted_horses or sorted_horses[0]["prob"] < min_prob:
        return []
    selected = [sorted_horses[0]]
    for h in sorted_horses[1:]:
        if len(selected) >= max_count:
            break
        if h["prob"] < min_prob:
            break
        if selected[-1]["prob"] - h["prob"] > max_gap:
            break
        selected.append(h)
    return selected if len(selected) >= min_count else []


def select_partners_combo(sorted_horses, floor_prob, max_gap, min_count=2, max_count=5):
    """絶対値フロア + ギャップ両方"""
    qualified = [h for h in sorted_horses if h["prob"] >= floor_prob]
    if len(qualified) < min_count:
        return []
    selected = [qualified[0]]
    for h in qualified[1:]:
        if len(selected) >= max_count:
            break
        if selected[-1]["prob"] - h["prob"] > max_gap:
            break
        selected.append(h)
    return selected if len(selected) >= min_count else []


VARIANTS = [
    # (label, selector_fn, args)
    ("baseline 3-flow partner>=0.35",   "fixed3", {"min_prob": 0.35}),
    # A. 絶対値ベース（動的点数）
    ("abs prob>=0.35 max5",             "abs",   {"min_prob": 0.35, "min_count": 1, "max_count": 5}),
    ("abs prob>=0.30 max5",             "abs",   {"min_prob": 0.30, "min_count": 1, "max_count": 5}),
    ("abs prob>=0.40 max5",             "abs",   {"min_prob": 0.40, "min_count": 1, "max_count": 5}),
    ("abs prob>=0.35 min2 max5",        "abs",   {"min_prob": 0.35, "min_count": 2, "max_count": 5}),
    # B. ギャップベース
    ("gap<=0.03 floor0.30",             "gap",   {"min_prob": 0.30, "max_gap": 0.03, "min_count": 2, "max_count": 5}),
    ("gap<=0.05 floor0.30",             "gap",   {"min_prob": 0.30, "max_gap": 0.05, "min_count": 2, "max_count": 5}),
    ("gap<=0.08 floor0.30",             "gap",   {"min_prob": 0.30, "max_gap": 0.08, "min_count": 2, "max_count": 5}),
    ("gap<=0.05 floor0.25",             "gap",   {"min_prob": 0.25, "max_gap": 0.05, "min_count": 2, "max_count": 5}),
    # C. 複合
    ("combo floor0.30 gap<=0.05",       "combo", {"floor_prob": 0.30, "max_gap": 0.05, "min_count": 2, "max_count": 5}),
    ("combo floor0.35 gap<=0.08",       "combo", {"floor_prob": 0.35, "max_gap": 0.08, "min_count": 2, "max_count": 5}),
    ("combo floor0.35 gap<=0.05",       "combo", {"floor_prob": 0.35, "max_gap": 0.05, "min_count": 2, "max_count": 5}),
]

print(f"{'Label':<38} {'Bets':>5} {'Hit%':>6} {'ROI':>7} {'Net':>12} {'AvgPay':>7} {'AvgN':>5}")
print("-" * 90)

for label, selector_type, sel_args in VARIANTS:
    t0 = time.time()
    result = BacktestResult()
    bankroll = 1_000_000
    engine = BacktestEngine()
    partner_counts = []

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
                   if h["pop"] >= 7 and h["prob"] >= 0.25 and h["odds"] <= 80]
        if not anchors:
            continue
        anchors.sort(key=lambda x: x["prob"], reverse=True)
        anchor = anchors[0]
        others = [h for h in horses if h["num"] != anchor["num"]]
        others.sort(key=lambda x: x["prob"], reverse=True)

        if selector_type == "fixed3":
            partners = [h for h in others if h["prob"] >= sel_args["min_prob"]][:3]
            if len(partners) < 3:
                partners = []
        elif selector_type == "abs":
            partners = select_partners_abs(others, **sel_args)
        elif selector_type == "gap":
            partners = select_partners_gap(others, **sel_args)
        elif selector_type == "combo":
            partners = select_partners_combo(others, **sel_args)
        else:
            partners = []

        if not partners:
            continue

        n = len(partners)
        partner_counts.append(n)
        # 1レース総ベット額 0.9% を点数で均等割
        bet_frac_per_combo = 0.009 / n
        rd = str(rdf["race_date"].iloc[0])
        for pt in partners:
            nums = sorted([anchor["num"], pt["num"]])
            combo = f"{nums[0]}-{nums[1]}"
            amt = max(100, round(bankroll * bet_frac_per_combo / 100) * 100)
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
    avg_n = np.mean(partner_counts) if partner_counts else 0
    marker = " ★" if m["roi_pct"] >= 100 else ""
    print(f"{label:<38} {m['total_bets']:>5} {m['hit_rate_pct']:>5.1f}% {m['roi_pct']:>6.1f}% {m['net_profit']:>+11,.0f} {avg_p:>6.2f}x {avg_n:>4.2f}{marker}")

print("=" * 90)
print("=== DONE ===")

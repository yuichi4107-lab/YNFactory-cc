"""Longshot Wide 3-flow で選ばれたパートナー馬の人気分布を集計"""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname("."), "..")))
from src.models.lgbm_model import LGBMModel
from src.utils.config_loader import get_db_path

df = pd.read_pickle("/opt/keiba-unified/jra/data/features_all.pkl")
df["target"] = (df["finish_order"] <= 3).astype(int)

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

# Collect partners from 3-flow partner>=0.35 strategy
partner_pops = []
anchor_pops = []
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
    others = [h for h in horses if h["num"] != anchor["num"] and h["prob"] >= 0.35]
    others.sort(key=lambda x: x["prob"], reverse=True)
    partners = others[:3]
    if len(partners) < 3:
        continue

    anchor_pops.append(anchor["pop"])
    for pt in partners:
        partner_pops.append(pt["pop"])

partner_arr = np.array(partner_pops)
anchor_arr = np.array(anchor_pops)

print(f"Total races with bets: {len(anchor_arr)}")
print(f"Total partners: {len(partner_arr)}")
print()
print("=== Anchor popularity distribution ===")
for p in range(7, 19):
    cnt = (anchor_arr == p).sum()
    pct = cnt / len(anchor_arr) * 100 if len(anchor_arr) else 0
    print(f"  {p:>2}番人気: {cnt:>4} ({pct:>5.1f}%)")
print(f"  Mean: {anchor_arr.mean():.2f}")
print()
print("=== Partner popularity distribution ===")
for p in range(1, 19):
    cnt = (partner_arr == p).sum()
    pct = cnt / len(partner_arr) * 100 if len(partner_arr) else 0
    bar = "█" * int(pct / 2)
    print(f"  {p:>2}番人気: {cnt:>4} ({pct:>5.1f}%) {bar}")
print(f"  Mean: {partner_arr.mean():.2f}")
print()
print("=== 本命判定（1-3番人気の割合）===")
fav_cnt = ((partner_arr >= 1) & (partner_arr <= 3)).sum()
mid_cnt = ((partner_arr >= 4) & (partner_arr <= 6)).sum()
long_cnt = (partner_arr >= 7).sum()
total = len(partner_arr)
print(f"  1-3番人気 (本命)   : {fav_cnt:>4} ({fav_cnt/total*100:>5.1f}%)")
print(f"  4-6番人気 (中位)   : {mid_cnt:>4} ({mid_cnt/total*100:>5.1f}%)")
print(f"  7番人気以下 (穴)   : {long_cnt:>4} ({long_cnt/total*100:>5.1f}%)")
print("=== DONE ===")

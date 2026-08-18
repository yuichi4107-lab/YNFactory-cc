#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""黒字化再挑戦 実験3: 軸オッズ帯 × 券種 のROI
人気薄軸(pop>=7)を軸オッズ帯で層別し、複勝/単勝/ワイドのROIを年別WFで比較。
中穴帯で黒字化する組み合わせがあるかを探る。
"""
import sys
sys.path.insert(0, '/opt/keiba-unified/jra/scripts')
import pandas as pd
import sqlite3
import re
from collections import defaultdict
from backtest_longshot_wide import get_db_path
from src.models.lgbm_model import LGBMModel

features_df = pd.read_pickle('/opt/keiba-unified/jra/data/features_all.pkl')
features_df['target'] = (features_df['finish_order'] <= 3).astype(int)
conn = sqlite3.connect(get_db_path())
payoffs_df = pd.read_sql("SELECT race_id, bet_type, combination, payout FROM payoffs", conn)
results_df = pd.read_sql("SELECT race_id, horse_number, finish_order FROM race_results", conn)
conn.close()

pay = {}
for rid, bt, combo, po in payoffs_df.itertuples(index=False):
    nums = tuple(sorted(int(x) for x in re.findall(r'\d+', str(combo))))
    pay[(rid, bt, nums)] = float(po)
res = defaultdict(dict)
for rid, hn, fo in results_df.itertuples(index=False):
    res[rid][int(hn)] = fo

meta_cols = {'race_id', 'race_date', 'horse_number', 'horse_id',
             'horse_name', 'finish_order', 'target', 'pred_proba'}
fcols = [c for c in features_df.columns if c not in meta_cols]
params = {'n_estimators': 500, 'max_depth': 5, 'learning_rate': 0.03,
          'num_leaves': 24, 'min_child_samples': 50, 'subsample': 0.7,
          'colsample_bytree': 0.6, 'reg_alpha': 0.5, 'reg_lambda': 2.0, 'verbose': -1}
BET = 100


def band(o):
    return '<15' if o < 15 else '15-30' if o < 30 else '30-60' if o < 60 else '60+'


def select(test_df, min_pop=7, min_prob=0.20, n_partner=3):
    picks = {}
    for rid, grp in test_df.groupby('race_id'):
        cand = grp[(grp['popularity'] >= min_pop) & (grp['pred_proba'] >= min_prob)]
        if cand.empty:
            continue
        anchor = grp.loc[cand['pred_proba'].idxmax()]
        others = grp[grp['horse_number'] != anchor['horse_number']].nlargest(n_partner, 'pred_proba')
        picks[rid] = (int(anchor['horse_number']),
                      [int(x) for x in others['horse_number']],
                      float(anchor.get('odds', 0) or 0))
    return picks


years = [2022, 2023, 2024, 2025]
dates = pd.to_datetime(features_df['race_date'])
agg = defaultdict(lambda: {'inv': 0.0, 'pay': 0.0, 'hit': 0, 'bets': 0})
yr = defaultdict(lambda: defaultdict(lambda: {'inv': 0.0, 'pay': 0.0}))

for year in years:
    tr = dates < f'{year}-01-01'
    te = (dates >= f'{year}-01-01') & (dates <= f'{year}-12-31')
    if tr.sum() < 10000:
        continue
    model = LGBMModel(params=params)
    model.fit(features_df[tr][fcols].fillna(0), features_df[tr]['target'])
    test_df = features_df[te].copy()
    test_df['pred_proba'] = model.predict_proba(test_df[fcols].fillna(0))
    picks = select(test_df)
    for rid, (a, partners, aodds) in picks.items():
        fo = res.get(rid, {})
        if not fo or aodds <= 0:
            continue
        b = band(aodds)
        # 複勝・単勝（軸単体）
        for ken, cond in [('複勝', fo.get(a, 99) <= 3), ('単勝', fo.get(a) == 1)]:
            k = (b, ken)
            agg[k]['inv'] += BET; agg[k]['bets'] += 1; yr[year][k]['inv'] += BET
            if cond:
                p = pay.get((rid, ken, (a,)), 0)/100*BET
                agg[k]['pay'] += p; agg[k]['hit'] += 1; yr[year][k]['pay'] += p
        # ワイド3点
        for pp in partners:
            k = (b, 'ワイド')
            agg[k]['inv'] += BET; agg[k]['bets'] += 1; yr[year][k]['inv'] += BET
            if fo.get(a, 99) <= 3 and fo.get(pp, 99) <= 3:
                p = pay.get((rid, 'ワイド', tuple(sorted([a, pp]))), 0)/100*BET
                agg[k]['pay'] += p; agg[k]['hit'] += 1; yr[year][k]['pay'] += p

print('===== 軸オッズ帯 × 券種 (pop>=7 p>=0.20, 年別WF合算) =====')
print(f'{"帯":<7}{"券種":<6}{"合算ROI":>7}{"年別ROI(22/23/24/25)":>24}{"hit%":>6}{"bets":>6}')
for b in ['<15', '15-30', '30-60', '60+']:
    for ken in ['複勝', '単勝', 'ワイド']:
        k = (b, ken)
        v = agg[k]
        if v['bets'] == 0:
            continue
        roi = v['pay']/v['inv']*100 if v['inv'] else 0
        hr = v['hit']/v['bets']*100 if v['bets'] else 0
        yrs = '/'.join(f"{(yr[y][k]['pay']/yr[y][k]['inv']*100 if yr[y][k]['inv'] else 0):.0f}" for y in years)
        print(f'{b:<7}{ken:<6}{roi:>6.0f}%{yrs:>24}{hr:>5.1f}%{v["bets"]:>6}')
print('\n※特定オッズ帯×券種で合算>100%かつ年別安定なら有望')

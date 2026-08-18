#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""黒字化再挑戦 実験1: 券種別 年別ウォークフォワードROI
同じ人気薄軸選定(pop/prob)で、単勝・複勝・ワイド・馬連・三連複のROIを年別WFで比較する。
"""
import sys
sys.path.insert(0, '/opt/keiba-unified/jra/scripts')
import pandas as pd
import numpy as np
import sqlite3
import re
import itertools
from collections import defaultdict
from backtest_longshot_wide import get_db_path
from src.models.lgbm_model import LGBMModel

features_df = pd.read_pickle('/opt/keiba-unified/jra/data/features_all.pkl')
features_df['target'] = (features_df['finish_order'] <= 3).astype(int)
conn = sqlite3.connect(get_db_path())
payoffs_df = pd.read_sql("SELECT race_id, bet_type, combination, payout FROM payoffs", conn)
results_df = pd.read_sql("SELECT race_id, horse_number, finish_order FROM race_results", conn)
conn.close()

# payoffs辞書化: (race_id, bet_type, sorted_nums_tuple) -> payout(100円あたり)
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


def select(test_df, min_pop, min_prob, n_partner=3):
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


def eval_bets(picks, st):
    for rid, (a, partners, aodds) in picks.items():
        fo = res.get(rid, {})
        if not fo:
            continue
        # 単勝（軸1着）
        st['単勝']['inv'] += BET; st['単勝']['bets'] += 1
        if fo.get(a) == 1:
            st['単勝']['pay'] += pay.get((rid, '単勝', (a,)), 0)/100*BET; st['単勝']['hit'] += 1
        # 複勝（軸3着内）
        st['複勝']['inv'] += BET; st['複勝']['bets'] += 1
        if fo.get(a, 99) <= 3:
            st['複勝']['pay'] += pay.get((rid, '複勝', (a,)), 0)/100*BET; st['複勝']['hit'] += 1
        # ワイド/馬連（軸-相手 各3点）
        for p in partners:
            st['ワイド']['inv'] += BET; st['ワイド']['bets'] += 1
            if fo.get(a, 99) <= 3 and fo.get(p, 99) <= 3:
                st['ワイド']['pay'] += pay.get((rid, 'ワイド', tuple(sorted([a, p]))), 0)/100*BET; st['ワイド']['hit'] += 1
            st['馬連']['inv'] += BET; st['馬連']['bets'] += 1
            if fo.get(a, 99) <= 2 and fo.get(p, 99) <= 2:
                st['馬連']['pay'] += pay.get((rid, '馬連', tuple(sorted([a, p]))), 0)/100*BET; st['馬連']['hit'] += 1
        # 三連複（軸＋相手2頭、C(3,2)=3点）
        for c2 in itertools.combinations(partners, 2):
            st['三連複']['inv'] += BET; st['三連複']['bets'] += 1
            trio = tuple(sorted([a]+list(c2)))
            if all(fo.get(x, 99) <= 3 for x in trio):
                st['三連複']['pay'] += pay.get((rid, '三連複', trio), 0)/100*BET; st['三連複']['hit'] += 1


years = [2022, 2023, 2024, 2025]
dates = pd.to_datetime(features_df['race_date'])
for min_pop, min_prob in [(7, 0.25), (7, 0.30)]:
    agg = defaultdict(lambda: {'inv': 0.0, 'pay': 0.0, 'hit': 0, 'bets': 0})
    yr_roi = defaultdict(list)
    for year in years:
        tr = dates < f'{year}-01-01'
        te = (dates >= f'{year}-01-01') & (dates <= f'{year}-12-31')
        if tr.sum() < 10000:
            continue
        model = LGBMModel(params=params)
        model.fit(features_df[tr][fcols].fillna(0), features_df[tr]['target'])
        test_df = features_df[te].copy()
        test_df['pred_proba'] = model.predict_proba(test_df[fcols].fillna(0))
        picks = select(test_df, min_pop, min_prob)
        st = defaultdict(lambda: {'inv': 0.0, 'pay': 0.0, 'hit': 0, 'bets': 0})
        eval_bets(picks, st)
        for k, v in st.items():
            roi = v['pay']/v['inv']*100 if v['inv'] else 0
            yr_roi[k].append(roi)
            for f in ['inv', 'pay', 'hit', 'bets']:
                agg[k][f] += v[f]
    print(f'\n===== pop>={min_pop} p>={min_prob} 券種別(年別WF) =====')
    print(f'{"券種":<6} {"合算ROI":>7} {"年別ROI(22/23/24/25)":>24} {"hit%":>6} {"bets":>6}')
    for k in ['単勝', '複勝', 'ワイド', '馬連', '三連複']:
        v = agg[k]
        roi = v['pay']/v['inv']*100 if v['inv'] else 0
        hr = v['hit']/v['bets']*100 if v['bets'] else 0
        yrs = '/'.join(f'{r:.0f}' for r in yr_roi[k])
        print(f'{k:<6} {roi:>6.0f}% {yrs:>24} {hr:>5.1f}% {v["bets"]:>6}')
print('\n※複勝など黒字かつ年別安定の券種があれば有望')

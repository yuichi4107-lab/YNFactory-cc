#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Longshot Wide 年別ウォークフォワード検証
各テスト年を、その前年までで訓練したモデルで予測し、実払戻でROIを年別＋合算で評価する。
オーバーフィット排除のため train/test を時系列分離。
"""
import sys
sys.path.insert(0, '/opt/keiba-unified/jra/scripts')
import pandas as pd
import numpy as np
import time
import sqlite3
from backtest_longshot_wide import (
    UnpopularAnchorWideStrategy, run_strategy, MetricsCalculator, get_db_path,
)
from src.models.lgbm_model import LGBMModel

features_df = pd.read_pickle('/opt/keiba-unified/jra/data/features_all.pkl')
features_df['target'] = (features_df['finish_order'] <= 3).astype(int)
conn = sqlite3.connect(get_db_path())
payoffs_df = pd.read_sql(
    'SELECT race_id, bet_type, combination, payout as payout_amount FROM payoffs', conn)
results_df = pd.read_sql(
    'SELECT race_id, horse_number, finish_order as finish_position FROM race_results', conn)
conn.close()

dates = pd.to_datetime(features_df['race_date'])
meta_cols = {'race_id', 'race_date', 'horse_number', 'horse_id',
             'horse_name', 'finish_order', 'target', 'pred_proba'}
fcols = [c for c in features_df.columns if c not in meta_cols]
params = {'n_estimators': 500, 'max_depth': 5, 'learning_rate': 0.03,
          'num_leaves': 24, 'min_child_samples': 50, 'subsample': 0.7,
          'colsample_bytree': 0.6, 'reg_alpha': 0.5, 'reg_lambda': 2.0, 'verbose': -1}

# 絞り込み候補（人気薄軸×少数化を中心に）
strategies = {
    'pop>=7 p>=0.25':            dict(anchor_min_pop=7, anchor_min_prob=0.25),
    'pop>=7 p>=0.28':            dict(anchor_min_pop=7, anchor_min_prob=0.28),
    'pop>=7 p>=0.30':            dict(anchor_min_pop=7, anchor_min_prob=0.30),
    'pop>=7 p>=0.25 part>=0.40': dict(anchor_min_pop=7, anchor_min_prob=0.25, partner_min_prob=0.40),
    'pop>=8 p>=0.25':            dict(anchor_min_pop=8, anchor_min_prob=0.25),
    'pop>=6 p>=0.28 part>=0.40': dict(anchor_min_pop=6, anchor_min_prob=0.28, partner_min_prob=0.40),
}
years = [2022, 2023, 2024, 2025]
agg = {n: {'bets': 0, 'pay': 0.0, 'hit': 0, 'inv': 0.0, 'yr_roi': []} for n in strategies}

for year in years:
    tr = dates < f'{year}-01-01'
    te = (dates >= f'{year}-01-01') & (dates <= f'{year}-12-31')
    if tr.sum() < 10000 or te.sum() < 500:
        print(f'{year}: skip (train={tr.sum()} test={te.sum()})')
        continue
    Xtr = features_df[tr][fcols].fillna(0)
    ytr = features_df[tr]['target']
    test_df = features_df[te].copy()
    t0 = time.time()
    model = LGBMModel(params=params)
    model.fit(Xtr, ytr)
    test_df['pred_proba'] = model.predict_proba(test_df[fcols].fillna(0))
    nr = test_df['race_id'].nunique()
    nd = pd.to_datetime(test_df['race_date']).dt.date.nunique()
    print(f'=== {year}: train {tr.sum()}行 / test {nr}R {nd}日 (model {time.time()-t0:.1f}s) ===')
    for name, kw in strategies.items():
        strat = UnpopularAnchorWideStrategy(**kw)
        res = run_strategy(strat, test_df, results_df, payoffs_df)
        met = MetricsCalculator.calculate_all(res, nr, nd)
        inv = sum(b.amount for b in res.bets)
        pay = sum(b.payout for b in res.bets)
        hits = sum(1 for b in res.bets if b.is_hit)
        roi = pay / inv * 100 if inv else 0
        perday = met['total_bets'] / nd / 3 if nd else 0  # ワイド3点流し→レース数換算
        print(f'  {name}: ROI={roi:.0f}% R/日={perday:.1f} bets={met["total_bets"]} hit={met["hit_rate_pct"]:.1f}%')
        agg[name]['bets'] += met['total_bets']
        agg[name]['hit'] += hits
        agg[name]['inv'] += inv
        agg[name]['pay'] += pay
        agg[name]['yr_roi'].append(roi)

print('\n' + '=' * 70)
print('年別ウォークフォワード 合算サマリ (オーバーフィット排除後)')
print('=' * 70)
print(f'{"戦略":<28} {"合算ROI":>7} {"年別ROI":>22} {"bets":>6} {"hit%":>5}')
for name, a in agg.items():
    roi = a['pay'] / a['inv'] * 100 if a['inv'] else 0
    hr = a['hit'] / a['bets'] * 100 if a['bets'] else 0
    yrs = '/'.join(f'{r:.0f}' for r in a['yr_roi'])
    print(f'{name:<28} {roi:>6.0f}% {yrs:>22} {a["bets"]:>6} {hr:>4.1f}%')
print('=' * 70)
print('※合算ROI>100%かつ年別が安定して高い基準が「黒字採用」候補')

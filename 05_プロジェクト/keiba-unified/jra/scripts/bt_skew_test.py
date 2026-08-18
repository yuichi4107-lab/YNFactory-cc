#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""train/serving skew 検証
モデルは実値(features_all.pkl)で訓練するが、テスト時は実運用_build_today_featuresと
同じく一部特徴量を0埋めして予測。ROIが実運用(66%)付近に落ちれば skew が主因と確定。
"""
import sys
sys.path.insert(0, '/opt/keiba-unified/jra/scripts')
import pandas as pd
import sqlite3
import re
from collections import defaultdict
from backtest_longshot_wide import get_db_path
from src.models.lgbm_model import LGBMModel

# 実運用 _build_today_features で 0埋め/固定されている = 訓練では実値の列
SKEW_COLS = ['speed_index_last3', 'speed_index_best3', 'speed_index_std',
             'pace_index_last3', 'running_style', 'final_3f_avg', 'final_3f_best',
             'condition_perf', 'class_level', 'corner_position_avg',
             'weight_carry_diff', 'field_quality', 'distance_wins',
             'surface_wins', 'venue_wins', 'post_position_bias']

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


def select(test_df, min_pop, min_prob, n_partner=3):
    picks = {}
    for rid, grp in test_df.groupby('race_id'):
        cand = grp[(grp['popularity'] >= min_pop) & (grp['pred_proba'] >= min_prob)]
        if cand.empty:
            continue
        anchor = grp.loc[cand['pred_proba'].idxmax()]
        others = grp[grp['horse_number'] != anchor['horse_number']].nlargest(n_partner, 'pred_proba')
        picks[rid] = (int(anchor['horse_number']), [int(x) for x in others['horse_number']])
    return picks


def wide_roi(picks):
    inv = pay_sum = hit = bets = 0
    for rid, (a, partners) in picks.items():
        fo = res.get(rid, {})
        if not fo:
            continue
        for p in partners:
            bets += 1; inv += BET
            if fo.get(a, 99) <= 3 and fo.get(p, 99) <= 3:
                pay_sum += pay.get((rid, 'ワイド', tuple(sorted([a, p]))), 0)/100*BET; hit += 1
    return (pay_sum/inv*100 if inv else 0), bets, (hit/bets*100 if bets else 0)


years = [2022, 2023, 2024, 2025]
dates = pd.to_datetime(features_df['race_date'])
for mode in ['実値(バックテスト)', '0埋め(実運用再現)']:
    print(f'\n===== モード: {mode} =====')
    for min_pop, min_prob in [(7, 0.25), (7, 0.30)]:
        roi_acc = {'inv': 0.0, 'pay': 0.0}
        yrs = []
        for year in years:
            tr = dates < f'{year}-01-01'
            te = (dates >= f'{year}-01-01') & (dates <= f'{year}-12-31')
            if tr.sum() < 10000:
                continue
            model = LGBMModel(params=params)
            model.fit(features_df[tr][fcols].fillna(0), features_df[tr]['target'])
            test_df = features_df[te].copy()
            X = test_df[fcols].fillna(0).copy()
            if mode.startswith('0埋め'):
                for c in SKEW_COLS:
                    if c in X.columns:
                        X[c] = 0
            test_df['pred_proba'] = model.predict_proba(X)
            picks = select(test_df, min_pop, min_prob)
            # 年内ROI
            inv = psum = 0
            for rid, (a, partners) in picks.items():
                fo = res.get(rid, {})
                if not fo:
                    continue
                for p in partners:
                    inv += BET
                    if fo.get(a, 99) <= 3 and fo.get(p, 99) <= 3:
                        psum += pay.get((rid, 'ワイド', tuple(sorted([a, p]))), 0)/100*BET
            yrs.append(psum/inv*100 if inv else 0)
            roi_acc['inv'] += inv; roi_acc['pay'] += psum
        roi = roi_acc['pay']/roi_acc['inv']*100 if roi_acc['inv'] else 0
        print(f'  pop>={min_pop} p>={min_prob} ワイド: 合算ROI={roi:.0f}% 年別={"/".join(f"{r:.0f}" for r in yrs)}')

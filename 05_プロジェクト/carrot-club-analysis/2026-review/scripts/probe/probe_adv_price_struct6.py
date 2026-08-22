# -*- coding: utf-8 -*-
"""攻撃5: 下限は絶対額か年内位置か / 2026年への当てはめ"""
import io, sys, os
import numpy as np, pandas as pd
from analyze5 import logit, design
from backtest import auc
from probe_adv_price_struct import build, BASE
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 240)
df = build()
df['bot25'] = (df['price_pct'] <= 0.25).astype(float)
df['bot15'] = (df['price_pct'] <= 0.15).astype(float)
print('=== 攻撃N: 絶対<2500 と 年内下位25% の直接対決 ===')
for cols in [['lo2500'], ['bot25'], ['lo2500', 'bot25'], BASE + ['lo2500'], BASE + ['bot25'],
             ['c_male', 'c_w420', 'lo2500', 'bot25']]:
    s = df.dropna(subset=[c for c in cols if c in df] + ['c_w420'])
    X, names = design(s, cols); r = logit(X, s['win_jra'], names)
    print(' ', ' + '.join(cols), '=>', ' '.join(f'{n}:z={z:+.2f}' for n, z in zip(names, r['z']) if not n.startswith('年度')))
print('  年内下位25%の該当割合と勝上:')
print(df.groupby(['year', 'lo2500']).size().unstack(fill_value=0).to_string())

p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'bosyu_2026.csv')
b = pd.read_csv(p, encoding='utf-8-sig')
print('\n=== 2026年度カタログ ===', b.shape, list(b.columns)[:20])

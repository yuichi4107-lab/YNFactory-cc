# -*- coding: utf-8 -*-
"""dam_club を既存3基準スコアに足したときの実用上の効き（率とAUC）。"""
import io, os, sys
import numpy as np
import pandas as pd
from analyze5 import load
from backtest import auc

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 200)
BASE = os.path.dirname(os.path.abspath(__file__))

df = load(central_only=True)
r = pd.read_csv(os.path.join(BASE, '..', '..', 'data', 'dam_age_rank.csv'), encoding='utf-8-sig')
keys = set(zip(r['募集年度'].astype(int), r['募集番号'].astype(int)))
df['no_i'] = pd.to_numeric(df['no'], errors='coerce')
df['dam_club'] = [1 if (y, n) in keys else 0 for y, n in zip(df['year'], df['no_i'])]
df = df[df['year'] >= 2021].copy()
df['p2539'] = df['total_man'].between(2500, 3999).astype(float)
df['w430n'] = pd.to_numeric(df['w430'], errors='coerce')
d = df.dropna(subset=['w430n', 'ret1', 'win_jra']).copy()
d['s3'] = d['male'] + d['p2539'] + d['w430n']
d['s4'] = d['s3'] + d['dam_club']

print('現行3点スコア')
print(d.groupby('s3').agg(頭数=('ret1', 'size'), 中央勝上=('win_jra', 'mean'),
                          回収1=('ret1', 'mean'), 回収中央=('ret', 'median')).round(3).to_string())
print('\n3点スコア x 母馬優先対象')
print(d.groupby(['s3', 'dam_club']).agg(頭数=('ret1', 'size'), 中央勝上=('win_jra', 'mean'),
                                        回収1=('ret1', 'mean')).round(3).to_string())
print('\n4点スコア（母馬優先対象を1点として追加）')
print(d.groupby('s4').agg(頭数=('ret1', 'size'), 中央勝上=('win_jra', 'mean'),
                          回収1=('ret1', 'mean'), 回収中央=('ret', 'median')).round(3).to_string())

print('\nAUC（年度内でスコアを比べる＝年度をまたぐ成績積み上がりの差を消す）')
for tgt in ['ret1', 'win_jra']:
    a3 = np.mean([auc(g[tgt].values, g['s3'].values) for _, g in d.groupby('year')])
    a4 = np.mean([auc(g[tgt].values, g['s4'].values) for _, g in d.groupby('year')])
    ac = np.mean([auc(g[tgt].values, g['dam_club'].values) for _, g in d.groupby('year')])
    print('  %-8s 3基準=%.3f  +母馬優先=%.3f  母馬優先のみ=%.3f' % (tgt, a3, a4, ac))
print('\n年度別AUC(ret1)')
for y, g in d.groupby('year'):
    print('  %d: 3基準=%.3f  +母馬優先=%.3f  n=%d' %
          (y, auc(g['ret1'].values, g['s3'].values), auc(g['ret1'].values, g['s4'].values), len(g)))

print('\n3基準すべて満たす馬のうち、母馬優先対象かどうか')
top = d[d['s3'] == 3]
print(top.groupby('dam_club').agg(頭数=('ret1', 'size'), 中央勝上=('win_jra', 'mean'),
                                  回収1=('ret1', 'mean'), 回収中央=('ret', 'median')).round(3).to_string())

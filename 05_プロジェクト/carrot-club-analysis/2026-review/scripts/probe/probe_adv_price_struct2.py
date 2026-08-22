# -*- coding: utf-8 -*-
"""攻撃1: 父内相対価格は 性別/馬体重/既存3基準 の代理ではないか"""
import io, sys
import numpy as np, pandas as pd
from analyze5 import logit, design
from probe_adv_price_struct import build, BASE, terc
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 220)
df = build()

print('=== 攻撃A: 父内相対価格 vs 性別・馬体重 ===')
for col in ['vs_sire_loo', 'vs_sire_crop']:
    sub = df.dropna(subset=[col, 'c_w420']).copy()
    print(f'\n[{col}] n={len(sub)}')
    # 父内価格が何と相関しているか
    print('  相関: 牡=%.3f 体重=%.3f 420up=%.3f 母年齢=%.3f 3-4月=%.3f' % (
        sub[col].corr(sub['male']), sub[col].corr(sub['weight']),
        sub[col].corr(sub['c_w420']), sub[col].corr(sub['dam_age']), sub[col].corr(sub['mar_apr'])))
    print('  父内価格の平均: 牡 %.3f / 牝せん %.3f' % (
        sub.loc[sub.male == 1, col].mean(), sub.loc[sub.male == 0, col].mean()))
    for cols in [[col], ['c_male', col], BASE + [col]]:
        X, names = design(sub, cols)
        r = logit(X, sub['win_jra'], names)
        print('  ', ' + '.join(cols))
        print(r[r['変数'].isin([n for n in names if not n.startswith('年度')])].round(3).to_string(index=False))

print('\n=== 攻撃B: 性別内で分けても効くか ===')
for col in ['vs_sire_loo', 'vs_sire_crop']:
    for m, lab in [(1, '牡'), (0, '牝せん')]:
        sub = df[(df['male'] == m)].dropna(subset=[col]).copy()
        X, names = design(sub, [col]); r = logit(X, sub['win_jra'], names).tail(1)
        sub['t'] = terc(col, sub)
        rr = sub.groupby('t', observed=True)['win_jra'].agg(['size', 'mean'])
        print(f'{col:14} {lab:4} n={len(sub):3}  z={float(r["z"].iloc[0]):+.2f}  '
              f'高{rr.loc["高","mean"]*100:.0f}%({rr.loc["高","size"]}) 安{rr.loc["安","mean"]*100:.0f}%({rr.loc["安","size"]})')

print('\n=== 攻撃C: ret1 でも効くか ===')
for col in ['vs_sire_loo', 'vs_sire_crop', 'lo2500']:
    sub = df.dropna(subset=[col, 'ret1', 'c_w420']).copy()
    for cols in [[col], BASE + [col]]:
        X, names = design(sub, cols); r = logit(X, sub['ret1'], names).tail(1)
        print(f'{col:14} {"+base" if len(cols)>1 else "単独":6} n={len(sub):3} z={float(r["z"].iloc[0]):+.2f} 係数={float(r["係数"].iloc[0]):+.3f}')

print('\n=== 攻撃D: クロップ版のサイズ依存（n2=2 の機械的な±） ===')
sub = df.dropna(subset=['vs_sire_crop']).copy()
print(sub.groupby('crop_n').apply(lambda d: pd.Series({
    'n': len(d), '勝上': round(d['win_jra'].mean(), 3),
    '高側勝上': round(d.loc[d.vs_sire_crop > 0, 'win_jra'].mean(), 3),
    '安側勝上': round(d.loc[d.vs_sire_crop < 0, 'win_jra'].mean(), 3),
    '高n': int((d.vs_sire_crop > 0).sum())}), include_groups=False).to_string())
sub2 = sub[sub.crop_n >= 3]
X, names = design(sub2, ['vs_sire_crop']); print('crop_n>=3のみ:', logit(X, sub2['win_jra'], names).tail(1).round(3).to_string(index=False))

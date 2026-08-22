# -*- coding: utf-8 -*-
"""価格 第4波: 3000万スパイクの多重検定を並べ替え検定で正しく評価する + 機構の確認。"""
import io, sys
import numpy as np
import pandas as pd
from analyze5 import load, logit, design

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 250)

df = load(central_only=True).dropna(subset=['win_jra']).copy()
df['logp_rel'] = np.log(df['total_man']) - np.log(df['total_man']).groupby(df['year']).transform('mean')
levels = [p for p in sorted(df['total_man'].unique()) if (df['total_man'] == p).sum() >= 5]
print('検定対象の価格水準:', len(levels))

yv = df['win_jra'].values.astype(float)
yr = df['year'].values
price = df['total_man'].values
Ybase = np.column_stack([(yr == y).astype(float) for y in sorted(df['year'].unique())])


def zmax(y):
    zs = []
    for p in levels:
        d = (price == p).astype(float)
        X = np.column_stack([Ybase, d])
        r = logit(X, y, [f'y{i}' for i in range(Ybase.shape[1])] + ['d'])
        zs.append(float(r['z'].iloc[-1]))
    return np.array(zs)


obs = zmax(yv)
obs_max = np.max(np.abs(obs))
print(f'観測された最大|z| = {obs_max:.2f} （3000万 z={obs[levels.index(3000.0)]:.2f}）')

rng = np.random.default_rng(1)
B = 2000
cnt = 0
cnt3 = 0
z3_null = []
for _ in range(B):
    yp = yv.copy()
    for y in np.unique(yr):
        m = yr == y
        yp[m] = rng.permutation(yp[m])       # 年内で並べ替え＝年度効果は保存
    zz = zmax(yp)
    z3_null.append(zz[levels.index(3000.0)])
    if np.max(np.abs(zz)) >= obs_max:
        cnt += 1
print(f'年内並べ替え {B}回: max|z| が {obs_max:.2f} 以上になった割合 = {cnt/B:.4f}')
print('→ これが「19水準ぜんぶ試した」ことを補正した後のp値')
z3_null = np.array(z3_null)
print(f'3000万だけを見たときの並べ替えp値（片側） = {(z3_null >= obs[levels.index(3000.0)]).mean():.4f}')

# ------------------------------------------------------------------
print('\n' + '=' * 90)
print('# 機構: 安い馬は「弱い」のか「そもそも中央で走らない」のか')
print('=' * 90)
def band(v):
    if v < 2500: return '1 -2400'
    if v < 4000: return '2 2500-3999'
    if v < 6000: return '3 4000-5999'
    return '4 6000+'
df['b4'] = df['total_man'].map(band)
df['jra_run'] = (pd.to_numeric(df['jra_starts'], errors='coerce').fillna(0) > 0).astype(int)
df['nar_only'] = ((df['win_all'] == 1) & (df['win_jra'] == 0)).astype(int)
t = df.groupby('b4').agg(n=('win_jra', 'size'), 中央出走あり=('jra_run', 'mean'),
                         中央出走数=('jra_starts', lambda s: pd.to_numeric(s, errors='coerce').mean()),
                         中央勝上=('win_jra', 'mean'), 地方のみ勝=('nar_only', 'mean'))
t['出走馬の中の勝上'] = df[df['jra_run'] == 1].groupby('b4')['win_jra'].mean()
print(t.round(3).to_string())

print('\n-- 中央に出走した馬だけに絞って価格を検定')
sub = df[df['jra_run'] == 1]
X, names = design(sub, ['logp_rel'])
print(logit(X, sub['win_jra'], names).round(3).to_string(index=False))
sub2 = sub.copy(); sub2['lo'] = (sub2['total_man'] < 2500).astype(int)
X, names = design(sub2, ['lo'])
print(logit(X, sub2['win_jra'], names).round(3).to_string(index=False))

print('\n-- 2勝以上・3勝以上でも同じか（勝ち上がりのハードルを上げる）')
df['w2'] = (pd.to_numeric(df['jra_wins'], errors='coerce').fillna(0) >= 2).astype(int)
df['w3'] = (pd.to_numeric(df['jra_wins'], errors='coerce').fillna(0) >= 3).astype(int)
for tgt in ['w2', 'w3']:
    for c in ['logp_rel']:
        X, names = design(df, [c])
        r = logit(X, df[tgt], names)
        print(f'  target={tgt} {c}: ' + r[r['変数'] == c][['係数', 'SE', 'z']].round(3).to_string(index=False, header=False))
    df['_d'] = (df['total_man'] == 3000).astype(int)
    X, names = design(df, ['_d'])
    r = logit(X, df[tgt], names)
    print(f'  target={tgt} p3000: ' + r[r['変数'] == '_d'][['係数', 'SE', 'z']].round(3).to_string(index=False, header=False))
print(df.groupby('b4').agg(n=('w2', 'size'), 中央2勝=('w2', 'mean'), 中央3勝=('w3', 'mean')).round(3).to_string())

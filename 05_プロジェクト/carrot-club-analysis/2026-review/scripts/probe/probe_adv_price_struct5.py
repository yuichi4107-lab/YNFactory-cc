# -*- coding: utf-8 -*-
"""攻撃4: 実際に2026年に使える形（過去年のみ／同年のみ）の父内相対価格と、下限の中身"""
import io, sys
import numpy as np, pandas as pd
from analyze5 import logit, design
from backtest import auc
from probe_adv_price_struct import build, BASE
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 240)
df = build()


def loyo(cols, target, data):
    out, sc = {}, pd.Series(np.nan, index=data.index)
    for y in sorted(data['year'].unique()):
        tr, te = data[data['year'] != y], data[data['year'] == y]
        X, names = design(tr, cols)
        b = logit(X, tr[target], names).set_index('変数')['係数']
        lp = np.zeros(len(te))
        for c, nm in zip(cols, names[-len(cols):]):
            lp += b[nm] * te[c].values
        sc.loc[te.index] = lp
        out[y] = auc(te[target], lp)
    out['全体'] = auc(data[target], sc)
    return out


# 過去年のみで測る版 / 過去年＋同年他馬（＝カタログ時点で本当に使える版）
past_mean, avail_mean = [], []
for i, r in df.iterrows():
    same = df[(df['sire'] == r['sire'])]
    p = same[same['year'] < r['year']]['logp_c']
    past_mean.append(p.mean() if len(p) >= 2 else np.nan)
    a = same[(same['year'] < r['year']) | ((same['year'] == r['year']) & (same.index != i))]['logp_c']
    avail_mean.append(a.mean() if len(a) >= 2 else np.nan)
df['vs_sire_past'] = df['logp_c'] - pd.Series(past_mean, index=df.index)
df['vs_sire_avail'] = df['logp_c'] - pd.Series(avail_mean, index=df.index)

print('=== 攻撃J: 実運用で計算できる版 ===')
for col in ['vs_sire_past', 'vs_sire_avail', 'vs_sire_crop', 'vs_sire_loo']:
    s = df.dropna(subset=[col, 'c_w420']).copy()
    for cols in [[col], BASE + [col]]:
        X, names = design(s, cols); r = logit(X, s['win_jra'], names).tail(1)
        tag = '+base3' if len(cols) > 1 else '単独  '
        print(f'{col:15}{tag} n={len(s):3} z={float(r["z"].iloc[0]):+.2f}', end='')
    a0 = loyo(BASE, 'win_jra', s); a1 = loyo(BASE + [col], 'win_jra', s)
    b0 = loyo(BASE, 'ret1', s); b1 = loyo(BASE + [col], 'ret1', s)
    print(f'  LOYO win {a0["全体"]:.3f}→{a1["全体"]:.3f} ({a1["全体"]-a0["全体"]:+.3f})'
          f'  ret1 {b0["全体"]:.3f}→{b1["全体"]:.3f} ({b1["全体"]-b0["全体"]:+.3f})'
          f'  年度別win ' + ' '.join(f'{y}:{a1[y]-a0[y]:+.02f}' for y in sorted(s['year'].unique())))

print('\n=== 攻撃K: 下限 <2500万 の年度別頭数と、回収面 ===')
for y, g in df.groupby('year'):
    lo = g[g.lo2500 == 1]; hi = g[g.lo2500 == 0]
    print(f'{y}: <2500 n={len(lo):2} 勝上{lo["win_jra"].mean()*100:4.0f}% 回収≥1{lo["ret1"].mean()*100:4.0f}% 回収中央{lo["ret"].median():.2f}'
          f' | >=2500 n={len(hi):2} 勝上{hi["win_jra"].mean()*100:4.0f}% 回収≥1{hi["ret1"].mean()*100:4.0f}% 回収中央{hi["ret"].median():.2f}')
print('価格3水準:')
df['band'] = pd.cut(df['total_man'], [0, 2499, 3999, 1e9], labels=['<2500', '2500-3999', '>=4000'])
print(df.groupby('band', observed=True).agg(n=('win_jra', 'size'), 勝上=('win_jra', 'mean'),
      回収1=('ret1', 'mean'), 回収中央=('ret', 'median'), 重賞=('graded', 'sum')).round(3).to_string())

print('\n=== 攻撃L: 単純合計スコアの実運用比較（同点は同じ扱い） ===')
s = df.dropna(subset=['c_w420']).copy()
defs = {'現行3基準(牡/2500-3999/420up)': s['c_male'] + s['c_price'] + s['c_w420'],
        '下限のみ(牡/>=2500/420up)': s['c_male'] + s['ge2500'] + s['c_w420']}
for lab, sc in defs.items():
    top = s[sc == 3]
    print(f'{lab:32} 通過{len(top):3}頭 勝上{top["win_jra"].mean()*100:.1f}% 重賞{int(top["graded"].sum())} '
          f'回収≥1 {top["ret1"].mean()*100:.1f}% 回収中央{top["ret"].median():.2f} 回収平均{top["ret"].mean():.2f}')

print('\n=== 攻撃M: 多重検定（同年クロップ版の並べ替え検定, 年内シャッフル1000回） ===')
rng = np.random.default_rng(0)
s = df.dropna(subset=['vs_sire_crop', 'c_w420']).copy()
X, names = design(s, BASE + ['vs_sire_crop'])
obs = float(logit(X, s['win_jra'], names).tail(1)['z'].iloc[0])
cnt = 0
for _ in range(1000):
    y = s.groupby('year')['win_jra'].transform(lambda v: rng.permutation(v.values))
    z = float(logit(X, y, names).tail(1)['z'].iloc[0])
    cnt += abs(z) >= abs(obs)
print(f'  観測 z={obs:+.2f}  並べ替えp={cnt/1000:.3f}  → 仮説を40件試したときのBonferroni閾値 p<0.00125')

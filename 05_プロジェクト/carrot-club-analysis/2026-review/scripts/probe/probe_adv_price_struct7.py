# -*- coding: utf-8 -*-
"""攻撃6: 上限を残したまま年内位置で表現し直したバンドの LOYO"""
import io, sys
import numpy as np, pandas as pd
from analyze5 import logit, design
from backtest import auc
from probe_adv_price_struct import build
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 240)
df = build().dropna(subset=['c_w420']).copy()


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


bands = {'現行 絶対2500-3999': df['total_man'].between(2500, 3999).astype(float)}
for lo, hi in [(0.25, 0.55), (0.25, 0.60), (0.20, 0.60), (0.15, 0.50), (0.25, 0.75), (0.30, 0.70)]:
    bands[f'年内位置 {lo}-{hi}'] = ((df['price_pct'] > lo) & (df['price_pct'] <= hi)).astype(float)
rows = []
for lab, v in bands.items():
    df['_b'] = v
    r = {'定式化': lab, '該当割合': round(v.mean(), 3)}
    for t in ['win_jra', 'ret1']:
        a = loyo(['c_male', '_b', 'c_w420'], t, df)
        r[t] = round(a['全体'], 3)
        r[t + '_年度'] = ' '.join(f'{a[y]:.2f}' for y in sorted(df['year'].unique()))
    top = df[(df['c_male'] + df['_b'] + df['c_w420']) == 3]
    r['通過'] = len(top); r['勝上'] = round(top['win_jra'].mean(), 3)
    r['回収1'] = round(top['ret1'].mean(), 3); r['回収中央'] = round(top['ret'].median(), 2)
    rows.append(r)
print(pd.DataFrame(rows).to_string(index=False))

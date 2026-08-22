# -*- coding: utf-8 -*-
"""攻撃2: leave-one-year-out AUC。既存3基準 vs 既存3基準+候補"""
import io, sys
import numpy as np, pandas as pd
from analyze5 import logit, design
from backtest import auc
from probe_adv_price_struct import build, BASE
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 240)
df = build()

# まず「既存3基準の単純合計」の当てはめAUC（報告の 0.614 / 0.621 の照合）
d0 = df.dropna(subset=['c_w420']).copy()
d0['s3'] = d0[BASE].sum(axis=1)
print('既存3基準 単純合計スコア: n=%d  win_jra 全体AUC=%.3f  ret1 全体AUC=%.3f' % (
    len(d0), auc(d0['win_jra'], d0['s3']), auc(d0['ret1'], d0['s3'])))
print('  年度別 win_jra:', ' '.join('%d=%.2f' % (y, auc(g['win_jra'], g['s3'])) for y, g in d0.groupby('year')))
print('  年度別 ret1   :', ' '.join('%d=%.2f' % (y, auc(g['ret1'], g['s3'])) for y, g in d0.groupby('year')))


def loyo(cols, target, data):
    """年度ごとに他4年で係数を推定し、その年を当てる。年度ダミーは除いて線形予測子を作る"""
    out, sc = {}, pd.Series(np.nan, index=data.index)
    for y in sorted(data['year'].unique()):
        tr = data[data['year'] != y]
        te = data[data['year'] == y]
        X, names = design(tr, cols)
        r = logit(X, tr[target], names)
        b = r.set_index('変数')['係数']
        lp = np.zeros(len(te))
        for c, nm in zip(cols, names[-len(cols):]):
            lp = lp + b[nm] * te[c].values
        sc.loc[te.index] = lp
        out[y] = auc(te[target], lp)
    out['全体'] = auc(data[target], sc)   # 年内でランク化しないプール
    # 年内順位に直してからプール（年度効果を消したプール）
    rk = pd.Series(sc).groupby(data['year']).rank(pct=True)
    out['全体(年内順位)'] = auc(data[target], rk)
    return out


CANDS = {
    '(なし)': [],
    '父内相対価格 全年LOO': ['vs_sire_loo'],
    '父内相対価格 同年クロップ': ['vs_sire_crop'],
    '<2500万ダミー': ['lo2500'],
    '価格の年内位置(連続)': ['price_pct'],
}
for target in ['win_jra', 'ret1']:
    print(f'\n=== LOYO AUC  target={target} ===')
    rows = []
    for lab, extra in CANDS.items():
        sub = df.dropna(subset=BASE + extra + [target]).copy()
        a0 = loyo(BASE, target, sub)
        a1 = loyo(BASE + extra, target, sub) if extra else a0
        rows.append(dict(候補=lab, n=len(sub),
                         **{f'{y}': f"{a0[y]:.3f}→{a1[y]:.3f}" for y in list(a0)},
                         差=round(a1['全体'] - a0['全体'], 3)))
    print(pd.DataFrame(rows).to_string(index=False))

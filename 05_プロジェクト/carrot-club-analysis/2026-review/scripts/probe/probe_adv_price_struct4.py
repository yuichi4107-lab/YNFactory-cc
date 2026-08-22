# -*- coding: utf-8 -*-
"""攻撃3: 下限だけ版・年内位置版の LOYO 比較 と 年度ドリフトの検証"""
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
        tr = data[data['year'] != y]; te = data[data['year'] == y]
        X, names = design(tr, cols)
        r = logit(X, tr[target], names)
        b = r.set_index('変数')['係数']
        lp = np.zeros(len(te))
        for c, nm in zip(cols, names[-len(cols):]):
            lp = lp + b[nm] * te[c].values
        sc.loc[te.index] = lp
        out[y] = auc(te[target], lp)
    out['全体'] = auc(data[target], sc)
    rk = pd.Series(sc).groupby(data['year']).rank(pct=True)
    out['全体順位'] = auc(data[target], rk)
    return out


print('=== 攻撃E: 価格変数の定式化を差し替えた LOYO（既存3基準の枠のまま） ===')
SPECS = {
    '現行 2500-3999万': ['c_male', 'c_price', 'c_w420'],
    '下限のみ >=2500万': ['c_male', 'ge2500', 'c_w420'],
    '3水準(<2500 / 2500-3999 / >=4000)': ['c_male', 'c_price', 'lo2500', 'c_w420'],
    '年内位置 上位75%': ['c_male', 'pct_top75', 'c_w420'],
    '価格を使わない': ['c_male', 'c_w420'],
}
for target in ['win_jra', 'ret1']:
    rows = []
    sub = df.dropna(subset=['c_w420', target]).copy()
    for lab, cols in SPECS.items():
        a = loyo(cols, target, sub)
        rows.append(dict(定式化=lab, **{str(k): round(v, 3) for k, v in a.items()}))
    print(f'\n--- {target} (n={len(sub)}) ---')
    print(pd.DataFrame(rows).to_string(index=False))

print('\n=== 攻撃F: 単純合計スコア（実運用形）での年度別該当数と勝ち上がり ===')
sub = df.dropna(subset=['c_w420']).copy()
for lab, cols in SPECS.items():
    sub['_s'] = sub[cols].sum(axis=1)
    full = sub[sub['_s'] == len(cols)]
    print(f'{lab:34} 全通過 n={len(full):3} 勝上={full["win_jra"].mean()*100:.1f}% '
          f'重賞={int(full["graded"].sum())} 回収≥1={full["ret1"].mean()*100:.1f}% '
          f'回収中央={full["ret"].median():.2f}')

print('\n=== 攻撃G: 年度ドリフトの事実確認 ===')
raw = df.copy()
print(raw.groupby('year')['total_man'].median().to_string())
for y, g in raw.groupby('year'):
    print(f'{y}: 2500万の年内位置={ (g["total_man"]<2500).mean():.3f} '
          f'4000万の年内位置={(g["total_man"]<4000).mean():.3f} '
          f'2500-3999の割合={g["total_man"].between(2500,3999).mean():.3f}')

print('\n=== 攻撃H: 父内相対価格 と 生の価格水準 の同時投入 ===')
for col in ['vs_sire_loo', 'vs_sire_crop']:
    s = df.dropna(subset=[col, 'c_w420']).copy()
    for cols in [['logp_c', col], ['c_male', 'c_w420', 'logp_c', col], ['c_male','c_w420','sire_loo',col]]:
        cols = [c for c in cols if c in s.columns and s[c].notna().all()]
        X, names = design(s, cols); r = logit(X, s['win_jra'], names)
        print(f'  [{col}] ' + ' + '.join(cols))
        print('   ', ' '.join(f'{n}:z={z:+.2f}' for n, z in zip(names, r['z']) if not n.startswith('年度')))

print('\n=== 攻撃I: 牡馬基準を父内価格で置き換えられるか（LOYO win_jra） ===')
s = df.dropna(subset=['vs_sire_loo', 'c_w420']).copy()
for cols in [['c_male','c_price','c_w420'], ['vs_sire_loo','c_price','c_w420'],
             ['c_male','c_price','c_w420','vs_sire_loo']]:
    a = loyo(cols, 'win_jra', s)
    print(f'  {"+".join(cols):48} 全体={a["全体"]:.3f} ' + ' '.join(f'{y}={a[y]:.2f}' for y in [2020,2021,2022,2023,2024]))

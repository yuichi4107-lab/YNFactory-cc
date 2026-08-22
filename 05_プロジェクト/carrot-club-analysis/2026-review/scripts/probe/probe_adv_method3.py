# -*- coding: utf-8 -*-
"""敵対的検証・第3弾。実務条件（3基準を満たした馬の中での並べ替え）と、
3-4月生×ret1 のLOYO改善が本物かの再確認。"""
import io, json, os, sys
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from analyze5 import load, logit, design
from backtest import auc
pd.set_option('display.width', 240)

DS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'datasets')
df = load(central_only=True)
rs = json.load(open(os.path.join(DS, 'race_summary.json'), encoding='utf-8'))
for c in ['jra_starts', 'jra_wins']:
    df[c] = pd.to_numeric(df['key'].map(lambda k: (rs.get(k) or {}).get(c)), errors='coerce')
df['win2'] = (df['jra_wins'].fillna(0) >= 2).astype(float)
d = df.dropna(subset=['win_jra', 'weight', 'total_man']).copy()
d['lprice'] = np.log(d['total_man'].astype(float))
d['lp_w'] = d['lprice'] - d.groupby('year')['lprice'].transform('mean')
d['male'] = d['male'].astype(float)
d['p2540'] = d['total_man'].between(2500, 3999).astype(float)
d['w420'] = (d['weight'] >= 420).astype(float)
d['pj'] = pd.to_numeric(d['prize_jra'], errors='coerce').fillna(0)
d['sc3'] = d[['male', 'p2540', 'w420']].sum(axis=1)
BASE3 = ['male', 'p2540', 'w420']

print('=== [I] 3基準を全部満たした馬だけを取り出して、その中で log価格 が効くか ===')
sub = d[d['sc3'] == 3].copy()
print('  該当 n=%d（年度別 %s）' % (len(sub), dict(sub.groupby('year').size())))
for tgt in ['win_jra', 'win2', 'ret1']:
    X, names = design(sub, ['lp_w'])
    r = logit(X, sub[tgt], names)
    z = float(r[r['変数'] == 'lp_w']['z'].iloc[0])
    print('  %-8s ショートリスト内 lp_w z=%+.2f （基準率%.0f%%）' % (tgt, z, 100 * sub[tgt].mean()))
print('  ※3基準を満たすと価格は 2500-3999 に閉じ込められるので、価格のレンジ自体が消える:')
print('   ', sub['total_man'].describe()[['min', '25%', '50%', '75%', 'max']].round(0).to_dict())

print('\n=== [J] 「安い方を切る」だけで足りるか（下位分位ダミー vs log価格）===')
d['q20'] = (d.groupby('year')['total_man'].rank(pct=True) <= 0.20).astype(float)
d['q80'] = (d.groupby('year')['total_man'].rank(pct=True) > 0.80).astype(float)
for tgt in ['win_jra', 'win2', 'ret1']:
    s = d.dropna(subset=[tgt])
    X, names = design(s, ['male', 'w420', 'q20', 'q80'])
    r = logit(X, s[tgt], names)
    r = r[~r['変数'].astype(str).str.startswith('年度')]
    print('  %-8s ' % tgt + '  '.join('%s z=%+.2f' % (a, b) for a, b in zip(r['変数'], r['z'])))
print('  q20=年内最安20%%ダミー / q80=年内最高20%%ダミー')

print('\n=== [K] 3-4月生の ret1 への効き：LOYO を目的別にやり直し + 単純加点でも確認 ===')


def loyo_rank(cols, tgt, data, ridge=1.0):
    s = data.dropna(subset=list(cols) + [tgt]).copy().reset_index(drop=True)
    pr = np.full(len(s), np.nan)
    for y in sorted(s['year'].unique()):
        tr, te = s[s['year'] != y], s[s['year'] == y]
        Xtr = np.column_stack([np.ones(len(tr))] + [tr[c].astype(float).values for c in cols])
        Xte = np.column_stack([np.ones(len(te))] + [te[c].astype(float).values for c in cols])
        r = logit(Xtr, tr[tgt], ['b'] + list(cols), ridge=ridge)
        pr[te.index] = Xte @ r['係数'].values
    s['_p'] = pr
    s['_r'] = s.groupby('year')['_p'].rank(pct=True)
    return s


for tgt in ['ret1', 'win_jra']:
    for ridge in [0.1, 1.0, 5.0]:
        a0 = loyo_rank(BASE3, tgt, d, ridge)
        a1 = loyo_rank(BASE3 + ['mar_apr'], tgt, d, ridge)
        print('  %-8s ridge=%.1f  3基準%.3f → +3-4月生%.3f (差%+.3f)'
              % (tgt, ridge, auc(a0[tgt], a0['_r']), auc(a1[tgt], a1['_r']),
                 auc(a1[tgt], a1['_r']) - auc(a0[tgt], a0['_r'])))
    s = d.dropna(subset=[tgt]).copy()
    s['s3'] = s[BASE3].sum(axis=1)
    s['s4'] = s['s3'] + s['mar_apr']
    print('  %-8s 単純加点   3基準%.3f → 4基準%.3f' % (tgt, auc(s[tgt], s['s3']), auc(s[tgt], s['s4'])))

print('\n=== [L] 4点（3基準+3-4月生）を実際に買ったら（当てはめ、年度別）===')
s = d.copy()
s['s4'] = s[BASE3].sum(axis=1) + s['mar_apr']
for thr, lab in [(3, '3基準3点'), (4, '4点満点')]:
    col = 'sc3' if thr == 3 else 's4'
    m = s[col] >= thr if thr == 3 else s['s4'] >= 4
    m = (s['sc3'] >= 3) if lab == '3基準3点' else (s['s4'] >= 4)
    g = s[m]
    per = ' '.join('%d:%.0f%%(%d)' % (y, 100 * gg['ret1'].mean(), len(gg)) for y, gg in g.groupby('year'))
    print('  %-10s n=%3d 勝上%.0f%% 回収≥1が%.0f%% 総賞金/総募集=%.3f  %s'
          % (lab, len(g), 100 * g['win_jra'].mean(), 100 * g['ret1'].mean(),
             g['pj'].sum() / g['total_man'].sum(), per))

print('\n=== [M] 2024年度(現3歳)の打ち切りが win2/win3 の結論をどれだけ動かすか ===')
for drop in [[], [2024], [2023, 2024]]:
    s = d[~d['year'].isin(drop)]
    X, names = design(s, BASE3 + ['lp_w'])
    r = logit(X, s['win2'], names)
    z = float(r[r['変数'] == 'lp_w']['z'].iloc[0])
    X, names = design(s, BASE3 + ['lp_w'])
    r2 = logit(X, s['win_jra'], names)
    z2 = float(r2[r2['変数'] == 'lp_w']['z'].iloc[0])
    print('  除外%-12s n=%3d  win2 lp_w z=%+.2f / win_jra lp_w z=%+.2f' % (str(drop), len(s), z, z2))

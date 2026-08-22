# -*- coding: utf-8 -*-
"""敵対的検証・第2弾。log価格の効きが年内なのか年間なのか、単調なのか非単調なのかを分解する。"""
import io, json, os, sys
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from analyze5 import load, logit, design
from backtest import auc
pd.set_option('display.width', 240)
rng = np.random.default_rng(7)

DS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'datasets')
df = load(central_only=True)
rs = json.load(open(os.path.join(DS, 'race_summary.json'), encoding='utf-8'))
for c in ['jra_starts', 'jra_wins']:
    df[c] = pd.to_numeric(df['key'].map(lambda k: (rs.get(k) or {}).get(c)), errors='coerce')
df['win2'] = (df['jra_wins'].fillna(0) >= 2).astype(float)
df['win3'] = (df['jra_wins'].fillna(0) >= 3).astype(float)
d = df.dropna(subset=['win_jra', 'weight', 'total_man']).copy()
d['lprice'] = np.log(d['total_man'].astype(float))
d['male'] = d['male'].astype(float)
d['p2540'] = d['total_man'].between(2500, 3999).astype(float)
d['w420'] = (d['weight'] >= 420).astype(float)
# 年内で中心化した log価格（年間の物価上昇分を完全に抜く）
d['lp_w'] = d['lprice'] - d.groupby('year')['lprice'].transform('mean')
d['lp_b'] = d.groupby('year')['lprice'].transform('mean')
BASE3 = ['male', 'p2540', 'w420']

print('年度別の募集価格（万円）')
print(d.groupby('year')['total_man'].agg(['size', 'median', 'mean']).round(0).to_string())

print('\n=== [A] log価格を「年内成分」と「年間成分」に分解して同時投入 ===')
print('   （年度ダミーを入れると年間成分は年度ダミーに吸収されるので、ここでは年度ダミーを外す）')
for tgt in ['win_jra', 'win2', 'win3', 'ret1']:
    s = d.dropna(subset=[tgt])
    cols = BASE3 + ['lp_w', 'lp_b']
    X = np.column_stack([np.ones(len(s))] + [s[c].astype(float).values for c in cols])
    r = logit(X, s[tgt], ['b'] + cols, ridge=1e-6)
    print('  %-8s ' % tgt + '  '.join('%s z=%+.2f' % (a, b) for a, b in zip(r['変数'][1:], r['z'][1:])))

print('\n=== [B] 年度ダミー入りで lp_w（年内成分）だけを使う＝真の年内効果 ===')
for tgt in ['win_jra', 'win2', 'win3', 'ret1']:
    s = d.dropna(subset=[tgt])
    X, names = design(s, BASE3 + ['lp_w'])
    r = logit(X, s[tgt], names)
    r = r[~r['変数'].astype(str).str.startswith('年度')]
    print('  %-8s ' % tgt + '  '.join('%s z=%+.2f' % (a, b) for a, b in zip(r['変数'], r['z'])))

print('\n=== [C] p2540 を外して lp_w 単独（共線性を疑う）年度ダミー入り ===')
for tgt in ['win_jra', 'win2', 'win3', 'ret1']:
    s = d.dropna(subset=[tgt])
    for cols in [['lp_w'], ['male', 'w420', 'lp_w']]:
        X, names = design(s, cols)
        r = logit(X, s[tgt], names)
        z = float(r[r['変数'] == 'lp_w']['z'].iloc[0])
        print('  %-8s %-24s lp_w z=%+.2f' % (tgt, str(cols), z), end='')
    print()

print('\n=== [D] 年度別 lp_w 単独（年度内, 3基準なし / 3基準あり）===')
for tgt in ['win_jra', 'win2', 'win3', 'ret1']:
    l1, l2 = [], []
    for y in sorted(d['year'].unique()):
        s = d[d['year'] == y].dropna(subset=[tgt])
        X = np.column_stack([np.ones(len(s)), s['lp_w'].values])
        r = logit(X, s[tgt], ['b', 'lp_w'], ridge=1e-3)
        l1.append('%d:%+.2f' % (y, r.iloc[-1]['z']))
        cols = BASE3 + ['lp_w']
        X = np.column_stack([np.ones(len(s))] + [s[c].astype(float).values for c in cols])
        r = logit(X, s[tgt], ['b'] + cols, ridge=1e-3)
        l2.append('%d:%+.2f' % (y, r.iloc[-1]['z']))
    print('  %-8s 単独   %s' % (tgt, ' '.join(l1)))
    print('  %-8s 3基準後 %s' % ('', ' '.join(l2)))

print('\n=== [E] 年内価格5分位ごとの実測（年度別・全体）===')
d['q5'] = d.groupby('year')['total_man'].transform(lambda s: pd.qcut(s, 5, labels=[1, 2, 3, 4, 5]))
for tgt in ['win_jra', 'win2', 'win3', 'ret1']:
    print('\n -- %s' % tgt)
    piv = d.pivot_table(index='q5', columns='year', values=tgt, aggfunc='mean', observed=True) * 100
    piv['全体'] = d.groupby('q5', observed=True)[tgt].mean() * 100
    print(piv.round(0).to_string())

print('\n=== [F] 単調性の検定：lp_w の2次項 ===')
d['lp_w2'] = d['lp_w'] ** 2
for tgt in ['win_jra', 'win2', 'win3', 'ret1']:
    s = d.dropna(subset=[tgt])
    X, names = design(s, ['male', 'w420', 'lp_w', 'lp_w2'])
    r = logit(X, s[tgt], names)
    r = r[~r['変数'].astype(str).str.startswith('年度')]
    print('  %-8s ' % tgt + '  '.join('%s z=%+.2f' % (a, b) for a, b in zip(r['変数'], r['z'])))

print('\n=== [G] 金額ベース：スコア上位が本当に儲かるか（LOYO・年内上位30%を買う） ===')
d['pj'] = pd.to_numeric(d['prize_jra'], errors='coerce').fillna(0)


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


SETS = [('3基準のみ', BASE3), ('+log価格', BASE3 + ['lprice']),
        ('+3-4月生', BASE3 + ['mar_apr']), ('+ノーザンF', BASE3 + ['nf']),
        ('+母8-11歳', BASE3 + ['dam811'])]
for nm, cols in SETS:
    s = loyo_rank(cols, 'win_jra', d)
    top = s[s['_r'] > 0.70]
    print('  %-12s 上位30%%: n=%3d 勝上%.0f%% 回収≥1が%.0f%% 平均募集%.0f万 総賞金/総募集=%.3f'
          % (nm, len(top), 100 * top['win_jra'].mean(), 100 * top['ret1'].mean(),
             top['total_man'].mean(), top['pj'].sum() / top['total_man'].sum()))
print('  %-12s        n=%3d 勝上%.0f%% 回収≥1が%.0f%% 平均募集%.0f万 総賞金/総募集=%.3f'
      % ('（全馬）', len(d), 100 * d['win_jra'].mean(), 100 * d['ret1'].mean(),
         d['total_man'].mean(), d['pj'].sum() / d['total_man'].sum()))

print('\n=== [H] 3-4月生 × JRA出走 の年度別（報告の再現）と、出走→勝ちへの伝播 ===')
d['ran'] = (pd.to_numeric(d['jra_starts'], errors='coerce').fillna(0) >= 1).astype(float)
for tgt in ['ran', 'win_jra', 'ret1']:
    line = []
    for y in sorted(d['year'].unique()):
        s = d[d['year'] == y]
        a = s[s['mar_apr'] == 1][tgt].mean() * 100
        b = s[s['mar_apr'] == 0][tgt].mean() * 100
        line.append('%d:%+.0fpt' % (y, a - b))
    s = d
    print('  %-8s 全体%+.1fpt  %s' % (tgt, (s[s['mar_apr'] == 1][tgt].mean() - s[s['mar_apr'] == 0][tgt].mean()) * 100, ' '.join(line)))
X, names = design(d, ['male', 'p2540', 'w420', 'mar_apr'])
r = logit(X, d['ran'], names)
print('  出走を目的に3基準同時: ' + '  '.join('%s z=%+.2f' % (a, b) for a, b in zip(r['変数'], r['z']) if not str(a).startswith('年度')))
print('  出走した馬のうち勝ち上がり率: 3-4月生 %.0f%% / それ以外 %.0f%%'
      % (100 * d[(d['ran'] == 1) & (d['mar_apr'] == 1)]['win_jra'].mean(),
         100 * d[(d['ran'] == 1) & (d['mar_apr'] == 0)]['win_jra'].mean()))

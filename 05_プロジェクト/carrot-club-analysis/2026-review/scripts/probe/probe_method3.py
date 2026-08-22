# -*- coding: utf-8 -*-
"""手法・第3弾。AUC差のブートストラップ／検出力の逆算／体重の最適域／実務案の検証。"""
import io, json, os, sys
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from analyze5 import load, logit, design
from backtest import auc
from scipy import stats
pd.set_option('display.width', 220)
rng = np.random.default_rng(0)

DS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'datasets')
df = load(central_only=True)
rs = json.load(open(os.path.join(DS, 'race_summary.json'), encoding='utf-8'))
for c in ['wins_by3', 'jra_starts', 'jra_wins']:
    df[c] = pd.to_numeric(df['key'].map(lambda k: (rs.get(k) or {}).get(c)), errors='coerce')
df['win2'] = (df['jra_wins'].fillna(0) >= 2).astype(float)
df['win3'] = (df['jra_wins'].fillna(0) >= 3).astype(float)
d = df.dropna(subset=['win_jra', 'weight']).copy()
d['lprice'] = np.log(d['total_man'].astype(float))
d['lprice2'] = (d['lprice'] - d['lprice'].mean()) ** 2
d['w10c'] = d['weight_rel'] / 10.0
d['w10c2'] = d['w10c'] ** 2
d['male'] = d['male'].astype(float)
d['p2540'] = d['total_man'].between(2500, 3999).astype(float)
d['w420'] = (d['weight'] >= 420).astype(float)
d['phi'] = (d.groupby('year')['total_man'].rank(pct=True) > 0.5).astype(float)

print('[1] 検出力の逆算: 真の効果がXptのとき z>1.96 になる確率（該当群のnで）')
for lab, col in [('3-4月生', 'mar_apr'), ('ノーザンF', 'nf'), ('母8-11歳', 'dam811')]:
    n1 = int((d[col] == 1).sum()); n2 = len(d) - n1
    se = np.sqrt(0.493 * 0.507 * (1 / n1 + 1 / n2))
    line = []
    for delta in [0.03, 0.05, 0.08, 0.10, 0.15]:
        pw = stats.norm.sf(1.96 - delta / se) + stats.norm.cdf(-1.96 - delta / se)
        line.append(f'{delta:.0%}→{pw:.0%}')
    print(f'  {lab:<10}(該当{n1}/非{n2}) 検出確率: ' + '  '.join(line))

print('\n[2] LOYO AUC の差にブートストラップ信頼区間をつける（目的=win_jra, 年内ランク化）')


def loyo_pred(cols, tgt, data, ridge=1.0):
    s = data.dropna(subset=cols + [tgt]).copy().reset_index(drop=True)
    pr = np.full(len(s), np.nan)
    for y in sorted(s['year'].unique()):
        tr, te = s[s['year'] != y], s[s['year'] == y]
        Xtr = np.column_stack([np.ones(len(tr))] + [tr[c].astype(float).values for c in cols])
        Xte = np.column_stack([np.ones(len(te))] + [te[c].astype(float).values for c in cols])
        r = logit(Xtr, tr[tgt], ['b'] + cols, ridge=ridge)
        pr[te.index] = Xte @ r['係数'].values
    s['_p'] = pr
    return s, s.groupby('year')['_p'].rank(pct=True).values


for tgt in ['win_jra', 'win2']:
    s = d.dropna(subset=[tgt]).copy().reset_index(drop=True)
    s['_sc'] = s[['male', 'p2540', 'w420']].sum(axis=1)
    a_score = s.groupby('year')['_sc'].rank(pct=True).values
    _, a_lin = loyo_pred(['male', 'lprice', 'w10c'], tgt, s)
    _, a_q = loyo_pred(['male', 'lprice', 'lprice2', 'w10c', 'w10c2'], tgt, s)
    _, a_mix = loyo_pred(['male', 'p2540', 'w420', 'lprice'], tgt, s)
    y = s[tgt].values
    labs = {'現行3基準加点': a_score, 'ロジ連続3変数': a_lin, 'ロジ連続+2次': a_q, '3基準+log価格': a_mix}
    base = auc(y, a_score)
    print(f'\n 目的={tgt}  n={len(s)}')
    for k, v in labs.items():
        diffs = []
        for _ in range(600):
            idx = rng.integers(0, len(y), len(y))
            if len(np.unique(y[idx])) < 2:
                continue
            diffs.append(auc(y[idx], v[idx]) - auc(y[idx], a_score[idx]))
        lo, hi = np.percentile(diffs, [2.5, 97.5])
        print(f'   {k:<14} AUC={auc(y,v):.3f}  対現行差={auc(y,v)-base:+.3f} [95%CI {lo:+.3f},{hi:+.3f}]')

print('\n[3] 馬体重の最適域（年内平均比のビン別）')
d['wb'] = pd.cut(d['weight_rel'], [-99, -30, -15, 0, 15, 30, 99])
t = d.groupby('wb', observed=True).agg(頭数=('win_jra', 'size'), 勝上=('win_jra', 'mean'),
                                       _2勝=('win2', 'mean'), _3勝=('win3', 'mean'),
                                       回収1=('ret1', 'mean'))
print(t.assign(**{c: (t[c] * 100).round(0) for c in ['勝上', '_2勝', '_3勝', '回収1']}).to_string())
print('\n生の馬体重ビン')
d['wb2'] = pd.cut(d['weight'], [0, 399, 419, 439, 459, 479, 999])
t = d.groupby('wb2', observed=True).agg(頭数=('win_jra', 'size'), 勝上=('win_jra', 'mean'),
                                        _2勝=('win2', 'mean'), 回収1=('ret1', 'mean'))
print(t.assign(**{c: (t[c] * 100).round(0) for c in ['勝上', '_2勝', '回収1']}).to_string())

print('\n[4] 現行3基準に「価格を連続で」足したときの上乗せ（年度ダミー入り, 同時投入）')
for tgt in ['win_jra', 'win2', 'win3', 'ret1']:
    s = d.dropna(subset=[tgt])
    X, names = design(s, ['male', 'p2540', 'w420', 'lprice'])
    r = logit(X, s[tgt], names)
    r = r[~r['変数'].astype(str).str.startswith('年度')]
    print(f'\n → {tgt} n={len(s)}')
    print(r.round(3).to_string(index=False))

print('\n[5] 「価格年内上位半分」を4つ目の基準に足したときの年度別')
for tgt in ['win_jra', 'win2', 'ret1']:
    s = d.dropna(subset=[tgt]).copy()
    s['sc3'] = s[['male', 'p2540', 'w420']].sum(axis=1)
    s['sc4'] = s['sc3'] + s['phi']
    for nm, col, hi in [('3基準 3点', 'sc3', 3), ('4基準 3点以上', 'sc4', 3), ('4基準 4点', 'sc4', 4)]:
        m = s[col] >= hi
        rows = []
        for y in sorted(s['year'].unique()):
            mm = m & (s['year'] == y)
            rows.append(f'{y}:{100*s.loc[mm,tgt].mean():.0f}%({int(mm.sum())})')
        print(f'  {tgt:<8} {nm:<14} 全体{100*s.loc[m,tgt].mean():.0f}%({int(m.sum())})  ' + ' '.join(rows))
    print(f'  {tgt:<8} {"（全馬）":<14} 全体{100*s[tgt].mean():.0f}%({len(s)})')
    print()

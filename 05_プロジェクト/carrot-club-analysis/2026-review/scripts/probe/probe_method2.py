# -*- coding: utf-8 -*-
"""手法・第2弾。価格の連続効果／アウトカム別検出力／LOYO AUC(win2)／多重検定。"""
import io, json, os, sys
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from analyze5 import load, logit, design
from backtest import auc
pd.set_option('display.width', 220)

BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')
df = load(central_only=True)
rs = json.load(open(os.path.join(DS, 'race_summary.json'), encoding='utf-8'))
for c in ['wins_by3', 'jra_starts', 'jra_wins', 'prize_by3']:
    df[c] = pd.to_numeric(df['key'].map(lambda k: (rs.get(k) or {}).get(c)), errors='coerce')
df['win2'] = (df['jra_wins'].fillna(0) >= 2).astype(float)
df['win3'] = (df['jra_wins'].fillna(0) >= 3).astype(float)
df['ran'] = (df['jra_starts'].fillna(0) > 0).astype(float)
df['winby3'] = (df['wins_by3'].fillna(0) >= 1).astype(float)
df['grd'] = (pd.to_numeric(df['graded'], errors='coerce').fillna(0) >= 1).astype(float)
d = df.dropna(subset=['win_jra']).copy()
d['lprice'] = np.log(d['total_man'].astype(float))
d['lprice2'] = (d['lprice'] - d['lprice'].mean()) ** 2
d['w10c'] = d['weight_rel'] / 10.0
d['w10c2'] = d['w10c'] ** 2
d['male'] = d['male'].astype(float)
d['price25_60_n'] = d['total_man'].between(2500, 3999).astype(float)
d['w420'] = (d['weight'] >= 420).astype(float)
d['n_foals_n'] = pd.to_numeric(d['n_foals'], errors='coerce')
print('n_foals 非欠損:'); print(d.groupby('year')['n_foals_n'].apply(lambda s: s.notna().sum()).to_string())

print('\n' + '=' * 80)
print('[A] 価格: 二値バンド vs 連続。アウトカム別に符号が変わるか')
print('=' * 80)
d['pb'] = pd.cut(d['total_man'], [0, 1999, 2499, 3999, 5999, 999999],
                 labels=['~1999', '2000-2499', '2500-3999', '4000-5999', '6000+'])
tab = d.groupby('pb', observed=True).agg(頭数=('win_jra', 'size'), 出走=('ran', 'mean'),
                                         勝上=('win_jra', 'mean'), _2勝=('win2', 'mean'),
                                         _3勝=('win3', 'mean'), 重賞=('grd', 'sum'),
                                         回収1=('ret1', 'mean'), 回収中央=('ret', 'median'))
print((tab.assign(**{c: (tab[c] * 100).round(0) for c in ['出走', '勝上', '_2勝', '_3勝', '回収1']})).to_string())
print('\n年内価格パーセンタイル5分位')
d['pq'] = d.groupby('year')['total_man'].transform(lambda s: pd.qcut(s.rank(method='first'), 5, labels=[1, 2, 3, 4, 5]))
t2 = d.groupby('pq', observed=True).agg(頭数=('win_jra', 'size'), 勝上=('win_jra', 'mean'),
                                        _2勝=('win2', 'mean'), _3勝=('win3', 'mean'),
                                        重賞=('grd', 'sum'), 回収1=('ret1', 'mean'))
print(t2.assign(**{c: (t2[c] * 100).round(0) for c in ['勝上', '_2勝', '_3勝', '回収1']}).to_string())


def run(cols, tgt, data=None, label=''):
    s = (data if data is not None else d).dropna(subset=cols + [tgt])
    X, names = design(s, cols)
    r = logit(X, s[tgt], names)
    r = r[~r['変数'].astype(str).str.startswith('年度')]
    print(f'\n-- {label or ",".join(cols)} → {tgt}  n={len(s)}')
    print(r.round(3).to_string(index=False))
    return r


for tgt in ['win_jra', 'win2', 'win3', 'grd']:
    run(['lprice', 'lprice2'], tgt, label='log価格 連続+2次')
print('\n-- 価格バンド二値 vs 連続を同時投入（どちらが本体か）')
for tgt in ['win_jra', 'win2', 'win3']:
    run(['price25_60_n', 'lprice'], tgt, label='2500-3999ダミー + log価格')

print('\n-- log価格 の年度別安定性（連続なので四分位で代用: 上位50% vs 下位50%）')
d['phi'] = (d.groupby('year')['total_man'].rank(pct=True) > 0.5).astype(float)
for tgt in ['win_jra', 'win2', 'win3', 'ret1']:
    out = []
    for y in sorted(d['year'].unique()):
        s = d[d['year'] == y]
        g = s.groupby('phi')[tgt].mean()
        out.append(f'{y}:{100*(g.get(1.0,np.nan)-g.get(0.0,np.nan)):+.0f}pt')
    print(f'  価格年内上位半分 {tgt:<8}', '  '.join(out))

print('\n' + '=' * 80)
print('[B] アウトカム別 検出力（発生率が低いほど検出は難しい）')
print('=' * 80)
for ocol, olab in [('ran', '出走'), ('win_jra', '1勝'), ('win2', '2勝'), ('win3', '3勝'), ('grd', '重賞')]:
    p = d[ocol].mean()
    for frac in [0.3, 0.5]:
        n1 = int(444 * frac); n2 = 444 - n1
        m = 1.96 * np.sqrt(p * (1 - p) * (1 / n1 + 1 / n2)) * (2.802 / 1.96)
        print(f'  {olab:<5}(率{p:.1%}) 該当{frac:.0%}: 検出力80%必要差={100*m:4.1f}pt '
              f'(相対では{m/p:.0%}の増加が必要)')

print('\n' + '=' * 80)
print('[C] LOYO AUC: 目的を 2勝以上 にしたとき')
print('=' * 80)


def loyo(cols, tgt, data, ridge=1.0):
    s = data.dropna(subset=cols + [tgt]).copy().reset_index(drop=True)
    pr = np.full(len(s), np.nan)
    for y in sorted(s['year'].unique()):
        tr, te = s[s['year'] != y], s[s['year'] == y]
        Xtr = np.column_stack([np.ones(len(tr))] + [tr[c].astype(float).values for c in cols])
        Xte = np.column_stack([np.ones(len(te))] + [te[c].astype(float).values for c in cols])
        r = logit(Xtr, tr[tgt], ['b'] + cols, ridge=ridge)
        pr[te.index] = Xte @ r['係数'].values
    s['_p'] = pr
    s['_pr'] = s.groupby('year')['_p'].rank(pct=True)
    return auc(s[tgt], pr), auc(s[tgt], s['_pr'])


def score_auc(cols, tgt, data):
    s = data.dropna(subset=cols + [tgt]).copy()
    s['_s'] = s[cols].astype(float).sum(axis=1)
    s['_sr'] = s.groupby('year')['_s'].rank(pct=True)
    return auc(s[tgt], s['_s']), auc(s[tgt], s['_sr'])


for tgt in ['win_jra', 'win2', 'win3', 'grd']:
    print(f'\n目的={tgt} (raw / 年内ランク化)')
    a = score_auc(['male', 'price25_60_n', 'w420'], tgt, d); print(f'  現行3基準 加点            {a[0]:.3f} / {a[1]:.3f}')
    a = loyo(['male', 'lprice', 'w10c'], tgt, d);            print(f'  LOYO 性+log価格+体重連続  {a[0]:.3f} / {a[1]:.3f}')
    a = loyo(['male', 'lprice', 'lprice2', 'w10c', 'w10c2'], tgt, d)
    print(f'  LOYO +2次項              {a[0]:.3f} / {a[1]:.3f}')

print('\n' + '=' * 80)
print('[D] 多重検定: 今回の探索の仮説数')
print('=' * 80)
K = {'検出力(検定なし)': 0, '連続変数の主効果(2目的x8仕様)': 16, '交互作用(2目的x5)': 10,
     'アウトカム定義(7目的x10変数)': 70, 'log賞金OLS(10変数)': 10,
     '価格連続+2次(4目的)': 4, '価格二値vs連続(3目的)': 3, 'LOYO AUC(検定でない)': 0}
tot = sum(K.values())
print(pd.Series(K).to_string())
print(f'\n合計 {tot} 検定')
from scipy import stats
for m in [tot, 113, 50, 20, 10]:
    print(f'  m={m:>3}: Bonferroni α=0.05/m → |z|>{stats.norm.ppf(1-0.025/m):.2f}')
print('\n本担当の中で |z|>3.0 を超えたもの（Bonferroni m=113 の閾値3.44 と比較）:')

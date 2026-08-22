# -*- coding: utf-8 -*-
"""dam_club / lot の敵対的検証その2：順列検定・年度層別の分布・支持頭数の実数。"""
import io, os, sys
import numpy as np
import pandas as pd
import scipy.stats as st
from analyze5 import load, logit, design
from backtest import auc

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 220)
BASE = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(20260822)


def sec(t):
    print('\n' + '=' * 78)
    print('■ ' + t)
    print('=' * 78)


df = load(central_only=True)
df['no_i'] = pd.to_numeric(df['no'], errors='coerce')
r = pd.read_csv(os.path.join(BASE, '..', '..', 'data', 'dam_age_rank.csv'), encoding='utf-8-sig')
r['no_i'] = pd.to_numeric(r['募集番号'], errors='coerce')
keys = set(zip(r['募集年度'], r['no_i']))
lotk = {(y, n) for y, n, l in zip(r['募集年度'], r['no_i'], r['母馬優先枠で抽選']) if l == 1}
df['dam_club'] = [1.0 if (y, n) in keys else 0.0 for y, n in zip(df['year'], df['no_i'])]
df['lot'] = [1.0 if (y, n) in lotk else 0.0 for y, n in zip(df['year'], df['no_i'])]
df.loc[df['year'] == 2020, ['dam_club', 'lot']] = np.nan
df['p2539'] = df['total_man'].between(2500, 3999).astype(float)
df['w420'] = (df['weight'] >= 420).astype(float)
df.loc[df['weight'].isna(), 'w420'] = np.nan
BASE3 = ['male', 'p2539', 'w420']
d = df[df['dam_club'].notna()].dropna(subset=BASE3).copy()

sec('A. 効果を支えている実数（回収≥1の頭数）')
t = d.pivot_table(index='dam_club', columns='year', values='ret1', aggfunc=['sum', 'size'])
print(t.to_string())
print('\n回収≥1の合計: 該当 %d/%d  非該当 %d/%d' %
      (d[d.dam_club == 1]['ret1'].sum(), (d.dam_club == 1).sum(),
       d[d.dam_club == 0]['ret1'].sum(), (d.dam_club == 0).sum()))
print('\n年度別 retの中央値/平均（分布の中心はどちらが上か）')
print(d.pivot_table(index='dam_club', columns='year', values='ret',
                    aggfunc=['median', 'mean']).round(3).to_string())
print('\n年度別 募集総額の平均（分母）')
print(d.pivot_table(index='dam_club', columns='year', values='total_man', aggfunc='mean').round(0).to_string())

sec('B. 年度層別の分布検定（ret を年度内パーセンタイルに直して比較）')
d['ret_pct'] = d.groupby('year')['ret'].rank(pct=True)
a = d[d.dam_club == 1]['ret_pct']
b = d[d.dam_club == 0]['ret_pct']
print('  年度内パーセンタイル平均 該当 %.3f vs 非該当 %.3f' % (a.mean(), b.mean()))
print('  Mann-Whitney(年度内順位) p=%.4f' % st.mannwhitneyu(a, b, alternative='two-sided').pvalue)
print('  生retのMann-Whitney p=%.4f' % st.mannwhitneyu(d[d.dam_club == 1]['ret'],
                                                       d[d.dam_club == 0]['ret'],
                                                       alternative='two-sided').pvalue)
print('\n  回収率しきい値を下から順に（該当% vs 非該当%、年度ダミー付きロジットz）')
for th in [0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 1.0, 1.5, 2.0, 3.0]:
    s = d.dropna(subset=['ret']).copy()
    s['y'] = (s['ret'] >= th).astype(float)
    if s['y'].nunique() < 2:
        continue
    X, names = design(s, ['dam_club'] + BASE3)
    z = logit(X, s['y'], names).iloc[4]['z']
    print('   ≥%.2f  %5.1f%% vs %5.1f%%  (陽性 %3d)  z=%+.2f' %
          (th, 100 * s[s.dam_club == 1]['y'].mean(), 100 * s[s.dam_club == 0]['y'].mean(),
           int(s['y'].sum()), z))

sec('C. LOYO AUC の順列検定（dam_clubのラベルを年度内でシャッフル）')


def loyo_tot(dd, cols, tgt, lab_override=None):
    dd = dd.dropna(subset=cols + [tgt]).copy()
    if lab_override is not None:
        dd = dd.assign(**{cols[-1]: lab_override})
    allsc, ally, per = [], [], {}
    for y in sorted(dd['year'].unique()):
        tr = dd[dd['year'] != y]
        te = dd[dd['year'] == y]
        Xtr, names = design(tr, cols)
        b = logit(Xtr, tr[tgt], names)['係数'].values[-len(cols):]
        sc = te[cols].values.astype(float) @ b
        per[y] = auc(te[tgt].values, sc)
        allsc.append(pd.Series(sc).rank(pct=True).values)
        ally.append(te[tgt].values)
    return auc(np.concatenate(ally), np.concatenate(allsc)), per


for tgt in ['ret1', 'win_jra']:
    dd = d.dropna(subset=BASE3 + ['dam_club', tgt]).copy()
    base, _ = loyo_tot(dd, BASE3, tgt)
    obs, perobs = loyo_tot(dd, BASE3 + ['dam_club'], tgt)
    gain = obs - base
    null = []
    for _ in range(400):
        perm = dd.groupby('year')['dam_club'].transform(lambda s: pd.Series(rng.permutation(s.values), index=s.index))
        g, _p = loyo_tot(dd, BASE3 + ['dam_club'], tgt, lab_override=perm.values)
        null.append(g - base)
    null = np.array(null)
    print('  %-8s 3基準 %.3f → +dam_club %.3f  ΔAUC=%+.4f' % (tgt, base, obs, gain))
    print('           年度内ランダム化400回の Δ: 平均%+.4f SD%.4f 95%%上限%+.4f  片側p=%.3f'
          % (null.mean(), null.std(), np.quantile(null, 0.95), (null >= gain).mean()))

sec('D. lot（母馬優先枠で抽選）— 標本と事前利用可能性')
for tgt in ['ret1', 'win_jra']:
    dd = d.dropna(subset=BASE3 + ['lot', tgt]).copy()
    base, _ = loyo_tot(dd, BASE3, tgt)
    obs, per = loyo_tot(dd, BASE3 + ['lot'], tgt)
    print('  %-8s 3基準 %.3f → +lot %.3f  ΔAUC=%+.4f  年度別 %s'
          % (tgt, base, obs, obs - base, ' '.join('%d:%.3f' % kv for kv in per.items())))
print('  lot=1の年度別頭数:', d.groupby('year')['lot'].sum().to_dict())
print('  lot=1かつ回収≥1の実数:')
print(d[d.lot == 1].groupby('year')['ret1'].agg(['sum', 'size']).to_string())
# lot は dam_club の部分集合。dam_club を入れた上で lot に追加情報があるか
s = d.dropna(subset=['ret1'])
X, names = design(s, ['lot', 'dam_club'] + BASE3)
print('\n  dam_club と同時投入(ret1):')
print(logit(X, s['ret1'], names)[4:].round(3).to_string(index=False))
X, names = design(s, ['lot', 'dam_club'] + BASE3)
print('  同 win_jra:')
s2 = d.dropna(subset=['win_jra'])
X, names = design(s2, ['lot', 'dam_club'] + BASE3)
print(logit(X, s2['win_jra'], names)[4:].round(3).to_string(index=False))

sec('E. プラセボ: 同じ出現率のランダム2値変数を1000回作り、LOYO ΔAUC(ret1)の分布を見る')
dd = d.dropna(subset=BASE3 + ['ret1']).copy()
base, _ = loyo_tot(dd, BASE3, 'ret1')
rates = dd.groupby('year')['dam_club'].mean().to_dict()
gains = []
for _ in range(200):
    lab = np.array([1.0 if rng.random() < rates[y] else 0.0 for y in dd['year']])
    if lab.std() == 0:
        continue
    g, _p = loyo_tot(dd, BASE3 + ['dam_club'], 'ret1', lab_override=lab)
    gains.append(g - base)
gains = np.array(gains)
print('  ランダム変数200本の ΔAUC: 平均%+.4f SD%.4f  最大%+.4f  |Δ|≥0.027の割合 %.3f'
      % (gains.mean(), gains.std(), gains.max(), (np.abs(gains) >= 0.027).mean()))
print('  実測 ΔAUC=+%.4f が上位何%%か: %.1f%%' % (0.0, 100 * (gains >= (loyo_tot(dd, BASE3 + ['dam_club'], 'ret1')[0] - base)).mean()))

sec('F. 2026年度の該当数と、年度をまたぐ運用可能性')
b26 = pd.read_csv(os.path.join(BASE, '..', '..', 'data', 'bosyu_2026.csv'), encoding='utf-8-sig')
c = [x for x in b26.columns if '母馬優先' in x]
print('  bosyu_2026列:', c)
if c:
    print(b26[c[0]].value_counts(dropna=False).to_string())
print('  dam_age_rank.csv 収録年度:', sorted(r['募集年度'].unique()), ' → 2020年度は欠落')
print('  各年度の該当率:', d.groupby('year')['dam_club'].mean().round(3).to_dict())

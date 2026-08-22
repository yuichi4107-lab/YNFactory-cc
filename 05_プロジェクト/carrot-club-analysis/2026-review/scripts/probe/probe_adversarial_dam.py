# -*- coding: utf-8 -*-
"""母の質（dam_club / 母馬優先枠抽選）候補の敵対的検証。潰しにかかる立場。"""
import io, os, sys
import numpy as np
import pandas as pd
import scipy.stats as st
from analyze5 import load, logit, design
from backtest import auc

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 220)
BASE = os.path.dirname(os.path.abspath(__file__))


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
df['dam_club'] = [1 if (y, n) in keys else 0 for y, n in zip(df['year'], df['no_i'])]
df['lot'] = [1 if (y, n) in lotk else 0 for y, n in zip(df['year'], df['no_i'])]
df.loc[df['year'] == 2020, ['dam_club', 'lot']] = np.nan

# 公式の既存3基準（依頼文の定義：牡 / 2500-3999万 / 馬体重420kg以上）
df['p2539'] = df['total_man'].between(2500, 3999).astype(float)
df['w420'] = (df['weight'] >= 420).astype(float)
df.loc[df['weight'].isna(), 'w420'] = np.nan
df['w430n'] = (df['weight'] >= 430).astype(float)
df.loc[df['weight'].isna(), 'w430n'] = np.nan
df['n_foals_i'] = pd.to_numeric(df['n_foals'], errors='coerce')
BASE3 = ['male', 'p2539', 'w420']

d = df[df['dam_club'].notna()].copy()      # 2021-2024


def logit_cl(X, y, names, cluster=None):
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    b = np.zeros(X.shape[1])
    for _ in range(200):
        p = 1 / (1 + np.exp(-(X @ b)))
        W = np.clip(p * (1 - p), 1e-9, None)
        H = X.T @ (X * W[:, None]) + 1e-6 * np.eye(X.shape[1])
        step = np.linalg.solve(H, X.T @ (y - p) - 1e-6 * b)
        b = b + step
        if np.max(np.abs(step)) < 1e-10:
            break
    Hinv = np.linalg.inv(H)
    se = np.sqrt(np.diag(Hinv))
    out = pd.DataFrame({'変数': names, '係数': b, 'SE': se, 'z': b / se, 'OR': np.exp(b)})
    if cluster is not None:
        u = X * (y - p)[:, None]
        cl = pd.Series(np.asarray(cluster).astype(str)).reset_index(drop=True)
        M = np.zeros((X.shape[1], X.shape[1]))
        for _, idx in cl.groupby(cl).groups.items():
            s = u[np.asarray(idx)].sum(axis=0)
            M += np.outer(s, s)
        g = cl.nunique()
        V = Hinv @ M @ Hinv * (g / max(g - 1, 1))
        se_c = np.sqrt(np.diag(V))
        out['SE_cl'] = se_c
        out['z_cl'] = b / se_c
        out['クラスタ数'] = g
    return out


sec('0. 標本と再現')
print('全体 n=%d / dam_club有効(2021-24) n=%d' % (len(df), len(d)))
print(d.groupby(['year', 'dam_club']).agg(n=('ret1', 'size'), 回収1=('ret1', 'mean'),
      中央勝上=('win_jra', 'mean'), 回収中央値=('ret', 'median'),
      総額=('total_man', 'mean')).round(3).to_string())
print()
print(d.groupby('dam_club').agg(n=('ret1', 'size'), 回収1=('ret1', 'mean'),
      中央勝上=('win_jra', 'mean'), 重賞=('graded', 'sum'), 総額=('total_man', 'mean')).round(3).to_string())
print('\nlot:')
print(d.groupby('lot').agg(n=('ret1', 'size'), 回収1=('ret1', 'mean'), 中央勝上=('win_jra', 'mean')).round(3).to_string())
print('lot 年度別 n:')
print(pd.crosstab(d['year'], d['lot']).to_string())
print('dam_club x lot:')
print(pd.crosstab(d['dam_club'], d['lot']).to_string())

sec('1. 既存3基準（公式定義:牡/2500-3999万/420kg以上）と同時投入')
for tgt in ['win_jra', 'ret1']:
    for cols in [BASE3, BASE3 + ['dam_club']]:
        s = d.dropna(subset=cols + [tgt])
        X, names = design(s, cols)
        rr = logit_cl(X, s[tgt], names, cluster=s['dam'])
        print('\n-- %s  n=%d  vars=%s' % (tgt, len(s), cols))
        print(rr[len(rr) - len(cols):].round(3).to_string(index=False))

sec('1b. 母馬報告が使った430kg版でも確認（報告のz=+2.46が出るか）')
for tgt in ['ret1', 'win_jra']:
    s = d.dropna(subset=['male', 'p2539', 'w430n', 'dam_club', tgt])
    X, names = design(s, ['dam_club', 'male', 'p2539', 'w430n'])
    print('\n-- %s n=%d' % (tgt, len(s)))
    print(logit_cl(X, s[tgt], names, cluster=s['dam'])[4:].round(3).to_string(index=False))

sec('2. 交絡: 母年齢・産次・NF・価格の年内位置を入れても残るか')
d['dam_age_c'] = d['dam_age'].fillna(d['dam_age'].median())
d['nf_i'] = d['nf'].astype(float)
d['nfoal'] = d['n_foals_i'].fillna(d['n_foals_i'].median())
for tgt in ['ret1', 'win_jra']:
    cols = ['dam_club'] + BASE3 + ['dam_age_c', 'nfoal', 'nf_i', 'price_rel']
    s = d.dropna(subset=cols + [tgt])
    X, names = design(s, cols)
    print('\n-- %s n=%d' % (tgt, len(s)))
    print(logit_cl(X, s[tgt], names, cluster=s['dam'])[4:].round(3).to_string(index=False))

sec('3. 同一母の重複（クラスタ）')
print('母のユニーク数 %d / 頭数 %d' % (d['dam'].nunique(), len(d)))
vc = d['dam'].value_counts()
print('同一母2頭以上: %d母 %d頭' % ((vc >= 2).sum(), vc[vc >= 2].sum()))
v1 = d[d['dam_club'] == 1]['dam'].value_counts()
print('該当側   母%d / 頭%d / 2頭以上の母%d' % (len(v1), v1.sum(), (v1 >= 2).sum()))
v0 = d[d['dam_club'] == 0]['dam'].value_counts()
print('非該当側 母%d / 頭%d / 2頭以上の母%d' % (len(v0), v0.sum(), (v0 >= 2).sum()))

sec('4. LOYO（その年を学習に使わずその年を当てる）')


def loyo(dd, cols, tgt):
    dd = dd.dropna(subset=cols + [tgt]).copy()
    res, allsc, ally = {}, [], []
    for y in sorted(dd['year'].unique()):
        tr = dd[dd['year'] != y]
        te = dd[dd['year'] == y]
        Xtr, names = design(tr, cols)
        b = logit(Xtr, tr[tgt], names)['係数'].values
        w = b[-len(cols):]
        sc = te[cols].values.astype(float) @ w
        res[y] = auc(te[tgt].values, sc)
        allsc.append(pd.Series(sc).rank(pct=True).values)
        ally.append(te[tgt].values)
    tot = auc(np.concatenate(ally), np.concatenate(allsc))
    return res, tot


for tgt in ['win_jra', 'ret1']:
    print('\n-- 目的変数 %s（2021-2024／dam_clubが定義できる範囲）' % tgt)
    for lab, cols in [('3基準', BASE3), ('3基準+dam_club', BASE3 + ['dam_club']),
                      ('3基準+lot', BASE3 + ['lot'])]:
        res, tot = loyo(d, cols, tgt)
        print('  %-16s 全体%.3f  ' % (lab, tot) + ' '.join('%d:%.3f' % (y, v) for y, v in res.items()))
    res, tot = loyo(df, BASE3, tgt)
    print('  %-16s 全体%.3f  ' % ('3基準(5年参考)', tot) + ' '.join('%d:%.3f' % (y, v) for y, v in res.items()))

sec('4b. 素点スコア（重みなし加点）の年度内AUC ※報告の0.658→0.687の再現')
d['s3'] = d['male'] + d['p2539'] + d['w420']
d['s3b'] = d['male'] + d['p2539'] + d['w430n']
for tgt in ['ret1', 'win_jra']:
    print('\n--', tgt)
    for lab, base in [('420版', 's3'), ('430版', 's3b')]:
        s = d.dropna(subset=[base, tgt])
        per0 = [(y, auc(g[tgt].values, g[base].values)) for y, g in s.groupby('year')]
        per1 = [(y, auc(g[tgt].values, (g[base] + g['dam_club']).values)) for y, g in s.groupby('year')]
        print('  %s 3基準%.3f → +dam_club %.3f' % (lab, np.mean([v for _, v in per0]),
                                                  np.mean([v for _, v in per1])))
        print('     年度別 ' + ' '.join('%d:%.3f→%.3f' % (y, v, w) for (y, v), (_, w) in zip(per0, per1)))

sec('5. 頑健性: 外れ値・年度落とし（3基準420版と同時投入、ret1）')
s = d.dropna(subset=['ret1'] + BASE3)
for k in [0, 5, 10, 15, 20]:
    ss = s.sort_values('ret', ascending=False).iloc[k:]
    X, names = design(ss, ['dam_club'] + BASE3)
    rr = logit_cl(X, ss['ret1'], names, cluster=ss['dam'])
    print('  回収率上位%2d頭を除外 n=%3d  z=%+.2f (クラスタ頑健 z=%+.2f)' % (k, len(ss), rr.iloc[4]['z'], rr.iloc[4]['z_cl']))
print()
for y in sorted(d['year'].unique()):
    ss = s[s['year'] != y]
    X, names = design(ss, ['dam_club'] + BASE3)
    rr = logit_cl(X, ss['ret1'], names, cluster=ss['dam'])
    print('  %d年度を抜く n=%3d  z=%+.2f (cl %+.2f)' % (y, len(ss), rr.iloc[3]['z'], rr.iloc[3]['z_cl']))

sec('6. 連続量にすると効くか（ret1のしきい値依存を疑う）')
s = d.dropna(subset=['ret'])
a = s[s['dam_club'] == 1]['ret']
b_ = s[s['dam_club'] == 0]['ret']
print('  ret平均 %.3f vs %.3f / 中央値 %.3f vs %.3f' % (a.mean(), b_.mean(), a.median(), b_.median()))
print('  Mann-Whitney U p=%.4f' % st.mannwhitneyu(a, b_, alternative='two-sided').pvalue)
s2 = s.copy()
s2['lret'] = np.log1p(s2['ret'])
X, names = design(s2, ['dam_club'])
bb = np.linalg.lstsq(X, s2['lret'].values, rcond=None)[0]
resid = s2['lret'].values - X @ bb
sig = resid @ resid / (len(resid) - X.shape[1])
V = sig * np.linalg.inv(X.T @ X)
print('  log1p(ret) 線形回帰 dam_club係数 %.4f  t=%+.2f' % (bb[-1], bb[-1] / np.sqrt(V[-1, -1])))

sec('7. 多重検定')
for z in [2.46, 2.26, 2.20, 1.95]:
    print('  z=%.2f -> 両側p=%.4f' % (z, 2 * (1 - st.norm.cdf(z))))
print('  30仮説のBonferroni p<0.00167 -> 必要z=3.14 / 20仮説 p<0.0025 -> 必要z=3.02')

sec('8. 2026年度への適用可能性')
b26 = pd.read_csv(os.path.join(BASE, '..', '..', 'data', 'bosyu_2026.csv'), encoding='utf-8-sig')
print(b26.columns.tolist())
c = [x for x in b26.columns if '母馬優先' in x]
if c:
    print(b26[c[0]].value_counts().to_string())
print('dam_age_rank.csv の収録年度:', sorted(r['募集年度'].unique()))

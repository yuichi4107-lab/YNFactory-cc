# -*- coding: utf-8 -*-
"""厩舎と育成の切り口を検定する（既存ファイルは触らない）。"""
import io, os, sys, csv, json
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from analyze5 import load, logit, design
from backtest import auc
DS = os.path.join(BASE, '..', 'datasets')
pd.set_option('display.width', 200); pd.set_option('display.max_rows', 400)

df = load(central_only=True).dropna(subset=['win_jra']).copy()
df = df.sort_values(['year', 'no']).reset_index(drop=True)
print('n =', len(df), ' 年度別:', dict(df.groupby('year').size()))

def sec(t): print('\n' + '=' * 78 + '\n■ ' + t + '\n' + '=' * 78)

# ---------- 厩舎の所属地（自分自身を除いた多数決） ----------
sec('関東/関西（厩舎の所属地。自分の district は使わず厩舎の多数決で決める）')
ok = df[df['district'].isin(['美浦', '栗東'])]
cnt = ok.groupby(['trainer_key', 'district']).size().unstack(fill_value=0)
def loo_district(r):
    t = r['trainer_key']
    if t not in cnt.index: return np.nan
    row = cnt.loc[t].copy()
    if r['district'] in row.index: row[r['district']] -= 1
    if row.sum() == 0: return np.nan
    return row.idxmax()
df['tr_dist'] = df.apply(loo_district, axis=1)
print(df.groupby('tr_dist')[['win_jra', 'ret1']].agg(['mean', 'size']).round(3).to_string())
print(df.pivot_table(index='tr_dist', columns='year', values='win_jra', aggfunc=['mean','size']).round(2).to_string())
sub = df[df['tr_dist'].notna()].copy()
sub['関西'] = (sub['tr_dist'] == '栗東').astype(int)
for tgt in ['win_jra', 'ret1']:
    X, nm = design(sub, ['関西'])
    print(tgt, logit(X, sub[tgt], nm).round(3).iloc[-1].to_dict())

# ---------- 厩舎の過去実績（前年度までのみ＝リーク無し） ----------
sec('厩舎prior: その厩舎の「自分より前の年度」のキャロット産駒の中央勝上率')
def prior_feats(df, k=6):
    out_n, out_r, out_raw = [], [], []
    for i, r in df.iterrows():
        past = df[(df['year'] < r['year']) & (df['trainer_key'] == r['trainer_key'])]
        base = df[df['year'] < r['year']]['win_jra'].mean() if (df['year'] < r['year']).any() else np.nan
        n = len(past)
        out_n.append(n)
        out_raw.append(past['win_jra'].mean() if n else np.nan)
        out_r.append((past['win_jra'].sum() + k * base) / (n + k) if n and not np.isnan(base) else np.nan)
    return pd.Series(out_n, index=df.index), pd.Series(out_r, index=df.index), pd.Series(out_raw, index=df.index)

df['pn'], df['pshrunk'], df['praw'] = prior_feats(df)
d = df[(df['year'] >= 2021) & df['pshrunk'].notna()].copy()
print('検定対象（2021年度以降・前年度実績あり）n =', len(d))
print('厩舎prior頭数の分布:', dict(d['pn'].value_counts().sort_index().head(12)))
d['prior_c'] = d['pshrunk'] - d.groupby('year')['pshrunk'].transform('mean')
for tgt in ['win_jra', 'ret1']:
    X, nm = design(d, ['prior_c'])
    print('\n--', tgt); print(logit(X, d[tgt], nm).round(3).to_string(index=False))

print('\n-- prior を3分位に切って年度別に並べる')
d['pq'] = d.groupby('year')['pshrunk'].transform(lambda s: pd.qcut(s, 3, labels=['低','中','高'], duplicates='drop'))
print(d.pivot_table(index='pq', columns='year', values='win_jra', aggfunc=['mean','size'], observed=False).round(2).to_string())
print(d.groupby('pq', observed=False)[['win_jra','ret1','ret']].agg(['mean','size']).round(3).to_string())

print('\n-- prior頭数3頭以上に限る（薄い厩舎を除く）')
d3 = d[d['pn'] >= 3].copy()
d3['prior_c'] = d3['praw'] - d3.groupby('year')['praw'].transform('mean')
for tgt in ['win_jra', 'ret1']:
    X, nm = design(d3, ['prior_c'])
    print(tgt, 'n=%d' % len(d3), logit(X, d3[tgt], nm).round(3).iloc[-1].to_dict())
print(d3.pivot_table(index=pd.qcut(d3['praw'], 3, duplicates='drop'), columns='year',
                     values='win_jra', aggfunc=['mean','size'], observed=False).round(2).to_string())

print('\n-- 年度別 AUC（prior単体、年度内で比較）')
for y in sorted(d['year'].unique()):
    dy = d[d['year'] == y]
    if dy['win_jra'].nunique() < 2: continue
    print(f'  {y}: n={len(dy):3d} AUC(prior)={auc(dy["win_jra"], dy["pshrunk"]):.3f}  勝上率={dy["win_jra"].mean():.2f}')

# ---------- 厩舎の規模（キャロット預託頭数） ----------
sec('厩舎の規模＝前年度までのキャロット預託頭数')
d['many'] = (d['pn'] >= 3).astype(int)
print(d.groupby('many')[['win_jra','ret1']].agg(['mean','size']).round(3).to_string())
print(d.pivot_table(index='many', columns='year', values='win_jra', aggfunc=['mean','size']).round(2).to_string())
for tgt in ['win_jra','ret1']:
    X, nm = design(d, ['many']); print(tgt, logit(X, d[tgt], nm).round(3).iloc[-1].to_dict())
d['pn_c'] = d['pn'] - d.groupby('year')['pn'].transform('mean')
for tgt in ['win_jra','ret1']:
    X, nm = design(d, ['pn_c']); print(tgt+' (連続)', logit(X, d[tgt], nm).round(3).iloc[-1].to_dict())

# ---------- 育成牧場 ----------
sec('育成牧場（roster 2020-2022 + club_2023 2023年度）')
ik = {}
for r in csv.DictReader(open(os.path.join(DS, 'roster.csv'), encoding='utf-8-sig')):
    v = (r.get('ikusei') or '').strip()
    if v: ik[f"{r['year']}#{r['no']}"] = v
for r in csv.DictReader(open(os.path.join(DS, 'club_2023.csv'), encoding='utf-8-sig')):
    v = (r.get('ikusei') or '').strip()
    if v: ik[f"2023#{r['no']}"] = v
def norm(v):
    return v.replace('Ｎ','N').replace('Ｆ','F').replace(' ','').strip()
df['ikusei'] = df['key'].map(lambda k: norm(ik[k]) if k in ik else np.nan)
di = df[df['ikusei'].notna()].copy()
print('育成牧場あり n =', len(di), ' 年度:', dict(di.groupby('year').size()))
print(di['ikusei'].value_counts().to_string())
g = di.groupby('ikusei')[['win_jra','ret1','ret']].agg(['mean','size']).round(3)
print(g[g[('win_jra','size')] >= 5].to_string())
big = di['ikusei'].value_counts()
big = big[big >= 10].index
print('\n年度別（頭数10以上の育成牧場）')
print(di[di['ikusei'].isin(big)].pivot_table(index='ikusei', columns='year', values='win_jra',
      aggfunc=['mean','size']).round(2).to_string())
for name in big:
    di['_f'] = (di['ikusei'] == name).astype(int)
    X, nm = design(di, ['_f'])
    r1 = logit(X, di['win_jra'], nm).round(3).iloc[-1]
    r2 = logit(X, di['ret1'], nm).round(3).iloc[-1]
    print(f'{name:<10} n={int(di["_f"].sum()):3d}  win z={r1["z"]:+.2f} OR={r1["オッズ比"]:.2f}   ret z={r2["z"]:+.2f}')
di['nf_ik'] = di['ikusei'].str.contains('NF').astype(int)
print('\nNF系育成 vs その他')
print(di.groupby('nf_ik')[['win_jra','ret1']].agg(['mean','size']).round(3).to_string())
X, nm = design(di, ['nf_ik'])
print('win', logit(X, di['win_jra'], nm).round(3).iloc[-1].to_dict())
print('ret', logit(X, di['ret1'], nm).round(3).iloc[-1].to_dict())

# ---------- 転厩・地方移籍 ----------
sec('予定厩舎と現厩舎の不一致（転厩・地方移籍）※出資後に起きる事象＝基準には使えない')
def moved(r):
    p = (r['trainer_planned'] or '').replace(' ','')
    n = (r['trainer'] or '').replace(' ','')
    if not p or not n: return np.nan
    return 0 if n.startswith(p) else 1
df['moved'] = df.apply(moved, axis=1)
print(df.groupby('moved')[['win_jra','ret1','starts']].agg(['mean','size']).round(3).to_string())
print(df.pivot_table(index='moved', columns='year', values='win_jra', aggfunc=['mean','size']).round(2).to_string())
print('中央以外の所属になった馬:', int((~df['district'].isin(['美浦','栗東'])).sum()),
      ' その中央勝上率:', round(df[~df['district'].isin(['美浦','栗東'])]['win_jra'].mean(), 3))

# ---------- 既存3基準への上乗せ ----------
sec('既存3基準（牡・2500-3999万・420kg以上）に厩舎priorを足すと効くか')
d['price2539'] = d['total_man'].between(2500, 3999).astype(int)
d['w420'] = (d['weight'] >= 420).astype(int)
dd = d.dropna(subset=['w420']).copy()
for tgt in ['win_jra','ret1']:
    X, nm = design(dd, ['male','price2539','w420','prior_c'])
    print('\n--', tgt, 'n=%d' % len(dd)); print(logit(X, dd[tgt], nm).round(3).to_string(index=False))
dd['base3'] = dd['male'] + dd['price2539'] + dd['w420']
dd['ptop'] = (dd.groupby('year')['pshrunk'].rank(pct=True) > 0.667).astype(int)
print('\n3基準スコア × 厩舎prior上位1/3')
print(dd.pivot_table(index='base3', columns='ptop', values='win_jra', aggfunc=['mean','size']).round(2).to_string())

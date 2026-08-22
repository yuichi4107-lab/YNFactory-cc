# -*- coding: utf-8 -*-
"""厩舎prior・育成牧場の頑健性チェック（交絡の除去・LOYO・2026適用可否）。"""
import io, os, sys, csv
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from analyze5 import load, logit, design
from backtest import auc
DS = os.path.join(BASE, '..', 'datasets')
DATA = os.path.join(BASE, '..', '..', 'data')
pd.set_option('display.width', 200); pd.set_option('display.max_rows', 400)
def sec(t): print('\n' + '=' * 78 + '\n■ ' + t + '\n' + '=' * 78)

df = load(central_only=True).dropna(subset=['win_jra']).copy().sort_values(['year','no']).reset_index(drop=True)

def prior(df, k, col='win_jra', maxback=99):
    ns, rs = [], []
    for _, r in df.iterrows():
        past = df[(df['year'] < r['year']) & (df['year'] >= r['year']-maxback) & (df['trainer_key'] == r['trainer_key'])]
        base = df[df['year'] < r['year']][col].mean()
        n = len(past); ns.append(n)
        rs.append((past[col].sum() + k*base)/(n+k) if n and not np.isnan(base) else np.nan)
    return pd.Series(ns, index=df.index), pd.Series(rs, index=df.index)

df['pn'], df['pw'] = prior(df, 6)
_, df['pr'] = prior(df, 6, 'ret1')
_, df['pw2'] = prior(df, 6, 'win_jra', maxback=2)
d = df[(df['year'] >= 2021) & df['pw'].notna()].copy()
for c in ['pw','pr','pw2']:
    d[c+'_c'] = d[c] - d.groupby('year')[c].transform('mean')

sec('厩舎prior の交絡チェック（価格・馬体重・性別を入れても残るか）')
d['price2539'] = d['total_man'].between(2500,3999).astype(int)
d['w420'] = (d['weight'] >= 420).astype(int)
print('prior と価格の相関:', round(d[['pw','total_man','price_pct','weight']].corr()['pw'].round(3).to_dict().__str__(), 0) if False else d[['pw','total_man','price_pct','weight']].corr()['pw'].round(3).to_dict())
dd = d.dropna(subset=['w420']).copy()
for cols in [['pw_c'], ['pw_c','price_pct'], ['male','price2539','w420','pw_c'], ['male','price_pct','weight_rel','pw_c']]:
    X, nm = design(dd, cols)
    r = logit(X, dd['win_jra'], nm)
    print(' + '.join(cols), '->', {n: round(z,2) for n, z in zip(r['変数'], r['z']) if not n.startswith('年度')})

sec('prior の作り方を変えても符号が残るか（縮小定数k・過去2年のみ・回収率prior）')
for c, lab in [('pw_c','勝上prior(k=6,全過去)'), ('pw2_c','勝上prior(直近2年)'), ('pr_c','回収prior')]:
    X, nm = design(d, [c])
    a = logit(X, d['win_jra'], nm).iloc[-1]; b = logit(X, d['ret1'], nm).iloc[-1]
    print(f'{lab:<22} win z={a["z"]:+.2f}  ret z={b["z"]:+.2f}')
for k in [2, 4, 6, 10, 20]:
    _, pk = prior(df, k)
    dk = df[(df['year']>=2021) & pk.notna()].copy(); dk['x'] = pk[dk.index]
    dk['x'] = dk['x'] - dk.groupby('year')['x'].transform('mean')
    X, nm = design(dk, ['x'])
    print(f'  k={k:<3} win z={logit(X, dk["win_jra"], nm).iloc[-1]["z"]:+.2f}')

sec('leave-one-year-out: 他の4年で厩舎率を作り、対象年で検証（AUC）')
for y in sorted(df['year'].unique()):
    tr = df[df['year'] != y]
    base = tr['win_jra'].mean()
    g = tr.groupby('trainer_key')['win_jra'].agg(['sum','size'])
    sc = df[df['year']==y]['trainer_key'].map(lambda t: (g.loc[t,'sum']+6*base)/(g.loc[t,'size']+6) if t in g.index else base)
    dy = df[df['year']==y]
    print(f'  {y}: n={len(dy)}  AUC={auc(dy["win_jra"].values, sc.values):.3f}  (勝上率{dy["win_jra"].mean():.2f})')
print('  ※前年度までのみ版のAUCは probe_trainer.py 参照')

sec('厩舎prior 上位/下位で、既存3基準を満たす馬だけを見る（実用形）')
dd['base3'] = dd['male'] + dd['price2539'] + dd['w420']
dd['ptop'] = (dd.groupby('year')['pw'].rank(pct=True) > 0.5).astype(int)
sel = dd[dd['base3'] == 3]
print('3基準クリア馬 n=%d' % len(sel))
print(sel.pivot_table(index='ptop', columns='year', values='win_jra', aggfunc=['mean','size']).round(2).to_string())
print(sel.groupby('ptop')[['win_jra','ret1','ret']].agg(['mean','size']).round(3).to_string())

sec('育成牧場 NF空港 vs NF早来 の交絡チェック')
ik = {}
for r in csv.DictReader(open(os.path.join(DS,'roster.csv'), encoding='utf-8-sig')):
    if (r.get('ikusei') or '').strip(): ik[f"{r['year']}#{r['no']}"] = r['ikusei'].strip()
for r in csv.DictReader(open(os.path.join(DS,'club_2023.csv'), encoding='utf-8-sig')):
    if (r.get('ikusei') or '').strip(): ik[f"2023#{r['no']}"] = r['ikusei'].strip()
df['ikusei'] = df['key'].map(lambda k: ik[k].replace('Ｎ','N').replace('Ｆ','F').replace(' ','') if k in ik else np.nan)
di = df[df['ikusei'].isin(['NF空港','NF早来'])].copy()
di['kuko'] = (di['ikusei']=='NF空港').astype(int)
di['price2539'] = di['total_man'].between(2500,3999).astype(int)
di['w420'] = (di['weight']>=420).astype(int)
print('空港/早来の中身の違い:')
print(di.groupby('ikusei')[['male','total_man','price_pct','weight','nf','month','dam_age']].mean().round(2).to_string())
print(di.groupby(['ikusei','sex']).size().unstack(fill_value=0).to_string())
dv = di.dropna(subset=['w420']).copy()
for cols in [['kuko'], ['kuko','male'], ['male','price2539','w420','kuko'], ['male','price_pct','weight_rel','kuko']]:
    X, nm = design(dv, cols)
    r = logit(X, dv['win_jra'], nm)
    print(' + '.join(cols), '->', {n: round(z,2) for n,z in zip(r['変数'], r['z']) if not n.startswith('年度')})
print('\n性別ごとに空港/早来を分けて見る')
print(di.pivot_table(index=['sex','ikusei'], values=['win_jra','ret1'], aggfunc=['mean','size']).round(3).to_string())
print('\n年度別（再掲、率と頭数）')
print(di.pivot_table(index='ikusei', columns='year', values='win_jra', aggfunc=['mean','size']).round(2).to_string())
print('\n2024年度・2026年度に育成牧場の列があるか:')
print(' roster_new_raw.csv 列:', open(os.path.join(DS,'roster_new_raw.csv'), encoding='utf-8').readline().strip())
print(' bosyu_2026.csv 列:', open(os.path.join(DATA,'bosyu_2026.csv'), encoding='utf-8-sig').readline().strip())

sec('2026年度94頭に厩舎priorを当てられるか（厩舎名の一致率）')
b26 = list(csv.DictReader(open(os.path.join(DATA,'bosyu_2026.csv'), encoding='utf-8-sig')))
known = set(df['trainer_key'])
hit = [ (r.get('厩舎') or '').replace(' ','') in known for r in b26 ]
print('2026年度 n=%d, 5年パネルに同名厩舎がある: %d頭 (%.0f%%)' % (len(b26), sum(hit), 100*np.mean(hit)))
miss = sorted({(r.get('厩舎') or '').replace(' ','') for r,h in zip(b26,hit) if not h})
print('未知の厩舎:', ' '.join(miss))
print('2026 入厩(関東/関西)の分布:', pd.Series([r.get('入厩') for r in b26]).value_counts().to_dict())

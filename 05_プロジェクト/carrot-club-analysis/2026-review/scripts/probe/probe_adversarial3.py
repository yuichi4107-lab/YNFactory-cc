# -*- coding: utf-8 -*-
"""敵対的検証 仕上げ：実運用形（単純加点チェックリスト）でのLOYOと選抜後の上乗せ。"""
import io, os, sys, csv
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, BASE)
from analyze5 import load, logit, design
from backtest import auc
DS = os.path.join(BASE, '..', 'datasets'); DATA = os.path.join(BASE, '..', '..', 'data')
pd.set_option('display.width', 220)
def sec(t): print('\n' + '=' * 78 + '\n■ ' + t + '\n' + '=' * 78)

df = load(central_only=True).dropna(subset=['win_jra']).copy().sort_values(['year', 'no']).reset_index(drop=True)
df['price2539'] = df['total_man'].between(2500, 3999).astype(float)
df['w420'] = (df['weight'] >= 420).astype(float)
df.loc[df['weight'].isna(), 'w420'] = np.nan
df['male'] = df['male'].astype(float)
pn, pwn, pw = [], [], []
for _, r in df.iterrows():
    past = df[(df['year'] < r['year']) & (df['trainer_key'] == r['trainer_key'])]
    prev = df[df['year'] < r['year']]
    base = prev['win_jra'].mean() if len(prev) else np.nan
    n = len(past); w = past['win_jra'].sum()
    pn.append(n); pwn.append(int(w))
    pw.append((w + 6 * base) / (n + 6) if n and not np.isnan(base) else np.nan)
df['pn'] = pn; df['pwn'] = pwn; df['pw'] = pw
df['pbin'] = (df['pwn'] >= 2).astype(float)
d = df[df['year'] >= 2021].dropna(subset=['w420']).copy()
d['base3'] = d['male'] + d['price2539'] + d['w420']

sec('G. 実運用形：単純加点チェックリストでのLOYO相当AUC（重み推定なし）')
rows = []
for tgt in ['win_jra', 'ret1']:
    for lab, sc in [('3基準のみ', d['base3']), ('3基準+二値prior', d['base3'] + d['pbin'])]:
        r = {'目的': tgt, 'スコア': lab, 'プール': round(auc(d[tgt], sc), 3)}
        for y in [2021, 2022, 2023, 2024]:
            m = d['year'] == y
            r[y] = round(auc(d.loc[m, tgt], sc[m]), 3)
        rows.append(r)
print(pd.DataFrame(rows).to_string(index=False))

sec('H. 選抜後の上乗せ：3基準を全部クリアした馬の中で二値priorは効くか')
sel = d[d['base3'] == 3]
print('3基準クリア n=%d' % len(sel))
print(sel.groupby('pbin')[['win_jra', 'ret1', 'ret']].agg(['mean', 'size']).round(3).to_string())
print(sel.pivot_table(index='pbin', columns='year', values='win_jra', aggfunc=['mean', 'size']).round(3).to_string())
print('\n各base3層での二値priorの差:')
print(d.pivot_table(index='base3', columns='pbin', values='win_jra', aggfunc=['mean', 'size']).round(3).to_string())

sec('I. 「本命は牡馬」との重複：二値priorは牡馬の中でも効くのか')
for lab, s in [('牡馬のみ', d[d['male'] == 1]), ('牝馬のみ', d[d['male'] == 0])]:
    a = s[s.pbin == 1]['win_jra']; b = s[s.pbin == 0]['win_jra']
    X, nm = design(s, ['pbin']); z = float(logit(X, s['win_jra'], nm).iloc[-1]['z'])
    print(f' {lab}: 該当{a.mean():.3f}(n={len(a)}) vs 非該当{b.mean():.3f}(n={len(b)})  z={z:+.2f}')

sec('J. 育成NF空港：単純加点形のLOYO相当AUC')
ik = {}
for r in csv.DictReader(open(os.path.join(DS, 'roster.csv'), encoding='utf-8-sig')):
    if (r.get('ikusei') or '').strip():
        ik[f"{r['year']}#{r['no']}"] = r['ikusei'].strip()
for r in csv.DictReader(open(os.path.join(DS, 'club_2023.csv'), encoding='utf-8-sig')):
    if (r.get('ikusei') or '').strip():
        ik[f"2023#{r['no']}"] = r['ikusei'].strip()
df['ikusei'] = df['key'].map(lambda k: ik[k].replace('Ｎ', 'N').replace('Ｆ', 'F').replace(' ', '') if k in ik else np.nan)
di = df[df['ikusei'].isin(['NF空港', 'NF早来'])].dropna(subset=['w420']).copy()
di['kuko'] = (di['ikusei'] == 'NF空港').astype(float)
di['base3'] = di['male'] + di['price2539'] + di['w420']
rows = []
for tgt in ['win_jra', 'ret1']:
    for lab, sc in [('3基準のみ', di['base3']), ('3基準+空港', di['base3'] + di['kuko'])]:
        r = {'目的': tgt, 'スコア': lab, 'プール': round(auc(di[tgt], sc), 3)}
        for y in [2020, 2021, 2022, 2023]:
            m = di['year'] == y
            r[y] = round(auc(di.loc[m, tgt], sc[m]), 3)
        rows.append(r)
print(pd.DataFrame(rows).to_string(index=False))
print('\n空港/早来の年度別 勝上率（再確認）')
print(di.pivot_table(index='ikusei', columns='year', values='win_jra', aggfunc=['mean', 'size']).round(3).to_string())
print('\n差分の推移(空港-早来, pt):')
p = di.pivot_table(index='ikusei', columns='year', values='win_jra', aggfunc='mean')
print({int(y): round(100 * (p.loc['NF空港', y] - p.loc['NF早来', y]), 1) for y in p.columns})

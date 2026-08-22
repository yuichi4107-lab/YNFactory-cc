# -*- coding: utf-8 -*-
"""追試: 人気変数の頑健性・交絡・年度安定性を詰める。"""
import io, os, sys
import numpy as np
import pandas as pd
from analyze5 import load, logit, design
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 220)
BASE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(BASE, '..', '..', 'data')
RANK_LEGACY_OUT = {"A":"A","B":"C","C":"A","D":"B","E":"C","F":"A","G":"B","H":"C","I":"D","J":"D","確定":"E"}
OUT_SCORE = {"A":5,"B":4,"C":3,"D":2,"E":1}
def out_rank(y,r):
    r=str(r)
    return RANK_LEGACY_OUT.get(r,None) if y<=2023 else (r[1] if len(r)==2 else None)

df = load(central_only=True); df['no_i']=pd.to_numeric(df['no'],errors='coerce')
rk = pd.read_csv(os.path.join(D,'dam_age_rank.csv'),encoding='utf-8-sig')
rk.columns=['year','no','dam','dam_born','dam_age_r','dam_season','t','rank','pool_filled']
rk['out']=[out_rank(y,r) for y,r in zip(rk['year'],rk['rank'])]
rk['out_s']=rk['out'].map(OUT_SCORE)
m=df.merge(rk[['year','no','rank','out','out_s','pool_filled']],left_on=['year','no_i'],right_on=['year','no'],how='left',suffixes=('','_r'))
m['dam_prio']=m['rank'].notna().astype(int)
s=m[m['year'].between(2021,2024)].dropna(subset=['win_jra']).copy()
p=s[s['dam_prio']==1].copy()
p['out_low']=p['out'].isin(['D','E']).astype(int)
p['out_hi']=p['out'].isin(['A','B','C']).astype(int)

def reg(d,cols,ys=('win_jra','ret1'),tag=''):
    for y in ys:
        dd=d.dropna(subset=list(cols)+[y])
        X,names=design(dd,list(cols)); r=logit(X,dd[y],names)
        print(f'  {tag}[{y}] n={len(dd)}')
        print(r[~r['変数'].astype(str).str.startswith('年度')].to_string(index=False))

print('='*78); print('■ A. 年度別に out_hi(A/B/C) vs out_low(D/E) を並べる'); print('='*78)

for y in [2021,2022,2023,2024]:
    d=p[p['year']==y]
    a=d[d['out_low']==0]; b=d[d['out_low']==1]
    print(f'  {y}: 人気上位(A/B/C) n={len(a)} 勝上{a["win_jra"].mean():.0%} 回収≥1 {a["ret1"].mean():.0%} | '
          f'下位(D/E) n={len(b)} 勝上{b["win_jra"].mean():.0%} 回収≥1 {b["ret1"].mean():.0%}')
print()
print('確定(=E,2021-23)を除いた場合:')
p2=p[~((p['year']<=2023)&(p['rank']=='確定'))].copy()
for y in [2021,2022,2023,2024]:
    d=p2[p2['year']==y]; a=d[d['out_low']==0]; b=d[d['out_low']==1]
    print(f'  {y}: 上位 n={len(a)} 勝上{a["win_jra"].mean():.0%} | 下位 n={len(b)} 勝上{b["win_jra"].mean():.0%}')
reg(p2,['out_s'],tag='確定除外 ')

print(); print('='*78); print('■ B. 交絡チェック: 人気は価格・性・馬体重の写しではないか'); print('='*78)
print('out ごとの平均:')
print(p.groupby('out')[['total_man','price_pct','weight','male','nf','dam_age']].mean().round(2).to_string())
print()
print('  既存3基準(牡・総額2500-3999・420kg以上)を入れたうえで out_s:')
p['price2539']=p['total_man'].between(2500,3999).astype(int)
p['w420']=(p['weight']>=420).astype(float); p.loc[p['weight'].isna(),'w420']=np.nan
reg(p,['out_s','male','price2539','w420'])
print('  out_s のみ vs 価格連続をコントロール:')
reg(p,['out_s','price_rel'])

print(); print('='*78); print('■ C. 母馬優先対象ダミーの交絡（ret1 z=+2.26 の中身）'); print('='*78)
print(s.groupby('dam_prio')[['total_man','price_pct','ret','male','nf','dam_age','weight']].mean().round(2).to_string())
print('年度別 回収≥1 %:')
print((s.pivot_table(index='dam_prio',columns='year',values='ret1',aggfunc=['mean','size'])*1).round(2).to_string())
print('  価格をコントロールした dam_prio:')
reg(s,['dam_prio','price_rel'])
print('  既存3基準込み:')
s['price2539']=s['total_man'].between(2500,3999).astype(int)
s['w420']=(s['weight']>=420).astype(float); s.loc[s['weight'].isna(),'w420']=np.nan
reg(s,['dam_prio','male','price2539','w420'])
print('  重賞馬数: 対象', int(s[s['dam_prio']==1]['graded'].sum()), '/',len(s[s['dam_prio']==1]),
      ' 非対象', int(s[s['dam_prio']==0]['graded'].sum()),'/',len(s[s['dam_prio']==0]))

print(); print('='*78); print('■ D. pool_filled（母馬の出資者の評価）を年度別に'); print('='*78)
for y in [2021,2022,2023,2024]:
    d=p[p['year']==y]; a=d[d['pool_filled']==1]; b=d[d['pool_filled']==0]
    print(f'  {y}: 埋 n={len(a)} 勝上{a["win_jra"].mean():.0%} 回収≥1 {a["ret1"].mean():.0%} | '
          f'余 n={len(b)} 勝上{b["win_jra"].mean():.0%} 回収≥1 {b["ret1"].mean():.0%}')
print('  母馬年齢をコントロール（pool_filledは母馬年齢の関数でもある）:')
reg(p,['pool_filled','dam_age'])
print('  out_s と同時投入:')
reg(p,['pool_filled','out_s'])

print(); print('='*78); print('■ E. 多重検定の目安 / AUC'); print('='*78)
from backtest import auc
for y in ['win_jra','ret1']:
    d=p.dropna(subset=['out_s',y])
    print(f'  out_s 単独 AUC({y}) = {auc(d[y].values, d["out_s"].values):.3f}  n={len(d)}')
    print(f'  価格pct    AUC({y}) = {auc(d[y].values, d["price_pct"].values):.3f}')

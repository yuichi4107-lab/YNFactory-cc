# -*- coding: utf-8 -*-
"""馬体切り口 その4：体高152cm閾値の安定性と、体重との住み分け。"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import numpy as np, pandas as pd
from analyze5 import load, logit, design
from backtest import auc
pd.set_option('display.width', 250)

df = load(central_only=True).dropna(subset=['win_jra']).copy()
df = df.dropna(subset=['weight','height','girth','cannon']).copy()
df['price25_40'] = df['total_man'].between(2500,3999).astype(int)
df['w420'] = (df['weight']>=420).astype(int)
df['h152'] = (df['height']>=152).astype(int)

def run(cols, target, d=None):
    d = df if d is None else d
    d = d.dropna(subset=cols+[target])
    X, names = design(d, cols)
    r = logit(X, d[target], names)
    return r[~r['変数'].astype(str).str.startswith('年度')].assign(n=len(d)).round(3)

print('=== 体高152cm：年度別 ===')
print(df.groupby('year')['h152'].agg(['sum','size']).to_string())
print((df.pivot_table(index='h152', columns='year', values='win_jra', aggfunc='mean')*100).round(0).to_string())
print(df.pivot_table(index='h152', columns='year', values='win_jra', aggfunc='size').to_string())
print((df.pivot_table(index='h152', columns='year', values='ret1', aggfunc='mean')*100).round(0).to_string())

print('\n=== 体高152 と 体重420 のクロス ===')
ct = df.groupby(['h152','w420']).agg(n=('win_jra','size'), 勝上=('win_jra','mean'), 回収1=('ret1','mean'), 回収中央=('ret','median'))
print(ct.round(3).to_string())

print('\n=== 4基準（牡・価格・420kg・152cm）同時 ===')
for t_ in ['win_jra','ret1']:
    print(f'-- {t_}'); print(run(['male','price25_40','w420','h152'], t_).to_string(index=False))

print('\n=== 体高を連続で（w420統制）===')
df['h_z'] = df.groupby('year')['height'].transform(lambda s:(s-s.mean())/s.std())
for t_ in ['win_jra','ret1']:
    print(f'-- {t_}'); print(run(['male','price25_40','w420','h_z'], t_).to_string(index=False))

print('\n=== 年度別に h152 単独ロジット（符号安定性）===')
for t_ in ['win_jra','ret1']:
    rows=[]
    for y in sorted(df['year'].unique()):
        d=df[df['year']==y]
        if d['h152'].nunique()<2: continue
        X=np.column_stack([np.ones(len(d)), d['h152']])
        r=logit(X,d[t_],['切片','h152'])
        rows.append({'年度':y,'n低':int((d.h152==0).sum()),'低群率':round(d[d.h152==0][t_].mean(),3),
                     '高群率':round(d[d.h152==1][t_].mean(),3),'z':round(r.iloc[1]['z'],2)})
    print(f'-- {t_}'); print(pd.DataFrame(rows).to_string(index=False))

print('\n=== 体重420 vs 体高152 どちらが基準として強いか（AUC, 3基準の3つ目を差し替え）===')
for name, col in [('体重420', 'w420'), ('体高152','h152'), ('両方AND', None)]:
    d=df.copy()
    third = d[col] if col else ((d['w420']==1)&(d['h152']==1)).astype(int)
    d['sc']=d['male']+d['price25_40']+third
    per=d[d['sc']==3]
    print(f'{name}: AUC(win)={auc(d["win_jra"].values,d["sc"].values):.4f} AUC(ret)={auc(d["ret1"].values,d["sc"].values):.4f} '
          f'| 3点{len(per)}頭 勝上{per["win_jra"].mean():.3f} 回収1{per["ret1"].mean():.3f} 回収中央{per["ret"].median():.2f}')

print('\n=== 3点該当を h152 でさらに絞ると？ ===')
d=df.copy(); d['sc']=d['male']+d['price25_40']+d['w420']
per=d[d['sc']==3]
print(per.groupby('h152').agg(n=('win_jra','size'),勝上=('win_jra','mean'),回収1=('ret1','mean'),回収中央=('ret','median')).round(3).to_string())
print((per.pivot_table(index='h152',columns='year',values='win_jra',aggfunc='mean')*100).round(0).to_string())
print(per.pivot_table(index='h152',columns='year',values='win_jra',aggfunc='size').to_string())

print('\n=== 参考：2026年度94頭に測尺があるか ===')
import os
p = os.path.join('..','..','data','bosyu_2026.csv')
if os.path.exists(p):
    b = pd.read_csv(p, encoding='utf-8-sig')
    print(b.columns.tolist())
    for c in ['weight','height','girth','cannon','馬体重','体高','胸囲','管囲']:
        if c in b.columns: print(c, b[c].notna().sum(), '/', len(b))

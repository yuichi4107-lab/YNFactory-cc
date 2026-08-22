# -*- coding: utf-8 -*-
"""馬体切り口 その5：体高閾値の頑健性チェック（LOYO・細かい刻み・性別別）。"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import numpy as np, pandas as pd
from analyze5 import load, logit, design
from backtest import auc
pd.set_option('display.width', 250)
df = load(central_only=True).dropna(subset=['win_jra']).copy()
df = df.dropna(subset=['weight','height','girth','cannon']).copy()
df['price25_40']=df['total_man'].between(2500,3999).astype(int)
df['w420']=(df['weight']>=420).astype(int)

def run(cols,target,d):
    d=d.dropna(subset=cols+[target]); X,names=design(d,cols)
    r=logit(X,d[target],names); return r[~r['変数'].astype(str).str.startswith('年度')].round(3)

print('=== 体高閾値の細かいスキャン（既存3基準を統制）===')
for thr in [149,150,151,152,153,154,155]:
    d=df.copy(); d['f']=(d['height']>=thr).astype(int)
    r1=run(['male','price25_40','w420','f'],'win_jra',d).iloc[3]
    r2=run(['male','price25_40','w420','f'],'ret1',d).iloc[3]
    print(f'体高>={thr}: 非該当{int((d.f==0).sum())}頭 勝上{d[d.f==0]["win_jra"].mean():.3f} vs {d[d.f==1]["win_jra"].mean():.3f} '
          f'z(win)={r1["z"]:+.2f} z(ret)={r2["z"]:+.2f}')

print('\n=== 体高152 の性別別 ===')
df['h152']=(df['height']>=152).astype(int)
for s in ['牡','メス']:
    d=df[df['sex']==s]
    print(f'{s}: 低{int((d.h152==0).sum())}頭 勝上{d[d.h152==0]["win_jra"].mean():.3f} vs {d[d.h152==1]["win_jra"].mean():.3f} '
          f'| 回収1 {d[d.h152==0]["ret1"].mean():.3f} vs {d[d.h152==1]["ret1"].mean():.3f} '
          f'z(win)={run(["h152"],"win_jra",d).iloc[0]["z"]:+.2f}')

print('\n=== Leave-one-year-out：4年で係数を作り残り1年で当てる ===')
def loyo(cols):
    aw, ar = [], []
    for y in sorted(df['year'].unique()):
        tr, te = df[df['year']!=y], df[df['year']==y]
        sc_te = te[cols].sum(axis=1)
        aw.append(auc(te['win_jra'].values, sc_te.values))
        ar.append(auc(te['ret1'].values, sc_te.values))
    return np.mean(aw), np.mean(ar), aw, ar
for label, cols in [('現行3基準',['male','price25_40','w420']),
                    ('+体高152(4点)',['male','price25_40','w420','h152']),
                    ('体重420を 420AND152 に置換',None)]:
    if cols is None:
        df['wh']=((df.w420==1)&(df.h152==1)).astype(int); cols=['male','price25_40','wh']
    aw,ar,lw,lr = loyo(cols)
    print(f'{label}: 平均AUC(win)={aw:.4f} (年度別 {[round(x,3) for x in lw]})  平均AUC(ret)={ar:.4f} ({[round(x,3) for x in lr]})')

print('\n=== 「馬体重420以上 かつ 体高152以上」を第3基準にした場合の実運用 ===')
df['wh']=((df.w420==1)&(df.h152==1)).astype(int)
for name,third in [('現行 w420','w420'),('w420 AND h152','wh')]:
    d=df.copy(); d['sc']=d['male']+d['price25_40']+d[third]
    for k in [3,2]:
        g=d[d['sc']==k]
        print(f'{name} {k}点: {len(g)}頭 勝上{g["win_jra"].mean():.3f} 回収1{g["ret1"].mean():.3f} 回収中央{g["ret"].median():.2f}')
    g=d[d['sc']==3]
    print('   3点の年度別勝上', (g.groupby('year')['win_jra'].mean()*100).round(0).to_dict(), '頭数', g.groupby('year').size().to_dict())
    print('   3点の年度別回収1', (g.groupby('year')['ret1'].mean()*100).round(0).to_dict())

print('\n=== 体高が落とす馬（w420は満たすが h152 を満たさない）===')
d=df[(df.w420==1)&(df.h152==0)]
print(f'n={len(d)} 勝上{d["win_jra"].mean():.3f} 回収1{d["ret1"].mean():.3f} 平均体重{d["weight"].mean():.1f} 平均体高{d["height"].mean():.1f}')
print((d.groupby('year')['win_jra'].agg(['size','mean'])).round(2).to_string())

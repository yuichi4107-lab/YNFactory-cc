# -*- coding: utf-8 -*-
"""敵対的検証2：LOYO（係数を4年で推定して残り1年を当てる）と多重検定。"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import numpy as np, pandas as pd
from analyze5 import load, logit
from backtest import auc
pd.set_option('display.width', 250)

df = load(central_only=True).dropna(subset=['win_jra']).copy()
df = df.dropna(subset=['weight','height','girth','cannon']).copy()
df['price25_40']=df['total_man'].between(2500,3999).astype(int)
df['w420']=(df['weight']>=420).astype(int)
df['fem']=(df['sex']!='牡').astype(int)
df['h152']=(df['height']>=152).astype(int)
df['femsmall']=((df['fem']==1)&(df['height']<152)).astype(int)
df['w430']=(df['weight']>=430).astype(int)
df['wh']=((df.w420==1)&(df.h152==1)).astype(int)
BASE=['male','price25_40','w420']
YEARS=sorted(df['year'].unique())

def loyo_fit(cols, target):
    """4年で切片+係数を推定し、残り1年に適用してAUC。年度ダミーは切片1本に置換。"""
    out={}
    for y in YEARS:
        tr=df[df['year']!=y].dropna(subset=cols+[target])
        te=df[df['year']==y].dropna(subset=cols+[target])
        Xtr=np.column_stack([np.ones(len(tr))]+[tr[c].astype(float).values for c in cols])
        r=logit(Xtr, tr[target], ['const']+cols)
        b=r['係数'].values
        Xte=np.column_stack([np.ones(len(te))]+[te[c].astype(float).values for c in cols])
        out[y]=auc(te[target].values, (Xte@b))
    return out

def loyo_sum(cols,target):
    return {y: auc(df[df.year==y][target].values, df[df.year==y][cols].sum(axis=1).values) for y in YEARS}

print('=== LOYO：係数を4年で学習して残り1年に適用 ===')
for target in ['win_jra','ret1']:
    print(f'-- {target}')
    base=loyo_fit(BASE,target); bm=np.mean(list(base.values()))
    print(f'  既存3基準       平均{bm:.4f}  {[round(base[y],3) for y in YEARS]}')
    for lab,cols in [('+femsmall',BASE+['femsmall']),('+h152',BASE+['h152']),
                     ('w420→wh(420&152)',['male','price25_40','wh']),
                     ('w420→w430(参考)',['male','price25_40','w430'])]:
        a=loyo_fit(cols,target); m=np.mean(list(a.values()))
        print(f'  {lab:18s} 平均{m:.4f} ({m-bm:+.4f})  {[round(a[y],3) for y in YEARS]}')

print('\n=== LOYO（単純合計スコア版：報告書と同じ計算）===')
for target in ['win_jra','ret1']:
    base=loyo_sum(BASE,target); bm=np.mean(list(base.values()))
    print(f'-- {target} 既存3基準 平均{bm:.4f} {[round(base[y],3) for y in YEARS]}')
    for lab,cols in [('+femsmall(減点)',None),('+h152',BASE+['h152'])]:
        if cols is None:
            df['nfs']=1-df['femsmall']; cols=BASE+['nfs']
        a=loyo_sum(cols,target); m=np.mean(list(a.values()))
        print(f'   {lab:14s} 平均{m:.4f} ({m-bm:+.4f}) {[round(a[y],3) for y in YEARS]}')

print('\n=== 閾値・目的変数をまたいだ多重検定の実態（既存3基準統制、全数スキャン）===')
from analyze5 import design
def z_of(d,cols,t,name):
    d=d.dropna(subset=cols+[t]); X,names=design(d,cols); r=logit(X,d[t],names)
    return float(r[r['変数']==name]['z'].iloc[0])
zs=[]
for thr in np.arange(146,161,1.0):
    d=df.copy(); d['f']=(d['height']>=thr).astype(int)
    if d['f'].nunique()<2: continue
    for t in ['win_jra','ret1']:
        z=z_of(d,BASE+['f'],t,'f'); zs.append((f'h>={thr:.0f}',t,z))
for thr in np.arange(162,190,2.0):
    d=df.copy(); d['f']=(d['girth']>=thr).astype(int)
    if d['f'].nunique()<2: continue
    for t in ['win_jra','ret1']:
        zs.append((f'胸囲>={thr:.0f}',t,z_of(d,BASE+['f'],t,'f')))
for thr in np.arange(19.0,22.1,0.2):
    d=df.copy(); d['f']=(d['cannon']>=thr).astype(int)
    if d['f'].nunique()<2: continue
    for t in ['win_jra','ret1']:
        zs.append((f'管囲>={thr:.1f}',t,z_of(d,BASE+['f'],t,'f')))
zs=pd.DataFrame(zs,columns=['変数','目的','z'])
print('試行数',len(zs),' |z|>2の件数',int((zs['z'].abs()>2).sum()),' |z|>2.5',int((zs['z'].abs()>2.5).sum()))
print(zs.reindex(zs['z'].abs().sort_values(ascending=False).index).head(12).round(2).to_string(index=False))

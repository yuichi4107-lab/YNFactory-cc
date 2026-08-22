# -*- coding: utf-8 -*-
"""敵対的検証：馬体（測尺）候補を潰しにかかる。"""
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
df['fem'] = (df['sex']!='牡').astype(int)
df['h152'] = (df['height']>=152).astype(int)
df['femsmall'] = ((df['fem']==1)&(df['height']<152)).astype(int)
BASE = ['male','price25_40','w420']
print('n=',len(df))

def fit(d, cols, target):
    d = d.dropna(subset=cols+[target])
    X,names = design(d, cols)
    r = logit(X, d[target], names)
    return r[~r['変数'].astype(str).str.startswith('年度')]

print('\n=== 1. 報告数字の再現 ===')
for lab,flag in [('牝×体高<152','femsmall'),('体高>=152','h152')]:
    a=df[df[flag]==1]; b=df[df[flag]==0]
    print(f'{lab}: 該当{len(a)}頭 勝上{a["win_jra"].mean():.3f} 回収1 {a["ret1"].mean():.3f} 回収中央{a["ret"].median():.2f}'
          f' | 非該当{len(b)}頭 勝上{b["win_jra"].mean():.3f} 回収1 {b["ret1"].mean():.3f} 回収中央{b["ret"].median():.2f}')
    for t in ['win_jra','ret1']:
        r=fit(df,BASE+[flag],t)
        print('   ',t, r.set_index('変数')[['係数','z']].round(3).to_dict('index'))

print('\n=== 2. 牝×小柄：牝の中だけで見る（＝牡馬基準に吸収されていないか）===')
fe = df[df['fem']==1].copy()
print('牝のみ n=',len(fe))
for t in ['win_jra','ret1']:
    r=fit(fe,['price25_40','w420','femsmall'],t)
    print(t, r.set_index('変数')[['係数','z']].round(3).to_dict('index'))
print('牝の中の体高<152:', int(fe['femsmall'].sum()),'頭  勝上',round(fe[fe.femsmall==1]['win_jra'].mean(),3),
      '/ 牝で152以上',int((fe.femsmall==0).sum()),'頭 勝上',round(fe[fe.femsmall==0]['win_jra'].mean(),3))
print('ret1 件数: 小柄牝',int(fe[fe.femsmall==1]['ret1'].sum()),'/ 大柄牝',int(fe[fe.femsmall==0]['ret1'].sum()))

print('\n=== 3. 牝×小柄フラグは運用上意味があるか（3点満点スコア下で）===')
df['sc3']=df[BASE].sum(axis=1)
print('スコア分布', df['sc3'].value_counts().sort_index().to_dict())
print('femsmall該当馬のsc3分布', df[df.femsmall==1]['sc3'].value_counts().sort_index().to_dict())
print('→ femsmallは全員 male=0 なので sc3<=2。3点しきい値では既に落ちている')

print('\n=== 4. 牝の中での体高＝連続 vs 閾値、閾値スキャン ===')
fe['hz']=fe.groupby('year')['height'].transform(lambda s:(s-s.mean())/s.std())
r=fit(fe,['price25_40','w420','hz'],'win_jra'); print('牝 体高連続z(win)', r.set_index('変数').loc['hz',['係数','z']].round(3).to_dict())
r=fit(fe,['price25_40','w420','hz'],'ret1'); print('牝 体高連続z(ret)', r.set_index('変数').loc['hz',['係数','z']].round(3).to_dict())
for thr in [148,149,150,151,152,153,154,155,156]:
    fe['f']=(fe['height']<thr).astype(int)
    if fe['f'].nunique()<2: continue
    zw=fit(fe,['price25_40','w420','f'],'win_jra').set_index('変数').loc['f','z']
    zr=fit(fe,['price25_40','w420','f'],'ret1').set_index('変数').loc['f','z']
    print(f'  牝 体高<{thr}: n={int(fe.f.sum()):3d} z(win)={zw:+.2f} z(ret)={zr:+.2f}')

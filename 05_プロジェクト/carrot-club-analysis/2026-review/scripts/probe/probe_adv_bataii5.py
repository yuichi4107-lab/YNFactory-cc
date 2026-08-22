# -*- coding: utf-8 -*-
"""敵対的検証5：femsmall の並べ替え検定（性別×閾値の探索込み）と入れ子LOYO。"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import numpy as np, pandas as pd
from analyze5 import load, logit, design
from backtest import auc
rng=np.random.default_rng(7)
df = load(central_only=True).dropna(subset=['win_jra']).copy()
df = df.dropna(subset=['weight','height','girth','cannon']).copy()
df['price25_40']=df['total_man'].between(2500,3999).astype(int)
df['w420']=(df['weight']>=420).astype(int)
df['fem']=(df['sex']!='牡').astype(int)
BASE=['male','price25_40','w420']
YEARS=sorted(df['year'].unique())
THR=np.arange(147,160,1.0)
GRP=[('全体',None),('牝',1),('牡',0)]

def scan(d,target):
    best=0.0; arg=None
    for gl,g in GRP:
        for thr in THR:
            d2=d.copy()
            base = (d2['height']<thr)
            if g is not None: base = base & (d2['fem']==g)
            d2['f']=base.astype(int)
            if d2['f'].sum()<10 or d2['f'].nunique()<2: continue
            s=d2.dropna(subset=BASE+['f',target]); X,names=design(s,BASE+['f'])
            z=float(logit(X,s[target],names).query('変数=="f"')['z'].iloc[0])
            if abs(z)>best: best,arg=abs(z),(gl,thr)
    return best,arg

for target in ['win_jra','ret1']:
    obs,arg=scan(df,target)
    null=[]
    for i in range(200):
        d=df.copy()
        d['height']=d.groupby('year')['height'].transform(lambda s: rng.permutation(s.values))
        null.append(scan(d,target)[0])
    null=np.array(null)
    print(f'{target}: 観測max|z|={obs:.2f} {arg}  帰無 中央値{np.median(null):.2f} 95%点{np.quantile(null,.95):.2f} p={np.mean(null>=obs):.3f}')

print('\n=== 入れ子LOYO：性別×閾値をその年を見ずに選ぶ ===')
for target in ['win_jra','ret1']:
    rows=[]
    for y in YEARS:
        tr,te=df[df.year!=y],df[df.year==y]
        b_,arg=scan(tr,target)
        gl,thr=arg
        def mk(d):
            v=(d['height']<thr)
            if gl=='牝': v=v&(d['fem']==1)
            elif gl=='牡': v=v&(d['fem']==0)
            return v.astype(float).values
        cols=BASE
        Xtr=np.column_stack([np.ones(len(tr))]+[tr[c].astype(float) for c in cols])
        bb=logit(Xtr,tr[target],['c']+cols)['係数'].values
        Xte=np.column_stack([np.ones(len(te))]+[te[c].astype(float) for c in cols])
        ab=auc(te[target].values,Xte@bb)
        Xtr2=np.column_stack([Xtr,mk(tr)]); Xte2=np.column_stack([Xte,mk(te)])
        b2=logit(Xtr2,tr[target],['c']+cols+['f'])['係数'].values
        a2=auc(te[target].values,Xte2@b2)
        rows.append((y,gl,thr,round(b_,2),round(ab,4),round(a2,4),round(a2-ab,4)))
    r=pd.DataFrame(rows,columns=['年','選ばれた群','閾値','学習内|z|','AUC基準','AUC+候補','差'])
    print(f'-- {target}');print(r.to_string(index=False));print('   平均差',round(r['差'].mean(),4),' 改善',int((r['差']>0).sum()),'/5')

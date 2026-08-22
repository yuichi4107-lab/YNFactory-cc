# -*- coding: utf-8 -*-
"""敵対的検証3：閾値探索込みの並べ替え検定と、閾値を年外で選ぶ入れ子LOYO。"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import numpy as np, pandas as pd
from analyze5 import load, logit, design
from backtest import auc
rng=np.random.default_rng(20260822)

df = load(central_only=True).dropna(subset=['win_jra']).copy()
df = df.dropna(subset=['weight','height','girth','cannon']).copy()
df['price25_40']=df['total_man'].between(2500,3999).astype(int)
df['w420']=(df['weight']>=420).astype(int)
df['fem']=(df['sex']!='牡').astype(int)
BASE=['male','price25_40','w420']
YEARS=sorted(df['year'].unique())
HTHR=np.arange(147,160,1.0)

def zmax(d,target,ycol='win_jra'):
    """既存3基準統制下で体高閾値をスキャンした最大|z|"""
    best=0.0; bt=None
    for thr in HTHR:
        d2=d.copy(); d2['f']=(d2['height']>=thr).astype(int)
        if d2['f'].nunique()<2: continue
        s=d2.dropna(subset=BASE+['f',target])
        X,names=design(s,BASE+['f']); r=logit(X,s[target],names)
        z=float(r[r['変数']=='f']['z'].iloc[0])
        if abs(z)>best: best,bt=abs(z),thr
    return best,bt

print('=== 並べ替え検定：年度内でhightを入れ替え、閾値スキャンの最大|z|の分布 ===')
for target in ['win_jra','ret1']:
    obs,ot=zmax(df,target)
    null=[]
    for i in range(300):
        d=df.copy()
        d['height']=d.groupby('year')['height'].transform(lambda s: rng.permutation(s.values))
        null.append(zmax(d,target)[0])
    null=np.array(null)
    print(f'{target}: 観測max|z|={obs:.2f}(閾値{ot:.0f})  帰無分布 中央値{np.median(null):.2f} 95%点{np.quantile(null,0.95):.2f} '
          f'→ p={np.mean(null>=obs):.3f}')

print('\n=== 入れ子LOYO：閾値を「その年を見ずに」選ぶ ===')
for target in ['win_jra','ret1']:
    rows=[]
    for y in YEARS:
        tr=df[df.year!=y]; te=df[df.year==y]
        best=None;bz=0
        for thr in HTHR:
            d=tr.copy(); d['f']=(d['height']>=thr).astype(int)
            if d['f'].nunique()<2: continue
            s=d.dropna(subset=BASE+['f',target]); X,names=design(s,BASE+['f']); r=logit(X,s[target],names)
            z=float(r[r['変数']=='f']['z'].iloc[0])
            if z>bz: bz,best=z,thr
        tr2=tr.copy(); tr2['f']=(tr2['height']>=best).astype(int)
        te2=te.copy(); te2['f']=(te2['height']>=best).astype(int)
        cols=BASE+['f']
        Xtr=np.column_stack([np.ones(len(tr2))]+[tr2[c].astype(float) for c in cols])
        b=logit(Xtr,tr2[target],['c']+cols)['係数'].values
        Xte=np.column_stack([np.ones(len(te2))]+[te2[c].astype(float) for c in cols])
        a=auc(te2[target].values,Xte@b)
        Xtrb=np.column_stack([np.ones(len(tr))]+[tr[c].astype(float) for c in BASE])
        bb=logit(Xtrb,tr[target],['c']+BASE)['係数'].values
        Xteb=np.column_stack([np.ones(len(te))]+[te[c].astype(float) for c in BASE])
        ab=auc(te[target].values,Xteb@bb)
        rows.append((y,best,bz,ab,a,a-ab))
    r=pd.DataFrame(rows,columns=['年','選ばれた体高閾値','学習内z','AUC基準','AUC+体高','差'])
    print(f'-- {target}'); print(r.round(4).to_string(index=False))
    print(f'   平均差 {r["差"].mean():+.4f}  改善した年 {int((r["差"]>0).sum())}/5')

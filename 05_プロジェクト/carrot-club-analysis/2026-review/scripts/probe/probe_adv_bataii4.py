# -*- coding: utf-8 -*-
"""敵対的検証4：femsmall/h152 の標本の薄さ・運用上の意味・代替仮説。"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import numpy as np, pandas as pd
from scipy import stats
from analyze5 import load, logit, design
pd.set_option('display.width',250)
df = load(central_only=True).dropna(subset=['win_jra']).copy()
df = df.dropna(subset=['weight','height','girth','cannon']).copy()
df['price25_40']=df['total_man'].between(2500,3999).astype(int)
df['w420']=(df['weight']>=420).astype(int)
df['fem']=(df['sex']!='牡').astype(int)
df['h152']=(df['height']>=152).astype(int)
df['femsmall']=((df['fem']==1)&(df['height']<152)).astype(int)
BASE=['male','price25_40','w420']

print('=== femsmall：牝の中での年度別（正しい比較相手は牝、牡ではない）===')
fe=df[df.fem==1]
t=fe.groupby(['year','femsmall']).agg(n=('win_jra','size'),win=('win_jra','mean'),ret1=('ret1','mean'),ret1n=('ret1','sum'))
print(t.round(3).to_string())
print('\n牝全体 ret1件数', int(fe['ret1'].sum()),'/',len(fe))
a=fe[fe.femsmall==1]; b=fe[fe.femsmall==0]
print('Fisher(ret1, 牝内):', stats.fisher_exact([[int(a.ret1.sum()),len(a)-int(a.ret1.sum())],
      [int(b.ret1.sum()),len(b)-int(b.ret1.sum())]])[1].round(4))
print('Fisher(win_jra, 牝内):', stats.fisher_exact([[int(a.win_jra.sum()),len(a)-int(a.win_jra.sum())],
      [int(b.win_jra.sum()),len(b)-int(b.win_jra.sum())]])[1].round(4))
print('年度別に符号が一貫しているか（牝内 win_jra 差）:')
for y in sorted(fe.year.unique()):
    d=fe[fe.year==y]; aa=d[d.femsmall==1]; bb=d[d.femsmall==0]
    print(f'  {y}: 小柄{len(aa)}頭 {aa.win_jra.mean():.2f} vs 他{len(bb)}頭 {bb.win_jra.mean():.2f} 差{aa.win_jra.mean()-bb.win_jra.mean():+.2f}')

print('\n=== 運用：スコア閾値ごとに femsmall が何頭落とすか ===')
df['sc']=df[BASE].sum(axis=1)
for cut in [3,2]:
    sel=df[df.sc>=cut]
    print(f'  {cut}点以上で選ぶ: {len(sel)}頭中 femsmall該当 {int(sel.femsmall.sum())}頭 '
          f'({sel.femsmall.mean()*100:.1f}%) → 除外後 勝上 {sel[sel.femsmall==0].win_jra.mean():.3f} '
          f'(除外前 {sel.win_jra.mean():.3f}) 回収1 {sel[sel.femsmall==0].ret1.mean():.3f} (前 {sel.ret1.mean():.3f})')

print('\n=== 代替仮説：体高ではなく「牝×軽い」ではないか ===')
for lab,flag in [('牝×体高<152','femsmall'),
                 ('牝×体重<430',((df.fem==1)&(df.weight<430)).astype(int)),
                 ('牝×体重<440',((df.fem==1)&(df.weight<440)).astype(int)),
                 ('牝×胸囲<178',((df.fem==1)&(df.girth<178)).astype(int)),
                 ('牝×管囲<20.4',((df.fem==1)&(df.cannon<20.4)).astype(int))]:
    d=df.copy(); d['f']=d[flag] if isinstance(flag,str) else flag
    out=[]
    for t2 in ['win_jra','ret1']:
        s=d.dropna(subset=BASE+['f',t2]); X,names=design(s,BASE+['f']); r=logit(X,s[t2],names)
        out.append(float(r[r['変数']=='f']['z'].iloc[0]))
    print(f'  {lab:14s} n={int(d.f.sum()):3d} z(win)={out[0]:+.2f} z(ret)={out[1]:+.2f}')

print('\n=== h152：年度別単独z と、w420通過者の中だけで見た効果 ===')
for y in sorted(df.year.unique()):
    d=df[df.year==y]
    a=d[d.h152==1];b=d[d.h152==0]
    print(f'  {y}: 152+ {len(a)}頭{a.win_jra.mean():.2f}/ret1 {a.ret1.mean():.2f}  vs 152- {len(b)}頭{b.win_jra.mean():.2f}/ret1 {b.ret1.mean():.2f}')
d=df[df.w420==1]
print(f'\nw420通過{len(d)}頭の中: h152+ {int((d.h152==1).sum())}頭 勝上{d[d.h152==1].win_jra.mean():.3f} ret1 {d[d.h152==1].ret1.mean():.3f}'
      f' | h152- {int((d.h152==0).sum())}頭 勝上{d[d.h152==0].win_jra.mean():.3f} ret1 {d[d.h152==0].ret1.mean():.3f}')
s=d.dropna(subset=['price25_40','male','h152']);X,names=design(s,['male','price25_40','h152']);r=logit(X,s['win_jra'],names)
print('w420通過者内 h152 z(win)=',round(float(r[r['変数']=='h152']['z'].iloc[0]),2))
r=logit(X,s['ret1'],names);print('w420通過者内 h152 z(ret)=',round(float(r[r['変数']=='h152']['z'].iloc[0]),2))
print('\n=== h152 の性別分解（牡だけで残るか）===')
for lab,d2 in [('牡',df[df.fem==0]),('牝',df[df.fem==1])]:
    s=d2.dropna(subset=['price25_40','w420','h152'])
    X,names=design(s,['price25_40','w420','h152'])
    zw=float(logit(X,s['win_jra'],names).query('変数=="h152"')['z'].iloc[0])
    zr=float(logit(X,s['ret1'],names).query('変数=="h152"')['z'].iloc[0])
    print(f'  {lab} n={len(s)} 152未満{int((s.h152==0).sum())}頭 z(win)={zw:+.2f} z(ret)={zr:+.2f}')

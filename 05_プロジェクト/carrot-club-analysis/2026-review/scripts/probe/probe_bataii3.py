# -*- coding: utf-8 -*-
"""馬体切り口 その3：性別内偏差、牝の閾値、体高、既存3基準との増分検証。"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import numpy as np, pandas as pd
from analyze5 import load, logit, design
from backtest import auc
pd.set_option('display.width', 250)

df = load(central_only=True).dropna(subset=['win_jra']).copy()
df = df.dropna(subset=['weight','height','girth','cannon']).copy()
df['price25_40'] = df['total_man'].between(2500, 3999).astype(int)
df['w420'] = (df['weight'] >= 420).astype(int)
# 性別×年度内での標準化（性差を抜いた「同性の中で大きいか」）
for c in ['weight','height','girth','cannon']:
    df[c+'_sz'] = df.groupby(['year','sex'])[c].transform(lambda s: (s-s.mean())/s.std())
    df[c+'_z']  = df.groupby('year')[c].transform(lambda s: (s-s.mean())/s.std())

def run(cols, target, d=None):
    d = df if d is None else d
    d = d.dropna(subset=cols+[target])
    X, names = design(d, cols)
    r = logit(X, d[target], names)
    return r[~r['変数'].astype(str).str.startswith('年度')].assign(n=len(d)).round(3)

print('=== A) 性別×年度内偏差（性差を抜いた体格）===')
for t_ in ['win_jra','ret1']:
    rows=[run([c+'_sz'], t_).iloc[0] for c in ['weight','height','girth','cannon']]
    print(f'-- {t_}'); print(pd.DataFrame(rows)[['変数','係数','z','n']].to_string(index=False))
print('-- 既存3基準に足す（性別内体重偏差）')
for t_ in ['win_jra','ret1']:
    print(f'  {t_}'); print(run(['male','price25_40','w420','weight_sz'], t_).to_string(index=False))

print('\n=== B) 性別ごとの体重帯 ===')
df['_wb'] = pd.cut(df['weight'], [0,409,419,429,439,459,479,999])
for s in ['牡','メス']:
    d = df[df['sex']==s]
    t = d.groupby('_wb', observed=True).agg(n=('win_jra','size'), 勝上=('win_jra','mean'),
            回収1=('ret1','mean'), 回収中央=('ret','median'))
    t['勝上']*=100; t['回収1']*=100
    print(f'-- {s} (全体勝上{d["win_jra"].mean()*100:.0f}%)'); print(t.round(1).to_string())

print('\n=== C) 牝の 420-439 帯は 440+ と比べて劣るか（年度別）===')
d = df[(df['sex']!='牡') & (df['weight']>=420)].copy()
d['g'] = np.where(d['weight']>=440, '440+', '420-439')
print(d.groupby(['g']).agg(n=('win_jra','size'), 勝上=('win_jra','mean'), 回収1=('ret1','mean')).round(3).to_string())
print((d.pivot_table(index='g', columns='year', values='win_jra', aggfunc='mean')*100).round(0).to_string())
print(d.pivot_table(index='g', columns='year', values='win_jra', aggfunc='size').to_string())
d['flag440'] = (d['weight']>=440).astype(int)
print(run(['flag440'],'win_jra',d).to_string(index=False)); print(run(['flag440'],'ret1',d).to_string(index=False))
print('-- 牡の同じ比較')
dm = df[(df['sex']=='牡') & (df['weight']>=420)].copy()
dm['flag440'] = (dm['weight']>=440).astype(int)
print(dm.groupby('flag440').agg(n=('win_jra','size'), 勝上=('win_jra','mean'), 回収1=('ret1','mean')).round(3).to_string())
print(run(['flag440'],'win_jra',dm).to_string(index=False))

print('\n=== D) 現行3基準 vs 「牝だけ440」に差し替え（AUC・年度別）===')
def mk(d, femthr):
    f = np.where(d['male']==1, d['weight']>=420, d['weight']>=femthr).astype(int)
    return d['male'] + d['price25_40'] + f
for femthr in [420, 430, 440]:
    d = df.copy(); d['sc'] = mk(d, femthr)
    a1 = auc(d['win_jra'].values, d['sc'].values); a2 = auc(d['ret1'].values, d['sc'].values)
    per = d[d['sc']==3]
    print(f'牝閾値{femthr}: AUC(win)={a1:.4f} AUC(ret)={a2:.4f} | 3点該当{len(per)}頭 '
          f'勝上{per["win_jra"].mean():.3f} 回収1{per["ret1"].mean():.3f} 回収中央{per["ret"].median():.2f}')
    print('   3点該当の年度別勝上:', (per.groupby('year')['win_jra'].mean()*100).round(0).to_dict(),
          '頭数', per.groupby('year').size().to_dict())

print('\n=== E) 体高・胸囲の閾値（既存3基準を統制）===')
for col, thrs in [('height',[150,152,154,156]), ('girth',[170,173,175,178])]:
    for thr in thrs:
        d = df.copy(); d['f'] = (d[col]>=thr).astype(int)
        r1 = run(['male','price25_40','w420','f'],'win_jra',d).iloc[3]
        r2 = run(['male','price25_40','w420','f'],'ret1',d).iloc[3]
        print(f'{col}>={thr}: 該当{int(d.f.sum())} 勝上 {d[d.f==1]["win_jra"].mean():.3f} vs {d[d.f==0]["win_jra"].mean():.3f} '
              f'z(win)={r1["z"]:+.2f} z(ret)={r2["z"]:+.2f}')

print('\n=== F) 体重上限（既存3基準を統制、上限をスキャン）===')
for hi in [480, 490, 500, 510]:
    d = df.copy(); d['over'] = (d['weight']>=hi).astype(int)
    r1 = run(['male','price25_40','w420','over'],'win_jra',d).iloc[3]
    r2 = run(['male','price25_40','w420','over'],'ret1',d).iloc[3]
    print(f'{hi}kg以上: n={int(d.over.sum())} 勝上{d[d.over==1]["win_jra"].mean():.3f} 回収1{d[d.over==1]["ret1"].mean():.3f} '
          f'z(win)={r1["z"]:+.2f} z(ret)={r2["z"]:+.2f}')

print('\n=== G) 多重検定の目安 ===')
print('今回の主要候補数: 単独12 + 比率×体重12 + 閾値スキャン(牡13+牝13) + 体高/胸囲8 + 上限4 ≒ 62')
print('Bonferroni 0.05/62 -> |z| > 3.15 が必要')

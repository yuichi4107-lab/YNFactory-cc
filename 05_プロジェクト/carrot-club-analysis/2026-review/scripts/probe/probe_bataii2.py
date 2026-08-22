# -*- coding: utf-8 -*-
"""馬体切り口 その2：管囲を深掘り、現行3基準との重複を見る。"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import numpy as np, pandas as pd
from analyze5 import load, logit, design
pd.set_option('display.width', 250)

df = load(central_only=True).dropna(subset=['win_jra']).copy()
df = df.dropna(subset=['weight', 'height', 'girth', 'cannon']).copy()
for c in ['weight', 'height', 'girth', 'cannon']:
    df[c + '_z'] = df.groupby('year')[c].transform(lambda s: (s - s.mean()) / s.std())
df['price25_40'] = df['total_man'].between(2500, 3999).astype(int)

def run(cols, target, d=None):
    d = df if d is None else d
    d = d.dropna(subset=cols + [target])
    X, names = design(d, cols)
    r = logit(X, d[target], names)
    return r[~r['変数'].astype(str).str.startswith('年度')].assign(n=len(d)).round(3)

print('=== 管囲の分布 ===')
print(df['cannon'].describe().round(2).to_string())
print(df.groupby('year')['cannon'].agg(['mean', 'std', 'min', 'max']).round(2).to_string())

print('\n=== 管囲帯ごとの成績（全年プール）===')
df['_cb'] = pd.cut(df['cannon'], [0, 19.2, 19.7, 20.2, 20.7, 99])
t = df.groupby('_cb', observed=True).agg(頭数=('win_jra','size'), 中央勝上=('win_jra','mean'),
        回収1=('ret1','mean'), 平均体重=('weight','mean'), 平均総額=('total_man','mean'))
t['中央勝上'] *= 100; t['回収1'] *= 100
print(t.round(1).to_string())
print('\n-- 年度別 中央勝上率 / 頭数')
print((df.pivot_table(index='_cb', columns='year', values='win_jra', aggfunc='mean', observed=True)*100).round(0).to_string())
print(df.pivot_table(index='_cb', columns='year', values='win_jra', aggfunc='size', observed=True).to_string())

print('\n=== 管囲：年度別に単独ロジット（符号の安定性）===')
for t_ in ['win_jra', 'ret1']:
    rows = []
    for y in sorted(df['year'].unique()):
        d = df[df['year'] == y]
        X = np.column_stack([np.ones(len(d)), d['cannon_z']])
        r = logit(X, d[t_], ['切片', '管囲z'])
        rw = logit(np.column_stack([np.ones(len(d)), d['weight_z']]), d[t_], ['切片','体重z'])
        rows.append({'年度': y, 'n': len(d), '管囲z係数': round(r.iloc[1]['係数'],3), 'z': round(r.iloc[1]['z'],2),
                     '体重z係数': round(rw.iloc[1]['係数'],3), 'z(体重)': round(rw.iloc[1]['z'],2)})
    print(f'-- {t_}')
    print(pd.DataFrame(rows).to_string(index=False))

print('\n=== 管囲 vs 体重：どちらが残るか（4測尺すべて同時）===')
for t_ in ['win_jra', 'ret1']:
    print(f'-- {t_}')
    print(run(['weight_z','height_z','girth_z','cannon_z'], t_).to_string(index=False))

print('\n=== 現行3基準（牡・2500-3999万・420kg以上）に管囲を足す ===')
df['w420'] = (df['weight'] >= 420).astype(int)
for t_ in ['win_jra', 'ret1']:
    print(f'-- {t_}')
    print(run(['male','price25_40','w420','cannon_z'], t_).to_string(index=False))

print('\n=== 管囲の閾値スキャン（現行3基準を統制した上で）===')
for thr in [19.0, 19.2, 19.5, 19.7, 20.0, 20.2, 20.5]:
    d = df.copy(); d['cflag'] = (d['cannon'] >= thr).astype(int)
    if d['cflag'].nunique() < 2: continue
    r1 = run(['male','price25_40','w420','cflag'], 'win_jra', d)
    r2 = run(['male','price25_40','w420','cflag'], 'ret1', d)
    print(f'管囲>={thr}: 該当{int(d.cflag.sum())}/{len(d)}  '
          f'勝上 {d[d.cflag==1]["win_jra"].mean():.3f} vs {d[d.cflag==0]["win_jra"].mean():.3f} '
          f'z={r1.iloc[3]["z"]:+.2f} | 回収1 {d[d.cflag==1]["ret1"].mean():.3f} vs {d[d.cflag==0]["ret1"].mean():.3f} z={r2.iloc[3]["z"]:+.2f}')

print('\n=== 管囲は価格・性別と相関するか ===')
print(df[['cannon','weight','height','girth','total_man','price_pct']].corr().round(3)['cannon'].to_string())
print(df.groupby('sex')['cannon'].agg(['mean','std','size']).round(2).to_string())
print('管囲z 対 male のt検定的:', df.groupby('male')['cannon_z'].mean().round(3).to_dict())

print('\n=== 体重×性別の交互作用（連続）===')
df['w_x_male'] = df['weight_z'] * df['male']
for t_ in ['win_jra','ret1']:
    print(f'-- {t_}')
    print(run(['male','weight_z','w_x_male'], t_).to_string(index=False))

print('\n=== 500kg超は不利か（440kg以上に限って上限を見る）===')
d = df[df['weight'] >= 440].copy()
d['big'] = (d['weight'] >= 500).astype(int)
print('n=', len(d), '500kg以上', int(d.big.sum()))
print(run(['big'], 'win_jra', d).to_string(index=False))
print(run(['big'], 'ret1', d).to_string(index=False))
print(d.groupby('big').agg(n=('win_jra','size'), 勝上=('win_jra','mean'), 回収1=('ret1','mean'), 回収中央=('ret','median')).round(3).to_string())

print('\n=== 牝に閾値を変えたときの実運用インパクト（牡420 / 牝X）===')
for wthr in [420, 430, 440]:
    d = df.copy()
    d['flag'] = np.where(d['male']==1, d['weight']>=420, d['weight']>=wthr).astype(int)
    n1 = int(d.flag.sum())
    print(f'牝{wthr}kg: 通過{n1}/{len(d)} 勝上 {d[d.flag==1]["win_jra"].mean():.3f} vs {d[d.flag==0]["win_jra"].mean():.3f} '
          f'| 回収1 {d[d.flag==1]["ret1"].mean():.3f} vs {d[d.flag==0]["ret1"].mean():.3f} '
          f'| z(win)={run(["flag"],"win_jra",d).iloc[0]["z"]:+.2f} z(ret)={run(["flag"],"ret1",d).iloc[0]["z"]:+.2f}')
    print('   年度別通過群勝上:', (d[d.flag==1].groupby('year')['win_jra'].mean()*100).round(0).to_dict(),
          ' 非通過:', (d[d.flag==0].groupby('year')['win_jra'].mean()*100).round(0).to_dict(),
          ' 非通過n:', d[d.flag==0].groupby('year').size().to_dict())

# -*- coding: utf-8 -*-
"""馬体（測尺）切り口の探索。既存ファイルは書き換えない。"""
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import numpy as np, pandas as pd
from analyze5 import load, logit, design

pd.set_option('display.width', 250)

df = load(central_only=True).dropna(subset=['win_jra']).copy()
df = df.dropna(subset=['weight', 'height', 'girth', 'cannon']).copy()
print('n =', len(df), ' 年度別:', df.groupby('year').size().to_dict())

# ---- 派生変数 ----
df['g_h']    = df['girth'] / df['height']          # 胸囲/体高
df['c_h']    = df['cannon'] / df['height']         # 管囲/体高
df['w_h']    = df['weight'] / df['height']         # 体重/体高
df['g_m_h']  = df['girth'] - df['height']          # 胸囲-体高
df['bmi']    = df['weight'] / (df['height'] / 100) ** 2      # BMI的
df['bmi3']   = df['weight'] / (df['height'] / 100) ** 3      # 体積比
df['c_g']    = df['cannon'] / df['girth']
df['w_pred_resid'] = np.nan   # 後で
# 年内偏差
for c in ['weight', 'height', 'girth', 'cannon', 'g_h', 'c_h', 'w_h', 'g_m_h', 'bmi', 'bmi3', 'c_g']:
    df[c + '_dev'] = df[c] - df.groupby('year')[c].transform('mean')
    s = df.groupby('year')[c].transform('std')
    df[c + '_z'] = df[c + '_dev'] / s

# 体高・胸囲から予測した体重との残差（＝同じ骨格で重いか軽いか）
import numpy.linalg as la
A = np.column_stack([np.ones(len(df)), df['height'], df['girth']])
coef, *_ = la.lstsq(A, df['weight'].values, rcond=None)
df['w_resid'] = df['weight'] - A @ coef
df['w_resid_z'] = df.groupby('year')['w_resid'].transform(lambda s: (s - s.mean()) / s.std())

VARS = ['weight_z', 'height_z', 'girth_z', 'cannon_z', 'g_h_z', 'c_h_z', 'w_h_z',
        'g_m_h_z', 'bmi_z', 'bmi3_z', 'c_g_z', 'w_resid_z']

def run(cols, target='win_jra', sub=None):
    d = sub if sub is not None else df
    d = d.dropna(subset=cols + [target])
    X, names = design(d, cols)
    r = logit(X, d[target], names)
    return r[~r['変数'].astype(str).str.startswith('年度')].assign(n=len(d))

print('\n=== 1) 各測尺・比率を単独で（年度ダミー入り、標準化済み）===')
for t in ['win_jra', 'ret1']:
    rows = []
    for v in VARS:
        rows.append(run([v], t).iloc[0])
    print(f'-- 目的変数 {t}')
    print(pd.DataFrame(rows)[['変数', '係数', 'z', 'オッズ比', 'n']].round(3).to_string(index=False))

print('\n=== 2) 馬体重を入れたら残るか（weight_z と同時投入）===')
for t in ['win_jra', 'ret1']:
    print(f'-- 目的変数 {t}')
    rows = []
    for v in VARS:
        if v == 'weight_z':
            continue
        r = run(['weight_z', v], t)
        rows.append({'追加変数': v,
                     'z(weight)': round(r.iloc[0]['z'], 2),
                     'z(追加)': round(r.iloc[1]['z'], 2)})
    print(pd.DataFrame(rows).to_string(index=False))

print('\n=== 3) 馬体重の非線形性 ===')
d = df.copy()
d['w2'] = d['weight_z'] ** 2
print(run(['weight_z', 'w2'], 'win_jra', d).round(3).to_string(index=False))
print(run(['weight_z', 'w2'], 'ret1', d).round(3).to_string(index=False))
bins = [0, 399, 419, 439, 459, 479, 499, 999]
d['_b'] = pd.cut(d['weight'], bins)
tb = d.groupby('_b', observed=True).agg(頭数=('win_jra', 'size'), 中央勝上=('win_jra', 'mean'),
                                        回収1=('ret1', 'mean'), 回収中央値=('ret', 'median'))
print((tb * [1, 100, 100, 1]).round(1).to_string())
print('\n-- 年度別 中央勝ち上がり率（体重帯）')
print((d.pivot_table(index='_b', columns='year', values='win_jra', aggfunc='mean', observed=True) * 100).round(0).to_string())
print((d.pivot_table(index='_b', columns='year', values='win_jra', aggfunc='size', observed=True)).to_string())

print('\n=== 4) 性別ごとの体重閾値スキャン ===')
for sexlab, mask in [('牡', df['male'] == 1), ('牝', df['male'] == 0)]:
    d = df[mask]
    print(f'\n-- {sexlab}  n={len(d)}  中央勝上率={d["win_jra"].mean():.3f} 回収1率={d["ret1"].mean():.3f}')
    rows = []
    for thr in range(390, 501, 10):
        d2 = d.copy()
        d2['flag'] = (d2['weight'] >= thr).astype(int)
        if d2['flag'].nunique() < 2:
            continue
        r1 = run(['flag'], 'win_jra', d2).iloc[0]
        r2 = run(['flag'], 'ret1', d2).iloc[0]
        rows.append({'閾値': thr, '該当n': int(d2['flag'].sum()),
                     '該当勝上': round(d2[d2.flag == 1]['win_jra'].mean(), 3),
                     '非該当勝上': round(d2[d2.flag == 0]['win_jra'].mean(), 3),
                     'z(win)': round(r1['z'], 2),
                     '該当回収1': round(d2[d2.flag == 1]['ret1'].mean(), 3),
                     '非該当回収1': round(d2[d2.flag == 0]['ret1'].mean(), 3),
                     'z(ret)': round(r2['z'], 2)})
    print(pd.DataFrame(rows).to_string(index=False))

print('\n=== 5) 現行420kg基準の性別別の効き ===')
df['w420'] = (df['weight'] >= 420).astype(int)
for sexlab, mask in [('牡', df['male'] == 1), ('牝', df['male'] == 0)]:
    d = df[mask]
    r1 = run(['w420'], 'win_jra', d).iloc[0]
    r2 = run(['w420'], 'ret1', d).iloc[0]
    print(f'{sexlab}: n={len(d)} 該当{int(d["w420"].sum())}  '
          f'勝上 {d[d.w420==1]["win_jra"].mean():.3f} vs {d[d.w420==0]["win_jra"].mean():.3f} z={r1["z"]:.2f} | '
          f'回収1 {d[d.w420==1]["ret1"].mean():.3f} vs {d[d.w420==0]["ret1"].mean():.3f} z={r2["z"]:.2f}')
print('\n-- 年度別（性別×420kg）中央勝上率')
print((df.pivot_table(index=['sex', 'w420'], columns='year', values='win_jra', aggfunc='mean') * 100).round(0).to_string())
print(df.pivot_table(index=['sex', 'w420'], columns='year', values='win_jra', aggfunc='size').to_string())

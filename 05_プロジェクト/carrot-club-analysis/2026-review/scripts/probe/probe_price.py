# -*- coding: utf-8 -*-
"""価格まわりの未検定変数を洗う。中央400口・年度コントロール。"""
import io, os, sys, json
import numpy as np
import pandas as pd
from analyze5 import load, logit, design

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 250)
pd.set_option('display.max_rows', 400)
BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, '..', '..', 'data')

df = load(central_only=True).dropna(subset=['win_jra']).copy()
df['logp'] = np.log(df['total_man'])
df['logp_rel'] = df['logp'] - df.groupby('year')['logp'].transform('mean')
df['price_pctile'] = df.groupby('year')['total_man'].rank(pct=True)


def sec(t):
    print('\n' + '=' * 90)
    print('# ' + t)
    print('=' * 90)


def yr_table(sub, col):
    piv = sub.pivot_table(index=col, columns='year', values='win_jra',
                          aggfunc=['mean', 'size'], dropna=False)
    m, n = piv['mean'] * 100, piv['size']
    tot = sub.groupby(col, observed=False)['win_jra'].agg(['mean', 'size'])
    print('  ' + f'{"":<16}' + ''.join(f'{y:>11}' for y in m.columns) + f'{"ALL":>13}')
    for idx in m.index:
        cells = []
        for y in m.columns:
            mv, nv = m.loc[idx, y], n.loc[idx, y]
            cells.append(f'{int(round(mv)):>3}%({int(nv):>2})' if pd.notna(mv) and nv > 0 else f'{"-":>8}')
        t = tot.loc[idx]
        cells.append(f'{int(round(t["mean"]*100)):>3}%({int(t["size"]):>3})')
        print(f'  {str(idx):<16}' + ''.join(f'{c:>11}' for c in cells))


def run(cols, y='win_jra', sub=None, label=''):
    s = df if sub is None else sub
    s = s.dropna(subset=cols + [y])
    X, names = design(s, cols)
    r = logit(X, s[y], names)
    r = r[~r['変数'].str.startswith('年度')]
    print(f'  [{label or ",".join(cols)}] target={y} n={len(s)}')
    print(r.round(3).to_string(index=False))
    return r


# ---------------------------------------------------------------- 1口価格
sec('1) 1口価格そのもの')
u = pd.to_numeric(df['unit_man'], errors='coerce')
print('max |unit_man*400 - total_man| =', float((u * 400 - df['total_man']).abs().max()))
print('-> 中央400口では 1口価格 = 総額/400。独立な情報はゼロ。')
print('総額のとりうる値:', sorted(df['total_man'].unique()))
print('※3800万は存在しない。よって 2500-3999万 = {2600,2800,3000,3200,3400,3600}')

# ---------------------------------------------------------------- 価格水準
sec('2) 価格水準ごとの中央勝ち上がり（年度別）')
def band(v):
    if v < 2500: return '01 -2400'
    if v < 3000: return '02 2600-2800'
    if v == 3000: return '03 3000jd'
    if v < 4000: return '04 3200-3600'
    if v < 5000: return '05 4000-4800'
    if v < 6000: return '06 5000-5600'
    if v < 8000: return '07 6000-7000'
    return '08 8000+'
df['band'] = df['total_man'].map(band)
yr_table(df, 'band')

print('\n-- 総額の生値ごと（5頭以上）')
g = df.groupby('total_man')['win_jra'].agg(['size', 'mean'])
print(g[g['size'] >= 5].assign(mean=lambda d: (d['mean'] * 100).round(0)).to_string())

print('\n-- 3000万ちょうど vs それ以外（年度別）')
df['p3000'] = (df['total_man'] == 3000).astype(int)
yr_table(df, 'p3000')
run(['p3000'], 'win_jra')
run(['p3000'], 'ret1')

print('\n-- 近傍比較: 2600-3600 の中だけで 3000 vs それ以外')
nb = df[df['total_man'].between(2600, 3600)]
yr_table(nb, 'p3000')
run(['p3000'], 'win_jra', sub=nb, label='p3000 near')

# ---------------------------------------------------------------- 非線形
sec('3) 価格の非線形性（線形 / log / 年内順位）')
for c in ['total_man', 'logp', 'logp_rel', 'price_pctile', 'price_rel']:
    run([c], 'win_jra')
print('\n-- 二次項: 山型かどうか')
df['logp_rel2'] = df['logp_rel'] ** 2
run(['logp_rel', 'logp_rel2'], 'win_jra')
print('\n-- 参考 ret1 (★分母が価格。機械的に負に出る)')
run(['logp_rel'], 'ret1')
run(['logp_rel', 'logp_rel2'], 'ret1')

# ---------------------------------------------------------------- 上限
sec('4) 上限は本当に不要か（中央勝ち上がりで見る）')
for lo, hi in [(2500, 3999), (2500, 4999), (2500, 5999), (2500, 7999), (2500, 999999)]:
    df['_b'] = df['total_man'].between(lo, hi).astype(int)
    run(['_b'], 'win_jra', label=f'{lo}-{hi}')
    print()
print('-- 高額側ダミー')
for th in [4000, 5000, 6000, 8000]:
    df['_h'] = (df['total_man'] >= th).astype(int)
    run(['_h'], 'win_jra', label=f'>={th}')
    yr_table(df, '_h')
    print()
print('-- 高額馬は重賞・賞金では報われるか')
df['_hi'] = (df['total_man'] >= 6000).astype(int)
print(df.groupby('_hi').agg(n=('win_jra', 'size'), win_jra=('win_jra', 'mean'),
                            graded_n=('graded', lambda s: (s > 0).sum()),
                            prize_mean=('prize', 'mean'), ret_med=('ret', 'median')).round(3).to_string())

# ---------------------------------------------------------------- 残差
sec('5) 価格の割に馬体が良い/悪い = 価格の残差')
m = df.dropna(subset=['weight', 'height', 'girth', 'cannon']).copy()
gs = m.groupby('sire')['logp_rel']
m['sire_n'] = gs.transform('size')
m['sire_loo'] = np.where(m['sire_n'] > 1,
                         (gs.transform('sum') - m['logp_rel']) / (m['sire_n'] - 1), 0.0)

def ols_resid(y, cols):
    X = np.column_stack([np.ones(len(m))] + [m[c].astype(float).values for c in cols])
    b, *_ = np.linalg.lstsq(X, m[y].astype(float).values, rcond=None)
    pred = X @ b
    yv = m[y].astype(float).values
    return yv - pred, b, np.corrcoef(pred, yv)[0, 1] ** 2

phys = ['weight', 'height', 'girth', 'cannon', 'male']
r1, b1, R1 = ols_resid('logp_rel', phys)
m['resid_phys'] = r1
print(f'logp_rel ~ 測尺+性        R2={R1:.3f} coef={np.round(b1,4)}  (順: 定数,weight,height,girth,cannon,male)')
r2, b2, R2 = ols_resid('logp_rel', phys + ['sire_loo'])
m['resid_ps'] = r2
print(f'logp_rel ~ 測尺+性+父LOO  R2={R2:.3f} coef={np.round(b2,4)}')

for c in ['resid_phys', 'resid_ps']:
    print()
    run([c], 'win_jra', sub=m, label=c)
    m['_t'] = pd.qcut(m[c], 3, labels=['A_cheap', 'B_mid', 'C_rich'])
    yr_table(m, '_t')
    print('  ret1 (★価格が分母。cheap側が機械的に有利)')
    run([c], 'ret1', sub=m, label=c)

print('\n-- 価格と残差を同時に入れる')
run(['logp_rel', 'resid_ps'], 'win_jra', sub=m, label='price+resid')

print('\n-- 逆向き: 価格調整後の馬体重（価格の割に重い）')
mm = m.copy()
X = np.column_stack([np.ones(len(mm)), mm['logp_rel'], mm['male']])
b, *_ = np.linalg.lstsq(X, mm['weight'].values, rcond=None)
mm['w_resid'] = mm['weight'].values - X @ b
run(['w_resid'], 'win_jra', sub=mm, label='w_resid')
mm['_t'] = pd.qcut(mm['w_resid'], 3, labels=['A_light', 'B_mid', 'C_heavy'])
yr_table(mm, '_t')

# ---------------------------------------------------------------- 母馬優先
sec('6) 価格と母馬優先')
try:
    rank = pd.read_csv(os.path.join(DATA, 'dam_age_rank.csv'), encoding='utf-8-sig')
    print(rank.head().to_string())
    rank['year'] = pd.to_numeric(rank['募集年度'], errors='coerce')
    rank['no_i'] = pd.to_numeric(rank['募集番号'], errors='coerce')
    d2 = df.copy()
    d2['no_i'] = pd.to_numeric(d2['no'], errors='coerce')
    mg = d2.merge(rank[['year', 'no_i', '抽選ランク', '母馬優先枠で抽選']],
                  on=['year', 'no_i'], how='left')
    mg['dam_priority'] = mg['抽選ランク'].notna().astype(int)
    print('\n母馬優先対象の頭数（年度別）')
    print(mg.pivot_table(index='dam_priority', columns='year', values='win_jra', aggfunc='size').to_string())
    sub = mg[mg['year'].between(2021, 2024)].dropna(subset=['win_jra'])
    print('\n-- 母馬優先 x 中央勝ち上がり（2021-2024）')
    yr_table(sub, 'dam_priority')
    X, names = design(sub, ['dam_priority'])
    print(logit(X, sub['win_jra'], names).round(3).to_string(index=False))
    print('\n-- 母馬優先対象の価格分布')
    print(sub.groupby('dam_priority')['total_man'].describe().to_string())
    print('\n-- 価格を入れた上で母馬優先が残るか')
    X, names = design(sub, ['logp_rel', 'dam_priority'])
    print(logit(X, sub['win_jra'], names).round(3).to_string(index=False))
    print('\n-- 抽選ランク別')
    print(sub.groupby('抽選ランク').agg(n=('win_jra', 'size'), win=('win_jra', 'mean'),
                                        price_med=('total_man', 'median')).round(3).to_string())
except Exception as e:
    import traceback; traceback.print_exc()

# ---------------------------------------------------------------- 人気
sec('7) 価格と申込人気（carrot_interim）')
try:
    it = pd.read_csv(os.path.join(DATA, 'carrot_interim.csv'), encoding='utf-8-sig')
    print(it.head().to_string())
    print('年度別:', it['募集年度'].value_counts().to_dict())
    it['year'] = pd.to_numeric(it['募集年度'], errors='coerce')
    it['no_i'] = pd.to_numeric(it['募集番号'], errors='coerce')
    d2 = df.copy()
    d2['no_i'] = pd.to_numeric(d2['no'], errors='coerce')
    mg = d2.merge(it, on=['year', 'no_i'], how='inner')
    print('結合:', len(mg), mg['year'].value_counts().to_dict())
    if len(mg) > 20:
        mg['pop'] = pd.to_numeric(mg['総申込'], errors='coerce')
        print(mg[['total_man', 'pop']].corr().round(3).to_string())
        X = np.column_stack([np.ones(len(mg)), np.log(mg['total_man'])])
        yv = np.log(mg['pop'].clip(lower=1))
        b, *_ = np.linalg.lstsq(X, yv, rcond=None)
        mg['pop_resid'] = yv - X @ b
        s = mg.dropna(subset=['win_jra', 'pop_resid'])
        X2, names = design(s, ['pop_resid'])
        print(logit(X2, s['win_jra'], names).round(3).to_string(index=False))
except Exception as e:
    import traceback; traceback.print_exc()

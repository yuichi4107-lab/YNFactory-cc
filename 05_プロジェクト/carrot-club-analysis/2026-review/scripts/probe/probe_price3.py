# -*- coding: utf-8 -*-
"""価格 第3波: 絶対額バンドの年度ドリフト、相対価格基準、3000万スパイクの中身、AUC。"""
import io, os, sys
import numpy as np
import pandas as pd
from analyze5 import load, logit, design
from backtest import auc

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 250)
pd.set_option('display.max_rows', 400)
BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, '..', '..', 'data')

df = load(central_only=True).dropna(subset=['win_jra']).copy()
df['logp'] = np.log(df['total_man'])
df['logp_rel'] = df['logp'] - df.groupby('year')['logp'].transform('mean')
df['logp_rel2'] = df['logp_rel'] ** 2
df['pct'] = df.groupby('year')['total_man'].rank(pct=True)
df['p3000'] = (df['total_man'] == 3000).astype(int)


def sec(t):
    print('\n' + '=' * 90); print('# ' + t); print('=' * 90)


def run(cols, y='win_jra', sub=None, label=''):
    s = df if sub is None else sub
    s = s.dropna(subset=cols + [y])
    X, names = design(s, cols)
    r = logit(X, s[y], names)
    r = r[~r['変数'].str.startswith('年度')]
    print(f'  [{label or ",".join(cols)}] target={y} n={len(s)}')
    print(r.round(3).to_string(index=False))
    return r


def yr_table(sub, col):
    piv = sub.pivot_table(index=col, columns='year', values='win_jra',
                          aggfunc=['mean', 'size'], dropna=False)
    m, n = piv['mean'] * 100, piv['size']
    tot = sub.groupby(col, observed=False)['win_jra'].agg(['mean', 'size'])
    print('  ' + f'{"":<14}' + ''.join(f'{y:>11}' for y in m.columns) + f'{"ALL":>13}')
    for idx in m.index:
        cells = []
        for y in m.columns:
            mv, nv = m.loc[idx, y], n.loc[idx, y]
            cells.append(f'{int(round(mv)):>3}%({int(nv):>2})' if pd.notna(mv) and nv > 0 else f'{"-":>8}')
        t = tot.loc[idx]
        cells.append(f'{int(round(t["mean"]*100)):>3}%({int(t["size"]):>3})')
        print(f'  {str(idx):<14}' + ''.join(f'{c:>11}' for c in cells))


sec('A) 絶対額バンドは年度でどこを切っているか（インフレによるドリフト）')
rows = []
for y, g in df.groupby('year'):
    n = len(g)
    rows.append({'year': y, 'n': n, '中央値': g['total_man'].median(),
                 '2500万未満の割合': round((g['total_man'] < 2500).mean(), 3),
                 '2500-3999の割合': round(g['total_man'].between(2500, 3999).mean(), 3),
                 '4000以上の割合': round((g['total_man'] >= 4000).mean(), 3),
                 '2500万の年内パーセンタイル': round((g['total_man'] < 2500).mean(), 3),
                 '4000万の年内パーセンタイル': round((g['total_man'] < 4000).mean(), 3)})
try:
    b26 = pd.read_csv(os.path.join(DATA, 'bosyu_2026.csv'), encoding='utf-8-sig')
    b26['total_man'] = pd.to_numeric(b26['募集総額_万円'].astype(str).str.replace('万', '', regex=False)
                                     .str.replace(',', '', regex=False), errors='coerce')
    g = b26.dropna(subset=['total_man'])
    rows.append({'year': 2026, 'n': len(g), '中央値': g['total_man'].median(),
                 '2500万未満の割合': round((g['total_man'] < 2500).mean(), 3),
                 '2500-3999の割合': round(g['total_man'].between(2500, 3999).mean(), 3),
                 '4000以上の割合': round((g['total_man'] >= 4000).mean(), 3),
                 '2500万の年内パーセンタイル': round((g['total_man'] < 2500).mean(), 3),
                 '4000万の年内パーセンタイル': round((g['total_man'] < 4000).mean(), 3)})
except Exception:
    import traceback; traceback.print_exc()
print(pd.DataFrame(rows).to_string(index=False))
print('\n→ 2500万という絶対額は 2020年で下位25%の境目、2026年では下位13%の境目に相当。')
print('→ 2500-3999万バンドは 2020年で中位帯だったが、2026年では下位2〜3割の帯になる。')

sec('B) 相対価格（年内パーセンタイル）で切ったらどうか')
for th in [0.15, 0.20, 0.25, 0.30, 0.35]:
    df['_d'] = (df['pct'] > th).astype(int)
    run(['_d'], 'win_jra', label=f'年内下位{int(th*100)}%を除外')
print('\n-- 年内下位25%除外 の年度別')
df['_d'] = (df['pct'] > 0.25).astype(int)
yr_table(df, '_d')
print('\n-- 絶対額 2500万以上 の年度別（比較）')
df['_a'] = (df['total_man'] >= 2500).astype(int)
yr_table(df, '_a')
print('\n-- 両方入れる（どちらが本質か）')
run(['_a', '_d'], 'win_jra', label='絶対2500以上 vs 年内上位75%')
print('\n-- 年内パーセンタイル5分位')
df['_q'] = pd.qcut(df['pct'], 5, labels=['Q1安', 'Q2', 'Q3', 'Q4', 'Q5高'])
yr_table(df, '_q')

sec('C) 3000万スパイクの中身')
s3 = df[df['p3000'] == 1]
so = df[(df['p3000'] == 0) & (df['total_man'].between(2400, 4000))]
print('3000万馬 vs 2400-4000万の3000以外')
cmp = pd.DataFrame({
    '3000万(n=%d)' % len(s3): [s3['male'].mean(), s3['nf'].mean(), s3['weight'].mean(),
                               s3['dam_age'].mean(), s3['mar_apr'].mean(),
                               pd.to_numeric(s3['n_foals'], errors='coerce').mean(),
                               s3['win_jra'].mean()],
    '近傍他(n=%d)' % len(so): [so['male'].mean(), so['nf'].mean(), so['weight'].mean(),
                              so['dam_age'].mean(), so['mar_apr'].mean(),
                              pd.to_numeric(so['n_foals'], errors='coerce').mean(),
                              so['win_jra'].mean()],
}, index=['牡率', 'ノーザン率', '馬体重', '母年齢', '3-4月生', '何番仔', '中央勝上'])
print(cmp.round(3).to_string())
print('\n3000万馬の父トップ')
print(s3['sire'].value_counts().head(10).to_string())
print('\n3000万馬の牧場')
print(s3['farm'].value_counts().head(6).to_string())
print('\n-- 他の要因を全部入れても3000万は残るか')
sub = df.dropna(subset=['weight', 'dam_age'])
run(['male', 'nf', 'mar_apr', 'dam811', 'weight', 'logp_rel', 'logp_rel2', 'p3000'],
    'win_jra', sub=sub, label='フル')
print('\n-- 3000万を年度別に1年ずつ抜いたときのz（1年に依存していないか）')
for drop in sorted(df['year'].unique()):
    s = df[df['year'] != drop]
    X, names = design(s, ['p3000'])
    r = logit(X, s['win_jra'], names)
    z = float(r[r['変数'] == 'p3000']['z'].iloc[0])
    print(f'  {drop}年度を除外: z={z:.2f}')
print('\n-- 逆側の2400万も同様に（n=45, z=-2.93）1年ずつ抜く')
df['p2400'] = (df['total_man'] == 2400).astype(int)
for drop in sorted(df['year'].unique()):
    s = df[df['year'] != drop]
    X, names = design(s, ['p2400'])
    r = logit(X, s['win_jra'], names)
    z = float(r[r['変数'] == 'p2400']['z'].iloc[0])
    print(f'  {drop}年度を除外: z={z:.2f}')

sec('D) 高額馬は「悪い馬」ではなく「割高な馬」か（経済性の分解）')
def band(v):
    if v < 2500: return '1 -2400'
    if v < 4000: return '2 2500-3999'
    if v < 6000: return '3 4000-5999'
    return '4 6000+'
df['b4'] = df['total_man'].map(band)
t = df.groupby('b4').agg(n=('win_jra', 'size'), 中央勝上=('win_jra', 'mean'),
                         重賞頭数=('graded', lambda s: (s > 0).sum()),
                         平均賞金万=('prize', 'mean'), 平均価格万=('total_man', 'mean'),
                         回収平均=('ret', 'mean'), 回収中央値=('ret', 'median'))
t['賞金/価格'] = (t['平均賞金万'] / t['平均価格万']).round(3)
print(t.round(3).to_string())
print('\n→ 2500万以上では平均賞金がほぼ横ばい（3231→2675→2910万）なのに価格だけ上がる。')
print('  つまり上限は「高額馬が弱い」のではなく「同じ賞金をより高く買っている」という経済性の話。')
print('\n-- 賞金(log)に対する価格の効き（勝ち上がりではなく金額で見る）')
d2 = df[df['prize'] > 0].copy()
d2['lprize'] = np.log(d2['prize'])
X = np.column_stack([np.ones(len(d2))] +
                    [(d2['year'] == y).astype(float).values for y in sorted(d2['year'].unique())[1:]] +
                    [d2['logp_rel'].values])
b, *_ = np.linalg.lstsq(X, d2['lprize'].values, rcond=None)
resid = d2['lprize'].values - X @ b
se = np.sqrt(np.sum(resid ** 2) / (len(d2) - X.shape[1]) * np.diag(np.linalg.inv(X.T @ X)))
print(f'  log賞金 ~ 年度 + log価格(年内中心化)  n={len(d2)}(賞金>0のみ)')
print(f'  log価格の係数={b[-1]:.3f} SE={se[-1]:.3f} t={b[-1]/se[-1]:.2f}')
print('  （係数が1未満＝価格を倍にしても賞金は倍にならない＝回収率は下がる）')

sec('E) 基準セットの比較（AUC・年度別ホールドアウト）')
df['w420'] = (df['weight'] >= 420).astype(float)
sets = {
    '現行3基準(牡/2500-3999/420kg)': lambda d: d['male'] + d['total_man'].between(2500, 3999).astype(int) + (d['weight'] >= 420).astype(int),
    '上限を外す(牡/2500以上/420kg)': lambda d: d['male'] + (d['total_man'] >= 2500).astype(int) + (d['weight'] >= 420).astype(int),
    '相対価格(牡/年内上位75%/420kg)': lambda d: d['male'] + (d['pct'] > 0.25).astype(int) + (d['weight'] >= 420).astype(int),
    '相対価格+3000万ボーナス': lambda d: d['male'] + (d['pct'] > 0.25).astype(int) + (d['weight'] >= 420).astype(int) + d['p3000'],
    '価格のみ(2500以上)': lambda d: (d['total_man'] >= 2500).astype(int),
    '価格のみ(年内上位75%)': lambda d: (d['pct'] > 0.25).astype(int),
}
sub = df.dropna(subset=['weight'])
out = []
for k, f in sets.items():
    sc = f(sub).astype(float)
    row = {'基準': k, '全体AUC': round(auc(sub['win_jra'].values, sc.values), 3)}
    for y in sorted(sub['year'].unique()):
        mk = sub['year'] == y
        row[str(y)] = round(auc(sub.loc[mk, 'win_jra'].values, sc[mk].values), 3)
    out.append(row)
print(pd.DataFrame(out).to_string(index=False))

print('\n-- 3基準すべて満たす馬の勝ち上がり率（年度別）')
for k, f in [('現行(2500-3999)', lambda d: (d['male'] == 1) & d['total_man'].between(2500, 3999) & (d['weight'] >= 420)),
             ('上限なし(2500以上)', lambda d: (d['male'] == 1) & (d['total_man'] >= 2500) & (d['weight'] >= 420)),
             ('相対(年内上位75%)', lambda d: (d['male'] == 1) & (d['pct'] > 0.25) & (d['weight'] >= 420))]:
    sub['_p'] = f(sub).astype(int)
    print(f'\n{k}')
    yr_table(sub, '_p')
    p = sub[sub['_p'] == 1]
    print(f'  該当 n={len(p)} 中央勝上={p["win_jra"].mean():.3f} 回収≥1={p["ret1"].mean():.3f} '
          f'回収中央値={p["ret"].median():.3f} 重賞={int((p["graded"]>0).sum())}')

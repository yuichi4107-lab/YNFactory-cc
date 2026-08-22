# -*- coding: utf-8 -*-
"""敵対的検証 第2ラウンド: dam_prio の ret1 効果がどこから来ているかを解体する。"""
import io, os, sys
import numpy as np
import pandas as pd
from analyze5 import load, logit, design
from backtest import auc

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 220)
BASE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(BASE, '..', '..', 'data')

df = load(central_only=True)
df['no_i'] = pd.to_numeric(df['no'], errors='coerce')
rk = pd.read_csv(os.path.join(D, 'dam_age_rank.csv'), encoding='utf-8-sig')
rk.columns = ['year', 'no', 'dam', 'dam_born', 'dam_age_r', 'dam_season', 't', 'rank', 'pool_filled']
m = df.merge(rk[['year', 'no', 'rank']], left_on=['year', 'no_i'], right_on=['year', 'no'],
             how='left', suffixes=('', '_r'))
m['dam_prio'] = m['rank'].notna().astype(int)
m['price2539'] = m['total_man'].between(2500, 3999).astype(int)
m['w420'] = (m['weight'] >= 420).astype(float)
m.loc[m['weight'].isna(), 'w420'] = np.nan
S = m[m['year'].between(2021, 2024)].dropna(subset=['win_jra']).copy()
base = ['male', 'price2539', 'w420']


def zof(d, cols, y):
    dd = d.dropna(subset=list(cols) + [y])
    X, names = design(dd, list(cols))
    r = logit(X, dd[y], names)
    row = r[r['変数'] == cols[0]].iloc[0]
    return len(dd), float(row['z']), float(row['オッズ比'])


print('=' * 80)
print('■ A. 独立データでの dam_prio 検証（carrot_interim.csv の 区分 列, 2024年度）')
print('=' * 80)
it = pd.read_csv(os.path.join(D, 'carrot_interim.csv'), encoding='utf-8-sig')
it.columns = ['year', 'no', 'name', 'kubun', 'total', 'prio_only', 'prio', 'only_prio']
it24 = it[it.year == 2024].copy()
mm = S[S.year == 2024].merge(it24[['no', 'kubun']], left_on='no_i', right_on='no', how='left', suffixes=('', '_it'))
print('carrot_interim 2024 に載っている頭数(申込200口以上のみ):', it24.shape[0])
have = mm[mm['kubun'].notna()]
print('panel5(2024,中央)と突合できた:', len(have))
print(pd.crosstab(have['dam_prio'], have['kubun']).to_string())
mis = have[(have['dam_prio'] == 0) & (have['kubun'] == '対象')]
print('→ dam_prio=0 なのに interim では「対象」= 判定漏れ:', len(mis))
if len(mis):
    print(mis[['no_i', 'name', 'ret', 'win_jra']].to_string(index=False))

print('\n' + '=' * 80)
print('■ B. ret1 効果は何頭で持っているか（イベント数）')
print('=' * 80)
for y in [2021, 2022, 2023, 2024]:
    d = S[S.year == y]
    a, b = d[d.dam_prio == 1], d[d.dam_prio == 0]
    print('  %d  対象 ret1=%d/%d   非対象 ret1=%d/%d' %
          (y, a.ret1.sum(), len(a), b.ret1.sum(), len(b)))
print('  合計 対象 %d/%d 非対象 %d/%d' % (S[S.dam_prio == 1].ret1.sum(), (S.dam_prio == 1).sum(),
                                        S[S.dam_prio == 0].ret1.sum(), (S.dam_prio == 0).sum()))

print('\n' + '=' * 80)
print('■ C. 1年抜き（どの年が効果を持っているか）')
print('=' * 80)
for y in [None, 2021, 2022, 2023, 2024]:
    d = S if y is None else S[S.year != y]
    n1, z1, o1 = zof(d, ['dam_prio'], 'ret1')
    n2, z2, o2 = zof(d, ['dam_prio'], 'win_jra')
    print('  %s除外  n=%d  ret1 z=%+.2f OR=%.2f | win_jra z=%+.2f OR=%.2f'
          % ('なし' if y is None else str(y), n1, z1, o1, z2, o2))

print('\n' + '=' * 80)
print('■ D. 重賞・大物依存の解体')
print('=' * 80)
print('  重賞出走(graded>0): 対象 %d/%d(%.1f%%) 非対象 %d/%d(%.1f%%)' %
      (S[S.dam_prio == 1].graded.gt(0).sum(), (S.dam_prio == 1).sum(),
       S[S.dam_prio == 1].graded.gt(0).mean() * 100,
       S[S.dam_prio == 0].graded.gt(0).sum(), (S.dam_prio == 0).sum(),
       S[S.dam_prio == 0].graded.gt(0).mean() * 100))
n, z, o = zof(S[S.graded.fillna(0) == 0], ['dam_prio'], 'ret1')
print('  重賞出走馬を除く: n=%d z=%+.2f OR=%.2f' % (n, z, o))
# 回収0.3〜1.0の「地味な回収」層だけで見る（大物の寄与を切る）
sub = S[S.ret < 2.0]
n, z, o = zof(sub, ['dam_prio'], 'ret1')
print('  回収2.0未満に限定: n=%d z=%+.2f OR=%.2f' % (n, z, o))
# 年内順位（ノンパラ）
print('\n  年内 ret 順位（0-1正規化）の平均差 ＝ Mann-Whitney 相当:')
S['ret_pct'] = S.groupby('year')['ret'].rank(pct=True)
print('   ', S.groupby('dam_prio')['ret_pct'].mean().round(3).to_dict())
for y in [2021, 2022, 2023, 2024]:
    d = S[S.year == y]
    print('    %d 対象%.3f 非対象%.3f' % (y, d[d.dam_prio == 1].ret_pct.mean(),
                                         d[d.dam_prio == 0].ret_pct.mean()))

print('\n' + '=' * 80)
print('■ E. LOYO を年度別AUCの平均で見る（プールAUCは年度差を混ぜるので不適）')
print('=' * 80)


def loyo(data, cols, target, years, mode='reg'):
    out = {}
    for y in years:
        tr = data[data.year != y].dropna(subset=list(cols) + [target])
        te = data[data.year == y].dropna(subset=list(cols) + [target])
        if mode == 'reg':
            Xtr = np.column_stack([np.ones(len(tr))] + [tr[c].astype(float).values for c in cols])
            Xte = np.column_stack([np.ones(len(te))] + [te[c].astype(float).values for c in cols])
            b = logit(Xtr, tr[target], ['c'] + list(cols))['係数'].values
            p = Xte @ b
        else:
            p = te[list(cols)].astype(float).sum(axis=1).values
        out[y] = auc(te[target], p)
    return out


YRS = [2021, 2022, 2023, 2024]
for mode in ['reg', 'score']:
    for target in ['win_jra', 'ret1']:
        a = loyo(S, base, target, YRS, mode)
        b = loyo(S, base + ['dam_prio'], target, YRS, mode)
        print('  [%s/%s] 既存3 平均AUC=%.3f (%s) → +dam_prio 平均AUC=%.3f (%s)  差%+.3f'
              % (mode, target, np.mean(list(a.values())),
                 '/'.join('%.3f' % a[y] for y in YRS), np.mean(list(b.values())),
                 '/'.join('%.3f' % b[y] for y in YRS),
                 np.mean(list(b.values())) - np.mean(list(a.values()))))

print('\n' + '=' * 80)
print('■ F. プラセボ: 年度内でランダムに同数を「対象」にしたとき z>=2.26 が出る頻度')
print('=' * 80)
rng = np.random.default_rng(0)
cnt = 0
zs = []
for i in range(400):
    d = S.copy()
    d['fake'] = d.groupby('year')['dam_prio'].transform(lambda x: rng.permutation(x.values))
    _, z, _ = zof(d, ['fake'], 'ret1')
    zs.append(z)
    if z >= 2.26:
        cnt += 1
print('  400回中 z>=+2.26 は %d 回 (%.1f%%)  z分布 sd=%.2f' % (cnt, cnt / 4.0, np.std(zs)))
print('  → 単発の検定としての p はおよそ %.3f（片側）' % (cnt / 400.0))
print('  この分析全体で試した仮説数を仮に40とすると、どれか1つが z>=2.26 になる確率')
print('    = 1-(1-%.3f)^40 = %.2f' % (cnt / 400.0, 1 - (1 - cnt / 400.0) ** 40))

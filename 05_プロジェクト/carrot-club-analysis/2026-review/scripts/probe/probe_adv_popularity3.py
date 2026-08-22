# -*- coding: utf-8 -*-
"""敵対的検証 第3ラウンド: 重賞の裾を抜いたLOYO / out_s の実用可能性 / 多重検定の分母。"""
import io, os, re, sys, glob
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
RANK_LEGACY_OUT = {"A": "A", "B": "C", "C": "A", "D": "B", "E": "C",
                   "F": "A", "G": "B", "H": "C", "I": "D", "J": "D", "確定": "E"}
OUT_SCORE = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1}
rk['out'] = [RANK_LEGACY_OUT.get(str(r)) if y <= 2023 else (str(r)[1] if len(str(r)) == 2 else None)
             for y, r in zip(rk['year'], rk['rank'])]
rk['out_s'] = rk['out'].map(OUT_SCORE)
m = df.merge(rk[['year', 'no', 'rank', 'out_s']], left_on=['year', 'no_i'],
             right_on=['year', 'no'], how='left', suffixes=('', '_r'))
m['dam_prio'] = m['rank'].notna().astype(int)
m['price2539'] = m['total_man'].between(2500, 3999).astype(int)
m['w420'] = (m['weight'] >= 420).astype(float)
m.loc[m['weight'].isna(), 'w420'] = np.nan
S = m[m['year'].between(2021, 2024)].dropna(subset=['win_jra']).copy()
base = ['male', 'price2539', 'w420']
YRS = [2021, 2022, 2023, 2024]


def loyo(data, cols, target, years, mode='score'):
    out = {}
    for y in years:
        tr = data[data.year != y].dropna(subset=list(cols) + [target])
        te = data[data.year == y].dropna(subset=list(cols) + [target])
        if te[target].nunique() < 2:
            out[y] = np.nan
            continue
        if mode == 'reg':
            Xtr = np.column_stack([np.ones(len(tr))] + [tr[c].astype(float).values for c in cols])
            Xte = np.column_stack([np.ones(len(te))] + [te[c].astype(float).values for c in cols])
            b = logit(Xtr, tr[target], ['c'] + list(cols))['係数'].values
            p = Xte @ b
        else:
            p = te[list(cols)].astype(float).sum(axis=1).values
        out[y] = auc(te[target], p)
    return out


def cmp(data, target, extra, tag):
    for mode in ['reg', 'score']:
        a = loyo(data, base, target, YRS, mode)
        b = loyo(data, base + [extra], target, YRS, mode)
        va = [a[y] for y in YRS if a[y] == a[y]]
        vb = [b[y] for y in YRS if b[y] == b[y]]
        print('  %-28s [%s/%s] %.3f (%s) → %.3f (%s)  差%+.3f'
              % (tag, mode, target, np.mean(va), '/'.join('%.3f' % v for v in va),
                 np.mean(vb), '/'.join('%.3f' % v for v in vb), np.mean(vb) - np.mean(va)))


print('=' * 80)
print('■ G. 重賞出走馬を除いたうえでの LOYO（裾を抜いても改善が残るか）')
print('=' * 80)
ng = S[S.graded.fillna(0) == 0].copy()
print('  n=%d (重賞出走16頭を除外)  ret1イベント: 対象%d/%d 非対象%d/%d'
      % (len(ng), ng[ng.dam_prio == 1].ret1.sum(), (ng.dam_prio == 1).sum(),
         ng[ng.dam_prio == 0].ret1.sum(), (ng.dam_prio == 0).sum()))
cmp(S, 'ret1', 'dam_prio', '全頭')
cmp(ng, 'ret1', 'dam_prio', '重賞出走馬を除外')
cmp(S, 'win_jra', 'dam_prio', '全頭')

print('\n' + '=' * 80)
print('■ H. 回収率の連続版（年内ret順位）でのLOYO — 二値化のしきい値依存を外す')
print('=' * 80)
S['ret_hi'] = S.groupby('year')['ret'].rank(pct=True).ge(0.75).astype(int)  # 年内上位25%
cmp(S, 'ret_hi', 'dam_prio', '年内回収上位25%')
S['ret_hi10'] = S.groupby('year')['ret'].rank(pct=True).ge(0.90).astype(int)
cmp(S, 'ret_hi10', 'dam_prio', '年内回収上位10%')

print('\n' + '=' * 80)
print('■ I. out_s の実用可能性')
print('=' * 80)
print('  out_s が定義できるのは 母馬優先対象馬のみ:', int(S.dam_prio.sum()), '/', len(S),
      '(%.0f%%)' % (S.dam_prio.mean() * 100))
print('  非対象 %d頭は out_s が欠測 → パネルの %.0f%% を採点できない'
      % ((S.dam_prio == 0).sum(), (1 - S.dam_prio.mean()) * 100))
p = S[S.dam_prio == 1].copy()
for tag, d in [('全対象', p), ('確定除外', p[~((p.year <= 2023) & (p['rank'] == '確定'))])]:
    print('  --', tag, 'n=%d' % len(d))
    cmp(d, 'win_jra', 'out_s', tag)
    cmp(d, 'ret1', 'out_s', tag)
print('\n  out_s のカテゴリ別頭数（片側20頭未満か）:')
print(p.groupby(p['out_s']).size().rename('n').to_string())

print('\n' + '=' * 80)
print('■ J. 多重検定の分母: このプロジェクトで試された仮説の規模')
print('=' * 80)
files = sorted(glob.glob(os.path.join(BASE, 'probe_*.py')))
print('  probe_*.py のファイル数:', len(files))
tot = 0
for f in files:
    src = open(f, encoding='utf-8').read()
    n = len(re.findall(r"reg\(|zscore\(|logit\(", src))
    tot += n
print('  reg/logit/zscore の呼び出し箇所の合計: %d 箇所（各呼び出しが1〜6個のz値を出す）' % tot)
print('  backtest.py の CANDIDATES だけで閾値候補は 35 通り')

# -*- coding: utf-8 -*-
"""dam_club(母馬優先対象＝母がキャロット在籍馬) の頑健性チェック。"""
import io, os, sys
import numpy as np
import pandas as pd
from analyze5 import load, logit, design

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 200)
BASE = os.path.dirname(os.path.abspath(__file__))


def prep():
    df = load(central_only=True)
    r = pd.read_csv(os.path.join(BASE, '..', '..', 'data', 'dam_age_rank.csv'), encoding='utf-8-sig')
    keys = set(zip(r['募集年度'].astype(int), r['募集番号'].astype(int)))
    lot = {(int(a), int(b)): int(c) for a, b, c in
           zip(r['募集年度'], r['募集番号'], r['母馬優先枠で抽選'])}
    df['no_i'] = pd.to_numeric(df['no'], errors='coerce')
    df['dam_club'] = [1 if (y, n) in keys else 0 for y, n in zip(df['year'], df['no_i'])]
    df.loc[df['year'] == 2020, 'dam_club'] = np.nan
    df['lot'] = [lot.get((y, n)) for y, n in zip(df['year'], df['no_i'])]
    df['dam_k'] = df['dam'].astype(str).str.strip()
    cnt = df.groupby('dam_k').size()
    df['multi'] = (df['dam_k'].map(cnt) >= 2).astype(int)
    return df


def zz(df, cols, tgt, want, tag):
    sub = df.dropna(subset=list(cols) + [tgt])
    X, names = design(sub, list(cols))
    t = logit(X, sub[tgt], names)
    r = t[t['変数'] == want]
    print('  %-40s z=%+.2f OR=%.2f n=%d' % (tag, r['z'].iloc[0], r['オッズ比'].iloc[0], len(sub)))


def sec(t):
    print('\n' + '=' * 78 + '\n[ ' + t + ' ]\n' + '=' * 78)


df = prep()
d = df[df['dam_club'].notna()].copy()

sec('F. 回収率のしきい値を変えても効くか（ret1=回収>=1 だけの偶然か）')
for th in [0.3, 0.5, 0.8, 1.0, 1.5, 2.0, 3.0]:
    d['y'] = (d['ret'] >= th).astype(float)
    d.loc[d['ret'].isna(), 'y'] = np.nan
    print('  回収>=%.1f: 該当群 %.3f / 非該当群 %.3f' %
          (th, d[d['dam_club'] == 1]['y'].mean(), d[d['dam_club'] == 0]['y'].mean()), end='')
    zz(d, ['dam_club'], 'y', 'dam_club', '')

sec('G. 中央勝ち上がり以外の「走った度合い」')
for tgt, lab in [('win_jra', '中央1勝'), ('win_all', '中+地1勝')]:
    zz(d, ['dam_club'], tgt, 'dam_club', lab)
d['multi_win'] = (pd.to_numeric(d['wins'], errors='coerce') >= 2).astype(float)
zz(d, ['dam_club'], 'multi_win', 'dam_club', '2勝以上')
d['g'] = (pd.to_numeric(d['graded'], errors='coerce') >= 1).astype(float)
print('  重賞勝ち: 該当 %d/%d  非該当 %d/%d' %
      (d[d['dam_club'] == 1]['g'].sum(), (d['dam_club'] == 1).sum(),
       d[d['dam_club'] == 0]['g'].sum(), (d['dam_club'] == 0).sum()))
d['p1000'] = (pd.to_numeric(d['prize'], errors='coerce') >= 2000).astype(float)
print('  賞金2000万以上: 該当 %.3f / 非該当 %.3f' %
      (d[d['dam_club'] == 1]['p1000'].mean(), d[d['dam_club'] == 0]['p1000'].mean()), end='')
zz(d, ['dam_club'], 'p1000', 'dam_club', '')

sec('H. 外れ値を落としても効くか（回収率上位を除外して賞金で見る）')
for k in [0, 3, 5, 10]:
    s = d.sort_values('ret', ascending=False).iloc[k:]
    print('  上位%2d頭除外 ret1:' % k, end='')
    zz(s, ['dam_club'], 'ret1', 'dam_club', '')

sec('I. multi(同母きょうだい) と dam_club は同じものか')
print(pd.crosstab(d['dam_club'], d['multi']).to_string())
zz(d, ['dam_club', 'multi'], 'ret1', 'dam_club', 'dam_club (multi同時)')
zz(d, ['dam_club', 'multi'], 'ret1', 'multi', 'multi (dam_club同時)')

sec('J. 母馬優先枠で実際に抽選になった馬（＝人気）だけの効果')
d['lot'] = d['lot'].fillna(0)
print(d.groupby('lot').agg(頭数=('ret1', 'size'), 中央勝上=('win_jra', 'mean'),
                           回収1=('ret1', 'mean'), 総額=('total_man', 'mean')).round(3).to_string())
zz(d, ['lot'], 'ret1', 'lot', '母馬優先枠で抽選になった')
zz(d, ['lot'], 'win_jra', 'lot', '母馬優先枠で抽選になった')

sec('K. 2026年度の該当頭数（運用可能性）')
b = pd.read_csv(os.path.join(BASE, '..', '..', 'data', 'bosyu_2026.csv'), encoding='utf-8-sig')
print(b.columns.tolist())
for c in b.columns:
    if '優先' in c:
        print(b[c].value_counts(dropna=False).to_string())

# -*- coding: utf-8 -*-
"""probe_dam.py の追試。母馬優先対象(dam_club)の年度安定性・交絡・多重検定の点検。"""
import io, os, sys
import numpy as np
import pandas as pd
from analyze5 import load, logit, design

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 200)
BASE = os.path.dirname(os.path.abspath(__file__))


def prep():
    df = load(central_only=True)
    df['n_foals'] = pd.to_numeric(df['n_foals'], errors='coerce')
    df.loc[df['year'] >= 2023, 'n_foals'] = np.nan
    p = os.path.join(BASE, '..', '..', 'data', 'dam_age_rank.csv')
    r = pd.read_csv(p, encoding='utf-8-sig')
    keys = set(zip(r['募集年度'].astype(int), r['募集番号'].astype(int)))
    df['no_i'] = pd.to_numeric(df['no'], errors='coerce')
    df['dam_club'] = [1 if (y, n) in keys else 0 for y, n in zip(df['year'], df['no_i'])]
    df.loc[df['year'] == 2020, 'dam_club'] = np.nan
    return df


def z_of(df, cols, tgt, want):
    sub = df.dropna(subset=list(cols) + [tgt])
    X, names = design(sub, list(cols))
    t = logit(X, sub[tgt], names)
    r = t[t['変数'] == want]
    return float(r['z'].iloc[0]), float(r['オッズ比'].iloc[0]), len(sub)


def sec(t):
    print('\n' + '=' * 78 + '\n[ ' + t + ' ]\n' + '=' * 78)


df = prep()
df['dam_k'] = df['dam'].astype(str).str.strip()
cnt = df.groupby('dam_k').size()
df['multi'] = (df['dam_k'].map(cnt) >= 2).astype(int)

sec('A. 母がクラブ在籍馬(dam_club) x 回収>=1 の年度安定性')
d4 = df[df['dam_club'].notna()].copy()
print(d4.pivot_table(index='dam_club', columns='year', values='ret1',
                     aggfunc=['mean', 'size']).round(3).to_string())
print('\n年度別 単年ロジット（年度ダミーなし・切片のみ）')
for y in sorted(d4['year'].unique()):
    s = d4[d4['year'] == y]
    a = s[s['dam_club'] == 1]['ret1']
    b = s[s['dam_club'] == 0]['ret1']
    print('  %d: 該当 %.3f (n=%d) / 非該当 %.3f (n=%d)  差=%+.3f'
          % (y, a.mean(), len(a), b.mean(), len(b), a.mean() - b.mean()))
print('\nleave-one-year-out（1年ずつ抜いてz値が持つか / ret1）')
for y in sorted(d4['year'].unique()):
    s = d4[d4['year'] != y]
    z, orr, n = z_of(s, ['dam_club'], 'ret1', 'dam_club')
    print('  %d除外: z=%+.2f OR=%.2f n=%d' % (y, z, orr, n))

sec('B. dam_club を既存3基準と一緒に入れる')
d4['w430n'] = pd.to_numeric(d4['w430'], errors='coerce')
d4['p2539'] = d4['total_man'].between(2500, 3999).astype(int)
for tgt in ['win_jra', 'ret1']:
    sub = d4.dropna(subset=['dam_club', 'w430n', tgt])
    X, names = design(sub, ['dam_club', 'male', 'p2539', 'w430n'])
    print('-- %s n=%d' % (tgt, len(sub)))
    t = logit(X, sub[tgt], names)
    print(t[~t['変数'].astype(str).str.startswith('年度')].round(3).to_string(index=False))

sec('C. dam_club は他の変数と相関しているか')
print(d4.groupby('dam_club').agg(
    牡=('male', 'mean'), ノーザン=('nf', 'mean'), 馬体重=('weight', 'mean'),
    総額=('total_man', 'mean'), 母年齢=('dam_age', 'mean'),
    出走=('starts', 'mean'), 賞金=('prize', 'mean')).round(2).to_string())
print('\n回収率そのもの（分母=価格）')
print(d4.groupby('dam_club')['ret'].describe().round(3).to_string())
print('\n賞金(prize)を目的にした線形比較 年度別平均')
print(d4.pivot_table(index='dam_club', columns='year', values='prize', aggfunc='mean').round(0).to_string())

sec('D. パネル内に同母きょうだいが居る(multi) の年度安定性 / ret1')
print(df.pivot_table(index='multi', columns='year', values='ret1',
                     aggfunc=['mean', 'size']).round(3).to_string())
for y in sorted(df['year'].unique()):
    s = df[df['year'] != y]
    z, orr, n = z_of(s, ['multi'], 'ret1', 'multi')
    print('  %d除外: z=%+.2f OR=%.2f n=%d' % (y, z, orr, n))
z, orr, n = z_of(df.dropna(subset=['total_man']), ['multi', 'price_rel'], 'ret1', 'multi')
print('  価格(price_rel)を入れると: z=%+.2f OR=%.2f n=%d' % (z, orr, n))

sec('E. 母の父(bms) — roster から補完して大枠だけ')
r1 = pd.read_csv(os.path.join(BASE, '..', 'datasets', 'roster.csv'), encoding='utf-8-sig')
r2 = pd.read_csv(os.path.join(BASE, '..', 'datasets', 'roster_new_raw.csv'), encoding='utf-8-sig')
bms = {}
for r in (r1, r2):
    for y, n, b in zip(r['year'], r['no'], r['bms']):
        bms[(int(y), int(n))] = b
df['bms'] = [bms.get((y, n)) for y, n in zip(df['year'], df['no_i'])]
print('bms 取得率: %.1f%%' % (df['bms'].notna().mean() * 100))
g = df.dropna(subset=['bms']).groupby('bms').agg(
    頭数=('win_jra', 'size'), 中央勝上=('win_jra', 'mean'), 回収1=('ret1', 'mean'))
print(g[g['頭数'] >= 8].sort_values('中央勝上', ascending=False).round(3).to_string())
# 米国型BMS（サンデー系でない大種牡馬）などの粗いグルーピングは恣意的なので、
# ここでは「BMSがサンデーサイレンス系か」だけを機械的に見る
ss = ['ディープインパクト', 'ダイワメジャー', 'ハーツクライ', 'ステイゴールド', 'キングカメハメハ',
      'マンハッタンカフェ', 'ゼンノロブロイ', 'アグネスタキオン', 'ネオユニヴァース', 'フジキセキ',
      'スペシャルウィーク', 'ハートレイ']
df['bms_jp'] = df['bms'].isin(ss).astype(float)
df.loc[df['bms'].isna(), 'bms_jp'] = np.nan
for tgt in ['win_jra', 'ret1']:
    z, orr, n = z_of(df.dropna(subset=['bms_jp']), ['bms_jp'], tgt, 'bms_jp')
    print('  BMS=日本主流種牡馬 / %s: z=%+.2f OR=%.2f n=%d' % (tgt, z, orr, n))

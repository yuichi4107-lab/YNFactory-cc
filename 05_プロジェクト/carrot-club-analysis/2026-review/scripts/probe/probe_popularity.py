# -*- coding: utf-8 -*-
"""切り口: 募集時点の人気（他会員の評価）が成績を予測するか。

使うデータ
  ../../data/dam_age_rank.csv   2021〜2025年度の母馬優先対象馬の抽選ランク（募集年度・募集番号つき）
  ../../data/carrot_interim.csv 2024・2025年度の締切前日の申込口数内訳（総申込200口以上の馬のみ）
panel5 は 2020〜2024年度なので、重なるのは 2021〜2024年度。
"""
import io, os, sys
import numpy as np
import pandas as pd
from analyze5 import load, logit, design

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 200)
BASE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(BASE, '..', '..', 'data')

# 枠外（母馬優先権を持たない一般層）の競争の厳しさ A(最も人気)〜E(残口)
RANK_LEGACY_OUT = {"A": "A", "B": "C", "C": "A", "D": "B", "E": "C",
                   "F": "A", "G": "B", "H": "C", "I": "D", "J": "D", "確定": "E"}
OUT_SCORE = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1}


def out_rank(year, rank):
    rank = str(rank)
    if year <= 2023:
        return RANK_LEGACY_OUT.get(rank, None)
    return rank[1] if len(rank) == 2 else None


df = load(central_only=True)
df['no_i'] = pd.to_numeric(df['no'], errors='coerce')

rk = pd.read_csv(os.path.join(D, 'dam_age_rank.csv'), encoding='utf-8-sig')
rk.columns = ['year', 'no', 'dam', 'dam_born', 'dam_age_r', 'dam_season', 't', 'rank', 'pool_filled']
rk['out'] = [out_rank(y, r) for y, r in zip(rk['year'], rk['rank'])]
rk['out_s'] = rk['out'].map(OUT_SCORE)

print('=' * 78)
print('■ 0. 突合できた頭数')
print('=' * 78)
print('panel5(中央400口) 年度別頭数:')
print(df.groupby('year').size().to_string())
print()
m = df.merge(rk[['year', 'no', 'rank', 'out', 'out_s', 'pool_filled', 'dam_age_r']],
             left_on=['year', 'no_i'], right_on=['year', 'no'], how='left', suffixes=('', '_r'))
m['dam_prio'] = m['rank'].notna().astype(int)
sub = m[m['year'].between(2021, 2024)].copy()
print('dam_age_rank.csv 側の行数（2021〜2024年度）:', (rk['year'] <= 2024).sum())
print('panel5 と (年度,募集番号) で突合できた頭数:')
print(sub.groupby('year')['dam_prio'].agg(['size', 'sum']).rename(
    columns={'size': 'panel5中央頭数', 'sum': '突合(母馬優先対象)'}).to_string())
print('突合できなかったランク行（地方馬など）:')
mm = rk[rk['year'] <= 2024].merge(df[['year', 'no_i']], left_on=['year', 'no'],
                                  right_on=['year', 'no_i'], how='left')
print(mm[mm['no_i'].isna()][['year', 'no', 'dam', 'rank']].to_string())
print()

sub = sub.dropna(subset=['win_jra']).copy()
print('検定に使える（win_jra 非欠測）:', len(sub), '頭  うち母馬優先対象', int(sub['dam_prio'].sum()))
print()


def show(name, d, col, cols=('win_jra', 'ret1')):
    print('-' * 70)
    print(f'【{name}】 n={len(d)}')
    g = d.groupby(col, dropna=False)
    t = pd.DataFrame({'頭数': g.size(),
                      '勝上(中央)%': (g['win_jra'].mean() * 100).round(0),
                      '回収≥1 %': (g['ret1'].mean() * 100).round(0),
                      '回収中央値': g['ret'].median().round(2),
                      '重賞': g['graded'].sum()})
    print(t.to_string())
    print('年度別 勝上(中央)%:')
    print((d.pivot_table(index=col, columns='year', values='win_jra',
                         aggfunc=['mean', 'size'])* 1).round(2).to_string())


def reg(d, cols, ys=('win_jra', 'ret1')):
    for y in ys:
        dd = d.dropna(subset=list(cols) + [y])
        X, names = design(dd, list(cols))
        r = logit(X, dd[y], names)
        print(f'  [{y}] n={len(dd)}')
        print(r[~r['変数'].astype(str).str.startswith('年度')].to_string(index=False))


print('=' * 78)
print('■ 1. 母馬優先対象かどうか（母がクラブ在籍）')
print('=' * 78)
show('母馬優先対象=1', sub, 'dam_prio')
reg(sub, ['dam_prio'])

print()
print('=' * 78)
print('■ 2. 母馬優先枠が埋まったか（母馬の出資者たちの評価）— 対象馬のみ')
print('=' * 78)
p = sub[sub['dam_prio'] == 1].copy()
show('母馬優先枠が埋まった=1', p, 'pool_filled')
reg(p, ['pool_filled'])

print()
print('=' * 78)
print('■ 3. 枠外ランク（＝一般会員全体での人気。A最上位〜E残口）— 対象馬のみ')
print('=' * 78)
show('枠外ランク', p, 'out')
p['out_top'] = p['out'].isin(['A', 'B']).astype(int)
p['out_low'] = p['out'].isin(['D', 'E']).astype(int)
show('枠外A/B（上位人気）', p, 'out_top')
print('  連続スコア out_s (A=5..E=1) の回帰:')
reg(p.dropna(subset=['out_s']), ['out_s'])
print('  上位人気ダミー(A/B) の回帰:')
reg(p, ['out_top'])
print('  下位人気ダミー(D/E) の回帰:')
reg(p, ['out_low'])
print('  募集総額をコントロールしたうえで out_s:')
reg(p.dropna(subset=['out_s']), ['out_s', 'price_pct'])

print()
print('=' * 78)
print('■ 4. 中間発表（締切前日の申込口数）— 2024年度のみ panel5 と重なる')
print('=' * 78)
it = pd.read_csv(os.path.join(D, 'carrot_interim.csv'), encoding='utf-8-sig')
it.columns = ['year', 'no', 'name', 'kubun', 'total_app', 'dp_top', 'dp_gen', 'top_only']
print('中間発表 年度別行数:')
print(it.groupby('year').size().to_string())
i24 = it[it['year'] == 2024]
d24 = df[(df['year'] == 2024)].dropna(subset=['win_jra']).copy()
i24b = i24[['year', 'no', 'total_app', 'kubun']].rename(columns={'no': 'no_i'})
d24 = d24.merge(i24b, on=['year', 'no_i'], how='left')
d24['listed'] = d24['total_app'].notna().astype(int)
print(f'2024年度 panel5中央 {len(d24)}頭 のうち中間発表に載った(総申込200口以上) {int(d24["listed"].sum())}頭')
print('※2024年度は現3歳。成績はまだ積み上がる途中なので水準は低い')
show('中間発表に掲載=1（総申込200口以上＝人気上位）', d24, 'listed')
hi = d24[d24['listed'] == 1].copy()
hi['app_hi'] = (hi['total_app'] >= hi['total_app'].median()).astype(int)
print(f'  掲載馬内 総申込の中央値 {hi["total_app"].median():.0f}口')
show('掲載馬内で総申込が中央値以上', hi, 'app_hi')
print('  掲載馬内 総申込(連続) と win_jra の相関:',
      round(np.corrcoef(hi['total_app'], hi['win_jra'])[0, 1], 3),
      ' ret1:', round(np.corrcoef(hi['total_app'], hi['ret1'])[0, 1], 3))
print('  勝上馬の総申込 中央値:', hi[hi['win_jra'] == 1]['total_app'].median(),
      ' 未勝利:', hi[hi['win_jra'] == 0]['total_app'].median())

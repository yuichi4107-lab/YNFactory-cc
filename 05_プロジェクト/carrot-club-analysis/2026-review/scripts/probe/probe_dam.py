# -*- coding: utf-8 -*-
"""母まわりの未検定変数を検定する（読み取り専用・新規ファイル）。"""
import io, json, os, sys
import numpy as np
import pandas as pd
from analyze5 import load, logit, design

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 200)
BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')


def prep():
    df = load(central_only=True)
    df['n_foals'] = pd.to_numeric(df['n_foals'], errors='coerce')
    # 2023/2024の n_foals は foal_order.json が全件1で取得失敗 -> 欠測扱い
    df.loc[df['year'] >= 2023, 'n_foals'] = np.nan
    # 母馬優先対象（母がキャロット在籍馬）
    p = os.path.join(BASE, '..', '..', 'data', 'dam_age_rank.csv')
    r = pd.read_csv(p, encoding='utf-8-sig')
    keys = set(zip(r['募集年度'].astype(int), r['募集番号'].astype(int)))
    df['no_i'] = pd.to_numeric(df['no'], errors='coerce')
    df['dam_club'] = [1 if (y, n) in keys else 0 for y, n in zip(df['year'], df['no_i'])]
    df.loc[df['year'] == 2020, 'dam_club'] = np.nan       # 2020はファイルに無い
    tt = {(int(a), int(b)): c for a, b, c in zip(r['募集年度'], r['募集番号'], r['経過年数t'])}
    df['dam_t'] = [tt.get((y, n)) for y, n in zip(df['year'], df['no_i'])]
    return df


def show(df, col, label, extra=()):
    cols = [col] + list(extra)
    for tgt in ['win_jra', 'ret1']:
        sub = df.dropna(subset=cols + [tgt])
        if len(sub) < 30 or sub[col].nunique() < 2:
            print('  [%s] n不足 (%d)' % (label, len(sub)))
            return
        X, names = design(sub, cols)
        t = logit(X, sub[tgt], names)
        print('-- %s / %s n=%d' % (label, tgt, len(sub)))
        print(t[~t['変数'].astype(str).str.startswith('年度')].round(3).to_string(index=False))


def byyear(df, col, label, tgt='win_jra'):
    sub = df.dropna(subset=[col, tgt])
    piv = sub.pivot_table(index=col, columns='year', values=tgt,
                          aggfunc=['mean', 'size'], observed=True)
    m, s = piv['mean'] * 100, piv['size']
    print('\n[%s] 年度別 %s%% (頭数)' % (label, tgt))
    print('  ' + ' ' * 12 + ''.join('%12s' % y for y in m.columns))
    for i in m.index:
        cells = []
        for y in m.columns:
            mv, nv = m.loc[i, y], s.loc[i, y]
            cells.append('%5.0f%%(%2.0f)' % (mv, nv) if pd.notna(mv) else '%9s' % '-')
        print('  %-12s' % str(i) + ''.join('%12s' % c for c in cells))


def sec(t):
    print('\n' + '=' * 78 + '\n[ ' + t + ' ]\n' + '=' * 78)


df = prep()
print('中央400口 n=%d  win_jra有効=%d' % (len(df), df['win_jra'].notna().sum()))

# ---------------------------------------------------------------- 1. 何番仔
sec('1. 何番仔 n_foals（2020-2022のみ有効。2023/24はデータ破損で欠測）')
print(df.groupby('year')['n_foals'].agg(['count', 'median', 'max']).to_string())
d3 = df[df['n_foals'].notna()].copy()
d3['first'] = (d3['n_foals'] == 1).astype(int)
d3['nf_bin'] = pd.cut(d3['n_foals'], [0, 1, 2, 4, 6, 99],
                      labels=['1(初仔)', '2', '3-4', '5-6', '7+'])
print(d3.groupby('nf_bin', observed=True).agg(
    頭数=('win_jra', 'size'), 中央勝上=('win_jra', 'mean'),
    回収1=('ret1', 'mean'), 回収中央=('ret', 'median')).round(3).to_string())
byyear(d3, 'nf_bin', '何番仔')
show(d3, 'n_foals', '何番仔(連続)')
show(d3, 'first', '初仔ダミー')
d3['nf2'] = d3['n_foals'] ** 2
show(d3, 'n_foals', '何番仔(連続)+2乗', extra=['nf2'])
print('\n-- 母年齢と同時に入れる（どちらが残るか）')
show(d3, 'n_foals', '何番仔', extra=['dam_age'])
show(d3, 'first', '初仔', extra=['dam811'])
print('\n-- 依頼者仮説: 母年齢+何番仔 が 10-14 でピーク')
d3['sumv'] = d3['dam_age'] + d3['n_foals']
d3['peak'] = d3['sumv'].between(10, 14).astype(int)
print(d3.groupby(pd.cut(d3['sumv'], [0, 9, 14, 19, 99]), observed=True).agg(
    頭数=('win_jra', 'size'), 中央勝上=('win_jra', 'mean'),
    回収1=('ret1', 'mean')).round(3).to_string())
show(d3, 'peak', '母年齢+何番仔=10-14')
byyear(d3, 'peak', '和10-14')

# ------------------------------------------------------- 2. 同一母きょうだい
sec('2. 同じ母のきょうだい（母単位クラスタ効果）')
df['dam_k'] = df['dam'].astype(str).str.strip()
cnt = df.groupby('dam_k').size()
print('パネル内の同一母出現数の分布:')
print(cnt.value_counts().sort_index().to_string())
print('2頭以上出ている母: %d頭 -> 該当馬 %d頭' % ((cnt >= 2).sum(), int(cnt[cnt >= 2].sum())))
df['sib_n'] = df['dam_k'].map(cnt)
df['multi'] = (df['sib_n'] >= 2).astype(int)
show(df, 'multi', 'パネル内に同母きょうだいが居る')

recs = []
for k, g in df.groupby('dam_k'):
    g = g.sort_values('year')
    for i, row in g.iterrows():
        prev = g[g['year'] < row['year']]
        recs.append((i, len(prev),
                     prev['win_jra'].max() if len(prev) else np.nan,
                     prev['win_jra'].mean() if len(prev) else np.nan,
                     prev['ret'].max() if len(prev) else np.nan))
pr = pd.DataFrame(recs, columns=['idx', 'prev_n', 'prev_win', 'prev_rate', 'prev_ret']).set_index('idx')
df = df.join(pr)
print('\n上の仔がパネル内に居る馬: %d頭' % int((df['prev_n'] > 0).sum()))
sub = df[df['prev_n'] > 0].dropna(subset=['prev_win', 'win_jra'])
print(sub.groupby('prev_win').agg(頭数=('win_jra', 'size'), 中央勝上=('win_jra', 'mean'),
                                  回収1=('ret1', 'mean')).round(3).to_string())
print('（参考）上の仔がパネルに居ない馬の中央勝上=%.3f n=%d'
      % (df[df['prev_n'] == 0]['win_jra'].mean(), (df['prev_n'] == 0).sum()))
show(sub, 'prev_win', '上の仔が中央勝上（該当馬のみ）')
byyear(sub, 'prev_win', '上の仔が中央勝上')
print('\n-- 上の仔の回収率>=1 だったか')
sub2 = sub.dropna(subset=['prev_ret']).copy()
sub2['prev_ret1'] = (sub2['prev_ret'] >= 1).astype(int)
print(sub2.groupby('prev_ret1').agg(頭数=('win_jra', 'size'), 中央勝上=('win_jra', 'mean'),
                                    回収1=('ret1', 'mean')).round(3).to_string())
show(sub2, 'prev_ret1', '上の仔が回収>=1')

# ------------------------------------------------------- 3. 母馬優先対象
sec('3. 母がキャロット在籍馬（母馬優先対象・2021-2024）')
d4 = df[df['dam_club'].notna()].copy()
print(d4.groupby(['year', 'dam_club']).agg(頭数=('win_jra', 'size'),
      中央勝上=('win_jra', 'mean'), 回収1=('ret1', 'mean')).round(3).to_string())
print(d4.groupby('dam_club').agg(頭数=('win_jra', 'size'), 中央勝上=('win_jra', 'mean'),
      回収1=('ret1', 'mean'), 回収中央=('ret', 'median'),
      総額中央=('total_man', 'median'), 母年齢中央=('dam_age', 'median')).round(3).to_string())
show(d4, 'dam_club', '母がクラブ在籍馬')
show(d4, 'dam_club', '母がクラブ在籍馬+母年齢+価格', extra=['dam_age', 'price_rel'])
byyear(d4, 'dam_club', '母がクラブ在籍馬')

# ------------------------------------------------------- 4. 母年齢の形
sec('4. 母年齢の入れ方（二値の切り方が悪いだけではないか）')
d5 = df.dropna(subset=['dam_age', 'win_jra']).copy()
print(d5.groupby(pd.cut(d5['dam_age'], [0, 5, 7, 9, 11, 13, 15, 30]), observed=True).agg(
    頭数=('win_jra', 'size'), 中央勝上=('win_jra', 'mean'), 回収1=('ret1', 'mean'),
    回収中央=('ret', 'median')).round(3).to_string())
show(d5, 'dam_age', '母年齢(連続)')
d5['da2'] = d5['dam_age'] ** 2
show(d5, 'dam_age', '母年齢 連続+2乗', extra=['da2'])
print('\n-- 二値の切り方を総当たり（多重検定に注意）')
for lo, hi in [(6, 10), (7, 11), (8, 11), (8, 12), (9, 12), (6, 12), (5, 9), (10, 14), (7, 12)]:
    d5['b'] = d5['dam_age'].between(lo, hi).astype(int)
    s = d5.dropna(subset=['b', 'win_jra'])
    X, names = design(s, ['b'])
    z = logit(X, s['win_jra'], names)
    z = z[z['変数'] == 'b']['z'].iloc[0]
    s2 = d5.dropna(subset=['b', 'ret1'])
    X2, n2 = design(s2, ['b'])
    z2 = logit(X2, s2['ret1'], n2)
    z2 = z2[z2['変数'] == 'b']['z'].iloc[0]
    print('  母年齢 %2d-%2d歳: 該当=%3d  z(win_jra)=%+.2f  z(ret1)=%+.2f'
          % (lo, hi, int(d5['b'].sum()), z, z2))
d5['old14'] = (d5['dam_age'] >= 14).astype(int)
show(d5, 'old14', '母14歳以上')
d5['young6'] = (d5['dam_age'] <= 6).astype(int)
show(d5, 'young6', '母6歳以下')
byyear(d5.assign(b=pd.cut(d5['dam_age'], [0, 7, 9, 11, 13, 30])), 'b', '母年齢帯')

# ------------------------------------------------------- 5. 経過年数
sec('5. 参考: 母の募集からの経過年数 dam_t（母馬優先対象のみ）')
d6 = df.dropna(subset=['dam_t', 'win_jra']).copy()
d6['dam_t'] = pd.to_numeric(d6['dam_t'], errors='coerce')
print(d6.groupby(pd.cut(d6['dam_t'], [0, 8, 11, 14, 99]), observed=True).agg(
    頭数=('win_jra', 'size'), 中央勝上=('win_jra', 'mean'), 回収1=('ret1', 'mean')).round(3).to_string())
show(d6, 'dam_t', '母の募集からの経過年数')

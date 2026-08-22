# -*- coding: utf-8 -*-
"""敵対的検証: クラブ内人気（母馬優先対象=dam_prio / 枠外ランク=out_s）を潰しにいく。"""
import io, os, sys
import numpy as np
import pandas as pd
from analyze5 import load, logit, design
from backtest import auc

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 220)
BASE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(BASE, '..', '..', 'data')

RANK_LEGACY_OUT = {"A": "A", "B": "C", "C": "A", "D": "B", "E": "C",
                   "F": "A", "G": "B", "H": "C", "I": "D", "J": "D", "確定": "E"}
OUT_SCORE = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1}


def out_rank(y, r):
    r = str(r)
    return RANK_LEGACY_OUT.get(r, None) if y <= 2023 else (r[1] if len(r) == 2 else None)


df = load(central_only=True)
df['no_i'] = pd.to_numeric(df['no'], errors='coerce')
df['n_foals_i'] = pd.to_numeric(df['n_foals'], errors='coerce')
rk = pd.read_csv(os.path.join(D, 'dam_age_rank.csv'), encoding='utf-8-sig')
rk.columns = ['year', 'no', 'dam', 'dam_born', 'dam_age_r', 'dam_season', 't', 'rank', 'pool_filled']
rk['out'] = [out_rank(y, r) for y, r in zip(rk['year'], rk['rank'])]
rk['out_s'] = rk['out'].map(OUT_SCORE)
m = df.merge(rk[['year', 'no', 'rank', 'out', 'out_s', 'pool_filled']],
             left_on=['year', 'no_i'], right_on=['year', 'no'], how='left', suffixes=('', '_r'))
m['dam_prio'] = m['rank'].notna().astype(int)
m['price2539'] = m['total_man'].between(2500, 3999).astype(int)
m['w420'] = (m['weight'] >= 420).astype(float)
m.loc[m['weight'].isna(), 'w420'] = np.nan

S = m[m['year'].between(2021, 2024)].copy()

print('=' * 80)
print('■ 1. 再現: 報告された基本数値')
print('=' * 80)
s = S.dropna(subset=['win_jra']).copy()
print('n=%d  dam_prio=1: %d  =0: %d' % (len(s), s.dam_prio.sum(), (1 - s.dam_prio).sum()))
for g, d in s.groupby('dam_prio'):
    print(' dam_prio=%d n=%d 勝上%.1f%% 回収>=1 %.1f%% 中央値%.3f 平均%.3f 90%%点%.3f 重賞%d'
          % (g, len(d), d.win_jra.mean() * 100, d.ret1.mean() * 100, d.ret.median(),
             d.ret.mean(), d.ret.quantile(.9), d.graded.sum()))
print('\n年度別:')
for y in [2021, 2022, 2023, 2024]:
    for g in [1, 0]:
        d = s[(s.year == y) & (s.dam_prio == g)]
        print('  %d prio=%d n=%3d 勝上%.1f%% ret1 %.1f%% med%.3f 重賞%d'
              % (y, g, len(d), d.win_jra.mean() * 100, d.ret1.mean() * 100, d.ret.median(), d.graded.sum()))


def reg(d, cols, y, tag=''):
    dd = d.dropna(subset=list(cols) + [y])
    X, names = design(dd, list(cols))
    r = logit(X, dd[y], names)
    r = r[~r['変数'].astype(str).str.startswith('年度')]
    print('  %s[%s] n=%d  ' % (tag, y, len(dd)) + ' | '.join(
        '%s: b=%.3f z=%+.2f OR=%.2f' % (a, b, z, o)
        for a, b, z, o in zip(r['変数'], r['係数'], r['z'], r['オッズ比'])))


print('\n再現: 回帰')
reg(s, ['dam_prio'], 'ret1', '単独 ')
reg(s, ['dam_prio'], 'win_jra', '単独 ')
reg(s, ['dam_prio', 'male', 'price2539', 'w420'], 'ret1', '+既存3 ')
reg(s, ['dam_prio', 'male', 'price2539', 'w420'], 'win_jra', '+既存3 ')

print('\n' + '=' * 80)
print('■ 2. 交絡: n_foals(何番仔) と dam_age')
print('=' * 80)
print(s.groupby('dam_prio')[['total_man', 'price_pct', 'weight', 'male', 'nf', 'dam_age', 'n_foals_i']].mean().round(2).to_string())
reg(s, ['dam_prio', 'dam_age', 'n_foals_i'], 'ret1', '母年齢+産次 ')
reg(s, ['dam_prio', 'dam_age', 'n_foals_i', 'male', 'price2539', 'w420'], 'ret1', '全部 ')
print('初仔(n_foals==1)比率:', s.groupby('dam_prio')['n_foals_i'].apply(lambda x: (x == 1).mean()).round(3).to_dict())

print('\n' + '=' * 80)
print('■ 3. 外れ値・重賞依存')
print('=' * 80)
for k in [0, 3, 5, 8, 12]:
    d = s.sort_values('ret', ascending=False).iloc[k:] if k else s
    dd = d.dropna(subset=['ret1'])
    X, names = design(dd, ['dam_prio'])
    r = logit(X, dd['ret1'], names)
    print('  回収上位%2d頭除外 n=%d z=%+.2f OR=%.2f' % (k, len(dd), r.iloc[-1]['z'], r.iloc[-1]['オッズ比']))
print('  重賞出走馬(graded>0)を全部除いた場合:')
reg(s[s['graded'].fillna(0) == 0], ['dam_prio'], 'ret1', '重賞除外 ')

print('\n' + '=' * 80)
print('■ 4. LOYO（その年を使わずにその年を当てる）')
print('=' * 80)


def loyo(data, cols, target, years):
    out = {}
    allp, ally = [], []
    for y in years:
        tr = data[data.year != y].dropna(subset=list(cols) + [target])
        te = data[data.year == y].dropna(subset=list(cols) + [target])
        if len(te) < 5 or te[target].nunique() < 2:
            out[y] = np.nan
            continue
        Xtr = np.column_stack([np.ones(len(tr))] + [tr[c].astype(float).values for c in cols])
        Xte = np.column_stack([np.ones(len(te))] + [te[c].astype(float).values for c in cols])
        b = logit(Xtr, tr[target], ['c'] + list(cols))['係数'].values
        p = Xte @ b
        out[y] = auc(te[target], p)
        allp.append(p)
        ally.append(te[target].values)
    ov = auc(np.concatenate(ally), np.concatenate(allp)) if allp else np.nan
    return out, ov


def loyo_score(data, cols, target, years):
    out = {}
    allp, ally = [], []
    for y in years:
        te = data[data.year == y].dropna(subset=list(cols) + [target])
        if len(te) < 5 or te[target].nunique() < 2:
            out[y] = np.nan
            continue
        p = te[list(cols)].astype(float).sum(axis=1).values
        out[y] = auc(te[target], p)
        allp.append(p)
        ally.append(te[target].values)
    return out, auc(np.concatenate(ally), np.concatenate(allp))


YRS = [2021, 2022, 2023, 2024]
base = ['male', 'price2539', 'w420']
for target in ['win_jra', 'ret1']:
    print('\n-- 目的変数 %s （2021〜2024, 中央400口）' % target)
    for tag, cols in [('既存3のみ', base), ('既存3+dam_prio', base + ['dam_prio'])]:
        o, ov = loyo(S, cols, target, YRS)
        print('   [回帰LOYO] %-16s 全体AUC=%.3f  ' % (tag, ov) + ' '.join('%d:%.3f' % (y, o[y]) for y in YRS))
    for tag, cols in [('既存3のみ', base), ('既存3+dam_prio', base + ['dam_prio'])]:
        o, ov = loyo_score(S, cols, target, YRS)
        print('   [素点     ] %-16s 全体AUC=%.3f  ' % (tag, ov) + ' '.join('%d:%.3f' % (y, o[y]) for y in YRS))

print('\n単独AUC(年度内):')
for target in ['win_jra', 'ret1']:
    d = S.dropna(subset=[target])
    print('  %s: dam_prio 全体AUC=%.3f  ' % (target, auc(d[target], d.dam_prio)) +
          ' '.join('%d:%.3f' % (y, auc(d[d.year == y][target], d[d.year == y].dam_prio)) for y in YRS))

print('\n' + '=' * 80)
print('■ 5. 枠外ランク out_s')
print('=' * 80)
p = S[S.dam_prio == 1].dropna(subset=['win_jra']).copy()
p['out_hi'] = p['out'].isin(['A', 'B', 'C']).astype(int)
print(p.groupby('out').agg(n=('win_jra', 'size'), 勝上=('win_jra', 'mean'),
                           ret1=('ret1', 'mean'), med=('ret', 'median')).round(3).to_string())
reg(p, ['out_s'], 'win_jra', 'out_s単独 ')
reg(p, ['out_s'], 'ret1', 'out_s単独 ')
reg(p, ['out_s', 'male', 'price2539', 'w420'], 'win_jra', 'out_s+既存3 ')
p2 = p[~((p.year <= 2023) & (p['rank'] == '確定'))]
reg(p2, ['out_s'], 'win_jra', '確定除外 ')
print('\n out_s LOYO（母馬優先対象馬の中だけ）:')
for target in ['win_jra', 'ret1']:
    for tag, cols in [('既存3のみ', base), ('既存3+out_s', base + ['out_s'])]:
        o, ov = loyo(p, cols, target, YRS)
        print('   [%-7s] %-14s 全体AUC=%.3f  ' % (target, tag, ov) +
              ' '.join('%d:%.3f' % (y, o[y]) for y in YRS))
print('\n out_hi(A/B/C) 年度別 n:')
print(p.groupby(['year', 'out_hi']).size().to_string())

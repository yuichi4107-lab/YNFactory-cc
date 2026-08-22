# -*- coding: utf-8 -*-
"""敵対的検証：厩舎prior(二値/連続)・育成牧場NF空港 を潰しにかかる。"""
import io, os, sys, csv
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, BASE)
from analyze5 import load, logit, design
from backtest import auc
DS = os.path.join(BASE, '..', 'datasets'); DATA = os.path.join(BASE, '..', '..', 'data')
pd.set_option('display.width', 220); pd.set_option('display.max_rows', 400)
def sec(t): print('\n' + '=' * 78 + '\n■ ' + t + '\n' + '=' * 78)

df = load(central_only=True).dropna(subset=['win_jra']).copy().sort_values(['year', 'no']).reset_index(drop=True)
df['price2539'] = df['total_man'].between(2500, 3999).astype(float)
df['w420'] = (df['weight'] >= 420).astype(float)
df.loc[df['weight'].isna(), 'w420'] = np.nan
df['male'] = df['male'].astype(float)
print('n =', len(df), dict(df.groupby('year').size()))


def build_prior(d, k=6):
    pn, pwin, praw, pbin = [], [], [], []
    for _, r in d.iterrows():
        past = d[(d['year'] < r['year']) & (d['trainer_key'] == r['trainer_key'])]
        prev = d[d['year'] < r['year']]
        base = prev['win_jra'].mean() if len(prev) else np.nan
        n = len(past); w = past['win_jra'].sum()
        pn.append(n)
        praw.append(past['win_jra'].mean() if n else np.nan)
        pwin.append((w + k * base) / (n + k) if n and not np.isnan(base) else np.nan)
        pbin.append(1.0 if w >= 2 else 0.0)
    return (pd.Series(pn, index=d.index), pd.Series(pwin, index=d.index),
            pd.Series(praw, index=d.index), pd.Series(pbin, index=d.index))


df['pn'], df['pw'], df['praw'], df['pbin'] = build_prior(df)
d = df[df['year'] >= 2021].copy()
d['pw_c'] = d['pw'] - d.groupby('year')['pw'].transform('mean')


def zof(dat, cols, tgt):
    X, nm = design(dat, cols)
    r = logit(X, dat[tgt], nm)
    return {n: round(float(v), 2) for n, v in zip(r['変数'], r['z']) if not n.startswith('年度')}, r


sec('1. 報告された数字の再現')
print('■ 二値prior（前年度まで中央勝ち馬2頭以上）')
print(d.groupby('pbin')[['win_jra', 'ret1']].agg(['mean', 'size']).round(3).to_string())
z, r = zof(d, ['pbin'], 'win_jra')
print(' 単体 win_jra:', z, 'OR=', round(float(r.iloc[-1]['オッズ比']), 3))
print(' 単体 ret1:', zof(d, ['pbin'], 'ret1')[0])
dd = d.dropna(subset=['w420']).copy()
print(' 3基準併用 n=%d:' % len(dd), zof(dd, ['male', 'price2539', 'w420', 'pbin'], 'win_jra')[0])
print(' 3基準+pn:', zof(dd, ['male', 'price2539', 'w420', 'pbin', 'pn'], 'win_jra')[0])
print(' 年度別 二値prior:')
print(d.pivot_table(index='pbin', columns='year', values='win_jra', aggfunc=['mean', 'size']).round(3).to_string())

print('\n■ 連続prior')
print(' 単体 win:', zof(d, ['pw_c'], 'win_jra')[0], ' ret1:', zof(d, ['pw_c'], 'ret1')[0])
d['pq'] = d.groupby('year')['pw'].transform(lambda s: pd.qcut(s, 3, labels=['低', '中', '高'], duplicates='drop'))
print(d.groupby('pq', observed=False)[['win_jra', 'ret1', 'ret']].agg(['mean', 'size']).round(3).to_string())

sec('2. 二値priorは「頭数(露出)」の言い換えではないか（pn層別）')
d['pn_bin'] = pd.cut(d['pn'], [-1, 0, 2, 4, 7, 99], labels=['0', '1-2', '3-4', '5-7', '8+'])
print('勝上率:')
print(pd.crosstab(d['pn_bin'], d['pbin'], values=d['win_jra'], aggfunc='mean').round(3).to_string())
print('頭数:')
print(pd.crosstab(d['pn_bin'], d['pbin']).to_string())
print('\n-- pn>=lo に限った二値prior（露出を揃える）')
for lo in [1, 3, 4, 5]:
    s = d[d['pn'] >= lo]
    if s['pbin'].nunique() < 2:
        print(f'  pn>={lo}: 片側消滅 n={len(s)}')
        continue
    a = s[s.pbin == 1]['win_jra']; b = s[s.pbin == 0]['win_jra']
    print(f'  pn>={lo}: n={len(s)}  該当{a.mean():.3f}(n={len(a)}) vs 非該当{b.mean():.3f}(n={len(b)})  z={zof(s, ["pbin"], "win_jra")[0]["pbin"]:+.2f}')
print('\n-- pn をカテゴリダミーで入れて二値priorを検定（線形pnより厳しい調整）')
s = d[d['pn'] > 0].copy()
for lv in ['1-2', '3-4', '5-7']:
    s['pn_' + lv] = (s['pn_bin'].astype(str) == lv).astype(float)
print('  n=%d' % len(s), zof(s, ['pn_1-2', 'pn_3-4', 'pn_5-7', 'pbin'], 'win_jra')[0])
print('\n-- 二値priorの中身: 前年度まで勝ち馬0頭/1頭/2頭以上')
d['pwn'] = d.apply(lambda r: int(df[(df['year'] < r['year']) & (df['trainer_key'] == r['trainer_key'])]['win_jra'].sum()), axis=1)
d['pwn_b'] = pd.cut(d['pwn'], [-1, 0, 1, 3, 99], labels=['0勝馬', '1頭', '2-3頭', '4頭+'])
print(d.groupby('pwn_b', observed=False)[['win_jra', 'ret1']].agg(['mean', 'size']).round(3).to_string())

sec('3. LOYO：既存3基準スコア vs 3基準+候補')


def loyo(dat, cand, label, years=(2021, 2022, 2023, 2024)):
    rows = []
    for tgt in ['win_jra', 'ret1']:
        sub = dat.dropna(subset=['w420', tgt, cand]).copy()
        allb, allc, ally = [], [], []
        for y in years:
            tr, te = sub[sub['year'] != y], sub[sub['year'] == y]
            if len(te) < 10 or te[tgt].nunique() < 2:
                continue
            Xb, nb = design(tr, ['male', 'price2539', 'w420']); rb = logit(Xb, tr[tgt], nb)
            Xc, nc = design(tr, ['male', 'price2539', 'w420', cand]); rc = logit(Xc, tr[tgt], nc)
            cb = rb['係数'].values[-3:]; cc = rc['係数'].values[-4:]
            sb = te[['male', 'price2539', 'w420']].values.astype(float) @ cb
            sc = te[['male', 'price2539', 'w420', cand]].values.astype(float) @ cc
            allb.append(sb); allc.append(sc); ally.append(te[tgt].values)
            ab, ac = auc(te[tgt], sb), auc(te[tgt], sc)
            rows.append({'目的': tgt, '年度': y, 'n': len(te), 'AUC基準3': round(ab, 3),
                         'AUC+候補': round(ac, 3), '差': round(ac - ab, 3)})
        if allb:
            yb = np.concatenate(ally)
            ab = auc(yb, np.concatenate(allb)); ac = auc(yb, np.concatenate(allc))
            rows.append({'目的': tgt, '年度': 'プール', 'n': len(yb), 'AUC基準3': round(ab, 3),
                         'AUC+候補': round(ac, 3), '差': round(ac - ab, 3)})
    print(f'\n--- {label}')
    print(pd.DataFrame(rows).to_string(index=False))


loyo(d, 'pbin', '厩舎prior 二値')
loyo(d, 'pw', '厩舎prior 連続(k=6)')

sec('4. 育成牧場 NF空港 vs NF早来')
ik = {}
for r in csv.DictReader(open(os.path.join(DS, 'roster.csv'), encoding='utf-8-sig')):
    if (r.get('ikusei') or '').strip():
        ik[f"{r['year']}#{r['no']}"] = r['ikusei'].strip()
for r in csv.DictReader(open(os.path.join(DS, 'club_2023.csv'), encoding='utf-8-sig')):
    if (r.get('ikusei') or '').strip():
        ik[f"2023#{r['no']}"] = r['ikusei'].strip()
df['ikusei'] = df['key'].map(lambda k: ik[k].replace('Ｎ', 'N').replace('Ｆ', 'F').replace(' ', '') if k in ik else np.nan)
di = df[df['ikusei'].isin(['NF空港', 'NF早来'])].copy()
di['kuko'] = (di['ikusei'] == 'NF空港').astype(float)
print('n=', len(di))
print(di.groupby(['year', 'ikusei']).size().unstack(fill_value=0).to_string())
print('全体 win:', zof(di, ['kuko'], 'win_jra')[0], ' ret1:', zof(di, ['kuko'], 'ret1')[0])
d3 = di[di['year'] >= 2021]
print('2020を除く n=%d win:' % len(d3), zof(d3, ['kuko'], 'win_jra')[0], ' ret1:', zof(d3, ['kuko'], 'ret1')[0])
dm = di[di['male'] == 1]
print('牡馬のみ n=%d win:' % len(dm), zof(dm, ['kuko'], 'win_jra')[0])
dm3 = dm[dm['year'] >= 2021]
print('牡馬・2020除く n=%d win:' % len(dm3), zof(dm3, ['kuko'], 'win_jra')[0])
loyo(di.assign(pbin=0.0), 'kuko', '育成 NF空港', years=(2020, 2021, 2022, 2023))
print('\n2024/2026年度に育成牧場の列があるか:')
print(' roster_new_raw:', open(os.path.join(DS, 'roster_new_raw.csv'), encoding='utf-8').readline().strip()[:300])
print(' bosyu_2026:', open(os.path.join(DATA, 'bosyu_2026.csv'), encoding='utf-8-sig').readline().strip()[:300])

sec('5. 多重検定：観測zの珍しさ（年度内シャッフル）')
rng = np.random.default_rng(0)
for cand, lab in [('pbin', '二値prior'), ('pw_c', '連続prior')]:
    obs = float(logit(*design(d, [cand])[0:1][0:1] and design(d, [cand])[0], d['win_jra'], design(d, [cand])[1]).iloc[-1]['z'])
    cnt = 0; N = 500; zz = []
    for _ in range(N):
        p = d.groupby('year')[cand].transform(lambda s: pd.Series(rng.permutation(s.values), index=s.index))
        s2 = d.assign(_p=p)
        X, nm = design(s2, ['_p'])
        z = float(logit(X, s2['win_jra'], nm).iloc[-1]['z']); zz.append(z)
        if abs(z) >= abs(obs):
            cnt += 1
    print(f' {lab}: 観測z={obs:.2f}  年度内シャッフル{N}回で|z|>=観測 が{cnt}回 → p={cnt/N:.3f} (帰無sd={np.std(zz):.2f})')
print(' ※ この分析全体で候補は数十。Bonferroni換算で必要な単発p ≒ 0.05/30 = 0.0017 → |z|>3.1')

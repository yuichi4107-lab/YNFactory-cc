# -*- coding: utf-8 -*-
"""敵対的検証 続き：閾値の恣意性・並べ替え検定・2026適用可否。"""
import io, os, sys, csv
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, BASE)
from analyze5 import load, logit, design
from backtest import auc
DS = os.path.join(BASE, '..', 'datasets'); DATA = os.path.join(BASE, '..', '..', 'data')
pd.set_option('display.width', 220)
def sec(t): print('\n' + '=' * 78 + '\n■ ' + t + '\n' + '=' * 78)

df = load(central_only=True).dropna(subset=['win_jra']).copy().sort_values(['year', 'no']).reset_index(drop=True)
df['price2539'] = df['total_man'].between(2500, 3999).astype(float)
df['w420'] = (df['weight'] >= 420).astype(float)
df.loc[df['weight'].isna(), 'w420'] = np.nan
df['male'] = df['male'].astype(float)

pn, pwn, pw = [], [], []
K = 6
for _, r in df.iterrows():
    past = df[(df['year'] < r['year']) & (df['trainer_key'] == r['trainer_key'])]
    prev = df[df['year'] < r['year']]
    base = prev['win_jra'].mean() if len(prev) else np.nan
    n = len(past); w = past['win_jra'].sum()
    pn.append(n); pwn.append(int(w))
    pw.append((w + K * base) / (n + K) if n and not np.isnan(base) else np.nan)
df['pn'] = pn; df['pwn'] = pwn; df['pw'] = pw
d = df[df['year'] >= 2021].copy()


def zof(dat, cols, tgt):
    X, nm = design(dat, cols)
    r = logit(X, dat[tgt], nm)
    return {n: round(float(v), 2) for n, v in zip(r['変数'], r['z']) if not n.startswith('年度')}


sec('A. 「2頭以上」という閾値の恣意性（他の切り方でも効くか）')
dd = d.dropna(subset=['w420']).copy()
print(f'{"閾値":<12}{"n(該当)":>8}{"該当勝上":>10}{"非該当":>8}{"単体z":>8}{"3基準併用z":>12}{"ret1 z":>9}')
for th in [1, 2, 3, 4, 5]:
    v = (d['pwn'] >= th).astype(float)
    s = d.assign(_v=v)
    if s['_v'].nunique() < 2:
        continue
    a = s[s._v == 1]['win_jra']; b = s[s._v == 0]['win_jra']
    z1 = zof(s, ['_v'], 'win_jra')['_v']
    z3 = zof(dd.assign(_v=(dd['pwn'] >= th).astype(float)), ['male', 'price2539', 'w420', '_v'], 'win_jra')['_v']
    zr = zof(s, ['_v'], 'ret1')['_v']
    print(f'{"勝ち馬>="+str(th)+"頭":<12}{len(a):>8}{a.mean():>10.3f}{b.mean():>8.3f}{z1:>8.2f}{z3:>12.2f}{zr:>9.2f}')
print('\n-- 勝ち馬頭数そのものを連続で入れる')
d['pwn_c'] = d['pwn'] - d.groupby('year')['pwn'].transform('mean')
print('  連続 pwn:', zof(d, ['pwn_c'], 'win_jra'), zof(d, ['pwn_c'], 'ret1'))

sec('B. 二値priorは「前歴のある厩舎か否か」ではないのか')
d['known'] = (d['pn'] >= 1).astype(float)
print(d.groupby(['known', d['pwn'] >= 2])[['win_jra']].agg(['mean', 'size']).round(3).to_string())
print(' known単体 z:', zof(d, ['known'], 'win_jra'))
kn = d[d['known'] == 1].copy()
kn['pb'] = (kn['pwn'] >= 2).astype(float)
print(' 前歴ある厩舎の中だけで二値prior z:', zof(kn, ['pb'], 'win_jra'), ' n=%d' % len(kn))
kn3 = kn[kn['pn'] >= 3].copy()
print(' pn>=3 の中だけ z:', zof(kn3, ['pb'], 'win_jra'), ' n=%d (該当%d/非該当%d)' % (len(kn3), int(kn3.pb.sum()), int((1-kn3.pb).sum())))

sec('C. 連続prior：NaN行を除いた正しい推定')
dp = d.dropna(subset=['pw']).copy()
dp['pw_c'] = dp['pw'] - dp.groupby('year')['pw'].transform('mean')
print(' n=%d 単体 win:' % len(dp), zof(dp, ['pw_c'], 'win_jra'), ' ret1:', zof(dp, ['pw_c'], 'ret1'))
dpp = dp.dropna(subset=['w420'])
print(' 3基準併用:', zof(dpp, ['male', 'price2539', 'w420', 'pw_c'], 'win_jra'))
print(' 年度別（priorを年度内で上下半分に割る）')
for y in sorted(dp['year'].unique()):
    dy = dp[dp['year'] == y]
    hi = dy[dy['pw'] > dy['pw'].median()]; lo = dy[dy['pw'] <= dy['pw'].median()]
    print(f'  {y}: 上{hi["win_jra"].mean():.3f}(n={len(hi)}) / 下{lo["win_jra"].mean():.3f}(n={len(lo)})  年度内AUC={auc(dy["win_jra"], dy["pw"]):.3f}')

sec('D. 並べ替え検定（年度内で候補列をシャッフル）')
rng = np.random.default_rng(0)
for dat, cand, lab in [(d, 'pbin2', '二値prior'), (dp, 'pw_c', '連続prior')]:
    s0 = dat.copy()
    if cand == 'pbin2':
        s0['pbin2'] = (s0['pwn'] >= 2).astype(float)
    X, nm = design(s0, [cand]); obs = float(logit(X, s0['win_jra'], nm).iloc[-1]['z'])
    cnt = 0; N = 500; zz = []
    for _ in range(N):
        p = s0.groupby('year')[cand].transform(lambda s: pd.Series(rng.permutation(s.values), index=s.index))
        s2 = s0.assign(_p=p)
        X, nm = design(s2, ['_p'])
        z = float(logit(X, s2['win_jra'], nm).iloc[-1]['z']); zz.append(z)
        if abs(z) >= abs(obs):
            cnt += 1
    print(f' {lab}: 観測z={obs:+.2f}  {N}回シャッフルで|z|>=観測 が{cnt}回 → p={cnt/N:.3f} (帰無sd={np.std(zz):.2f})')
print(' ※閾値5通り×目的2種×調整4通り≒40仮説。Bonferroni p<0.05 には単発p<0.0013（|z|>3.2）が必要')

sec('E. 2026年度94頭への適用可否')
b26 = list(csv.DictReader(open(os.path.join(DATA, 'bosyu_2026.csv'), encoding='utf-8-sig')))
known = set(df['trainer_key'])
from trainers import build_map
rows5 = list(csv.DictReader(open(os.path.join(DS, 'panel5.csv'), encoding='utf-8-sig')))
mp = build_map(rows5)
hit = []
for r in b26:
    t = (r.get('厩舎') or '').replace(' ', '').strip()
    hit.append(mp.get(t, t) in known)
print('2026 n=%d  5年パネルに厩舎あり: %d (%.0f%%)' % (len(b26), sum(hit), 100 * np.mean(hit)))
miss = sorted({(r.get('厩舎') or '').replace(' ', '') for r, h in zip(b26, hit) if not h})
print('未知の厩舎:', ' '.join(miss))
# 2026に当てたとき、二値priorが何頭を該当にするか
allw = df.groupby('trainer_key')['win_jra'].sum()
n26 = 0
for r, h in zip(b26, hit):
    if not h:
        continue
    t = mp.get((r.get('厩舎') or '').replace(' ', '').strip(), (r.get('厩舎') or '').replace(' ', '').strip())
    if allw.get(t, 0) >= 2:
        n26 += 1
print('2026で二値prior該当になる頭数: %d / %d（判定可能な馬のうち %.0f%%）' % (n26, sum(hit), 100 * n26 / sum(hit)))

sec('F. 育成牧場：2024・2026に列が無い＝今年適用不能の確認')
for f, enc in [('roster.csv', 'utf-8-sig'), ('roster_new_raw.csv', 'utf-8'), ('club_2023.csv', 'utf-8-sig')]:
    hdr = open(os.path.join(DS, f), encoding=enc).readline().strip()
    print(f' {f:<22} ikusei列: {"ikusei" in hdr}')
print(' bosyu_2026.csv        育成列:', '育成' in open(os.path.join(DATA, 'bosyu_2026.csv'), encoding='utf-8-sig').readline())

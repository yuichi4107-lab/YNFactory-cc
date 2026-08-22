# -*- coding: utf-8 -*-
"""追加確認：2024年度の反転の原因、育成牧場の年度別z、予定厩舎の欠測・地方。"""
import io, os, sys, csv, json
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, BASE)
from analyze5 import load, logit, design
DS = os.path.join(BASE, '..', 'datasets'); DATA = os.path.join(BASE, '..', '..', 'data')
pd.set_option('display.width', 200)
def sec(t): print('\n' + '='*78 + '\n■ ' + t + '\n' + '='*78)

df = load(central_only=True).dropna(subset=['win_jra']).copy().sort_values(['year','no']).reset_index(drop=True)
rs = json.load(open(os.path.join(DS,'race_summary.json'), encoding='utf-8'))
for c in ['starts_by3','wins_by3','prize_by3']:
    df[c] = df['key'].map(lambda k: (rs.get(k) or {}).get(c))
df['win3'] = (pd.to_numeric(df['wins_by3'], errors='coerce').fillna(0) >= 1).astype(int)
df['deb'] = (pd.to_numeric(df['starts_by3'], errors='coerce').fillna(0) > 0).astype(int)

def prior(df, k=6, col='win_jra'):
    ns, rs_ = [], []
    for _, r in df.iterrows():
        past = df[(df['year'] < r['year']) & (df['trainer_key'] == r['trainer_key'])]
        base = df[df['year'] < r['year']][col].mean(); n = len(past); ns.append(n)
        rs_.append((past[col].sum()+k*base)/(n+k) if n and not np.isnan(base) else np.nan)
    return pd.Series(ns, index=df.index), pd.Series(rs_, index=df.index)
df['pn'], df['pw'] = prior(df)
d = df[(df['year']>=2021) & df['pw'].notna()].copy()
d['pw_c'] = d['pw'] - d.groupby('year')['pw'].transform('mean')

sec('2024年度で厩舎priorが反転する理由を探す（3歳時点の指標で揃える）')
for tgt, lab in [('win_jra','中央1勝(現在まで)'), ('win3','3歳までに1勝'), ('deb','3歳までに出走')]:
    X, nm = design(d, ['pw_c'])
    r = logit(X, d[tgt], nm).iloc[-1]
    print(f'{lab:<18} 全体 z={r["z"]:+.2f}')
    row = []
    for y in sorted(d['year'].unique()):
        dy = d[d['year']==y]
        # 年度内で prior 上位半分 vs 下位半分
        hi = dy[dy['pw'] > dy['pw'].median()][tgt].mean(); lo = dy[dy['pw'] <= dy['pw'].median()][tgt].mean()
        row.append(f'{y}: 上{hi:.2f}/下{lo:.2f}')
    print('   ' + '  '.join(row))
print('\n2024年度の出走率:', round(d[d['year']==2024]['deb'].mean(),2),
      ' 2023:', round(d[d['year']==2023]['deb'].mean(),2))

sec('厩舎prior：2020-2023年度だけ（2024を除く）で見るとどうか')
d23 = d[d['year']<=2023]
X, nm = design(d23, ['pw_c'])
print('n=%d' % len(d23), logit(X, d23['win_jra'], nm).round(3).iloc[-1].to_dict())

sec('育成牧場 NF空港 の年度別z（1年ずつ単独ロジット）と牡馬限定')
ik = {}
for r in csv.DictReader(open(os.path.join(DS,'roster.csv'), encoding='utf-8-sig')):
    if (r.get('ikusei') or '').strip(): ik[f"{r['year']}#{r['no']}"] = r['ikusei'].strip()
for r in csv.DictReader(open(os.path.join(DS,'club_2023.csv'), encoding='utf-8-sig')):
    if (r.get('ikusei') or '').strip(): ik[f"2023#{r['no']}"] = r['ikusei'].strip()
df['ikusei'] = df['key'].map(lambda k: ik[k].replace('Ｎ','N').replace('Ｆ','F').replace(' ','') if k in ik else np.nan)
di = df[df['ikusei'].isin(['NF空港','NF早来'])].copy()
di['kuko'] = (di['ikusei']=='NF空港').astype(int)
from scipy import stats
for y in sorted(di['year'].unique()):
    dy = di[di['year']==y]
    a = dy[dy['kuko']==1]['win_jra']; b = dy[dy['kuko']==0]['win_jra']
    t = stats.fisher_exact([[int(a.sum()), len(a)-int(a.sum())],[int(b.sum()), len(b)-int(b.sum())]])
    print(f'  {y}: 空港 {a.mean():.2f}(n={len(a)}) vs 早来 {b.mean():.2f}(n={len(b)})  OR={t[0]:.2f} p={t[1]:.3f}')
print('\n牡馬限定')
dm = di[di['male']==1]
X, nm = design(dm, ['kuko']); print(' win', logit(X, dm['win_jra'], nm).round(3).iloc[-1].to_dict())
print(' ret', logit(X, dm['ret1'], nm).round(3).iloc[-1].to_dict())
print('メス限定')
dfm = di[di['male']==0]
X, nm = design(dfm, ['kuko']); print(' win', logit(X, dfm['win_jra'], nm).round(3).iloc[-1].to_dict())
print('\n空港/早来 × ret1 全体')
X, nm = design(di, ['kuko']); print(' ret1', logit(X, di['ret1'], nm).round(3).iloc[-1].to_dict())
print('\n空港/早来 × 提供牧場（ノーザン産以外も空港/早来で育成されている？）')
print(pd.crosstab(di['ikusei'], di['nf']).to_string())
print('\n重賞（graded）')
print(di.groupby('ikusei')['graded'].agg(['sum','size']).to_string())

sec('予定厩舎の欠測・地方名義')
raw = list(csv.DictReader(open(os.path.join(DS,'panel5.csv'), encoding='utf-8-sig')))
tp = pd.Series([ (r.get('trainer_planned') or '').strip() for r in raw ])
print('空欄:', int((tp=='').sum()), '/', len(tp))
print('地方名義を含む:', int(tp.str.contains('門別|南関|地方|大井|川崎|船橋|浦和|笠松|高知|佐賀|金沢').sum()))
df['tp_blank'] = (df['trainer_planned'].astype(str).str.strip()=='').astype(int)
print(df.groupby('tp_blank')[['win_jra','ret1']].agg(['mean','size']).round(3).to_string())

sec('関東/関西の年度別（回収率も）')
ok = df[df['district'].isin(['美浦','栗東'])]
cnt = ok.groupby(['trainer_key','district']).size().unstack(fill_value=0)
def loo(r):
    t=r['trainer_key']
    if t not in cnt.index: return np.nan
    row = cnt.loc[t].copy()
    if r['district'] in row.index: row[r['district']] -= 1
    return row.idxmax() if row.sum()>0 else np.nan
df['tr_dist'] = df.apply(loo, axis=1)
s = df[df['tr_dist'].notna()]
print(s.pivot_table(index='tr_dist', columns='year', values='ret1', aggfunc=['mean','size']).round(2).to_string())
print(s.groupby('tr_dist')[['ret','graded']].agg(['mean','size']).round(3).to_string())

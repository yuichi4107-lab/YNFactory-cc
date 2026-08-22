# -*- coding: utf-8 -*-
"""母・兄姉・父の新変数を検定する。

変数の性質が3種類あるので、扱いを分ける。

  母の競走成績   … リークなし。母の現役時代は産駒が生まれる前に終わっている
  父の産駒成績   … リークなし。募集年度Yに対してY-1年以前のリーディングだけを使う
  兄姉の獲得賞金 … **リークあり**。netkeibaが返すのは「今現在」の通算賞金で、
                   募集時点の賞金ではない。上の仔が募集後に稼いだぶんが入っている。
                   よってこれは「兄姉情報の上限性能」を測る診断用であり、
                   ここで効かなければ本物（募集時点の賞金）でも効かない、
                   効いたときだけ取り直す価値がある、という位置づけにする。

出力は標準出力。
"""
import csv
import io
import json
import math
import os
import sys

import numpy as np
import pandas as pd

from analyze5 import design, load, logit
from backtest import auc

BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')
if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 200)

S4 = [('牡馬', lambda d: d['male'] == 1),
      ('総額2500万以上', lambda d: d['total_man'] >= 2500),
      ('総額4000万未満', lambda d: d['total_man'].between(2500, 3999)),
      ('馬体重420kg以上', lambda d: d['weight'] >= 420)]


def base_score(df):
    s = np.zeros(len(df))
    for _, f in S4:
        s = s + f(df).astype(float).values
    return s


def build(df):
    fam = json.load(open(os.path.join(DS, 'family.json'), encoding='utf-8'))
    sl = json.load(open(os.path.join(DS, 'sire_leading.json'), encoding='utf-8'))
    dams, horses = fam['dams'], fam['horses']

    rows = []
    for _, r in df.iterrows():
        key = f"{r['year']}#{r['no']}"
        h = horses.get(key) or {}
        d = dams.get(h.get('dam_id') or '') or {}
        born = int(r['born'])
        sibs = [s for s in (d.get('sibs') or []) if s.get('born') and s['born'] < born]
        prizes = [s['prize'] for s in sibs if s.get('prize') is not None]
        dam_prize = (d.get('prize_jra') or 0) + (d.get('prize_nar') or 0)
        # 父：募集年度Yに対して Y-1 → Y-2 → Y-3 の順に、載っている最新の年を使う
        sire = (r['sire'] or '').strip().lstrip('*')
        sinfo, syear = None, None
        for back in (1, 2, 3):
            y = str(int(r['year']) - back)
            if sire in sl.get(y, {}):
                sinfo, syear = sl[y][sire], y
                break
        rows.append({
            'key': key,
            'dam_foreign': int(bool(d.get('foreign'))),
            'dam_starts': d.get('starts'),
            'dam_raced': None if d.get('foreign') else int((d.get('starts') or 0) > 0),
            'dam_win': None if d.get('foreign') else int((d.get('wins') or 0) >= 1),
            'dam_prize': dam_prize,
            'dam_prize_log': math.log1p(dam_prize),
            'dam_graded': int(d.get('graded') or 0),
            'n_older_sibs': len(sibs),
            'sib_max_prize': max(prizes) if prizes else 0.0,
            'sib_mean_prize': (sum(prizes) / len(prizes)) if prizes else 0.0,
            'sib_hit5000': int(bool(prizes) and max(prizes) >= 5000),
            'sib_any_earn': int(bool(prizes) and max(prizes) > 0),
            'sire_known': int(sinfo is not None),
            'sire_win_rate': sinfo['win_horse_rate'] if sinfo else None,
            'sire_runners': sinfo['runners'] if sinfo else None,
            'sire_year_back': (int(r['year']) - int(syear)) if syear else None,
        })
    add = pd.DataFrame(rows).set_index('key')
    df = df.copy()
    df['key'] = df['year'].astype(str) + '#' + df['no'].astype(str)
    return df.join(add, on='key')


def test(df, col, label, note='', binary=None):
    out = []
    for target in ('win_jra', 'ret1'):
        sub = df.dropna(subset=[col, target])
        if sub.empty or sub[col].nunique() < 2:
            return
        v = (binary(sub) if binary else sub[col]).astype(float)
        X, names = design(sub.assign(_v=v), ['_v'])
        r = logit(X, sub[target], names).iloc[-1]
        out.append((target, len(sub), float(r['係数']), float(r['z'])))
    w, rr = out[0], out[1]
    print(f'  {label:<34} n={w[1]:>3}  win_jra z={w[3]:+.2f}   ret1 z={rr[3]:+.2f}  {note}')


def rate(df, col, label, cut):
    sub = df.dropna(subset=[col, 'win_jra'])
    hi = sub[sub[col] >= cut]
    lo = sub[sub[col] < cut]
    if len(hi) < 10 or len(lo) < 10:
        return
    by = []
    for y in sorted(sub['year'].unique()):
        s = sub[sub['year'] == y]
        a, b = s[s[col] >= cut], s[s[col] < cut]
        by.append(f'{y}:{100*a["win_jra"].mean():.0f}/{100*b["win_jra"].mean():.0f}'
                  if len(a) and len(b) else f'{y}:-')
    print(f'    {label}: 該当{len(hi)}頭 {100*hi["win_jra"].mean():.0f}%・回収{100*hi["ret1"].mean():.0f}%'
          f' vs 非該当{len(lo)}頭 {100*lo["win_jra"].mean():.0f}%・{100*lo["ret1"].mean():.0f}%'
          f'  年度別(該当/非該当) {" ".join(by)}')


def loyo(df, col, label, binary):
    """4基準に足したときの入れ子なしLOYO（閾値は固定なので単純比較）。"""
    res = []
    for target in ('win_jra', 'ret1'):
        d = df.dropna(subset=[target, col])
        b, a = [], []
        for y in sorted(d['year'].unique()):
            te = d[d['year'] == y]
            s0 = base_score(te)
            s1 = s0 + binary(te).astype(float).values
            b.append(auc(te[target], s0))
            a.append(auc(te[target], s1))
        res.append((target, np.mean(b), np.mean(a), sum(1 for x, y_ in zip(a, b) if x > y_), len(b)))
    for t, b, a, n, k in res:
        print(f'    LOYO {t}: 4基準 {b:.3f} → 追加 {a:.3f} ({a-b:+.3f})  改善 {n}/{k}年')


def main():
    df = load(central_only=True)
    df = build(df)
    print(f'対象 {len(df)}頭（中央400口）')
    print(f'母の情報が取れた: {int(df["dam_starts"].notna().sum())}頭 / '
          f'うち外国産（戦績が日本に無い）: {int(df["dam_foreign"].sum())}頭')
    print(f'父リーディングと突合: {int(df["sire_known"].sum())}頭')

    print('\n■ 母の競走成績（リークなし）')
    test(df, 'dam_win', '母が1勝以上')
    test(df, 'dam_prize_log', '母の獲得賞金(log)')
    test(df, 'dam_graded', '母が重賞勝ち')
    test(df, 'dam_starts', '母の出走数')
    rate(df, 'dam_graded', '母が重賞勝ち', 1)
    rate(df, 'dam_prize', '母の賞金5000万以上', 5000)

    print('\n■ 兄姉（※リークあり。診断用）')
    test(df, 'n_older_sibs', '上の仔の数')
    test(df, 'sib_max_prize', '上の仔の最高賞金')
    test(df, 'sib_hit5000', '上の仔に5000万超がいる')
    test(df, 'sib_any_earn', '上の仔に賞金を稼いだ馬がいる')
    rate(df, 'sib_hit5000', '上の仔に5000万超', 1)

    print('\n■ 父（リークなし・募集年度より前のリーディング）')
    test(df, 'sire_known', '父に産駒実績がある')
    test(df, 'sire_win_rate', '父の勝馬率')
    test(df, 'sire_runners', '父の出走頭数')
    rate(df, 'sire_known', '父に産駒実績あり', 1)
    for c in (0.35, 0.40, 0.45):
        rate(df, 'sire_win_rate', f'父の勝馬率{c}以上', c)

    print('\n■ 既存4基準と同時に入れたとき')
    for col, lab, bfun in [
        ('dam_graded', '母が重賞勝ち', lambda d: d['dam_graded'] == 1),
        ('dam_prize_log', '母の賞金(log)', None),
        ('sib_hit5000', '上の仔に5000万超', lambda d: d['sib_hit5000'] == 1),
        ('sire_known', '父に産駒実績あり', lambda d: d['sire_known'] == 1),
        ('sire_win_rate', '父の勝馬率', None),
    ]:
        sub = df.dropna(subset=[col, 'win_jra', 'weight', 'total_man'])
        cols = ['male', 'w430', 'price25_60', col]
        sub = sub.assign(price_floor=(sub['total_man'] >= 2500).astype(float))
        X, names = design(sub, ['male', 'price_floor', 'price25_60', 'w430', col])
        r = logit(X, sub['win_jra'], names)
        z = float(r[r['変数'] == col]['z'].iloc[0])
        r2 = logit(X, sub['ret1'], names)
        z2 = float(r2[r2['変数'] == col]['z'].iloc[0])
        print(f'  {lab:<20} n={len(sub)}  win_jra z={z:+.2f}  ret1 z={z2:+.2f}')
        if bfun is not None:
            loyo(sub, col, lab, bfun)


if __name__ == '__main__':
    main()

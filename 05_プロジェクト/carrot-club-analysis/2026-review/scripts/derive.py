# -*- coding: utf-8 -*-
"""5年ぶん（2020〜2024年度募集）からスコア基準を作り直す。

やること
  1. 既存6基準を年度ダミーつきで検定して、残す／落とす／閾値を動かすを決める
  2. 候補の閾値を総当たりで走査（母年齢の帯・価格の帯・馬体重の切れ目・生まれ月）
  3. 決めた新スコアを leave-one-year-out で検証（その年のデータを使わずにその年を当てる）

目的変数は「中央で1勝以上（win_jra）」を主、「回収≥1」を従にする。
地方入厩予定馬（100口）は中央で走らないので導出からは外す。
"""
import io
import itertools
import sys

import numpy as np
import pandas as pd

from analyze5 import load, logit, design

pd.set_option('display.width', 220)


def auc(y, s):
    y = np.asarray(y, float)
    s = np.asarray(s, float)
    pos, neg = s[y == 1], s[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return np.nan
    order = np.argsort(np.concatenate([pos, neg]), kind='mergesort')
    ranks = np.empty(len(order), float)
    ranks[order] = np.arange(1, len(order) + 1)
    # 同値は平均順位に均す
    vals = np.concatenate([pos, neg])
    for v in np.unique(vals):
        idx = vals == v
        ranks[idx] = ranks[idx].mean()
    return (ranks[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def scan(df, target, col, cuts, label):
    """しきい値をずらしながら、年度ダミーつきの効き方を見る。"""
    print(f'\n-- {label}: 閾値の走査（目的変数 {target}）')
    rows = []
    for lo, hi in cuts:
        v = df[col].between(lo, hi).astype(float)
        sub = df.assign(_v=v).dropna(subset=[target, col])
        X, names = design(sub, ['_v'])
        r = logit(X, sub[target], names)
        z = r.iloc[-1]
        n = int(v.loc[sub.index].sum())
        rows.append({'区間': f'{lo}〜{hi}', '該当': n,
                     '該当の率': round(100 * sub.loc[v.loc[sub.index] == 1, target].mean(), 0),
                     '非該当の率': round(100 * sub.loc[v.loc[sub.index] == 0, target].mean(), 0),
                     '係数': round(z['係数'], 3), 'z': round(z['z'], 2)})
    print(pd.DataFrame(rows).to_string(index=False))


def main():
    target = 'win_jra'
    df = load(central_only=True)
    df = df.dropna(subset=[target])
    print(f'導出に使う母集団: {len(df)}頭（中央400口・成績が取れた馬）')
    print(df.groupby('year')[target].agg(['size', 'mean']).round(3).to_string())

    print('\n' + '=' * 82)
    print('■ 1. 既存6基準をそのまま検定')
    print('=' * 82)
    sub = df.dropna(subset=['dam_age', 'total_man', 'weight'])
    for t in [target, 'ret1']:
        X, names = design(sub, ['male', 'mar_apr', 'nf', 'dam811', 'price25_60', 'w430'])
        print(f'\n-- 目的変数 {t}  n={len(sub)}')
        print(logit(X, sub[t], names).round(3).to_string(index=False))

    print('\n' + '=' * 82)
    print('■ 2. 閾値の走査')
    print('=' * 82)
    scan(df, target, 'dam_age', [(6, 9), (7, 10), (8, 11), (8, 12), (9, 12), (6, 11), (7, 12)],
         '母年齢')
    scan(df, target, 'total_man', [(2000, 3999), (2500, 3999), (2500, 5999), (3000, 5999),
                                   (2500, 7999), (3000, 7999), (4000, 7999)], '募集総額(万)')
    scan(df, target, 'weight', [(410, 999), (420, 999), (430, 999), (440, 999), (450, 999)],
         '募集時馬体重')
    scan(df, target, 'month', [(1, 3), (2, 4), (3, 4), (1, 4), (3, 5)], '生まれ月')
    scan(df, target, 'height', [(150, 999), (153, 999), (155, 999), (157, 999)], '体高')
    scan(df, target, 'girth', [(170, 999), (175, 999), (178, 999), (180, 999)], '胸囲')
    scan(df, target, 'cannon', [(19, 999), (20, 999), (20.5, 999), (21, 999)], '管囲')


if __name__ == '__main__':
    main()

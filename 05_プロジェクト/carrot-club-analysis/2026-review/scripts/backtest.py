# -*- coding: utf-8 -*-
"""スコアの作り方そのものを leave-one-year-out で検証する。

「その年のデータを一切使わずに閾値を選び、その年を当てにいく」を5回まわす。
基準を5年ぶんで作り直すと当然5年ぶんへの当てはまりは良くなるので、
当てはまりではなく、この外挿の成績で良し悪しを判断する。
"""
import io
import sys

import numpy as np
import pandas as pd

from analyze5 import design, load, logit

pd.set_option('display.width', 200)

# 因子ごとの候補（ラベル, 列, 区間のリスト）
CANDIDATES = [
    ('性別', 'male', [(1, 1)]),
    ('生まれ月', 'month', [(3, 4), (2, 4), (1, 4), (1, 3), (3, 5)]),
    ('ノーザンＦ', 'nf', [(1, 1)]),
    ('母年齢', 'dam_age', [(8, 11), (7, 10), (8, 12), (6, 11), (9, 12)]),
    ('募集総額', 'total_man', [(2500, 3999), (2500, 5999), (2000, 3999), (3000, 5999),
                             (2500, 7999), (3000, 7999)]),
    ('価格の年内位置', 'price_pct', [(0.0, 0.5), (0.2, 0.8), (0.3, 1.0), (0.5, 1.0)]),
    ('馬体重', 'weight', [(420, 999), (430, 999), (440, 999), (450, 999)]),
    ('年内平均比の馬体重', 'weight_rel', [(-10, 999), (0, 999), (10, 999)]),
    ('管囲', 'cannon', [(20, 999), (20.5, 999), (21, 999)]),
    ('胸囲', 'girth', [(175, 999), (178, 999), (180, 999)]),
    ('体高', 'height', [(153, 999), (155, 999), (157, 999)]),
]


def auc(y, s):
    y, s = np.asarray(y, float), np.asarray(s, float)
    pos, neg = s[y == 1], s[y == 0]
    if not len(pos) or not len(neg):
        return np.nan
    vals = np.concatenate([pos, neg])
    order = np.argsort(vals, kind='mergesort')
    ranks = np.empty(len(vals), float)
    ranks[order] = np.arange(1, len(vals) + 1)
    for v in np.unique(vals):
        idx = vals == v
        ranks[idx] = ranks[idx].mean()
    return (ranks[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def zscore(df, col, lo, hi, target):
    sub = df.dropna(subset=[col, target])
    if sub.empty:
        return -np.inf, None
    v = sub[col].between(lo, hi).astype(float)
    if v.nunique() < 2:
        return -np.inf, None
    X, names = design(sub.assign(_v=v), ['_v'])
    r = logit(X, sub[target], names)
    return float(r.iloc[-1]['z']), float(r.iloc[-1]['係数'])


def select(train, target, zmin=1.5, exclude=()):
    """訓練データだけを見て、因子ごとに最良の閾値を選び、弱い因子は落とす。"""
    chosen = []
    for label, col, cuts in CANDIDATES:
        if label in exclude:
            continue
        best = None
        for lo, hi in cuts:
            z, b = zscore(train, col, lo, hi, target)
            if best is None or z > best[0]:
                best = (z, lo, hi)
        if best and best[0] >= zmin:
            chosen.append((label, col, best[1], best[2], round(best[0], 2)))
    return chosen


def apply_score(df, chosen):
    s = np.zeros(len(df))
    for _, col, lo, hi, _z in chosen:
        s = s + df[col].between(lo, hi).astype(float).values
    return s


def main():
    target = 'win_jra'
    df = load(central_only=True).dropna(subset=[target])
    # 価格の年内位置と絶対額は同じものを二重に数えるので、どちらか一方だけ使う
    excl_sets = {
        '絶対額を使う': ('価格の年内位置', '年内平均比の馬体重'),
        '年内位置を使う': ('募集総額', '馬体重'),
    }
    for tag, exclude in excl_sets.items():
        print('\n' + '=' * 82)
        print(f'■ {tag}')
        print('=' * 82)
        chosen = select(df, target, exclude=exclude)
        print('5年すべてで選ぶとこうなる:')
        for c in chosen:
            print(f'   {c[0]:<10} {c[2]}〜{c[3]}   z={c[4]}')
        s = apply_score(df, chosen)
        print(f'  5年に当てはめたAUC = {auc(df[target], s):.3f}（当てはめなので甘い）')
        if len(chosen) > 1:
            cols = []
            sub = df.copy()
            for label, col, lo, hi, _z in chosen:
                sub['_' + label] = sub[col].between(lo, hi).astype(float)
                cols.append('_' + label)
            sub = sub.dropna(subset=[target])
            X, names = design(sub, cols)
            print('  選ばれた基準を同時に入れたとき（重複していないかの確認）')
            print(logit(X, sub[target], names).round(3).to_string(index=False))

        rows = []
        for y in sorted(df['year'].unique()):
            tr, te = df[df['year'] != y], df[df['year'] == y]
            ch = select(tr, target, exclude=exclude)
            a = auc(te[target], apply_score(te, ch))
            rows.append({'検証した年度': y, '頭数': len(te),
                         '選ばれた基準数': len(ch), 'AUC': round(a, 3),
                         '基準': ' / '.join(f'{c[0]}{c[2]}-{c[3]}' for c in ch)})
        bt = pd.DataFrame(rows)
        print('\n  leave-one-year-out（その年を使わずにその年を当てる）')
        print(bt.to_string(index=False))
        print(f'  平均AUC = {bt["AUC"].mean():.3f}')

    print('\n' + '=' * 82)
    print('■ 参考：既存6基準をそのまま当てたときのAUC')
    print('=' * 82)
    old = [('牡馬', 'male', 1, 1, 0), ('3〜4月生', 'month', 3, 4, 0), ('ノーザンＦ', 'nf', 1, 1, 0),
           ('母8〜11歳', 'dam_age', 8, 11, 0), ('総額2500〜5999万', 'total_man', 2500, 5999, 0),
           ('馬体重430kg以上', 'weight', 430, 999, 0)]
    s = apply_score(df, old)
    print(f'  5年全体 AUC = {auc(df[target], s):.3f}')
    for y in sorted(df['year'].unique()):
        te = df[df['year'] == y]
        print(f'   {y}年度  n={len(te):>3}  AUC={auc(te[target], apply_score(te, old)):.3f}')


if __name__ == '__main__':
    main()

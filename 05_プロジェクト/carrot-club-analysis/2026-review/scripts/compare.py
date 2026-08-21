# -*- coding: utf-8 -*-
"""スコアの作り方を何通りか固定して、年度ごとの当たり具合を比べる。

閾値の選び方まで込みで検証したいときは backtest.py（leave-one-year-out）を見る。
こちらは「この定義でいくと決めたら、各年でどれくらい当たるか」を並べるもの。
"""
import numpy as np
import pandas as pd

from analyze5 import load
from backtest import auc

pd.set_option('display.width', 220)

DEFS = {
    '既存6基準': [('牡馬', 'male', 1, 1), ('3〜4月生', 'month', 3, 4), ('ノーザンＦ', 'nf', 1, 1),
                 ('母8〜11歳', 'dam_age', 8, 11), ('総額2500〜5999万', 'total_man', 2500, 5999),
                 ('馬体重430kg以上', 'weight', 430, 999)],
    '3基準(牡・価格・馬体重)': [('牡馬', 'male', 1, 1), ('総額2500〜7999万', 'total_man', 2500, 7999),
                            ('馬体重420kg以上', 'weight', 420, 999)],
    '2基準(価格・馬体重)': [('総額2500〜7999万', 'total_man', 2500, 7999),
                        ('馬体重420kg以上', 'weight', 420, 999)],
    '2基準(年内位置)': [('価格が年内下位30%でない', 'price_pct', 0.3, 1.0),
                     ('馬体重が年内平均−10kg以上', 'weight_rel', -10, 999)],
    '3基準(回収重視)': [('牡馬', 'male', 1, 1), ('総額2500〜3999万', 'total_man', 2500, 3999),
                     ('馬体重420kg以上', 'weight', 420, 999)],
    '3基準(価格2500〜5999)': [('牡馬', 'male', 1, 1), ('総額2500〜5999万', 'total_man', 2500, 5999),
                            ('馬体重420kg以上', 'weight', 420, 999)],
    '3基準(価格2500〜4999)': [('牡馬', 'male', 1, 1), ('総額2500〜4999万', 'total_man', 2500, 4999),
                            ('馬体重420kg以上', 'weight', 420, 999)],
    '3基準(年内2〜8割)': [('牡馬', 'male', 1, 1), ('価格が年内2〜8割', 'price_pct', 0.2, 0.8),
                       ('馬体重420kg以上', 'weight', 420, 999)],
    '3基準(年内15〜75%)': [('牡馬', 'male', 1, 1), ('価格が年内15〜75%', 'price_pct', 0.15, 0.75),
                        ('馬体重420kg以上', 'weight', 420, 999)],
    '3基準(年内2〜8割・相対体重)': [('牡馬', 'male', 1, 1), ('価格が年内2〜8割', 'price_pct', 0.2, 0.8),
                             ('馬体重が年内平均−10kg以上', 'weight_rel', -10, 999)],
    '3基準(430kg版)': [('牡馬', 'male', 1, 1), ('総額2500〜3999万', 'total_man', 2500, 3999),
                     ('馬体重430kg以上', 'weight', 430, 999)],
}


def score_of(df, d):
    s = np.zeros(len(df))
    for _, col, lo, hi in d:
        s = s + df[col].between(lo, hi).astype(float).values
    return s


def main():
    df = load(central_only=True)
    for target, tlab in [('win_jra', '中央勝ち上がり'), ('ret1', '回収≥1')]:
        sub = df.dropna(subset=[target])
        print('\n' + '=' * 82)
        print(f'■ 目的変数: {tlab}   n={len(sub)}')
        print('=' * 82)
        rows = []
        for name, d in DEFS.items():
            s = score_of(sub, d)
            row = {'定義': name, '基準数': len(d), '全体AUC': round(auc(sub[target], s), 3)}
            for y in sorted(sub['year'].unique()):
                m = sub['year'] == y
                row[f'{y}'] = round(auc(sub.loc[m, target], s[m.values]), 3)
            rows.append(row)
        print(pd.DataFrame(rows).to_string(index=False))

        print('\n-- スコア別の実績（5年プール）')
        for name, d in DEFS.items():
            s = score_of(sub, d)
            t = sub.assign(_s=s).groupby('_s').agg(
                頭数=('_s', 'size'), 中央勝上=('win_jra', 'mean'), 回収1=('ret1', 'mean'),
                回収中央値=('ret', 'median'), 重賞=('graded', 'sum'))
            t['中央勝上'] = (t['中央勝上'] * 100).round(0)
            t['回収1'] = (t['回収1'] * 100).round(0)
            t['回収中央値'] = t['回収中央値'].round(2)
            print(f'\n  [{name}]')
            print(t.to_string())


if __name__ == '__main__':
    main()

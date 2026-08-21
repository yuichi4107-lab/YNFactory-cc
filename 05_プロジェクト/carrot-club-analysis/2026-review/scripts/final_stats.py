# -*- coding: utf-8 -*-
"""採用する新スコアの実績表を出す（レポートとExcelに載せる数字）。"""
import numpy as np
import pandas as pd

from analyze5 import load
from backtest import auc

pd.set_option('display.width', 220)
pd.set_option('display.max_rows', 300)

NEW = [('牡馬', 'male', 1, 1), ('総額2500〜4999万', 'total_man', 2500, 4999),
       ('馬体重420kg以上', 'weight', 420, 999)]
OLD = [('牡馬', 'male', 1, 1), ('3〜4月生', 'month', 3, 4), ('ノーザンＦ', 'nf', 1, 1),
       ('母8〜11歳', 'dam_age', 8, 11), ('総額2500〜5999万', 'total_man', 2500, 5999),
       ('馬体重430kg以上', 'weight', 430, 999)]


def sc(df, d):
    s = np.zeros(len(df))
    for _, col, lo, hi in d:
        s = s + df[col].between(lo, hi).astype(float).values
    return s


def table(df, s, name):
    t = df.assign(_s=s).groupby('_s').agg(
        頭数=('_s', 'size'), 中央勝上=('win_jra', 'mean'), 勝上中地=('win_all', 'mean'),
        回収1=('ret1', 'mean'), 回収中央値=('ret', 'median'), 回収平均=('ret', 'mean'),
        重賞=('graded', 'sum'))
    for c in ('中央勝上', '勝上中地', '回収1'):
        t[c] = (t[c] * 100).round(0)
    t['回収中央値'] = t['回収中央値'].round(2)
    t['回収平均'] = t['回収平均'].round(2)
    print(f'\n【{name}】')
    print(t.to_string())
    return t


def main():
    df = load(central_only=True).dropna(subset=['win_jra'])
    print(f'中央400口・成績が取れた馬 {len(df)}頭')
    s_new, s_old = sc(df, NEW), sc(df, OLD)
    table(df, s_new, '新スコア（3点満点）5年プール')
    table(df, s_old, '既存6基準 5年プール')

    print('\n【新スコア】年度別の中央勝ち上がり率')
    piv = df.assign(_s=s_new).pivot_table(index='_s', columns='year', values='win_jra',
                                          aggfunc=['mean', 'size'])
    m, n = (piv['mean'] * 100).round(0), piv['size']
    print(m.to_string())
    print(n.to_string())

    print('\n【新スコア】年度別の回収≥1率')
    piv = df.assign(_s=s_new).pivot_table(index='_s', columns='year', values='ret1',
                                          aggfunc='mean')
    print((piv * 100).round(0).to_string())

    print('\n■ 回避条件の再確認（メス×小柄）')
    f = df[df['sex'] != '牡']
    t = f.assign(_b=pd.cut(f['weight'], [0, 409, 419, 429, 999])).groupby('_b', observed=False).agg(
        頭数=('weight', 'size'), 中央勝上=('win_jra', 'mean'), 回収1=('ret1', 'mean'),
        回収中央値=('ret', 'median'))
    t['中央勝上'] = (t['中央勝上'] * 100).round(0)
    t['回収1'] = (t['回収1'] * 100).round(0)
    t['回収中央値'] = t['回収中央値'].round(2)
    print(t.to_string())

    print('\n■ 高額馬（6000万以上）')
    t = df.assign(_b=pd.cut(df['total_man'], [0, 2499, 4999, 5999, 7999, 999999])).groupby(
        '_b', observed=False).agg(頭数=('total_man', 'size'), 中央勝上=('win_jra', 'mean'),
                                  回収1=('ret1', 'mean'), 回収中央値=('ret', 'median'),
                                  重賞=('graded', 'sum'))
    t['中央勝上'] = (t['中央勝上'] * 100).round(0)
    t['回収1'] = (t['回収1'] * 100).round(0)
    t['回収中央値'] = t['回収中央値'].round(2)
    print(t.to_string())

    print('\n■ AUC')
    for lab, d in [('新スコア(3点)', NEW), ('既存6基準', OLD)]:
        s = sc(df, d)
        line = f'  {lab}: 全体 勝上{auc(df["win_jra"], s):.3f} / 回収{auc(df["ret1"], s):.3f}  |'
        for y in sorted(df['year'].unique()):
            mm = (df['year'] == y).values
            line += f' {y}:{auc(df.loc[mm, "win_jra"], s[mm]):.2f}/{auc(df.loc[mm, "ret1"], s[mm]):.2f}'
        print(line)


if __name__ == '__main__':
    main()

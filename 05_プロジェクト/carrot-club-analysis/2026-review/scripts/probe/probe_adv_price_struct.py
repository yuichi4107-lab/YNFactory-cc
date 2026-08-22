# -*- coding: utf-8 -*-
"""敵対的検証：価格の構造（父内相対価格 / 下限 / 絶対額バンドの年度ドリフト）
build() でデータを作る。実行すると再現パートを出す。"""
import io, sys
import numpy as np, pandas as pd
from analyze5 import load, logit, design
from backtest import auc
pd.set_option('display.width', 220)


def build():
    df = load(central_only=True).dropna(subset=['win_jra']).copy()
    df['c_male'] = df['male'].astype(float)
    df['c_price'] = df['total_man'].between(2500, 3999).astype(float)
    df['c_w420'] = (df['weight'] >= 420).astype(float)
    df.loc[df['weight'].isna(), 'c_w420'] = np.nan
    df['logp'] = np.log(df['total_man'])
    df['logp_c'] = df['logp'] - df.groupby('year')['logp'].transform('mean')
    g = df.groupby('sire')['logp_c']
    n = g.transform('size'); s = g.transform('sum')
    df['sire_n'] = n
    df['vs_sire_loo'] = np.where(n >= 2, df['logp_c'] - (s - df['logp_c']) / (n - 1), np.nan)
    df['sire_loo'] = np.where(n >= 2, (s - df['logp_c']) / (n - 1), np.nan)
    df.loc[df['sire_n'] < 4, 'vs_sire_loo'] = np.nan
    g2 = df.groupby(['sire', 'year'])['logp_c']
    n2 = g2.transform('size'); s2 = g2.transform('sum')
    df['crop_n'] = n2
    df['vs_sire_crop'] = np.where(n2 >= 2, df['logp_c'] - (s2 - df['logp_c']) / (n2 - 1), np.nan)
    df['lo2500'] = (df['total_man'] < 2500).astype(float)
    df['hi4000'] = (df['total_man'] >= 4000).astype(float)
    df['ge2500'] = (df['total_man'] >= 2500).astype(float)
    df['price_pct'] = df.groupby('year')['total_man'].rank(pct=True)
    df['pct_top75'] = (df['price_pct'] > 0.25).astype(float)
    return df


BASE = ['c_male', 'c_price', 'c_w420']


def terc(col, sub):
    q = sub[col].quantile([1/3, 2/3]).values
    return pd.cut(sub[col], [-np.inf, q[0], q[1], np.inf], labels=['安', '中', '高'])


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    df = build()
    print('=== 1. 報告数字の再現 ===')
    for col in ['vs_sire_loo', 'vs_sire_crop']:
        sub = df.dropna(subset=[col]).copy()
        sub['t'] = terc(col, sub)
        r = sub.groupby('t', observed=True)['win_jra'].agg(['size', 'mean'])
        print(f'\n[{col}] n={len(sub)}  高{r.loc["高","mean"]*100:.1f}%({r.loc["高","size"]}) '
              f'中{r.loc["中","mean"]*100:.1f}%({r.loc["中","size"]}) 安{r.loc["安","mean"]*100:.1f}%({r.loc["安","size"]})')
        X, names = design(sub, [col]); print(logit(X, sub['win_jra'], names).tail(1).round(3).to_string(index=False))
    print('\n--- 下限 ---')
    print(df.groupby('lo2500')['win_jra'].agg(['size', 'mean']).round(3).to_string())
    X, names = design(df, ['lo2500']); print(logit(X, df['win_jra'], names).tail(1).round(3).to_string(index=False))
    X, names = design(df, ['lo2500', 'hi4000']); print(logit(X, df['win_jra'], names).tail(2).round(3).to_string(index=False))

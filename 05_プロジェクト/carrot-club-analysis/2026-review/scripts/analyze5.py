# -*- coding: utf-8 -*-
"""2020〜2024年度募集の5年パネルを分析する（レポート用の素材を標準出力に出す）。

年度は必ずコントロールする。若い世代（2023年度＝現4歳・2024年度＝現3歳）は
成績が積み上がる途中なので、横断で足すと若い世代が不利に出る。だから
  ・率は年度別に並べる
  ・プールするときは年度ダミー入りのロジスティック回帰を使う

勝ち上がりは2通り出す。
  win_all … netkeibaの通算成績で1勝以上（中央＋地方。従来の定義）
  win_jra … 中央で1勝以上（出走履歴をレース単位で見て判定）
"""
import csv
import io
import json
import os
import sys

import numpy as np
import pandas as pd

from trainers import build_map, resolve_all

BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')
if __name__ == '__main__':      # 取り込まれたときに標準出力を差し替えない
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 220)
pd.set_option('display.max_rows', 300)

CRIT = ['male', 'mar_apr', 'nf', 'dam811', 'price25_60', 'w430']
CRIT_LABEL = {'male': '牡馬', 'mar_apr': '3〜4月生', 'nf': 'ノーザンＦ',
              'dam811': '母8〜11歳', 'price25_60': '総額2500〜5999万',
              'w430': '馬体重430kg以上'}


def load(central_only=False):
    rows = list(csv.DictReader(open(os.path.join(DS, 'panel5.csv'), encoding='utf-8-sig')))
    m = build_map(rows)
    tr = resolve_all(rows, m)
    for r, t in zip(rows, tr):
        r['trainer_key'] = t
    df = pd.DataFrame(rows)
    for c in ['dam_age', 'total_man', 'weight', 'height', 'girth', 'cannon', 'starts',
              'wins', 'prize_jra', 'prize_nar', 'prize', 'ret', 'month', 'kuchi', 'graded']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df['year'] = df['year'].astype(int)
    df = df[df['horse_id'].astype(str) != ''].copy()

    rs = {}
    p = os.path.join(DS, 'race_summary.json')
    if os.path.exists(p):
        rs = json.load(open(p, encoding='utf-8'))
    df['key'] = df['year'].astype(str) + '#' + df['no'].astype(str)
    for col in ['jra_starts', 'jra_wins', 'nar_starts', 'nar_wins']:
        df[col] = df['key'].map(lambda k: (rs.get(k) or {}).get(col))
    df['win_all'] = (df['wins'].fillna(0) >= 1).astype(int)
    df['win_jra'] = (df['jra_wins'].fillna(0) >= 1).astype(int)
    df.loc[df['jra_wins'].isna(), 'win_jra'] = np.nan
    df['ret1'] = (df['ret'] >= 1).astype(int)
    df['nf'] = df['farm'].astype(str).str.contains('ノーザン').astype(int)
    df['male'] = (df['sex'] == '牡').astype(int)
    df['mar_apr'] = df['month'].isin([3, 4]).astype(int)
    df['dam811'] = df['dam_age'].between(8, 11).astype(int)
    df['price25_60'] = df['total_man'].between(2500, 5999).astype(int)
    df['w430'] = (df['weight'] >= 430).astype(int)
    df.loc[df['weight'].isna(), 'w430'] = np.nan
    # 募集価格は年々上がっている（中央値2800万→4000万）ので、
    # 絶対額のほかに「その年の中での位置」も持たせる
    df['price_pct'] = df.groupby('year')['total_man'].rank(pct=True)
    df['price_rel'] = df['total_man'] / df.groupby('year')['total_man'].transform('median')
    df['weight_rel'] = df['weight'] - df.groupby('year')['weight'].transform('mean')
    df['score6'] = df[CRIT].sum(axis=1)
    if central_only:
        df = df[df['kuchi'] == 400].copy()
    return df


def logit(X, y, names, ridge=1e-6):
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    b = np.zeros(X.shape[1])
    H = np.eye(X.shape[1])
    for _ in range(80):
        p = 1 / (1 + np.exp(-(X @ b)))
        W = np.clip(p * (1 - p), 1e-9, None)
        H = X.T @ (X * W[:, None]) + ridge * np.eye(X.shape[1])
        step = np.linalg.solve(H, X.T @ (y - p) - ridge * b)
        b = b + step
        if np.max(np.abs(step)) < 1e-9:
            break
    se = np.sqrt(np.diag(np.linalg.inv(H)))
    return pd.DataFrame({'変数': names, '係数': b, 'SE': se, 'z': b / se,
                         'オッズ比': np.exp(b)})


def design(df, cols):
    parts, names = [], []
    for y in sorted(df['year'].unique()):
        parts.append((df['year'] == y).astype(float).values)
        names.append(f'年度{y}')
    for c in cols:
        parts.append(df[c].astype(float).values)
        names.append(CRIT_LABEL.get(c, c))
    return np.column_stack(parts), names


def rate_table(df, by):
    g = df.groupby(by, dropna=False)
    return pd.DataFrame({
        '頭数': g.size(),
        '勝上(中+地)': g['win_all'].mean().mul(100).round(0),
        '勝上(中央)': g['win_jra'].mean().mul(100).round(0),
        '回収≥1': g['ret1'].mean().mul(100).round(0),
        '回収中央値': g['ret'].median().round(2),
        '回収平均': g['ret'].mean().round(2),
        '重賞': g['graded'].sum(),
    })


def by_year(df, col, label):
    print(f'\n【{label}】年度別 勝ち上がり率(中央)  ※かっこ内は頭数')
    piv = df.pivot_table(index=col, columns='year', values='win_jra',
                         aggfunc=['mean', 'size'], dropna=False)
    mean, size = piv['mean'] * 100, piv['size']
    print('    ' + ''.join(f'{y:>12}' for y in mean.columns))
    for idx in mean.index:
        cells = []
        for y in mean.columns:
            mv, nv = mean.loc[idx, y], size.loc[idx, y]
            cells.append(f'{int(mv):>4}%({int(nv):>2})' if pd.notna(mv) else f'{"-":>9}')
        print(f'  {str(idx):<10}' + ''.join(f'{c:>12}' for c in cells))


def section(title):
    print('\n' + '=' * 82)
    print('■ ' + title)
    print('=' * 82)


def main():
    central = '--central' in sys.argv
    df = load(central_only=central)
    print(f'対象: {len(df)}頭' + ('（中央400口のみ）' if central else '（地方100口を含む全馬）'))

    section('パネル全体（年度＝成績の積み上がり具合が違う）')
    print(rate_table(df, 'year').to_string())
    g = df.groupby('year')
    print('\n' + pd.DataFrame({
        '出走あり%': (g['starts'].apply(lambda s: (s.fillna(0) > 0).mean()) * 100).round(0),
        '平均出走数': g['starts'].mean().round(1),
        '平均賞金(万)': g['prize'].mean().round(0),
        '地方のみで勝った馬': g.apply(lambda d: int(((d['win_all'] == 1) & (d['win_jra'] == 0)).sum()),
                                      include_groups=False),
    }).to_string())

    section('既存6基準（2020〜2022年度で作ったもの）をそのまま5年に当てる')
    print(rate_table(df, 'score6').rename_axis('6点スコア').to_string())
    by_year(df, 'score6', '6点スコア')
    print('\n-- 新2年だけ（＝完全な外部検証）')
    print(rate_table(df[df['year'] >= 2023], 'score6').rename_axis('6点スコア').to_string())

    section('各基準の効き方（年度ダミーつきロジスティック回帰）')
    for target, tlab in [('win_jra', '中央勝ち上がり'), ('win_all', '勝ち上がり(中+地)'),
                         ('ret1', '回収≥1')]:
        sub = df.dropna(subset=['dam_age', 'total_man', 'weight', target])
        X, names = design(sub, CRIT)
        print(f'\n-- 目的変数: {tlab}   n={len(sub)}')
        print(logit(X, sub[target], names).round(3).to_string(index=False))

    section('要因ごとの内訳')
    for col, label in [('sex', '性別'), ('month', '生まれ月'), ('farm', '生産・提供牧場')]:
        print(f'\n【{label}】')
        print(rate_table(df, col).to_string())
    for col, bins, label in [
        ('dam_age', [0, 5, 7, 9, 11, 13, 15, 30], '母年齢'),
        ('total_man', [0, 1999, 2499, 3999, 5999, 7999, 999999], '募集総額(万)'),
        ('weight', [0, 409, 429, 449, 469, 999], '募集時馬体重'),
    ]:
        print(f'\n【{label}】')
        print(rate_table(df.assign(_b=pd.cut(df[col], bins)), '_b').to_string())
    print('\n【メス×小柄】')
    sub = df[df['sex'] != '牡']
    print(rate_table(sub.assign(_b=pd.cut(sub['weight'], [0, 429, 999])), '_b').to_string())

    section('厩舎（5年・4頭以上）')
    t = rate_table(df, 'trainer_key')
    t = t[t['頭数'] >= 4].sort_values(['回収≥1', '勝上(中央)'], ascending=False)
    print(t.to_string())

    section('父（5年・4頭以上）')
    t = rate_table(df, 'sire')
    t = t[t['頭数'] >= 4].sort_values(['回収≥1', '勝上(中央)'], ascending=False)
    print(t.to_string())


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""価格基準を「安すぎない」「高すぎない」の2本に割ってよいかを検証する。

複数エージェントによる探索で唯一生き延びた候補が「募集価格の下限を独立した基準にする」だった。
現行の3基準は価格を 2500〜3999万 の1本にまとめており、2500万未満と4000万以上を
どちらも0点として同一視している。実際には
  ・2500万未満   … 中央勝ち上がりが落ちる（走らない）
  ・4000万以上   … 走るが回収が伸びない
と効き方が違うので、割ったほうがよいのではないか、という主張。

閾値の選択まで含めて leave-one-year-out で確かめる（その年を見ずに閾値を選ぶ）。
"""
import io
import sys

import numpy as np
import pandas as pd

from analyze5 import design, load, logit
from backtest import auc

if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 200)

S3 = [('牡馬', lambda d: d['male'] == 1),
      ('総額2500〜3999万', lambda d: d['total_man'].between(2500, 3999)),
      ('馬体重420kg以上', lambda d: d['weight'] >= 420)]

FLOOR_ABS = [2000, 2400, 2500, 2800, 3000]
FLOOR_PCT = [0.15, 0.20, 0.25, 0.30]


def score(df, terms):
    s = np.zeros(len(df))
    for _, f in terms:
        s = s + f(df).astype(float).values
    return s


def floor_terms(kind, cut):
    if kind == 'abs':
        return (f'総額{cut}万以上', lambda d, c=cut: d['total_man'] >= c)
    return (f'価格が年内下位{int(cut*100)}%でない', lambda d, c=cut: d['price_pct'] > c)


def pick_floor(train, target):
    """訓練年だけを見て、下限の指標と閾値を選ぶ（zが最大のもの）。"""
    best = None
    for kind, cuts in (('abs', FLOOR_ABS), ('pct', FLOOR_PCT)):
        for c in cuts:
            name, f = floor_terms(kind, c)
            v = f(train).astype(float)
            if v.nunique() < 2:
                continue
            X, names = design(train.assign(_v=v), ['_v'])
            z = float(logit(X, train[target], names).iloc[-1]['z'])
            if best is None or z > best[0]:
                best = (z, kind, c)
    return best


def main():
    df = load(central_only=True)
    print('■ 価格を3水準に割ったときの実績（5年・中央400口）')
    sub = df.dropna(subset=['win_jra'])
    band = pd.cut(sub['total_man'], [0, 2499, 3999, 999999],
                  labels=['〜2499万', '2500〜3999万', '4000万〜'])
    t = sub.assign(_b=band).groupby('_b', observed=False).agg(
        頭数=('win_jra', 'size'), 中央勝上=('win_jra', 'mean'), 回収1=('ret1', 'mean'),
        回収中央値=('ret', 'median'), 重賞=('graded', 'sum'))
    t['中央勝上'] = (t['中央勝上'] * 100).round(0)
    t['回収1'] = (t['回収1'] * 100).round(0)
    t['回収中央値'] = t['回収中央値'].round(2)
    print(t.to_string())

    print('\n■ 年度別に「2500万未満」が毎年悪いか（中央勝ち上がり）')
    piv = sub.assign(cheap=sub['total_man'] < 2500).pivot_table(
        index='cheap', columns='year', values='win_jra', aggfunc=['mean', 'size'])
    print((piv['mean'] * 100).round(0).to_string())
    print(piv['size'].to_string())

    for target, tlab in [('win_jra', '中央勝ち上がり'), ('ret1', '回収≥1')]:
        d = df.dropna(subset=[target])
        print(f'\n{"=" * 78}\n■ 入れ子leave-one-year-out（目的変数: {tlab}）\n{"=" * 78}')
        rows = []
        for y in sorted(d['year'].unique()):
            tr, te = d[d['year'] != y], d[d['year'] == y]
            base_te = score(te, S3)
            z, kind, cut = pick_floor(tr, target)
            name, f = floor_terms(kind, cut)
            add_te = base_te + f(te).astype(float).values
            rows.append({'検証年度': y, '頭数': len(te),
                         '訓練年で選ばれた下限': name, '訓練z': round(z, 2),
                         '3基準AUC': round(auc(te[target], base_te), 3),
                         '＋下限AUC': round(auc(te[target], add_te), 3)})
        bt = pd.DataFrame(rows)
        bt['差'] = (bt['＋下限AUC'] - bt['3基準AUC']).round(3)
        print(bt.to_string(index=False))
        print(f'  平均 3基準={bt["3基準AUC"].mean():.3f} / ＋下限={bt["＋下限AUC"].mean():.3f}'
              f' / 差={bt["差"].mean():+.3f}  改善した年 {int((bt["差"] > 0).sum())}/{len(bt)}')

    print(f'\n{"=" * 78}\n■ 4基準にしたときのスコア別実績（5年プール・当てはめ）\n{"=" * 78}')
    S4 = [S3[0], ('総額2500万以上', lambda d: d['total_man'] >= 2500), S3[1], S3[2]]
    s4 = score(sub, S4)
    t = sub.assign(_s=s4).groupby('_s').agg(
        頭数=('win_jra', 'size'), 中央勝上=('win_jra', 'mean'), 回収1=('ret1', 'mean'),
        回収中央値=('ret', 'median'), 重賞=('graded', 'sum'))
    t['中央勝上'] = (t['中央勝上'] * 100).round(0)
    t['回収1'] = (t['回収1'] * 100).round(0)
    t['回収中央値'] = t['回収中央値'].round(2)
    print(t.to_string())
    print(f'\n  4基準 AUC: 中央勝ち上がり={auc(sub["win_jra"], s4):.3f} / '
          f'回収≥1={auc(sub["ret1"], s4):.3f}')
    s3 = score(sub, S3)
    print(f'  3基準 AUC: 中央勝ち上がり={auc(sub["win_jra"], s3):.3f} / '
          f'回収≥1={auc(sub["ret1"], s3):.3f}')

    print('\n■ 年度別AUC')
    for lab, s in [('3基準', s3), ('4基準', s4)]:
        line = f'  {lab}: '
        for y in sorted(sub['year'].unique()):
            m = (sub['year'] == y).values
            line += f'{y}:{auc(sub.loc[m, "win_jra"], s[m]):.2f}/{auc(sub.loc[m, "ret1"], s[m]):.2f} '
        print(line)


if __name__ == '__main__':
    main()

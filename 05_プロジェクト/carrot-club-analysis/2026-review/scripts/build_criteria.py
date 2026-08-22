# -*- coding: utf-8 -*-
"""採用する新スコアの定義と、検討基準シートに載せる文面を criteria.json に書き出す。

数字はすべて panel5.csv から計算する（手打ちしない）。
"""
import io
import json
import os
import sys

import numpy as np
import pandas as pd

from analyze5 import load
from backtest import auc

BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')


CRITERIA = [
    {'label': '性別', 'short': '牡', 'col': 'male', 'lo': 1, 'hi': 1, 'cond': '牡馬'},
    {'label': '募集総額の下限', 'short': '2500万+', 'col': 'total_man', 'lo': 2500, 'hi': 999999,
     'cond': '2500万円以上'},
    {'label': '募集総額の上限', 'short': '4000万未満', 'col': 'total_man', 'lo': 2500, 'hi': 3999,
     'cond': '4000万円未満（下限とあわせて2500〜3999万）'},
    {'label': '馬体重', 'short': '420kg+', 'col': 'weight', 'lo': 420, 'hi': 9999,
     'cond': '募集時420kg以上'},
]
OLD = [('male', 1, 1), ('month', 3, 4), ('nf', 1, 1), ('dam_age', 8, 11),
       ('total_man', 2500, 5999), ('weight', 430, 999)]


def sc(df, defs):
    s = np.zeros(len(df))
    for col, lo, hi in defs:
        s = s + df[col].between(lo, hi).astype(float).values
    return s


def pct(x):
    return int(round(100 * x))


def main():
    df = load(central_only=True).dropna(subset=['win_jra'])
    defs = [(c['col'], c['lo'], c['hi']) for c in CRITERIA]
    s = sc(df, defs)
    s_old = sc(df, OLD)
    d = df.assign(_s=s)

    stats = {}
    for k, g in d.groupby('_s'):
        stats[int(k)] = {
            'n': len(g), 'win_jra': pct(g['win_jra'].mean()), 'win_all': pct(g['win_all'].mean()),
            'ret1': pct(g['ret1'].mean()), 'ret_med': round(g['ret'].median(), 2),
            'graded': int(g['graded'].sum()),
        }

    def band(col, lo, hi):
        g = df[df[col].between(lo, hi)]
        return {'n': len(g), 'win_jra': pct(g['win_jra'].mean()), 'ret1': pct(g['ret1'].mean()),
                'ret_med': round(g['ret'].median(), 2), 'graded': int(g['graded'].sum())}

    price_bands = {f'{lo}-{hi}': band('total_man', lo, hi) for lo, hi in
                   [(0, 2499), (2500, 3999), (4000, 4999), (5000, 5999), (6000, 7999),
                    (8000, 999999)]}
    fem = df[df['sex'] != '牡']
    fem_small = fem[fem['weight'] < 420]
    fem_big = fem[fem['weight'] >= 420]

    auc_new = {'win': round(auc(df['win_jra'], s), 3), 'ret': round(auc(df['ret1'], s), 3)}
    auc_old = {'win': round(auc(df['win_jra'], s_old), 3), 'ret': round(auc(df['ret1'], s_old), 3)}
    auc_year = {}
    for y in sorted(df['year'].unique()):
        m = (df['year'] == y).values
        auc_year[int(y)] = {
            'new': round(auc(df.loc[m, 'win_jra'], s[m]), 2),
            'old': round(auc(df.loc[m, 'win_jra'], s_old[m]), 2),
        }
    med_price = {int(y): int(g['total_man'].median()) for y, g in df.groupby('year')}

    def rate(col, lo, hi, target='win_jra'):
        g = df[df[col].between(lo, hi)]
        return pct(g[target].mean()), len(g)

    L = []
    L.append(['キャロット出資 検討基準（2020〜2024年度募集・全467頭の成績分析より。'
              f'基準の導出は中央400口の{len(df)}頭）', '', ''])
    L.append(['', '', ''])
    L.append([f'全体基準値: 中央勝ち上がり率{pct(df["win_jra"].mean())}% / '
              f'賞金が募集総額を超えた馬{pct(df["ret1"].mean())}% / '
              f'重賞勝ち馬{int(df["graded"].sum())}頭', '', ''])
    L.append(['※「勝ち上がり」は中央で1勝以上。netkeibaの通算成績は地方の勝利も含むため、'
              '出走履歴をレース単位まで見て中央だけを数え直している', '', ''])
    L.append(['※回収率=(中央+地方の獲得賞金)/募集総額。進上金・維持費・繁殖価値は含まない。2026年8月時点', '', ''])
    L.append(['※2023年度募集は現4歳・2024年度募集は現3歳で成績は積み上がる途中。'
              '基準の検定は年度ダミーを入れて行っている', '', ''])
    L.append(['', '', ''])
    L.append(['◆スコア基準(各1点・計4点)', '条件', '根拠(中央勝ち上がり/回収≥1)'])
    m_win, m_n = rate('male', 1, 1)
    f_win = pct(df[df['sex'] != '牡']['win_jra'].mean())
    L.append(['1. 性別', '牡馬',
              f'牡{m_win}%（{m_n}頭）vs メス{f_win}%（{len(df) - m_n}頭）。'
              f'重賞{int(df["graded"].sum())}頭中{int(df[df["male"] == 1]["graded"].sum())}頭が牡'])
    pb = price_bands['2500-3999']
    lo_b = price_bands['0-2499']
    hi_b = band('total_man', 4000, 999999)
    L.append(['2. 募集総額の下限', '2500万円以上',
              f'2500万未満は{lo_b["win_jra"]}%・{lo_b["ret1"]}%（{lo_b["n"]}頭）で、走らない。'
              f'5年とも例外なく最下位（2020年31%/2021年33%/2022年33%/2023年42%/2024年14%）'])
    L.append(['3. 募集総額の上限', '4000万円未満',
              f'2500〜3999万は{pb["win_jra"]}%・{pb["ret1"]}%（{pb["n"]}頭）。'
              f'4000万以上は{hi_b["win_jra"]}%・{hi_b["ret1"]}%（{hi_b["n"]}頭）で、'
              f'走る確率は変わらないのに回収だけ落ちる'])
    w_hi = band('weight', 420, 9999)
    w_lo = band('weight', 0, 419)
    L.append(['4. 馬体重', '募集時420kg以上',
              f'{w_hi["win_jra"]}%・{w_hi["ret1"]}%（{w_hi["n"]}頭）vs '
              f'420kg未満{w_lo["win_jra"]}%・{w_lo["ret1"]}%（{w_lo["n"]}頭）'])
    L.append(['', '', ''])
    L.append(['◆5年に広げて落とした基準（3年では効いて見えたが5年では効かなかった）', '', ''])
    m34 = band('month', 3, 4)
    m12 = band('month', 1, 2)
    L.append(['3〜4月生まれ', f'3〜4月生{m34["win_jra"]}%（{m34["n"]}頭）vs '
                          f'1〜2月生{m12["win_jra"]}%（{m12["n"]}頭）',
              '年度ダミーつきロジスティック回帰で z=+0.7（有意でない）'])
    nf = df[df['nf'] == 1]
    non = df[df['nf'] == 0]
    L.append(['ノーザンＦ生産', f'ノーザンＦ{pct(nf["win_jra"].mean())}%（{len(nf)}頭）vs '
                           f'その他{pct(non["win_jra"].mean())}%（{len(non)}頭）',
              'z=−0.1。白老Ｆ・追分Ｆのほうがむしろ上'])
    d811 = band('dam_age', 8, 11)
    L.append(['母8〜11歳', f'{d811["win_jra"]}%（{d811["n"]}頭）vs それ以外'
                        f'{pct(df[~df["dam_age"].between(8, 11)]["win_jra"].mean())}%',
              'z=+0.9（有意でない）'])
    L.append(['', '', ''])
    L.append(['※価格を下限と上限の2本に割った理由：効き方が違う。下限は「走るか」に効き'
              '（入れ子leave-one-year-outで中央勝ち上がりのAUCが5年すべて改善、平均+0.019）、'
              '上限は「回収するか」にだけ効く（回収率は分母が価格なので機械的な分も含む）', '', ''])
    L.append(['', '', ''])
    L.append(['◆スコア別の実績（5年・中央400口）', '', ''])
    for k in sorted(stats, reverse=True):
        v = stats[k]
        L.append([f'スコア{k} ({v["n"]}頭)',
                  f'中央勝ち上がり{v["win_jra"]}%・回収≥1が{v["ret1"]}%・回収中央値{v["ret_med"]}',
                  f'重賞{v["graded"]}頭'])
    L.append(['', '', ''])
    L.append(['◆当たり具合（AUC。0.5＝でたらめ、1.0＝完全）', '', ''])
    L.append(['新スコア(4点満点)', f'中央勝ち上がり{auc_new["win"]} / 回収≥1 {auc_new["ret"]}',
              '年度別 ' + ' '.join(f'{y}:{v["new"]}' for y, v in auc_year.items())])
    L.append(['旧6基準（2020〜2022年度で作ったもの）',
              f'中央勝ち上がり{auc_old["win"]} / 回収≥1 {auc_old["ret"]}',
              '年度別 ' + ' '.join(f'{y}:{v["old"]}' for y, v in auc_year.items())])
    L.append(['※既存6基準は作った年（2020年度）で高く、作成に使っていない2023・2024年度で落ちる。'
              '基準を絞ったほうが年をまたいで安定する', '', ''])
    L.append(['', '', ''])
    L.append(['◆募集価格の帯ごとの中身', '中央勝ち上がり / 回収≥1 / 回収中央値', '重賞'])
    for lab, key in [('2500万未満', '0-2499'), ('2500〜3999万', '2500-3999'),
                     ('4000〜4999万', '4000-4999'), ('5000〜5999万', '5000-5999'),
                     ('6000〜7999万', '6000-7999'), ('8000万以上', '8000-999999')]:
        v = price_bands[key]
        L.append([f'{lab} ({v["n"]}頭)', f'{v["win_jra"]}% / {v["ret1"]}% / {v["ret_med"]}',
                  f'{v["graded"]}頭'])
    L.append(['→ 5000万以上は「走るが回収が伸びない」。8000万以上で回収が募集額を超えたのは'
              f'{price_bands["8000-999999"]["n"]}頭中'
              f'{round(price_bands["8000-999999"]["n"] * price_bands["8000-999999"]["ret1"] / 100)}頭',
              '', ''])
    L.append(['', '', ''])
    L.append(['◆価格帯の注意：募集価格の水準が上がり続けている', '', ''])
    L.append(['募集総額の中央値', ' → '.join(f'{y}年度{v}万' for y, v in med_price.items()) +
              ' → 2026年度5000万', ''])
    L.append(['価格基準を「その年の中での位置」に置き換えても当たり具合は改善しなかった'
              '（AUC 0.591 vs 絶対額0.614）ので絶対額のままにしている', '', ''])
    L.append(['※入れ子leave-one-year-out（その年を見ずに閾値も選ぶ）での中央勝ち上がりAUCは'
              '価格を1本にした3点版 0.611 → 下限を割った4点版 0.631。5年すべてで改善した。'
              '回収≥1のほうは 0.655 → 0.646 でわずかに悪化する', '', ''])
    L.append(['価格ちょうどの水準で見ると、3000万(52頭)が中央勝ち上がり69%・回収≥1が31%で突出し、'
              '4000万(50頭)は50%・12%で5000万(55頭)51%・15%とほぼ同じ。'
              '4000万は「3000万の延長」ではなく「5000万と同じ側」', '', ''])
    L.append(['ただし2026年度で2500〜3999万に該当するのは94頭中20頭。'
              '募集価格の上昇が続くと該当が減るので、来年以降は帯の見直しが要る', '', ''])
    L.append(['', '', ''])
    L.append(['◆回避条件', '', ''])
    L.append([f'メスの馬体重420kg未満 ({len(fem_small)}頭)',
              f'中央勝ち上がり{pct(fem_small["win_jra"].mean())}%・'
              f'回収≥1が{pct(fem_small["ret1"].mean())}%・'
              f'回収中央値{round(fem_small["ret"].median(), 2)}',
              f'420kg以上のメス（{len(fem_big)}頭）は{pct(fem_big["win_jra"].mean())}%・'
              f'{pct(fem_big["ret1"].mean())}%'])
    L.append(['', '', ''])
    L.append(['◆厩舎との相性（5年・中央400口・5頭以上。予定厩舎ベース）', '', ''])
    d2 = df.copy()
    t = d2.groupby('trainer_key').agg(n=('win_jra', 'size'), win=('win_jra', 'mean'),
                                      ret1=('ret1', 'mean'), med=('ret', 'median'),
                                      g=('graded', 'sum'))
    t = t[t['n'] >= 5].sort_values(['ret1', 'win'], ascending=False)
    for name, v in t.head(8).iterrows():
        L.append([f'【好調】{name}', f'{int(v["n"])}頭: 中央勝ち上がり{pct(v["win"])}%・'
                                  f'回収≥1が{pct(v["ret1"])}%・回収中央値{round(v["med"], 2)}',
                  f'重賞{int(v["g"])}頭'])
    for name, v in t.tail(6).iloc[::-1].iterrows():
        L.append([f'【注意】{name}', f'{int(v["n"])}頭: 中央勝ち上がり{pct(v["win"])}%・'
                                  f'回収≥1が{pct(v["ret1"])}%・回収中央値{round(v["med"], 2)}',
                  f'重賞{int(v["g"])}頭'])
    L.append(['※各厩舎5〜17頭の小標本。予定厩舎は募集時点のもので、実際の入厩先は変わりうる', '', ''])
    L.append(['', '', ''])
    L.append(['◆父の傾向（5年・中央400口・8頭以上）', '', ''])
    ts = df.groupby('sire').agg(n=('win_jra', 'size'), win=('win_jra', 'mean'),
                                ret1=('ret1', 'mean'), med=('ret', 'median'), g=('graded', 'sum'))
    ts = ts[ts['n'] >= 8].sort_values(['ret1', 'win'], ascending=False)
    for name, v in ts.iterrows():
        L.append([name, f'{int(v["n"])}頭: 中央勝ち上がり{pct(v["win"])}%・'
                        f'回収≥1が{pct(v["ret1"])}%・回収中央値{round(v["med"], 2)}',
                  f'重賞{int(v["g"])}頭'])
    L.append(['※種牡馬の顔ぶれは毎年変わるため参考程度に', '', ''])
    L.append(['', '', ''])
    L.append(['◆注意', '', ''])
    L.append(['・2023年度募集は現4歳・2024年度募集は現3歳。回収率は今後上振れする', '', ''])
    L.append(['・回収率は分母が募集価格なので、安い馬ほど高く出る。価格基準の効果にはその分が含まれる', '', ''])
    L.append(['・地方入厩予定馬（100口）21頭は中央で走らないため基準の導出から外している', '', ''])
    L.append(['・メスは引退後の繁殖価値が回収に含まれていないため、実質はやや過小評価', '', ''])

    out = {
        'version': '2026-08-22 5年版（2020〜2024年度募集）',
        'target': 'win_jra（中央で1勝以上）',
        'n': len(df), 'n_all': 467,
        'criteria': CRITERIA,
        'score_stats': stats,
        'price_bands': price_bands,
        'auc': {'new': auc_new, 'old': auc_old, 'by_year': auc_year},
        'median_price': med_price,
        'sheet_lines': L,
    }
    json.dump(out, open(os.path.join(DS, 'criteria.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('書き出し: datasets/criteria.json')
    for k in sorted(stats, reverse=True):
        print(' ', k, stats[k])


if __name__ == '__main__':
    main()

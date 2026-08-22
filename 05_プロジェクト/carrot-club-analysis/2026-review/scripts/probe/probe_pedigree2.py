# -*- coding: utf-8 -*-
"""probe_pedigree.py の続き。ロベルト系シグナルの頑健性と、個別父・bms群の追試。"""
import io, os, sys
import numpy as np
import pandas as pd
from analyze5 import load, logit, design
from probe_pedigree import add_bms, LINE, FIRST_CROP, desc, yearly, report
from backtest import auc

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 250)
pd.set_option('display.max_rows', 400)


def sec(t):
    print('\n' + '=' * 90)
    print('■ ' + t)
    print('=' * 90)


def main():
    df = load(central_only=True)
    df = add_bms(df)
    df['line'] = df['sire'].map(LINE).fillna('未分類')
    df['rob'] = (df['line'] == 'ロベルト系').astype(int)
    df['price2539'] = df['total_man'].between(2500, 3999).astype(int)
    df['w420'] = (df['weight'] >= 420).astype(float)
    df.loc[df['weight'].isna(), 'w420'] = np.nan

    sec('A. ロベルト系（エピファネイア/モーリス/ルヴァンスレーヴ/ナダル/スクリーンヒーロー）')
    print(desc(df, 'rob').to_string())
    print('\n内訳')
    print(desc(df[df['rob'] == 1], 'sire').to_string())
    print('\n年度別 win_jra')
    yearly(df, 'rob')
    print('\n年度別 ret1')
    yearly(df, 'rob', 'ret1')
    print('\n[単独] 年度ダミー+ロベルト')
    report(df, ['rob'])
    print('\n[価格・性] 追加')
    report(df, ['rob'], extra=['price_pct', 'male'])
    print('\n[現行3基準] 追加（牡・2500-3999万・420kg以上）')
    report(df, ['rob'], extra=['male', 'price2539', 'w420'])
    print('\n[牧場・母年齢・生月も追加]')
    report(df, ['rob'], extra=['male', 'price2539', 'w420', 'nf', 'dam811', 'mar_apr'])

    print('\nロベルト系を1頭ずつ抜いたときのz（win_jra, 3基準込み）')
    for s in sorted(df.loc[df['rob'] == 1, 'sire'].unique()):
        d2 = df[~((df['rob'] == 1) & (df['sire'] == s))]
        d2 = d2.dropna(subset=['w420', 'win_jra'])
        X, names = design(d2, ['rob', 'male', 'price2539', 'w420'])
        t = logit(X, d2['win_jra'], names)
        z = float(t.loc[t['変数'] == 'rob', 'z'].iloc[0])
        n = int((d2['rob'] == 1).sum())
        print(f'  除外={s:<14} 残ロベルト n={n:>3}  z={z:+.2f}')

    print('\n個別の父（4頭以上）')
    t = desc(df, 'sire')
    print(t[t['頭数'] >= 5].sort_values('勝上中央', ascending=False).to_string())

    sec('B. モーリス／エピファネイア単独')
    for s in ['モーリス', 'エピファネイア', 'ドゥラメンテ', 'ロードカナロア', 'ドレフォン', 'キズナ', 'レイデオロ']:
        df['S_' + s] = (df['sire'] == s).astype(int)
    for s in ['モーリス', 'エピファネイア']:
        print(f'\n--- {s}')
        yearly(df, 'S_' + s)
        report(df, ['S_' + s], extra=['male', 'price2539', 'w420'])

    sec('C. 増分の価値（AUC）: 現行3基準 vs 3基準+ロベルト系')
    d = df.dropna(subset=['w420', 'win_jra']).copy()
    base3 = d['male'] + d['price2539'] + d['w420']
    print(f'n={len(d)}')
    print(f'  3基準スコア        AUC(win_jra)={auc(d["win_jra"], base3):.3f}  AUC(ret1)={auc(d["ret1"], base3):.3f}')
    print(f'  3基準+ロベルト     AUC(win_jra)={auc(d["win_jra"], base3 + d["rob"]):.3f}  AUC(ret1)={auc(d["ret1"], base3 + d["rob"]):.3f}')
    print(f'  ロベルト単独       AUC(win_jra)={auc(d["win_jra"], d["rob"]):.3f}  AUC(ret1)={auc(d["ret1"], d["rob"]):.3f}')
    print('\n年度別 AUC')
    for y in sorted(d['year'].unique()):
        dy = d[d['year'] == y]
        b = dy['male'] + dy['price2539'] + dy['w420']
        print(f'  {y}: 3基準={auc(dy["win_jra"], b):.3f}  +ロベルト={auc(dy["win_jra"], b + dy["rob"]):.3f}')

    print('\n4基準スコア（牡+価格帯+420kg+ロベルト）別の実績')
    d['score4'] = base3 + d['rob']
    print(desc(d, 'score4').to_string())
    print('\n年度別 win_jra')
    yearly(d, 'score4')

    sec('D. bms 群（回収率まわり）')
    dd = df.dropna(subset=['bms']).copy()
    for name, mask in [('bms=ダイワメジャー', dd['bms'] == 'ダイワメジャー'),
                       ('bms=クロフネ', dd['bms'] == 'クロフネ'),
                       ('bmsダート系(クロフネ/ゴールドアリュール/フレンチデピュティ/ウォーエンブレム/エンパイアメーカー)',
                        dd['bms'].isin(['クロフネ', 'ゴールドアリュール', 'フレンチデピュティ',
                                        'ウォーエンブレム', 'エンパイアメーカー', 'シンボリクリスエス']))]:
        dd['_x'] = mask.astype(int)
        print(f'\n--- {name}  n1={int(dd["_x"].sum())}')
        print(desc(dd, '_x').to_string())
        report(dd, ['_x'], extra=['male', 'price2539', 'w420'])
        yearly(dd, '_x')
        yearly(dd, '_x', 'ret1')

    sec('E. 父×性別 / 父×価格帯の交互作用（ロベルト系）')
    d = df.dropna(subset=['w420']).copy()
    d['rob_male'] = d['rob'] * d['male']
    report(d, ['rob', 'male', 'rob_male'], extra=['price2539', 'w420'])
    print('\nロベルト系×牡 の実績')
    d['cell'] = np.where(d['rob'] == 1, 'ロベルト', '他') + '/' + np.where(d['male'] == 1, '牡', '牝')
    print(desc(d, 'cell').to_string())

    sec('F. 2026年度の該当頭数（参考。採点対象がどれだけ絞れるか）')
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'bosyu_2026.csv')
    if os.path.exists(p):
        b = pd.read_csv(p, encoding='utf-8-sig')
        print(list(b.columns))
        for c in b.columns:
            if '父' in c or 'sire' in c.lower():
                b['line'] = b[c].map(LINE).fillna('未分類')
                print(b['line'].value_counts().to_string())
                print('未分類:', sorted(set(b.loc[b['line'] == '未分類', c])))
                break
    else:
        print('bosyu_2026.csv なし')


if __name__ == '__main__':
    main()

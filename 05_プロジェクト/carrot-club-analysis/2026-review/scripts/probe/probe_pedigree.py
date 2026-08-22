# -*- coding: utf-8 -*-
"""血統（父・母の父・父系・ニックス・新種牡馬）を検定する。既存ファイルは触らない。"""
import io, os, sys
import numpy as np
import pandas as pd
from analyze5 import load, logit, design

if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 250)
pd.set_option('display.max_rows', 400)
BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')

# ---------------- 父系（手作業マッピング。外部知識） ----------------
LINE = {}


def put(line, names):
    for n in names.split():
        LINE[n] = line


put('サンデー系', 'ディープインパクト ハーツクライ ダイワメジャー キズナ サトノダイヤモンド キタサンブラック ブラックタイド リアルスティール ジャスタウェイ オルフェーヴル シルバーステート ディープブリランテ イスラボニータ アドマイヤマーズ トーセンラー ミッキーアイル リアルインパクト サトノアラジン シュヴァルグラン フィエールマン ダノンシャンティ コントレイル インディチャンプ キンシャサノキセキ スワーヴリチャード アルアイン ゴールドドリーム クリソベリル')
LINE['Saxon Warrior'] = 'サンデー系'
put('キングマンボ系', 'ロードカナロア キングカメハメハ ドゥラメンテ レイデオロ ルーラーシップ リオンディーズ サートゥルナーリア ミッキーロケット トゥザワールド エイシンフラッシュ')
put('ロベルト系', 'エピファネイア モーリス スクリーンヒーロー ルヴァンスレーヴ ナダル')
put('ストームキャット系', 'ドレフォン ヘニーヒューズ アジアエクスプレス ミスターメロディ')
LINE['No Nay Never'] = 'ストームキャット系'
LINE['Blue Point'] = 'ストームキャット系'
put('その他ノーザンダンサー系', 'ハービンジャー クロフネ マインドユアビスケッツ モズアスコット ポエティックフレア サトノクラウン ブリックスアンドモルタル')
for n in ['War Front', 'Frankel', 'Shalaa', 'Dark Angel', 'Sottsass']:
    LINE[n] = 'その他ノーザンダンサー系'
put('その他ミスプロ系', 'ニューイヤーズデイ ヴァンゴッホ ダンカーク')
for n in ['Quality Road', 'Arrogate', 'Gun Runner', 'シスキン',
          'Wootton Bassett', 'Ghaiyyath']:
    LINE[n] = 'その他ミスプロ系'
put('その他', 'バゴ マジェスティックウォリアー')

# 2026年度募集に出てくる父も分類しておく（2020〜24パネルには居ない）
put('サンデー系', 'イクイノックス')
put('ロベルト系', 'エフフォーリア ピクシーナイト')
put('キングマンボ系', 'タイトルホルダー ヴェラアズール ジュンライトボルト チュウワウィザード')
put('ストームキャット系', 'モーニン')
put('その他ミスプロ系', 'カフェファラオ')
put('その他ノーザンダンサー系', 'シュネルマイスター グレナディアガーズ ウエストオーバー ホットロッドチャーリー')
for n in ['Kingman', 'Forte']:
    LINE[n] = 'その他ノーザンダンサー系'
LINE['パレスマリス'] = 'その他ミスプロ系'

# ---------------- 新種牡馬：初年度産駒の生年（外部知識） ----------------
FIRST_CROP = {
    'キタサンブラック': 2019, 'サトノダイヤモンド': 2019, 'シルバーステート': 2019,
    'レイデオロ': 2021, 'サートゥルナーリア': 2021, 'ブリックスアンドモルタル': 2021,
    'スワーヴリチャード': 2021, 'ルヴァンスレーヴ': 2021, 'リアルスティール': 2020,
    'アルアイン': 2020, 'マインドユアビスケッツ': 2020, 'Saxon Warrior': 2020,
    'ナダル': 2022, 'アドマイヤマーズ': 2022, 'クリソベリル': 2023,
    'シスキン': 2022, 'コントレイル': 2023, 'インディチャンプ': 2022,
    'ミスターメロディ': 2021, 'モズアスコット': 2021, 'フィエールマン': 2022,
    'ヴァンゴッホ': 2022, 'ポエティックフレア': 2023, 'Ghaiyyath': 2021,
    'Sottsass': 2022, 'ドレフォン': 2018, 'モーリス': 2018, 'ドゥラメンテ': 2017,
    'エピファネイア': 2016, 'キズナ': 2016, 'リオンディーズ': 2018,
    'ゴールドドリーム': 2021, 'Blue Point': 2020,
    'ロードカナロア': 2014, 'ハービンジャー': 2012, 'ルーラーシップ': 2014,
    'ハーツクライ': 2007, 'ディープインパクト': 2008, 'ダイワメジャー': 2008,
    'キングカメハメハ': 2007, 'オルフェーヴル': 2014, 'ジャスタウェイ': 2016,
    'ミッキーアイル': 2017, 'リアルインパクト': 2017, 'サトノクラウン': 2019,
    'キンシャサノキセキ': 2012, 'ディープブリランテ': 2014, 'イスラボニータ': 2018,
    'ヘニーヒューズ': 2007, 'ニューイヤーズデイ': 2015, 'クロフネ': 2005,
    'サトノアラジン': 2019, 'スクリーンヒーロー': 2010, 'トゥザワールド': 2017,
    'アジアエクスプレス': 2017, 'エイシンフラッシュ': 2014, 'ダノンシャンティ': 2013,
    'トーセンラー': 2016, 'ブラックタイド': 2007, 'シュヴァルグラン': 2020,
    'ミッキーロケット': 2020, 'ダンカーク': 2010, 'War Front': 2008,
    'Frankel': 2014, 'Quality Road': 2012, 'Arrogate': 2019, 'Gun Runner': 2020,
    'No Nay Never': 2017, 'Dark Angel': 2011, 'Shalaa': 2018,
    'Wootton Bassett': 2013, 'マジェスティックウォリアー': 2011, 'バゴ': 2007,
    'ミスターメロディ2': 0,
}


def add_bms(df):
    a = pd.read_csv(os.path.join(DS, 'roster.csv'), encoding='utf-8-sig')
    b = pd.read_csv(os.path.join(DS, 'roster_new_raw.csv'), encoding='utf-8-sig')
    r = pd.concat([a[['year', 'no', 'bms', 'coat']], b[['year', 'no', 'bms', 'coat']]],
                  ignore_index=True)
    r['no'] = pd.to_numeric(r['no'], errors='coerce')
    df = df.copy()
    df['no_i'] = pd.to_numeric(df['no'], errors='coerce')
    out = df.merge(r, left_on=['year', 'no_i'], right_on=['year', 'no'],
                   how='left', suffixes=('', '_r'))
    return out


def sec(t):
    print('\n' + '=' * 90)
    print('■ ' + t)
    print('=' * 90)


def report(sub, cols, extra=None):
    use = cols + (extra or [])
    for target in ['win_jra', 'ret1']:
        s = sub.dropna(subset=use + [target])
        if len(s) < 30:
            print(f'  {target}: n不足({len(s)})')
            continue
        X, names = design(s, use)
        t = logit(X, s[target], names)
        t = t[~t['変数'].str.startswith('年度')]
        print(f'  -- {target} n={len(s)}')
        print(t.round(3).to_string(index=False))


def yearly(df, col, target='win_jra'):
    p = df.pivot_table(index=col, columns='year', values=target,
                       aggfunc=['mean', 'size'], dropna=False)
    m, s = p['mean'] * 100, p['size']
    print('  ' + f'{"":<28}' + ''.join(f'{y:>12}' for y in m.columns))
    for i in m.index:
        cells = []
        for y in m.columns:
            mv, nv = m.loc[i, y], s.loc[i, y]
            cells.append(f'{int(round(mv)):>3}%({int(nv):>2})' if pd.notna(mv) and nv > 0 else f'{"-":>8}')
        print(f'  {str(i):<28}' + ''.join(f'{c:>12}' for c in cells))


def desc(d, col):
    return d.groupby(col).agg(頭数=('win_jra', 'size'), 勝上中央=('win_jra', 'mean'),
                              回収1=('ret1', 'mean'), 回収中央値=('ret', 'median'),
                              価格中央値=('total_man', 'median')).round(3)


def main():
    df = load(central_only=True)
    df = add_bms(df)
    df['line'] = df['sire'].map(LINE).fillna('未分類')
    print('未分類の父:', sorted(set(df.loc[df['line'] == '未分類', 'sire'])))
    print('bms欠損:', int(df['bms'].isna().sum()), '/', len(df))
    print(df.groupby('year')['bms'].apply(lambda s: int(s.notna().sum())).to_string())

    sec('1. 父の格＝自分より前の年度の同父産駒の中央勝ち上がり率（リーク無し）')
    df = df.sort_values(['year', 'no_i']).reset_index(drop=True)
    base = df['win_jra'].mean()
    print(f'全体の中央勝ち上がり率 = {base:.3f}')
    pn, pr, prs = [], [], []
    for _, row in df.iterrows():
        prev = df[(df['year'] < row['year']) & (df['sire'] == row['sire'])].dropna(subset=['win_jra'])
        n = len(prev)
        pn.append(n)
        pr.append(prev['win_jra'].mean() if n else np.nan)
        prs.append((prev['win_jra'].sum() + 5.0 * base) / (n + 5.0))
    df['sire_prev_n'] = pn
    df['sire_prev_rate'] = pr
    df['sire_prev_shrunk_c'] = np.array(prs) - base

    print('\n過去産駒がある頭数（年度別）')
    print(df.assign(has=(df['sire_prev_n'] > 0).astype(int)).groupby('year')
          .agg(n=('has', 'size'), 過去あり=('has', 'sum'),
               過去頭数中央値=('sire_prev_n', 'median')).to_string())

    sub = df[df['sire_prev_n'] >= 3].copy()
    print(f'\n過去3頭以上ある馬のみ n={len(sub)} 年度内訳 {dict(sub.groupby("year").size())}')
    print('\n[a] 縮小推定した父の過去勝上率（中心化）')
    report(sub, ['sire_prev_shrunk_c'])
    print('\n[b] 価格・性を入れても残るか')
    report(sub, ['sire_prev_shrunk_c'], extra=['price_pct', 'male'])
    sub['sire_hot'] = (sub['sire_prev_shrunk_c'] > 0).astype(int)
    print('\n[c] 父の過去勝上率が全体平均超か否か')
    print(desc(sub, 'sire_hot').to_string())
    report(sub, ['sire_hot'], extra=['price_pct', 'male'])
    print('\n年度別 win_jra（父hot）')
    yearly(sub, 'sire_hot')
    print('\n年度別 ret1（父hot）')
    yearly(sub, 'sire_hot', 'ret1')

    print('\n[d] 2年以上前の年度だけ使う版（募集時点で実際に見えている情報に近い）')
    pn2, pr2 = [], []
    for _, row in df.iterrows():
        prev = df[(df['year'] <= row['year'] - 2) & (df['sire'] == row['sire'])].dropna(subset=['win_jra'])
        pn2.append(len(prev))
        pr2.append((prev['win_jra'].sum() + 5.0 * base) / (len(prev) + 5.0) - base)
    df['sire_prev2_n'] = pn2
    df['sire_prev2_c'] = pr2
    s2 = df[df['sire_prev2_n'] >= 3].copy()
    print(f'  n={len(s2)} 年度内訳 {dict(s2.groupby("year").size())}')
    report(s2, ['sire_prev2_c'], extra=['price_pct', 'male'])
    s2['hot2'] = (s2['sire_prev2_c'] > 0).astype(int)
    print(desc(s2, 'hot2').to_string())
    yearly(s2, 'hot2')

    sec('2. 父系')
    print(desc(df, 'line').to_string())
    print('\n年度別 勝上(中央)')
    yearly(df, 'line')
    print('\n年度別 ret1')
    yearly(df, 'line', 'ret1')
    for L in ['サンデー系', 'キングマンボ系', 'ロベルト系', 'ストームキャット系',
              'その他ノーザンダンサー系']:
        df['L_' + L] = (df['line'] == L).astype(int)
    lc = ['L_' + x for x in ['サンデー系', 'キングマンボ系', 'ロベルト系',
                             'ストームキャット系', 'その他ノーザンダンサー系']]
    print('\n父系ダミー（基準＝ミスプロ系その他）＋価格＋牡')
    report(df, lc, extra=['price_pct', 'male'])

    sec('3. 母の父（bms）')
    d = df.dropna(subset=['bms']).copy()
    print(f'bmsある n={len(d)}')
    tb = desc(d, 'bms')
    print(tb[tb['頭数'] >= 5].sort_values('勝上中央', ascending=False).to_string())
    d['bms_di'] = (d['bms'] == 'ディープインパクト').astype(int)
    d['bms_kk'] = (d['bms'] == 'キングカメハメハ').astype(int)
    d['bms_gaikoku'] = d['bms'].str.contains('[A-Za-z]', regex=True).astype(int)
    SS_BMS = set('''ディープインパクト ダイワメジャー ゼンノロブロイ スペシャルウィーク
    マンハッタンカフェ サンデーサイレンス ネオユニヴァース ステイゴールド ハーツクライ
    ゴールドアリュール ディープブリランテ フジキセキ アグネスタキオン ダンスインザダーク
    バブルガムフェロー スズカマンボ ゼンノエルシド キンシャサノキセキ ヴィクトワールピサ
    オルフェーヴル ハットトリック マツリダゴッホ タニノギムレット アドマイヤベガ
    デュランダル マンハッタンカフェ ジャングルポケット'''.split()) - {'ジャングルポケット', 'タニノギムレット'}
    d['bms_ss'] = d['bms'].isin(SS_BMS).astype(int)
    for c, lab in [('bms_di', 'bms=ディープインパクト'), ('bms_kk', 'bms=キングカメハメハ'),
                   ('bms_ss', 'bmsサンデー系'), ('bms_gaikoku', 'bms欧米種牡馬(英字表記)')]:
        print(f'\n--- {lab}  1の頭数={int(d[c].sum())}')
        print(desc(d, c).to_string())
        report(d, [c], extra=['price_pct', 'male'])
        yearly(d, c)

    sec('4. ニックス（父系 × bms系）')
    d['bmsgrp'] = np.where(d['bms_ss'] == 1, 'SS', np.where(d['bms_gaikoku'] == 1, '欧米', '内国産非SS'))
    d['nick'] = d['line'] + '×' + d['bmsgrp']
    t = desc(d, 'nick')
    print(t[t['頭数'] >= 8].sort_values('勝上中央', ascending=False).to_string())
    d['nick_out'] = ((d['line'] != 'サンデー系') & (d['bms_ss'] == 1)).astype(int)
    print('\n非サンデー系父 × サンデー系bms（王道アウトブリード）')
    print(desc(d, 'nick_out').to_string())
    report(d, ['nick_out'], extra=['price_pct', 'male'])
    yearly(d, 'nick_out')
    d['ss_cross'] = ((d['line'] == 'サンデー系') & (d['bms_ss'] == 1)).astype(int)
    print('\nサンデー系父 × サンデー系bms（SSクロス）')
    print(desc(d, 'ss_cross').to_string())
    report(d, ['ss_cross'], extra=['price_pct', 'male'])
    yearly(d, 'ss_cross')

    sec('5. 新種牡馬（初年度・2年目産駒）')
    df['fc'] = df['sire'].map(FIRST_CROP)
    df['crop_no'] = df['born'].astype(int) - df['fc'] + 1
    print('初年度産駒生年が判明している父の頭数:', int(df['fc'].notna().sum()), '/', len(df))
    print('不明な父:', sorted(set(df.loc[df['fc'].isna(), 'sire'])))
    df['is_new'] = (df['crop_no'] <= 1).astype(float)
    df.loc[df['fc'].isna(), 'is_new'] = np.nan
    df['is_new2'] = (df['crop_no'] <= 2).astype(float)
    df.loc[df['fc'].isna(), 'is_new2'] = np.nan
    df['club_first'] = (df['sire_prev_n'] == 0).astype(int)
    print('\n[産駒世代番号別]')
    print(desc(df.dropna(subset=['crop_no']).assign(cn=lambda x: x['crop_no'].clip(upper=7)), 'cn').to_string())
    for c, lab in [('is_new', '初年度産駒'), ('is_new2', '初〜2年目産駒'),
                   ('club_first', 'クラブ初登場の父')]:
        print(f'\n--- {lab}')
        dd = df.dropna(subset=[c])
        print(desc(dd, c).to_string())
        report(dd, [c], extra=['price_pct', 'male'])
        yearly(dd, c)
        yearly(dd, c, 'ret1')

    sec('6. 参考: 毛色')
    dc = df.dropna(subset=['coat'])
    print(desc(dc, 'coat').to_string())

    out = os.path.join(BASE, '_probe_pedigree_out.csv')
    df.to_csv(out, index=False, encoding='utf-8-sig')
    print('\nsaved:', out)


if __name__ == '__main__':
    main()

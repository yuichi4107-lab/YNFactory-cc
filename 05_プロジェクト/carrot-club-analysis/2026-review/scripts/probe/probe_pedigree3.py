# -*- coding: utf-8 -*-
"""多重検定の自覚チェック。ロベルト系シグナルが「たくさん試した中のたまたま」でないかを見る。"""
import io, sys
import numpy as np
import pandas as pd
from analyze5 import load, logit, design
from probe_pedigree import add_bms, LINE, desc, yearly

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 250)
rng = np.random.default_rng(0)


def zof(d, col, extra, target='win_jra'):
    s = d.dropna(subset=[col, target] + extra)
    X, names = design(s, [col] + extra)
    t = logit(X, s[target], names)
    return float(t.loc[t['変数'] == col, 'z'].iloc[0])


def main():
    df = load(central_only=True)
    df = add_bms(df)
    df['line'] = df['sire'].map(LINE).fillna('未分類')
    df['rob'] = (df['line'] == 'ロベルト系').astype(int)
    df['price2539'] = df['total_man'].between(2500, 3999).astype(int)
    df['w420'] = (df['weight'] >= 420).astype(float)
    df.loc[df['weight'].isna(), 'w420'] = np.nan
    ex = ['male', 'price2539', 'w420']

    print('■ 年度を1つ抜いたときのロベルト系のz（win_jra, 3基準込み）')
    for y in sorted(df['year'].unique()):
        d = df[df['year'] != y]
        print(f'  {y}を除外: z={zof(d, "rob", ex):+.2f}  n_rob={int(d["rob"].sum())}')
    print(f'  全年度      : z={zof(df, "rob", ex):+.2f}')

    print('\n■ 前3年(2020-22)で作って後2年(2023-24)で当てる純粋な外部検証')
    tr = df[df['year'] <= 2022]
    te = df[df['year'] >= 2023]
    print(f'  学習期 ロベルト {tr["rob"].sum()}頭 勝上{tr[tr["rob"]==1]["win_jra"].mean():.3f} / 他{tr[tr["rob"]==0]["win_jra"].mean():.3f}')
    print(f'  検証期 ロベルト {te["rob"].sum()}頭 勝上{te[te["rob"]==1]["win_jra"].mean():.3f} / 他{te[te["rob"]==0]["win_jra"].mean():.3f}')
    print(f'  検証期のみでz={zof(te, "rob", ex):+.2f}')
    print(f'  検証期 ret1 ロベルト{te[te["rob"]==1]["ret1"].mean():.3f} / 他{te[te["rob"]==0]["ret1"].mean():.3f}')

    print('\n■ この担当で試した2値仮説を一覧にして、最大zの偶然性を見る')
    d = df.dropna(subset=['bms']).copy()
    d['w420'] = df['w420']
    SS = set('''ディープインパクト ダイワメジャー ゼンノロブロイ スペシャルウィーク マンハッタンカフェ
    サンデーサイレンス ネオユニヴァース ステイゴールド ハーツクライ ゴールドアリュール
    ディープブリランテ フジキセキ アグネスタキオン ダンスインザダーク バブルガムフェロー
    スズカマンボ ゼンノエルシド キンシャサノキセキ ヴィクトワールピサ オルフェーヴル
    ハットトリック マツリダゴッホ アドマイヤベガ デュランダル'''.split())
    cands = {}
    for L in sorted(set(LINE.values())):
        cands['父系=' + L] = (d['line'] == L).astype(int)
    for s in d['sire'].value_counts()[lambda x: x >= 8].index:
        cands['父=' + s] = (d['sire'] == s).astype(int)
    for b in d['bms'].value_counts()[lambda x: x >= 8].index:
        cands['bms=' + b] = (d['bms'] == b).astype(int)
    cands['bmsサンデー系'] = d['bms'].isin(SS).astype(int)
    cands['bms英字表記'] = d['bms'].str.contains('[A-Za-z]').astype(int)
    cands['非SS父×SS母父'] = ((d['line'] != 'サンデー系') & d['bms'].isin(SS)).astype(int)
    cands['SS父×SS母父'] = ((d['line'] == 'サンデー系') & d['bms'].isin(SS)).astype(int)
    rows = []
    for k, v in cands.items():
        d['_x'] = v
        if v.sum() < 5:
            continue
        rows.append({'仮説': k, 'n1': int(v.sum()),
                     'z_win': zof(d, '_x', ex), 'z_ret': zof(d, '_x', ex, 'ret1')})
    t = pd.DataFrame(rows).sort_values('z_win', ascending=False)
    print(f'  試した仮説数 = {len(t)}')
    print(t.round(2).to_string(index=False))

    print('\n■ 並べ替え検定: 目的変数をシャッフルして「全仮説の最大|z|」の分布を作る')
    ys = d.dropna(subset=['w420', 'win_jra'])
    keys = [k for k in cands if cands[k].sum() >= 5]
    mats = {}
    for k in keys:
        mats[k] = cands[k].loc[ys.index].values.astype(float)
    base = np.column_stack([(ys['year'] == y).astype(float) for y in sorted(ys['year'].unique())]
                           + [ys[c].astype(float).values for c in ex])
    yv = ys['win_jra'].values.astype(float)
    obs = max(abs(zof(ys.assign(_x=mats[k]), '_x', ex)) for k in keys)
    null = []
    for i in range(200):
        yp = rng.permutation(yv)
        m = 0.0
        for k in keys:
            X = np.column_stack([mats[k], base])
            t2 = logit(X, yp, ['_x'] + ['o'] * base.shape[1])
            m = max(m, abs(float(t2.iloc[0]['z'])))
        null.append(m)
    null = np.array(null)
    print(f'  観測された最大|z| = {obs:.2f}')
    print(f'  シャッフル時の最大|z| 中央値={np.median(null):.2f}  95%点={np.percentile(null,95):.2f}')
    print(f'  family-wise p ≒ {(null >= obs).mean():.3f}')


if __name__ == '__main__':
    main()

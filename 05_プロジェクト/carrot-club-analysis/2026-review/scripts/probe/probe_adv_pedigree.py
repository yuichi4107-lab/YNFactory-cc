# -*- coding: utf-8 -*-
"""敵対的検証：父ロベルト系（および ロベルト×牝）を潰しにかかる。"""
import io, sys
import numpy as np
import pandas as pd
from analyze5 import load, logit, design
from probe_pedigree import LINE
from backtest import auc

if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 250)
pd.set_option('display.max_rows', 400)
rng = np.random.default_rng(42)

ROB = ['エピファネイア', 'モーリス', 'スクリーンヒーロー', 'ルヴァンスレーヴ', 'ナダル']
EX = ['male', 'price2539', 'w420']


def prep():
    df = load(central_only=True)
    df['line'] = df['sire'].map(LINE).fillna('未分類')
    df['rob'] = (df['line'] == 'ロベルト系').astype(int)
    df['price2539'] = df['total_man'].between(2500, 3999).astype(int)
    df['w420'] = (df['weight'] >= 420).astype(float)
    df.loc[df['weight'].isna(), 'w420'] = np.nan
    return df


def zof(d, col, extra=EX, target='win_jra'):
    s = d.dropna(subset=[col, target] + list(extra))
    X, names = design(s, [col] + list(extra))
    t = logit(X, s[target], names)
    return float(t.loc[t['変数'] == col, 'z'].iloc[0]), float(t.loc[t['変数'] == col, '係数'].iloc[0]), len(s)


def sec(t):
    print('\n' + '=' * 90)
    print('■ ' + t)
    print('=' * 90)


def cluster_z(d, col, extra=EX, target='win_jra', cluster='sire'):
    s = d.dropna(subset=[col, target] + list(extra)).copy()
    X, names = design(s, [col] + list(extra))
    X = np.asarray(X, float)
    y = s[target].values.astype(float)
    r = logit(X, y, names)
    b = r['係数'].values
    p = 1 / (1 + np.exp(-(X @ b)))
    W = np.clip(p * (1 - p), 1e-9, None)
    bread = np.linalg.inv(X.T @ (X * W[:, None]) + 1e-6 * np.eye(X.shape[1]))
    u = X * (y - p)[:, None]
    meat = np.zeros((X.shape[1], X.shape[1]))
    for g, idx in s.groupby(cluster).indices.items():
        ug = u[idx].sum(axis=0)
        meat += np.outer(ug, ug)
    V = bread @ meat @ bread
    i = names.index(col)
    return b[i] / np.sqrt(V[i, i]), b[i] / r['SE'].values[i], s[cluster].nunique()


def main():
    df = prep()
    d = df.dropna(subset=['win_jra'])
    sec('0. 報告された数字の再現')
    print(f"ロベルト系 n={int(d['rob'].sum())}  勝上(中央)={d[d.rob==1]['win_jra'].mean():.3f}  "
          f"非ロベルト n={int((1-d['rob']).sum())} 勝上={d[d.rob==0]['win_jra'].mean():.3f}")
    print(f"ret1  ロベルト={d[d.rob==1]['ret1'].mean():.3f}  非={d[d.rob==0]['ret1'].mean():.3f}  "
          f"回収中央値 {d[d.rob==1]['ret'].median():.3f} vs {d[d.rob==0]['ret'].median():.3f}")
    print('\n父ごとの内訳（ロベルト系）')
    t = d[d.rob == 1].groupby('sire').agg(頭数=('win_jra', 'size'), 勝上=('win_jra', 'mean'),
                                          ret1=('ret1', 'mean'), 回収中央値=('ret', 'median'),
                                          価格中央値=('total_man', 'median'),
                                          牝率=('male', lambda s: 1 - s.mean())).round(3)
    print(t.to_string())
    print('\n年度別')
    for y in sorted(d['year'].unique()):
        a = d[(d.year == y) & (d.rob == 1)]
        b_ = d[(d.year == y) & (d.rob == 0)]
        print(f'  {y}: rob {a["win_jra"].mean():.2f}({len(a)})  非 {b_["win_jra"].mean():.2f}({len(b_)})')
    for lab, ex in [('年度ダミーのみ', []), ('+価格pct+牡', ['price_pct', 'male']), ('+現行3基準', EX)]:
        z, b, n = zof(d, 'rob', ex)
        print(f'  z(win_jra) {lab}: {z:+.2f} (n={n})')
    print(f"  z(ret1) 3基準込み: {zof(d,'rob',EX,'ret1')[0]:+.2f}")

    sec('1. 父でクラスタした頑健SE（同じ父の産駒は独立でない）')
    zc, zn, ng = cluster_z(d, 'rob')
    print(f'  素のz={zn:+.2f} → 父クラスタ頑健z={zc:+.2f}  （全体のクラスタ数={ng}父／ロベルト側は5父）')
    print('  ※処置変数(rob)は父の中で一定なので、実効的な独立単位は「父」。しかも処置側は5父しかない。')
    print('    処置クラスタ数が5しかないとき CRVE は下方バイアスが強く（Cameron-Miller）、')
    print('    z=3.74 は信用できない。正しくは父を単位にした並べ替え検定（次節）で見る。')

    sec('2. 父単位の並べ替え検定（父クラスタを保ったまま同じ大きさの偽の系統を作る）')
    ys = d.dropna(subset=['w420']).copy()
    obs = zof(ys, 'rob')[0]
    sires = ys.groupby('sire').size()
    target_n = int(ys['rob'].sum())
    k = len(ROB)
    pool = list(sires.index)
    null = []
    for _ in range(3000):
        pick = None
        for _try in range(300):
            cand = rng.choice(pool, size=k, replace=False)
            if abs(sires[list(cand)].sum() - target_n) <= 12:
                pick = cand
                break
        if pick is None:
            continue
        v = ys['sire'].isin(pick).astype(float)
        if v.nunique() < 2:
            continue
        null.append(zof(ys.assign(_x=v), '_x')[0])
    null = np.array(null)
    print(f'  観測 z={obs:+.2f}   偽系統の作り方: 父を5頭ランダム抽出し合計{target_n}±12頭になるもの')
    print(f'  偽系統のz分布: 中央値={np.median(null):+.2f} 90%点={np.percentile(null,90):+.2f} '
          f'95%点={np.percentile(null,95):+.2f} 99%点={np.percentile(null,99):+.2f} 最大={null.max():+.2f}')
    print(f'  片側p（偽系統がこれ以上のzを出す確率）= {(null>=obs).mean():.3f}   n_draw={len(null)}')

    sec('3. 個体の父を1頭ずつ抜く／上位2父を抜く')
    for s_ in ROB:
        dd = d[d['sire'] != s_]
        z, b, n = zof(dd, 'rob')
        print(f'  {s_}除外: z={z:+.2f} 残りrob={int(dd["rob"].sum())}頭')
    dd = d[~d['sire'].isin(['エピファネイア', 'モーリス'])]
    z, b, n = zof(dd, 'rob')
    print(f'  エピ＋モーリス両方除外: z={z:+.2f} 残りrob={int(dd["rob"].sum())}頭 '
          f'勝上={dd[dd.rob==1]["win_jra"].mean():.3f} vs {dd[dd.rob==0]["win_jra"].mean():.3f}')

    sec('4. LOYO：既存3基準スコア vs +ロベルト（単純合計・閾値学習なし）')
    for target in ['win_jra', 'ret1']:
        s = d.dropna(subset=['w420', target]).copy()
        s['s3'] = s['male'] + s['price2539'] + s['w420']
        s['s4'] = s['s3'] + s['rob']
        rows = []
        for y in sorted(s['year'].unique()):
            te = s[s.year == y]
            rows.append({'年度': y, 'n': len(te),
                         '3基準': round(auc(te[target], te['s3']), 3),
                         '+rob': round(auc(te[target], te['s4']), 3)})
        bt = pd.DataFrame(rows)
        a3 = auc(s[target], s['s3'])
        a4 = auc(s[target], s['s4'])
        print(f'\n  [{target}]')
        print(bt.to_string(index=False))
        print(f'   全体 3基準={a3:.3f}  +rob={a4:.3f}  差={a4-a3:+.3f}')
        print(f'   年度別平均 3基準={bt["3基準"].mean():.3f} +rob={bt["+rob"].mean():.3f} '
              f'改善年度={(bt["+rob"]>bt["3基準"]).sum()}/{len(bt)}')

    sec('5. LOYO：係数を訓練年度で学習して当該年を予測（重みも外挿）')
    for target in ['win_jra', 'ret1']:
        s = d.dropna(subset=['w420', target]).copy()
        rows = []
        for y in sorted(s['year'].unique()):
            tr, te = s[s.year != y], s[s.year == y]
            out = {'年度': y, 'n': len(te)}
            for lab, cols in [('3基準', EX), ('+rob', EX + ['rob'])]:
                Xtr = np.column_stack([np.ones(len(tr))] + [tr[c].astype(float).values for c in cols])
                r = logit(Xtr, tr[target], ['c'] + cols)
                b = r['係数'].values
                Xte = np.column_stack([np.ones(len(te))] + [te[c].astype(float).values for c in cols])
                out[lab] = round(auc(te[target], Xte @ b), 3)
            rows.append(out)
        bt = pd.DataFrame(rows)
        print(f'\n  [{target}]')
        print(bt.to_string(index=False))
        print(f'   平均 3基準={bt["3基準"].mean():.3f} +rob={bt["+rob"].mean():.3f} '
              f'改善年度={(bt["+rob"]>bt["3基準"]).sum()}/{len(bt)}')

    sec('6. 交互作用 ロベルト×牡 のセル')
    d2 = d.copy()
    d2['cell'] = np.where(d2.rob == 1, 'rob', 'other') + '/' + np.where(d2.male == 1, '牡', '牝')
    print(d2.groupby('cell').agg(頭数=('win_jra', 'size'), 勝上=('win_jra', 'mean'),
                                 ret1=('ret1', 'mean'), 回収中央値=('ret', 'median'),
                                 価格中央値=('total_man', 'median')).round(3).to_string())
    print('\n  年度×セル 頭数')
    print(pd.crosstab(d2['year'], d2['cell']).to_string())
    d2['rob_male'] = d2['rob'] * d2['male']
    for target in ['win_jra', 'ret1']:
        s = d2.dropna(subset=['w420', target])
        X, names = design(s, ['rob', 'male', 'price2539', 'w420', 'rob_male'])
        t = logit(X, s[target], names)
        print(f'\n  [{target}]')
        print(t[~t['変数'].str.startswith('年度')].round(3).to_string(index=False))
    print('\n  ロベルト/牝 の年度別 勝上')
    for y in sorted(d2['year'].unique()):
        a = d2[(d2.year == y) & (d2.cell == 'rob/牝')]
        print(f'   {y}: {a["win_jra"].mean():.2f} ({len(a)}頭, 勝{a["win_jra"].sum():.0f})')
    print('\n  ロベルト/牝 の父別')
    print(d2[d2.cell == 'rob/牝'].groupby('sire').agg(頭数=('win_jra', 'size'),
                                                     勝上=('win_jra', 'mean')).round(3).to_string())

    sec('7. LOYO：ロベルト牝を牡と同等に扱う運用ヒントの検証')
    for target in ['win_jra', 'ret1']:
        s = d.dropna(subset=['w420', target]).copy()
        s['s3'] = s['male'] + s['price2539'] + s['w420']
        s['s3b'] = (((s['male'] == 1) | (s['rob'] == 1)).astype(float)
                    + s['price2539'] + s['w420'])
        rows = []
        for y in sorted(s['year'].unique()):
            te = s[s.year == y]
            rows.append({'年度': y, '3基準': round(auc(te[target], te['s3']), 3),
                         'ロベルト牝も牡扱い': round(auc(te[target], te['s3b']), 3)})
        bt = pd.DataFrame(rows)
        print(f'\n  [{target}] 全体 3基準={auc(s[target],s["s3"]):.3f} 牝緩和={auc(s[target],s["s3b"]):.3f}')
        print(bt.to_string(index=False))

    sec('8. 「ロベルト系なら4000-5999万も可」の実サンプル')
    for target in ['win_jra', 'ret1']:
        s = d.dropna(subset=['w420', target]).copy()
        s['band'] = pd.cut(s['total_man'], [0, 2499, 3999, 5999, 999999],
                           labels=['〜2499', '2500-3999', '4000-5999', '6000〜'])
        print(f'\n  [{target}]')
        print(s.pivot_table(index='band', columns='rob', values=target,
                            aggfunc=['mean', 'size'], observed=False).round(3).to_string())
    s = d.dropna(subset=['w420']).copy()
    m = s[(s.rob == 1) & (s.total_man.between(4000, 5999))]
    print(f'\n  ロベルト×4000-5999万 n={len(m)} 勝上={m["win_jra"].mean():.3f} ret1={m["ret1"].mean():.3f} '
          f'回収中央値={m["ret"].median():.3f}')
    print('  年度別頭数:', dict(m.groupby('year').size()))
    print('  父別:', dict(m.groupby('sire').size()))

    sec('9. ロベルト系だけが特別か：他系統も同様に見る（多重比較の実感）')
    rows = []
    for L in sorted(set(d['line'])):
        v = (d['line'] == L).astype(int)
        if v.sum() < 15:
            continue
        z1 = zof(d.assign(_x=v), '_x')[0]
        z2 = zof(d.assign(_x=v), '_x', EX, 'ret1')[0]
        zc = cluster_z(d.assign(_x=v), '_x')[0]
        rows.append({'系統': L, 'n': int(v.sum()), '父数': d.loc[v == 1, 'sire'].nunique(),
                     'z_win': round(z1, 2), 'z_win_父クラスタ': round(zc, 2), 'z_ret': round(z2, 2)})
    print(pd.DataFrame(rows).sort_values('z_win', ascending=False).to_string(index=False))


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""敵対的検証：手法系候補（検出力の壁 / log募集総額 / アウトカム定義）を潰しにかかる。"""
import io, json, os, sys
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from analyze5 import load, logit, design
from backtest import auc
from scipy import stats
pd.set_option('display.width', 240)
rng = np.random.default_rng(12345)

DS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'datasets')
df = load(central_only=True)
rs = json.load(open(os.path.join(DS, 'race_summary.json'), encoding='utf-8'))
for c in ['jra_starts', 'jra_wins', 'wins_by3', 'starts_by3', 'prize_by3']:
    df[c] = pd.to_numeric(df['key'].map(lambda k: (rs.get(k) or {}).get(c)), errors='coerce')
df['win2'] = (df['jra_wins'].fillna(0) >= 2).astype(float)
df['win3'] = (df['jra_wins'].fillna(0) >= 3).astype(float)
df['ran'] = (df['jra_starts'].fillna(0) >= 1).astype(float)
d = df.dropna(subset=['win_jra', 'weight', 'total_man']).copy()
d['lprice'] = np.log(d['total_man'].astype(float))
d['male'] = d['male'].astype(float)
d['p2540'] = d['total_man'].between(2500, 3999).astype(float)
d['w420'] = (d['weight'] >= 420).astype(float)
d['phi'] = (d.groupby('year')['total_man'].rank(pct=True) > 0.5).astype(float)
d['graded'] = pd.to_numeric(d['graded'], errors='coerce').fillna(0)
BASE3 = ['male', 'p2540', 'w420']
print('n=%d  win_jra基準率=%.3f' % (len(d), d['win_jra'].mean()))
print(d.groupby('year').agg(n=('win_jra', 'size'), win=('win_jra', 'mean'),
                            win2=('win2', 'mean'), ret1=('ret1', 'mean')).round(3).to_string())

print('\n=== [1] 検出力の壁の主張を検算 ===')
for lab, n1 in [('50%該当', 222), ('30%該当', 133), ('10%該当', 44)]:
    n2 = 444 - n1
    se = np.sqrt(0.493 * 0.507 * (1 / n1 + 1 / n2))
    print('  %s: z=1.96必要差=%.1fpt  検出力80%%必要差=%.1fpt' % (lab, 1.96 * se * 100, 2.80 * se * 100))
print('  → 報告値(9.3/13.3/14.5/22.3pt)と一致。算術は正しい。')
print('  同じ低検出力は「通った候補」にも効く（Type M / winner curse）:')
se = np.sqrt(0.493 * 0.507 * (2 / 222))
for true_d in [0.03, 0.05, 0.08]:
    sims = rng.normal(true_d, se, 200000)
    sig = np.abs(sims) > 1.96 * se
    print('   真の差%.0f%% → 有意になる確率%.0f%%, 有意時の推定差の平均%.1fpt (誇張%.1f倍)'
          % (true_d * 100, sig.mean() * 100, np.abs(sims[sig]).mean() * 100,
             np.abs(sims[sig]).mean() / true_d))

print('\n=== [2] 落とした3基準／log価格をスコアへ足したらLOYO AUCは上がるか ===')


def loyo_rank(cols, tgt, data, ridge=1.0):
    s = data.dropna(subset=list(cols) + [tgt]).copy().reset_index(drop=True)
    pr = np.full(len(s), np.nan)
    for y in sorted(s['year'].unique()):
        tr, te = s[s['year'] != y], s[s['year'] == y]
        Xtr = np.column_stack([np.ones(len(tr))] + [tr[c].astype(float).values for c in cols])
        Xte = np.column_stack([np.ones(len(te))] + [te[c].astype(float).values for c in cols])
        r = logit(Xtr, tr[tgt], ['b'] + list(cols), ridge=ridge)
        pr[te.index] = Xte @ r['係数'].values
    s['_p'] = pr
    s['_r'] = s.groupby('year')['_p'].rank(pct=True)
    return s


SETS = [
    ('3基準のみ', BASE3),
    ('+3-4月生', BASE3 + ['mar_apr']),
    ('+ノーザンF', BASE3 + ['nf']),
    ('+母8-11歳', BASE3 + ['dam811']),
    ('+落とした3つ全部', BASE3 + ['mar_apr', 'nf', 'dam811']),
    ('+log価格', BASE3 + ['lprice']),
    ('+価格年内上位半分', BASE3 + ['phi']),
    ('置換 male,lprice,w420', ['male', 'lprice', 'w420']),
]


def report(tgt):
    out = []
    for nm, cols in SETS:
        s = loyo_rank(cols, tgt, d)
        y = s[tgt].values
        sc = s['_r'].values
        row = {'モデル': nm, '全体AUC': round(auc(y, sc), 3)}
        for yr in sorted(s['year'].unique()):
            m = (s['year'] == yr).values
            row[str(yr)] = round(auc(y[m], sc[m]), 3)
        out.append(row)
    print('\n-- 目的=%s (LOYO)' % tgt)
    print(pd.DataFrame(out).to_string(index=False))


for tgt in ['win_jra', 'ret1']:
    report(tgt)

print('\n=== [2b] 参考: 単純加点スコア(3基準の合計)のLOYO相当AUC ===')
for tgt in ['win_jra', 'ret1']:
    s = d.dropna(subset=[tgt]).copy()
    s['_sc'] = s[BASE3].sum(axis=1)
    line = []
    for yr in sorted(s['year'].unique()):
        m = s['year'] == yr
        line.append('%d:%.3f' % (yr, auc(s.loc[m, tgt], s.loc[m, '_sc'])))
    print('  %s 全体%.3f  %s' % (tgt, auc(s[tgt], s['_sc']), ' '.join(line)))

print('\n=== [3] LOYO AUC差のブートストラップ95%CI（対 3基準のみ） ===')
for tgt in ['win_jra', 'ret1']:
    base = loyo_rank(BASE3, tgt, d)
    yb = base[tgt].values
    sb = base['_r'].values
    print('\n-- 目的=%s 基準AUC=%.3f' % (tgt, auc(yb, sb)))
    for nm, cols in SETS[1:]:
        s = loyo_rank(cols, tgt, d)
        sv = s['_r'].values
        diffs = []
        for _ in range(1000):
            idx = rng.integers(0, len(yb), len(yb))
            if len(np.unique(yb[idx])) < 2:
                continue
            diffs.append(auc(yb[idx], sv[idx]) - auc(yb[idx], sb[idx]))
        lo, hi = np.percentile(diffs, [2.5, 97.5])
        d0 = auc(yb, sv) - auc(yb, sb)
        print('   %-24s 差=%+.3f [95%%CI %+.3f,%+.3f] %s'
              % (nm, d0, lo, hi, 'OK' if lo > 0 else 'ns'))

print('\n=== [4] log価格を3基準と同時投入（年度ダミー入り）再現確認 ===')
for tgt in ['win_jra', 'win2', 'win3', 'ret1', 'ran']:
    s = d.dropna(subset=[tgt])
    X, names = design(s, BASE3 + ['lprice'])
    r = logit(X, s[tgt], names)
    r = r[~r['変数'].astype(str).str.startswith('年度')]
    print('  %-8s n=%d  %s' % (tgt, len(s),
          '  '.join('%s z=%+.2f' % (a, b) for a, b in zip(r['変数'], r['z']))))

print('\n=== [5] log価格の年度別（各年単独ロジ, 3基準コントロール後）===')
for tgt in ['win_jra', 'win2', 'win3', 'ret1']:
    line = []
    for y in sorted(d['year'].unique()):
        s = d[d['year'] == y].dropna(subset=[tgt])
        X = np.column_stack([np.ones(len(s))] + [s[c].astype(float).values for c in BASE3 + ['lprice']])
        r = logit(X, s[tgt], ['b'] + BASE3 + ['lprice'], ridge=1.0)
        line.append('%d:z=%+.2f' % (y, r.iloc[-1]['z']))
    print('  %-8s %s' % (tgt, '  '.join(line)))

print('\n=== [6] 価格と回収の機械的関係 ===')
d['ret_num'] = pd.to_numeric(d['ret'], errors='coerce')
d['pj'] = pd.to_numeric(d['prize_jra'], errors='coerce').fillna(0)
b = pd.cut(d['total_man'], [0, 1999, 2499, 3999, 5999, 999999])
t = d.groupby(b, observed=True).agg(頭数=('win_jra', 'size'), 勝上=('win_jra', 'mean'),
                                    _2勝=('win2', 'mean'), 重賞=('graded', 'sum'),
                                    回収1=('ret1', 'mean'), 回収中央値=('ret_num', 'median'),
                                    平均賞金万=('pj', 'mean'), 平均募集万=('total_man', 'mean'))
print(t.assign(勝上=(t['勝上'] * 100).round(0), _2勝=(t['_2勝'] * 100).round(0),
               回収1=(t['回収1'] * 100).round(0), 平均賞金万=t['平均賞金万'].round(0),
               平均募集万=t['平均募集万'].round(0)).to_string())
print('\n  価格帯ごとの「総賞金/総募集額」')
for iv, g in d.groupby(b, observed=True):
    print('   %-22s n=%3d  総賞金/総募集額=%.3f' % (str(iv), len(g), g['pj'].sum() / g['total_man'].sum()))

print('\n=== [7] 多重検定補正 ===')
zs = {'log価格(win_jra,3基準同時)': 2.57, 'log価格(win2)': 2.96, 'log価格(win3)': 3.01,
      '3-4月生(ran)': 2.65, '牡馬(win3)': 4.13, '体重420(win_jra)': 3.76}
for k, z in zs.items():
    p = 2 * stats.norm.sf(abs(z))
    print('  %-28s z=%.2f p=%.4f  Bonferroni(70検定)p=%.3f' % (k, z, p, min(1, p * 70)))

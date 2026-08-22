# -*- coding: utf-8 -*-
"""切り口=手法。検出力・二値化の損失・交互作用・アウトカム定義・多重検定。"""
import io, json, os, sys
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from analyze5 import load, logit, design
from backtest import auc
pd.set_option('display.width', 220)

BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')

df = load(central_only=True)
rs = json.load(open(os.path.join(DS, 'race_summary.json'), encoding='utf-8'))
for c in ['wins_by3', 'starts_by3', 'prize_by3', 'jra_starts', 'jra_wins']:
    df[c] = df['key'].map(lambda k: (rs.get(k) or {}).get(c))
    df[c] = pd.to_numeric(df[c], errors='coerce')

df['win2'] = (df['jra_wins'].fillna(0) >= 2).astype(float)
df.loc[df['jra_wins'].isna(), 'win2'] = np.nan
df['win3'] = (df['jra_wins'].fillna(0) >= 3).astype(float)
df['ran'] = (df['jra_starts'].fillna(0) > 0).astype(float)
df['winby3'] = (df['wins_by3'].fillna(0) >= 1).astype(float)
df['grd'] = (pd.to_numeric(df['graded'], errors='coerce').fillna(0) >= 1).astype(float)
df['lprize'] = np.log1p(pd.to_numeric(df['prize_jra'], errors='coerce').fillna(0))

d = df.dropna(subset=['win_jra']).copy()
print('n =', len(d), ' win_jra率 =', round(d['win_jra'].mean(), 4))

d['price25_60_n'] = d['total_man'].between(2500, 3999).astype(int)
d['w420'] = (d['weight'] >= 420).astype(float)

# ---------------- 1. 検出力 ----------------
print('\n' + '=' * 80)
print('[1] 検出力: n=444 / 基準率49.3% で必要な差')
print('=' * 80)


def mde(n1, n2, p=0.493, z=1.96):
    return z * np.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))


for lab, col in [('3〜4月生まれ', 'mar_apr'), ('ノーザンF', 'nf'), ('母8〜11歳', 'dam811'),
                 ('牡馬', 'male'), ('総額2500-3999万', 'price25_60_n'), ('馬体重420kg+', 'w420')]:
    s = d.dropna(subset=[col])
    n1 = int((s[col] == 1).sum())
    n2 = int((s[col] == 0).sum())
    r1 = s.loc[s[col] == 1, 'win_jra'].mean()
    r0 = s.loc[s[col] == 0, 'win_jra'].mean()
    m = mde(n1, n2)
    print(f'{lab:<16} 該当{n1:>3} 非該当{n2:>3}  実測差={100*(r1-r0):+5.1f}pt  '
          f'z=1.96に必要な差={100*m:4.1f}pt  検出力80%必要差={100*m*(2.802/1.96):4.1f}pt')
print('\n※検出力80%に必要な差 = z境界差 x 2.802/1.96。実測差がこれ未満なら「効果ゼロ」ではなく「見えない」')

# 群サイズ別の必要差テーブル
print('\n該当群の割合別（合計444頭, 基準率49.3%）:')
for frac in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]:
    n1 = int(444 * frac)
    n2 = 444 - n1
    m = mde(n1, n2)
    print(f'  該当{n1:>3}頭({frac:.0%})  z=1.96必要差={100*m:4.1f}pt  検出力80%必要差={100*m*(2.802/1.96):4.1f}pt')

# ---------------- 2. 二値化の損失 ----------------
print('\n' + '=' * 80)
print('[2] 二値化の損失: 連続変数として投入（年度ダミー入りロジット）')
print('=' * 80)
d['w10'] = d['weight'] / 10.0
d['w10c'] = d['weight_rel'] / 10.0
d['da'] = d['dam_age'].astype(float)
d['da2'] = (d['da'] - 9) ** 2
d['lprice'] = np.log(d['total_man'].astype(float))
d['lprice2'] = (d['lprice'] - np.log(d['total_man']).mean()) ** 2
d['mo'] = d['month'].astype(float)
d['mo2'] = (d['mo'] - 3.5) ** 2
d['n_foals_n'] = pd.to_numeric(d['n_foals'], errors='coerce')
d['first_foal'] = (d['n_foals_n'] == 1).astype(float)
d['w10c2'] = d['w10c'] ** 2


def run(cols, target, data=None, label=''):
    s = (data if data is not None else d).dropna(subset=cols + [target])
    X, names = design(s, cols)
    r = logit(X, s[target], names)
    r = r[~r['変数'].astype(str).str.startswith('年度')]
    print(f'\n-- {label or ",".join(cols)} → {target}  n={len(s)}')
    print(r.round(3).to_string(index=False))
    return r


for tgt in ['win_jra', 'ret1']:
    run(['w10'], tgt, label='馬体重(10kg単位, 生の連続)')
    run(['w10c'], tgt, label='馬体重(年内平均比, 10kg単位)')
    run(['w10c', 'w10c2'], tgt, label='馬体重 連続+2次')
    run(['da', 'da2'], tgt, label='母年齢 連続+2次(中心9歳)')
    run(['lprice'], tgt, label='log募集総額')
    run(['lprice', 'lprice2'], tgt, label='log価格 連続+2次')
    run(['price_pct'], tgt, label='価格の年内パーセンタイル')
    run(['mo', 'mo2'], tgt, label='生月 連続+2次(中心3.5月)')

print('\n-- 参考: 二値版（現行3基準）')
run(['male', 'price25_60_n', 'w420'], 'win_jra', label='現行3基準(二値)')
run(['male', 'price25_60_n', 'w420'], 'ret1', label='現行3基準(二値)')
print('\n-- 連続フル')
run(['male', 'lprice', 'lprice2', 'w10c', 'da', 'da2'], 'win_jra', label='連続フル')
run(['male', 'lprice', 'lprice2', 'w10c', 'da', 'da2'], 'ret1', label='連続フル')

# ---------------- 3. LOYO AUC ----------------
print('\n' + '=' * 80)
print('[3] leave-one-year-out AUC: 加点方式 vs ロジット予測確率')
print('=' * 80)


def loyo(cols, target, data, ridge=1.0):
    s = data.dropna(subset=cols + [target]).copy().reset_index(drop=True)
    preds = np.full(len(s), np.nan)
    for y in sorted(s['year'].unique()):
        tr = s[s['year'] != y]
        te = s[s['year'] == y]
        Xtr = np.column_stack([np.ones(len(tr))] + [tr[c].astype(float).values for c in cols])
        Xte = np.column_stack([np.ones(len(te))] + [te[c].astype(float).values for c in cols])
        r = logit(Xtr, tr[target], ['b'] + cols, ridge=ridge)
        preds[te.index] = Xte @ r['係数'].values
    # 年内でのランクに直してからプール（年度差を消す）
    s['_p'] = preds
    s['_pr'] = s.groupby('year')['_p'].rank(pct=True)
    return auc(s[target], preds), auc(s[target], s['_pr']), len(s)


def score_auc(scorecols, target, data):
    s = data.dropna(subset=scorecols + [target]).copy()
    sc = s[scorecols].astype(float).sum(axis=1)
    s['_s'] = sc
    s['_sr'] = s.groupby('year')['_s'].rank(pct=True)
    return auc(s[target], sc), auc(s[target], s['_sr']), len(s)


for tgt in ['win_jra', 'ret1']:
    print(f'\n目的={tgt}   (raw / 年内ランク化)')
    a, ar, n = score_auc(['male', 'price25_60_n', 'w420'], tgt, d)
    print(f'  現行3基準 加点(1点ずつ)          AUC={a:.3f} / {ar:.3f}  n={n}')
    a, ar, n = score_auc(['male', 'mar_apr', 'nf', 'dam811', 'price25_60', 'w430'], tgt, d)
    print(f'  旧6基準 加点                     AUC={a:.3f} / {ar:.3f}  n={n}')
    a, ar, n = loyo(['male', 'price25_60_n', 'w420'], tgt, d)
    print(f'  LOYOロジット 3基準を二値のまま重み付け AUC={a:.3f} / {ar:.3f}')
    a, ar, n = loyo(['male', 'lprice', 'w10c'], tgt, d)
    print(f'  LOYOロジット 性+log価格+体重(連続)    AUC={a:.3f} / {ar:.3f}')
    a, ar, n = loyo(['male', 'lprice', 'lprice2', 'w10c'], tgt, d)
    print(f'  LOYOロジット +価格2次                AUC={a:.3f} / {ar:.3f}')
    a, ar, n = loyo(['male', 'lprice', 'lprice2', 'w10c', 'da', 'da2', 'mar_apr', 'nf'], tgt, d)
    print(f'  LOYOロジット 連続フル8変数           AUC={a:.3f} / {ar:.3f}')

# ---------------- 4. 交互作用 ----------------
print('\n' + '=' * 80)
print('[4] 交互作用')
print('=' * 80)
lp = d['lprice'] - d['lprice'].mean()
d['male_x_w'] = d['male'] * d['w10c']
d['price_x_w'] = lp * d['w10c']
d['male_x_price'] = d['male'] * lp
d['male_x_w420'] = d['male'] * d['w420']
d['nf_x_price'] = d['nf'] * lp
for tgt in ['win_jra', 'ret1']:
    run(['male', 'w10c', 'male_x_w'], tgt, label='性別×馬体重(連続)')
    run(['male', 'lprice', 'male_x_price'], tgt, label='性別×log価格')
    run(['lprice', 'w10c', 'price_x_w'], tgt, label='価格×馬体重')
    run(['male', 'w420', 'male_x_w420'], tgt, label='性別×馬体重420+(二値)')
    run(['nf', 'lprice', 'nf_x_price'], tgt, label='ノーザンF×価格')

# ---------------- 5. アウトカム定義 ----------------
print('\n' + '=' * 80)
print('[5] アウトカム定義を変える')
print('=' * 80)
CAND = [('male', '牡馬'), ('mar_apr', '3-4月生'), ('nf', 'ノーザンF'), ('dam811', '母8-11歳'),
        ('price25_60_n', '総額2500-3999'), ('w420', '体重420+'), ('lprice', 'log価格'),
        ('w10c', '体重連続'), ('da', '母年齢連続'), ('first_foal', '初仔')]
OUT = [('ran', '出走(JRA)'), ('win_jra', '1勝'), ('winby3', '3歳末勝上'),
       ('win2', '2勝以上'), ('win3', '3勝以上'), ('grd', '重賞'), ('ret1', '回収>=1')]
rows = []
for ocol, olab in OUT:
    s0 = d.dropna(subset=[ocol])
    for c, clab in CAND:
        s = s0.dropna(subset=[c])
        if s[c].nunique() < 2:
            continue
        X, names = design(s, [c])
        r = logit(X, s[ocol], names)
        rows.append({'outcome': olab, '変数': clab, 'z': round(float(r.iloc[-1]['z']), 2)})
t = pd.DataFrame(rows).pivot(index='変数', columns='outcome', values='z')
t = t[[o[1] for o in OUT]]
print('\nz値 一覧（年度ダミー入りロジット）')
print(t.to_string())
print('\n各アウトカムの発生率')
print(pd.Series({olab: round(d[ocol].mean(), 3) for ocol, olab in OUT}).to_string())
print('\n年度別 重賞頭数 / 2勝以上頭数')
print(d.groupby('year')[['grd', 'win2', 'win3', 'ran', 'winby3']].sum().to_string())

print('\n-- log(JRA賞金+1) への効き（OLS, 年度ダミー入り）')
for c, clab in CAND:
    s = d.dropna(subset=[c, 'lprize'])
    X, names = design(s, [c])
    y = s['lprize'].values
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ b
    s2 = resid @ resid / (len(y) - X.shape[1])
    cov = s2 * np.linalg.pinv(X.T @ X)
    print(f'  {clab:<16} t={b[-1]/np.sqrt(cov[-1,-1]):+.2f}')

# ---------------- 6. 年度別安定性 ----------------
print('\n' + '=' * 80)
print('[6] 年度別安定性（該当群 - 非該当群 の率差）')
print('=' * 80)


def byyear(col, tgt, thresh=None):
    s = d.dropna(subset=[col, tgt])
    v = (s[col] >= thresh).astype(int) if thresh is not None else s[col].astype(int)
    out = []
    for y in sorted(s['year'].unique()):
        m = (s['year'] == y).values
        g = s[m].groupby(v[m].values)[tgt].agg(['size', 'mean'])
        if len(g) == 2:
            out.append(f"{y}:{100*(g['mean'].iloc[1]-g['mean'].iloc[0]):+.0f}pt({int(g['size'].iloc[1])}/{int(g['size'].iloc[0])})")
        else:
            out.append(f'{y}:-')
    return '  '.join(out)


for col, th, lab in [('w10c', 0, '体重 年内平均以上'), ('mar_apr', None, '3-4月生'),
                     ('nf', None, 'ノーザンF'), ('dam811', None, '母8-11歳'),
                     ('first_foal', None, '初仔'), ('male', None, '牡馬'),
                     ('price25_60_n', None, '総額2500-3999')]:
    for tgt in ['win_jra', 'ret1', 'win2']:
        print(f'{lab:<18} {tgt:<8} {byyear(col, tgt, th)}')
    print()

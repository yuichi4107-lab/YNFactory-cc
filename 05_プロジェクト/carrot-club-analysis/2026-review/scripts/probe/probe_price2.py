# -*- coding: utf-8 -*-
"""価格 第2波: 下限/上限の分解、3000万スパイクの多重検定チェック、牡馬内での再検定。"""
import io, os, sys
import numpy as np
import pandas as pd
from analyze5 import load, logit, design

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 250)
pd.set_option('display.max_rows', 400)
BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, '..', '..', 'data')
rng = np.random.default_rng(20260822)

df = load(central_only=True).dropna(subset=['win_jra']).copy()
df['logp'] = np.log(df['total_man'])
df['logp_rel'] = df['logp'] - df.groupby('year')['logp'].transform('mean')
df['logp_rel2'] = df['logp_rel'] ** 2
df['p3000'] = (df['total_man'] == 3000).astype(int)
df['lo'] = (df['total_man'] < 2500).astype(int)
df['hi40'] = (df['total_man'] >= 4000).astype(int)


def sec(t):
    print('\n' + '=' * 90); print('# ' + t); print('=' * 90)


def run(cols, y='win_jra', sub=None, label=''):
    s = df if sub is None else sub
    s = s.dropna(subset=cols + [y])
    X, names = design(s, cols)
    r = logit(X, s[y], names)
    r = r[~r['変数'].str.startswith('年度')]
    print(f'  [{label or ",".join(cols)}] target={y} n={len(s)}')
    print(r.round(3).to_string(index=False))
    return r


def yr_table(sub, col):
    piv = sub.pivot_table(index=col, columns='year', values='win_jra',
                          aggfunc=['mean', 'size'], dropna=False)
    m, n = piv['mean'] * 100, piv['size']
    tot = sub.groupby(col, observed=False)['win_jra'].agg(['mean', 'size'])
    print('  ' + f'{"":<14}' + ''.join(f'{y:>11}' for y in m.columns) + f'{"ALL":>13}')
    for idx in m.index:
        cells = []
        for y in m.columns:
            mv, nv = m.loc[idx, y], n.loc[idx, y]
            cells.append(f'{int(round(mv)):>3}%({int(nv):>2})' if pd.notna(mv) and nv > 0 else f'{"-":>8}')
        t = tot.loc[idx]
        cells.append(f'{int(round(t["mean"]*100)):>3}%({int(t["size"]):>3})')
        print(f'  {str(idx):<14}' + ''.join(f'{c:>11}' for c in cells))


sec('A) 下限と上限を分けて入れる')
print('現行基準 2500-3999 は「下限」と「上限」の合成。どちらが効いているか分解する。')
run(['lo'], 'win_jra', label='<2500ダミー')
yr_table(df, 'lo')
print()
run(['lo', 'hi40'], 'win_jra', label='<2500 と >=4000 を同時に')
print()
print('-- 3水準に切って比較（基準=2500-3999）')
df['lvl'] = np.where(df['total_man'] < 2500, '1_under2500',
                     np.where(df['total_man'] < 4000, '2_2500-3999', '3_4000plus'))
yr_table(df, 'lvl')
df['d_lo'] = (df['lvl'] == '1_under2500').astype(int)
df['d_hi'] = (df['lvl'] == '3_4000plus').astype(int)
run(['d_lo', 'd_hi'], 'win_jra', label='基準=2500-3999')
run(['d_lo', 'd_hi'], 'ret1', label='基準=2500-3999 / ret1(★分母が価格)')

print('\n-- ret1 側で「上限」がどう見えるか（なぜ3999で切られたのか）')
def band(v):
    if v < 2500: return '1 -2400'
    if v < 4000: return '2 2500-3999'
    if v < 6000: return '3 4000-5999'
    return '4 6000+'
df['b4'] = df['total_man'].map(band)
print(df.groupby('b4').agg(n=('ret1', 'size'), win_jra=('win_jra', 'mean'), ret1=('ret1', 'mean'),
                           ret_med=('ret', 'median'), ret_mean=('ret', 'mean'),
                           prize_mean=('prize', 'mean')).round(3).to_string())

sec('B) 3000万スパイクは価格水準で説明できるか')
run(['logp_rel', 'logp_rel2', 'p3000'], 'win_jra', label='価格の滑らかな効果を入れた上での3000万')
print()
print('-- 多重検定チェック: 5頭以上のすべての価格水準について同じ検定をした場合のz')
res = []
for p in sorted(df['total_man'].unique()):
    s = df.copy(); s['_d'] = (s['total_man'] == p).astype(int)
    n = int(s['_d'].sum())
    if n < 5: continue
    X, names = design(s, ['_d'])
    r = logit(X, s['win_jra'], names)
    z = float(r[r['変数'] == '_d']['z'].iloc[0])
    # 年度別に基準を上回った年の数
    ok = 0; yrs = 0
    for y in sorted(s['year'].unique()):
        a = s[(s['year'] == y) & (s['_d'] == 1)]['win_jra']
        b = s[(s['year'] == y) & (s['_d'] == 0)]['win_jra']
        if len(a) >= 3:
            yrs += 1; ok += int(a.mean() > b.mean())
    res.append({'price': p, 'n': n, 'win': round(float(s[s['_d'] == 1]['win_jra'].mean()), 3),
                'z': round(z, 2), '上回った年/評価年': f'{ok}/{yrs}'})
r = pd.DataFrame(res).sort_values('z', ascending=False)
print(r.to_string(index=False))
print(f'\n検定した水準数: {len(r)} / うち|z|>2: {(r["z"].abs() > 2).sum()}')

print('\n-- 3000万近辺をまとめた場合（2800-3200 / 2600-3600）はどうか')
for lo, hi, lab in [(2800, 3200, '2800-3200'), (2600, 3600, '2600-3600'), (3000, 3000, '3000のみ')]:
    df['_d'] = df['total_man'].between(lo, hi).astype(int)
    run(['_d'], 'win_jra', label=lab)
    yr_table(df, '_d')
    print()

sec('C) 牡馬に限っても価格は効くか（牡馬基準と重複していないか）')
print('価格と性別のクロス')
print(pd.crosstab(df['lvl'], df['sex']).to_string())
mal = df[df['male'] == 1]
fem = df[df['male'] == 0]
print(f'\n牡馬 n={len(mal)} / 牝せん n={len(fem)}')
for name, s in [('牡馬のみ', mal), ('牝馬のみ', fem)]:
    print(f'\n-- {name}')
    run(['logp_rel'], 'win_jra', sub=s, label=f'logp_rel {name}')
    run(['d_lo', 'd_hi'], 'win_jra', sub=s, label=f'価格3水準 {name}')
    run(['p3000'], 'win_jra', sub=s, label=f'3000万 {name}')
    yr_table(s, 'lvl')

print('\n-- 既存3基準（牡・2500-3999・420kg以上）と一緒に入れる')
df['w420'] = (df['weight'] >= 420).astype(int)
df['price_ok'] = df['total_man'].between(2500, 3999).astype(int)
df['price_ok2'] = (df['total_man'] >= 2500).astype(int)
s = df.dropna(subset=['weight'])
run(['male', 'price_ok', 'w420'], 'win_jra', sub=s, label='現行3基準')
run(['male', 'price_ok2', 'w420'], 'win_jra', sub=s, label='上限を外す(2500以上)')
run(['male', 'price_ok2', 'p3000', 'w420'], 'win_jra', sub=s, label='2500以上 + 3000万ボーナス')
run(['male', 'logp_rel', 'logp_rel2', 'w420'], 'win_jra', sub=s, label='価格を連続で')

sec('D) 「割安/割高」の再定義: 実価格 vs 測尺・父から予測される価格')
m = df.dropna(subset=['weight', 'height', 'girth', 'cannon']).copy()
gs = m.groupby('sire')['logp_rel']
m['sire_n'] = gs.transform('size')
m['sire_loo'] = np.where(m['sire_n'] > 1, (gs.transform('sum') - m['logp_rel']) / (m['sire_n'] - 1), 0.0)
Xd = np.column_stack([np.ones(len(m)), m['weight'], m['height'], m['girth'], m['cannon'],
                      m['male'], m['sire_loo']])
b, *_ = np.linalg.lstsq(Xd, m['logp_rel'].values, rcond=None)
m['pred_logp'] = Xd @ b
m['resid'] = m['logp_rel'] - m['pred_logp']
print('実価格と予測価格の相関:', round(float(np.corrcoef(m['logp_rel'], m['pred_logp'])[0, 1]), 3))
run(['logp_rel', 'pred_logp'], 'win_jra', sub=m, label='実価格 と 予測価格(測尺+父) を同時に')
print('→ pred_logp の係数がゼロ近傍なら「あるべき価格からの乖離＝割安/割高」に情報がない')
run(['resid'], 'win_jra', sub=m, label='残差のみ(=割高度)')
print('\n-- 割安上位/割高上位を年度別に（残差3分位）※上のprobe_priceと同じ')
m['_t'] = pd.qcut(m['resid'], 3, labels=['A_割安', 'B_中', 'C_割高'])
yr_table(m, '_t')
print('\n-- 割安馬の中身（何が安く見えているだけか）')
print(m.groupby('_t', observed=False).agg(n=('win_jra', 'size'), price_med=('total_man', 'median'),
                                          weight=('weight', 'mean'), male=('male', 'mean'),
                                          nf=('nf', 'mean'), win=('win_jra', 'mean')).round(3).to_string())

sec('E) 価格調整後の馬体重は 馬体重 と 価格 の和以上か')
run(['weight'], 'win_jra', sub=m, label='weight のみ')
run(['weight', 'logp_rel'], 'win_jra', sub=m, label='weight + 価格')
Xw = np.column_stack([np.ones(len(m)), m['logp_rel'], m['male']])
bw, *_ = np.linalg.lstsq(Xw, m['weight'].values, rcond=None)
m['w_resid'] = m['weight'].values - Xw @ bw
run(['w_resid', 'logp_rel'], 'win_jra', sub=m, label='価格調整後馬体重 + 価格')

sec('F) 2026年度94頭に当てはめたときの通過頭数')
try:
    b26 = pd.read_csv(os.path.join(DATA, 'bosyu_2026.csv'), encoding='utf-8-sig')
    b26['price'] = pd.to_numeric(b26['募集総額_万円'].astype(str).str.replace('万', '', regex=False)
                                 .str.replace(',', '', regex=False), errors='coerce')
    print('2026年度 価格分布')
    print(b26['price'].describe().to_string())
    print(b26['price'].value_counts().sort_index().to_string())
    print('\n牡馬:', (b26['性別'].astype(str).str.contains('牡')).sum(), '/', len(b26))
    for lab, mask in [('2500-3999', b26['price'].between(2500, 3999)),
                      ('2500以上', b26['price'] >= 2500),
                      ('3000ちょうど', b26['price'] == 3000),
                      ('2500-5999', b26['price'].between(2500, 5999))]:
        print(f'  {lab}: {int(mask.sum())}頭')
    print('\n※2026年度は価格水準がさらに上がっているか: 5年の年度中央値と比較')
    print(df.groupby('year')['total_man'].median().to_string())
    print('2026 median:', b26['price'].median())
except Exception:
    import traceback; traceback.print_exc()

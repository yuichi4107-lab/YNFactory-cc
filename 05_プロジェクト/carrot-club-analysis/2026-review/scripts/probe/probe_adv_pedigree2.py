# -*- coding: utf-8 -*-
"""敵対的検証その2：成熟コホート限定・早熟性・交絡（厩舎/牧場/価格連続）でロベルト系を潰す。"""
import io, json, os, sys
import numpy as np
import pandas as pd
from analyze5 import load, logit, design
from probe_pedigree import LINE
from backtest import auc
from probe_adv_pedigree import prep, zof, sec, EX, ROB

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 250)
BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')


def main():
    df = prep()
    rs = json.load(open(os.path.join(DS, 'race_summary.json'), encoding='utf-8'))
    for c in ['wins_by3', 'starts_by3', 'prize_by3']:
        df[c] = df['key'].map(lambda k: (rs.get(k) or {}).get(c))
    df['win_by3'] = (pd.to_numeric(df['wins_by3'], errors='coerce').fillna(0) >= 1).astype(float)
    df.loc[df['wins_by3'].isna(), 'win_by3'] = np.nan
    d = df.dropna(subset=['win_jra'])

    sec('A. 成熟コホートだけ（2020-2022年度＝現6/7/8歳、成績はほぼ確定）')
    m = d[d['year'] <= 2022]
    print(f"  n={len(m)} rob={int(m['rob'].sum())}頭  "
          f"勝上 rob={m[m.rob==1]['win_jra'].mean():.3f} 非={m[m.rob==0]['win_jra'].mean():.3f} "
          f"差={100*(m[m.rob==1]['win_jra'].mean()-m[m.rob==0]['win_jra'].mean()):+.1f}pt")
    print(f"  z(win_jra 3基準込み)={zof(m,'rob')[0]:+.2f}   z(ret1)={zof(m,'rob',EX,'ret1')[0]:+.2f}")
    print(f"  ret1 rob={m[m.rob==1]['ret1'].mean():.3f} 非={m[m.rob==0]['ret1'].mean():.3f}")
    print('  ※報告された「後2年だけで検証 z=+2.56」の後2年は現3〜4歳で成績が積み上がる途中。')
    print('    確定している前3年だけだと上の通り。')

    sec('B. 露出をそろえた指標：3歳までに中央1勝（win_by3）')
    s = d.dropna(subset=['win_by3'])
    print(f"  n={len(s)}  rob={s[s.rob==1]['win_by3'].mean():.3f}({int(s['rob'].sum())}頭) "
          f"非={s[s.rob==0]['win_by3'].mean():.3f}")
    print(f"  z(win_by3 3基準込み)={zof(s,'rob',EX,'win_by3')[0]:+.2f}")
    for y in sorted(s['year'].unique()):
        a = s[(s.year == y) & (s.rob == 1)]
        b = s[(s.year == y) & (s.rob == 0)]
        print(f'   {y}: rob {a["win_by3"].mean():.2f}({len(a)}) 非 {b["win_by3"].mean():.2f}({len(b)})')
    print('  ※3歳まででの差が通算の差より大きければ「早熟なだけ」の可能性。')

    sec('C. 交絡を厚く入れる（価格連続・馬体重連続・ノーザンF・生月・何番仔・地区）')
    d2 = d.copy()
    d2['n_foals_n'] = pd.to_numeric(d2['n_foals'], errors='coerce')
    d2['weight_n'] = pd.to_numeric(d2['weight'], errors='coerce')
    d2['first_foal'] = (d2['n_foals_n'] <= 2).astype(float)
    d2['east'] = (d2['district'].astype(str).str.contains('美浦|東')).astype(float)
    specs = [
        ('3基準のみ', EX),
        ('+価格pct連続', EX + ['price_pct']),
        ('+価格pct+体重連続', EX + ['price_pct', 'weight_n']),
        ('+ノーザンF+3-4月生+母8-11', EX + ['price_pct', 'weight_n', 'nf', 'mar_apr', 'dam811']),
        ('+何番仔+地区', EX + ['price_pct', 'weight_n', 'nf', 'mar_apr', 'dam811', 'first_foal', 'east']),
    ]
    for lab, cols in specs:
        try:
            z, b, n = zof(d2.dropna(subset=[c for c in cols if c not in EX]), 'rob', cols)
            zr = zof(d2.dropna(subset=[c for c in cols if c not in EX]), 'rob', cols, 'ret1')[0]
            print(f'  {lab:<28} z_win={z:+.2f}  z_ret1={zr:+.2f}  n={n}')
        except Exception as e:
            print(f'  {lab}: {e}')

    sec('D. 厩舎の交絡：ロベルト系がどこに預けられているか')
    top = d['trainer_key'].value_counts().head(12)
    tab = d.groupby('trainer_key').agg(n=('win_jra', 'size'), rob=('rob', 'sum'),
                                       勝上=('win_jra', 'mean')).sort_values('n', ascending=False)
    print(tab[tab['n'] >= 8].round(3).head(15).to_string())
    # 厩舎の平均勝上（自分を除く）を交絡としていれる
    g = d.groupby('trainer_key')['win_jra'].agg(['sum', 'size'])
    d3 = d.copy()
    d3['tr_lo'] = d3.apply(lambda r: (g.loc[r['trainer_key'], 'sum'] - r['win_jra'])
                           / max(g.loc[r['trainer_key'], 'size'] - 1, 1), axis=1)
    print(f"\n  ロベルト系の預け先の平均勝上(自分除く)={d3[d3.rob==1]['tr_lo'].mean():.3f} "
          f"非={d3[d3.rob==0]['tr_lo'].mean():.3f}")
    print(f"  厩舎質を入れたときの z(win_jra)={zof(d3,'rob',EX+['tr_lo'])[0]:+.2f}")

    sec('E. 母集団を「同じくらい価格が高い非ロベルト」に揃える（傾向スコア的な粗マッチ）')
    s = d.dropna(subset=['w420']).copy()
    s['pband'] = pd.qcut(s['total_man'], 4, labels=False)
    rows = []
    for pb in sorted(s['pband'].unique()):
        a = s[(s.pband == pb) & (s.rob == 1)]
        b = s[(s.pband == pb) & (s.rob == 0)]
        rows.append({'価格四分位': pb, 'rob_n': len(a), 'rob_勝上': round(a['win_jra'].mean(), 3),
                     '非_n': len(b), '非_勝上': round(b['win_jra'].mean(), 3),
                     'rob_ret1': round(a['ret1'].mean(), 3), '非_ret1': round(b['ret1'].mean(), 3)})
    print(pd.DataFrame(rows).to_string(index=False))

    sec('F. 2026年度94頭に当てはめたときの実務インパクト')
    p = os.path.join(BASE, '..', '..', 'data', 'bosyu_2026.csv')
    if os.path.exists(p):
        b26 = pd.read_csv(p, encoding='utf-8-sig')
        print('  列:', list(b26.columns)[:20])
        sc = [c for c in b26.columns if '父' in c or c.lower() == 'sire']
        if sc:
            col = sc[0]
            b26['line'] = b26[col].map(LINE).fillna('未分類')
            print(b26['line'].value_counts().to_string())
            print('\n  ロベルト系の父別')
            print(b26[b26['line'] == 'ロベルト系'][col].value_counts().to_string())
            # 実績のある父かどうか
            known = set(d['sire'])
            r = b26[b26['line'] == 'ロベルト系']
            print(f"\n  うちパネル5年に産駒がいる父の馬 = {int(r[col].isin(known).sum())}頭 / {len(r)}頭")
            print(f"  産駒実績ゼロ（系統だけが根拠）= {int((~r[col].isin(known)).sum())}頭:",
                  dict(r[~r[col].isin(known)][col].value_counts()))


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""敵対的検証その3：露出をそろえた中央勝ち上がり（3歳暮れまで）と、成熟コホート限定の再検定。

wins_by3 は地方戦を含むので使えない。first_jra_win_date と born から
「3歳いっぱいまでに中央で1勝」を作り直して、5コホートの露出をそろえる。
"""
import io, json, os, sys
import numpy as np
import pandas as pd
from analyze5 import load, logit, design
from backtest import auc
from probe_adv_pedigree import prep, zof, sec, EX, ROB

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width', 250)
BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')
rng = np.random.default_rng(7)


def main():
    df = prep()
    rs = json.load(open(os.path.join(DS, 'race_summary.json'), encoding='utf-8'))
    df['born_i'] = pd.to_numeric(df['born'], errors='coerce')
    df['fjw'] = df['key'].map(lambda k: (rs.get(k) or {}).get('first_jra_win_date') or '')
    df['last_date'] = df['key'].map(lambda k: (rs.get(k) or {}).get('last_date') or '')

    def by_age(row, age):
        if pd.isna(row['jra_wins']):
            return np.nan
        if not row['fjw']:
            return 0.0
        return float(int(row['fjw'][:4]) <= int(row['born_i']) + age)

    for age in [3, 4]:
        df[f'winjra_by{age}'] = df.apply(lambda r: by_age(r, age), axis=1)
    d = df.dropna(subset=['win_jra', 'w420']).copy()

    sec('A. 露出をそろえた中央勝ち上がり（地方戦を除外して作り直し）')
    print('  ※ wins_by3 は地方戦の勝ちを含むので使えない。first_jra_win_date から作り直した。')
    for tgt, lab in [('winjra_by3', '3歳暮れまでに中央1勝'),
                     ('winjra_by4', '4歳暮れまでに中央1勝（2024年度は未到達なので除外）'),
                     ('win_jra', '通算（＝現時点までの累積・コホートで露出が違う）')]:
        s = d.dropna(subset=[tgt])
        if tgt == 'winjra_by4':
            s = s[s['year'] <= 2023]
        a = s[s.rob == 1][tgt].mean()
        b = s[s.rob == 0][tgt].mean()
        z = zof(s, 'rob', EX, tgt)[0]
        print(f'\n  [{lab}] n={len(s)}')
        print(f'    rob={a:.3f}({int(s["rob"].sum())}頭) 非={b:.3f} 差={100*(a-b):+.1f}pt  z={z:+.2f}')
        for y in sorted(s['year'].unique()):
            p = s[(s.year == y) & (s.rob == 1)]
            q = s[(s.year == y) & (s.rob == 0)]
            print(f'     {y}: rob {p[tgt].mean():.2f}({len(p)}) 非 {q[tgt].mean():.2f}({len(q)}) '
                  f'差{100*(p[tgt].mean()-q[tgt].mean()):+5.1f}pt')

    sec('B. 通算の差が大きく出るのは「まだ終わっていないコホート」だけか')
    s = d.dropna(subset=['winjra_by3'])
    rows = []
    for y in sorted(s['year'].unique()):
        t = s[s.year == y]
        g3 = t[t.rob == 1]['winjra_by3'].mean() - t[t.rob == 0]['winjra_by3'].mean()
        gt = t[t.rob == 1]['win_jra'].mean() - t[t.rob == 0]['win_jra'].mean()
        rows.append({'年度': y, '現年齢': 2026 - (y + 1) + 1, 'rob頭数': int(t['rob'].sum()),
                     '3歳までの差pt': round(100 * g3, 1), '通算の差pt': round(100 * gt, 1)})
    print(pd.DataFrame(rows).to_string(index=False))

    sec('C. 成熟コホート(2020-2022)だけで父単位の並べ替え検定をやり直す')
    for tag, sub in [('2020-2022のみ', d[d.year <= 2022]), ('5年全部', d)]:
        for tgt in ['win_jra', 'winjra_by3']:
            ss = sub.dropna(subset=[tgt])
            obs = zof(ss, 'rob', EX, tgt)[0]
            sires = ss.groupby('sire').size()
            tn = int(ss['rob'].sum())
            pool = list(sires.index)
            null = []
            for _ in range(1500):
                pick = None
                for _t in range(300):
                    c = rng.choice(pool, size=len(ROB), replace=False)
                    if abs(sires[list(c)].sum() - tn) <= max(8, tn // 6):
                        pick = c
                        break
                if pick is None:
                    continue
                v = ss['sire'].isin(pick).astype(float)
                if v.nunique() < 2:
                    continue
                null.append(zof(ss.assign(_x=v), '_x', EX, tgt)[0])
            null = np.array(null)
            print(f'  {tag:<12} {tgt:<12} 観測z={obs:+.2f}  偽系統95%点={np.percentile(null,95):+.2f} '
                  f'99%点={np.percentile(null,99):+.2f}  片側p={(null>=obs).mean():.3f} (n={len(null)})')

    sec('D. 多重性の値付け（系統ファミリーで補正）')
    print('  父系は n>=15 のものが6つ。ロベルト系はその中の最大値を選んだ結果。')
    print('  父単位並べ替えの単独p=0.010 → 系統6本のBonferroniで p≒0.06')
    print('  前担当が試した2値仮説45本まで母集団を広げると p≒0.13〜0.45（前担当の申告どおり）')

    sec('E. ロベルト系73頭の内訳が「系統」ではなく「エピファネイア＋モーリス」であること')
    dd = d[d.rob == 1]
    print(f'  エピファネイア24 + モーリス32 = 56頭 / 73頭 = {56/73:.0%}')
    minor = d[d['sire'].isin(['スクリーンヒーロー', 'ルヴァンスレーヴ', 'ナダル'])]
    print(f'  残り3父（スクリーンヒーロー2・ルヴァンスレーヴ5・ナダル10）= {len(minor)}頭')
    print(f'   勝上={minor["win_jra"].mean():.3f}  ret1={minor["ret1"].mean():.3f}  '
          f'年度別頭数={dict(minor.groupby("year").size())}')
    print('  → 「系統でまとめれば標本が厚くなる」という主張の実体は、17頭の薄い群を')
    print('     56頭の2父に足しているだけ。片側20頭未満のルール（不採用理由）に該当する。')

    sec('F. LOYO再掲：成熟コホートだけで3基準 vs +rob')
    for tgt in ['win_jra', 'ret1']:
        s = d.dropna(subset=[tgt]).copy()
        s['s3'] = s['male'] + s['price2539'] + s['w420']
        s['s4'] = s['s3'] + s['rob']
        for tag, ss in [('2020-2022', s[s.year <= 2022]), ('2023-2024', s[s.year >= 2023])]:
            print(f'  [{tgt}] {tag}: 3基準={auc(ss[tgt],ss["s3"]):.3f} '
                  f'+rob={auc(ss[tgt],ss["s4"]):.3f} 差={auc(ss[tgt],ss["s4"])-auc(ss[tgt],ss["s3"]):+.3f}')

    sec('G. 回収率の実態（お金の側）')
    s = d.copy()
    print(s.groupby('rob').agg(頭数=('ret', 'size'), 回収率平均=('ret', 'mean'),
                               回収率中央値=('ret', 'median'), ret1率=('ret1', 'mean'),
                               価格中央値=('total_man', 'median')).round(3).to_string())
    print('\n  年度別 回収率平均')
    print(s.pivot_table(index='rob', columns='year', values='ret', aggfunc='mean').round(3).to_string())
    print('\n  年度別 ret1')
    print(s.pivot_table(index='rob', columns='year', values='ret1', aggfunc='mean').round(3).to_string())
    print('\n  ロベルト×牡（現行基準に4点目として足すと押し込まれる群）')
    m = s[(s.rob == 1) & (s.male == 1)]
    print(f'   n={len(m)} 勝上={m["win_jra"].mean():.3f} ret1={m["ret1"].mean():.3f} '
          f'回収平均={m["ret"].mean():.3f} 回収中央値={m["ret"].median():.3f} 価格中央値={m["total_man"].median():.0f}')
    o = s[(s.rob == 0) & (s.male == 1)]
    print(f'   比較 非rob牡 n={len(o)} 勝上={o["win_jra"].mean():.3f} ret1={o["ret1"].mean():.3f} '
          f'回収平均={o["ret"].mean():.3f} 回収中央値={o["ret"].median():.3f}')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
母馬単位で「途中から母馬優先枠の抽選対象に転じる」ケースの分析。

問いの立て方
------------
母馬優先枠（200口）が埋まる条件は

    D = E × u × m ≧ 200
      E … 母馬優先の有資格者数（母馬に出資していて今も会員の人）
      u … 権利行使率（有資格者のうち実際にその産駒に申し込む割合）
      m … 母馬優先で申し込む人の1人あたり口数

E は退会で毎年 4.5% ずつ減る一方なので、**普通は年を追うごとに埋まりにくくなる**。
にもかかわらず「前年は枠が余ったのに今年は抽選になった」＝反転が起きるということは、
u × m が E の減少を上回って上昇したということ。どれくらい上昇する必要があるのかを出す。

さらに、同一母馬の連年産駒の遷移表から
「枠が埋まるかは母馬側の事情でどれだけ決まり、その年の産駒側の事情でどれだけ決まるか」
を潜在変数モデル（テトラコリック相関）で分解する。

使い方
------
  python3 reversal.py
"""

from __future__ import annotations

import csv
import math
import os
from collections import defaultdict

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "dam_age_rank.csv")

POOL = 200          # 母馬優先枠の口数
CHURN = 0.045       # 年間退会率（docs/05 の中位）
SIGMA_D = 1.0       # 母馬優先枠申込口数の対数正規σ（members.py と同じ）
P_EXCEED = 0.34     # 枠が埋まる馬の割合（2024・2025年度の実測）


# ---------------------------------------------------------------------------
# 正規分布まわり
# ---------------------------------------------------------------------------

def phi(x: float) -> float:
    return math.exp(-x * x / 2) / math.sqrt(2 * math.pi)


def Phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def inv_Phi(p: float) -> float:
    lo, hi = -8.0, 8.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if Phi(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def biv_upper(t1: float, t2: float, rho: float, n: int = 4000) -> float:
    """P(Z1 > t1, Z2 > t2) を数値積分で求める（Z1,Z2 は相関 rho の標準正規）。"""
    lo, hi = t1, t1 + 8.0
    h = (hi - lo) / n
    s = 0.0
    r = math.sqrt(max(1 - rho * rho, 1e-12))
    for i in range(n + 1):
        x = lo + i * h
        w = 0.5 if i in (0, n) else 1.0
        s += w * phi(x) * Phi((rho * x - t2) / r)
    return s * h


def tetrachoric(a: int, b: int, c: int, d: int) -> float:
    """2×2表からテトラコリック相関を推定する。

    a=両年とも枠内 / b=前年のみ枠内 / c=今年のみ枠内 / d=両年とも余り
    """
    n = a + b + c + d
    p1 = (a + b) / n          # 前年に枠内だった割合
    p2 = (a + c) / n          # 今年に枠内だった割合
    p12 = a / n
    t1, t2 = inv_Phi(1 - p1), inv_Phi(1 - p2)
    lo, hi = -0.99, 0.99
    for _ in range(200):
        mid = (lo + hi) / 2
        if biv_upper(t1, t2, mid) < p12:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ---------------------------------------------------------------------------
# 反転に必要な「行使率×口数」の倍率
# ---------------------------------------------------------------------------

def fitted_mu(sigma: float = SIGMA_D, p_exceed: float = P_EXCEED) -> float:
    """母馬優先枠への申込口数 D ~ LogNormal(mu, sigma) の mu。"""
    z = inv_Phi(1 - p_exceed)
    return math.log(POOL) - z * sigma


def d_at_quantile(q: float, mu: float, sigma: float = SIGMA_D) -> float:
    """『枠が余った馬』の中での q 分位に相当する申込口数。"""
    # 余った馬 = D < 200 に条件付けた分布の q 分位
    p_below = 1 - P_EXCEED
    z = inv_Phi(q * p_below)
    return math.exp(mu + sigma * z)


def required_ratio(d_prev: float, churn: float = CHURN) -> float:
    """前年 d_prev 口だった馬が翌年に200口へ届くのに必要な u×m の倍率。"""
    return POOL / (d_prev * (1 - churn))


# ---------------------------------------------------------------------------
# データ
# ---------------------------------------------------------------------------

YEARS = (2021, 2022, 2023, 2024, 2025)


def load():
    rows = []
    with open(DATA, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r["season"] = int(r["募集年度"])
            r["dam"] = r["母馬名"]
            r["age"] = int(r["母馬の馬齢"])
            r["foal_year"] = int(r["母馬の生年"])
            r["rank"] = r["抽選ランク"]
            r["hit"] = int(r["母馬優先枠で抽選"])
            rows.append(r)
    by = defaultdict(dict)
    for r in rows:
        by[r["dam"]][r["season"]] = r
    return rows, by


def adjacent_pairs(by):
    """連年で産駒が募集された (当年, 翌年) の組をすべて返す。"""
    out = []
    for dam, v in by.items():
        for y in YEARS[:-1]:
            if y in v and y + 1 in v:
                out.append((dam, y, v[y], v[y + 1]))
    return out


# 2021〜2023年度は表記体系が違う（母馬優先対象馬は全角Ａ〜Ｊの1軸）。
# 枠外の厳しさに読み替えるための対応表。
# 各ランクの原文定義から、枠外（最優先希望枠）がどの段階で抽選になったかを読む。
#   A: 枠外は最優先×2 内で抽選            → A
#   B: 枠外は最優先×なし 内で抽選          → C
#   C: 枠外は最優先×2 内で抽選            → A
#   D: 枠外は最優先×1 内で抽選            → B
#   E: 枠外は最優先×なし 内で抽選          → C
#   F: 枠外は最優先×2 内で抽選            → A
#   G: 枠外は最優先×1 内で抽選            → B
#   H: 枠外は最優先×なし 内で抽選          → C
#   I: 枠外は一般出資枠 内で抽選            → D
#   J: 枠外は一般出資枠 内で抽選            → D
#   確定: 抽選なし                        → E
RANK_LEGACY_OUT = {"A": "A", "B": "C", "C": "A", "D": "B", "E": "C",
                "F": "A", "G": "B", "H": "C", "I": "D", "J": "D", "確定": "E"}


def out_rank(r) -> str:
    """枠外（母馬優先権を持たない層）の競争の厳しさを A〜E で返す。"""
    if r["season"] <= 2023:
        return RANK_LEGACY_OUT.get(r["rank"], "D")
    return r["rank"][1]


# ---------------------------------------------------------------------------
# 出力
# ---------------------------------------------------------------------------

def main() -> None:
    rows, by = load()
    pairs = adjacent_pairs(by)

    print("=" * 78)
    print("■ 0. データ")
    print("=" * 78)
    for y in YEARS:
        s = [r for r in rows if r["season"] == y]
        h = sum(r["hit"] for r in s)
        print(f"  {y}年度  母馬優先対象 {len(s):>3}頭  うち母馬優先枠が埋まった {h:>3}頭 = {h/len(s):.0%}")
    print(f"  実母馬 {len(by)}頭、うち2年以上登場 {sum(1 for v in by.values() if len(v)>=2)}頭、"
          f"3年以上 {sum(1 for v in by.values() if len(v)>=3)}頭")
    print(f"  連年ペア {len(pairs)}組")
    print()

    print("=" * 78)
    print("■ 1. 年をまたいだ遷移")
    print("=" * 78)
    a = b = c = d = 0
    rev, dec = [], []
    for dam, y, p, q in pairs:
        if p["hit"] and q["hit"]:
            a += 1
        elif p["hit"] and not q["hit"]:
            b += 1
            dec.append((dam, y, p, q))
        elif not p["hit"] and q["hit"]:
            c += 1
            rev.append((dam, y, p, q))
        else:
            d += 1
    print(f"{'':<14}{'翌年:埋まる':>12}{'翌年:余る':>12}")
    print(f"{'当年:埋まる':<14}{a:>12}{b:>12}")
    print(f"{'当年:余る':<14}{c:>12}{d:>12}")
    print()
    print(f"  継続率 P(埋 | 前年 埋) = {a}/{a+b} = {a/(a+b):.0%}")
    print(f"  **反転率 P(埋 | 前年 余) = {c}/{c+d} = {c/(c+d):.0%}**")
    print(f"  オッズ比 = {(a/max(b,1))/(c/max(d,1)):.1f}")
    print()
    print("  反転（余り → 埋まり）の全事例：")
    for dam, y, p, q in sorted(rev, key=lambda x: x[3]["age"]):
        print(f"    {dam:<16}母馬{q['age']:>2}歳  {y}年度 {p['rank']:>4} → {y+1}年度 {q['rank']:>4}"
              f"   枠外 {out_rank(p)}→{out_rank(q)}")
    print()
    print("  悪化（埋まり → 余り）の全事例：")
    for dam, y, p, q in sorted(dec, key=lambda x: x[3]["age"]):
        print(f"    {dam:<16}母馬{q['age']:>2}歳  {y}年度 {p['rank']:>4} → {y+1}年度 {q['rank']:>4}"
              f"   枠外 {out_rank(p)}→{out_rank(q)}")
    print()

    print("=" * 78)
    print("■ 1b. 反転・悪化の類型（枠内の変化 × 枠外の変化）")
    print("=" * 78)
    print("  枠外ランクが動いていなければ、産駒全体の人気は変わっていない。")
    print("  それでも枠内の結果が変わったなら、動いたのは母馬優先権者だけということ。")
    print()
    order = {c: i for i, c in enumerate("ABCDE")}

    def classify(p, q, direction):
        """枠外ランクが何段階動いたかで3分類する。

        2段階以上動いていれば産駒全体の人気が本当に変わったとみなす（連動型）。
        1段階なら誤差の範囲、0段階なら人気は動いていない。
        """
        dp = order[out_rank(q)] - order[out_rank(p)]   # 正 = 人気が下がった
        d = -dp if direction == "rev" else dp          # 正 = 枠内の変化と同じ向き
        if d >= 2:
            return "連動型（産駒の人気そのものが変わった）"
        if d == 1:
            return "やや連動（1段階）"
        return "母馬側だけが動いた（産駒の人気は不変）"

    for title, lst, direction in [("反転", rev, "rev"), ("悪化", dec, "dec")]:
        print(f"  【{title}】")
        for dam, y, p, q in sorted(lst, key=lambda x: x[3]["age"]):
            print(f"    {dam:<16}母馬{q['age']:>2}歳  枠外 {out_rank(p)}→{out_rank(q)}"
                  f"   {classify(p, q, direction)}")
        n_link = sum(1 for _, _, p, q in lst if classify(p, q, direction).startswith("連動型"))
        n_mid = sum(1 for _, _, p, q in lst if classify(p, q, direction).startswith("やや"))
        print(f"      → 連動型 {n_link}件 / やや連動 {n_mid}件 / 母馬側だけ {len(lst)-n_link-n_mid}件")
        print()
    print("  読みどころ：")
    print("    ・反転のうち4件（セレナズヴォイス・ブルーメンクローネ・エスティタート・ビットレート）は")
    print("      枠外がD→Dで動いていない。産駒全体の人気は据え置きなのに母馬優先枠だけが埋まった")
    print("      ＝優先権を持つ層だけが動いたケース。反転の半分近くがこの型。")
    print("    ・悪化側のリカビトス（枠外C→C）とエスティタート（D→D）は枠外が動かないまま枠内が余った。")
    print("      有資格者が実際に減ったと読める、退会のもっとも素直な現れ方。")
    print("    ・シンハライトは枠外A→Bで依然として最上位人気だが枠内は余った。")
    print("      母馬12歳で母馬優先の層が薄くなり、人気は一般層が支えている構図。")
    print("    ・エスティタートは 2021→2022 で悪化し、2022→2023 で反転している。")
    print("      同じ母馬が2年で逆向きに振れる＝産駒側のブレが小さくないことの実例。")
    print()

    print("=" * 78)
    print("■ 1c. しきい値のすぐ近くで往復している母馬")
    print("=" * 78)
    print("  同じ母馬が期間中に反転も悪化も両方経験していれば、その母馬の申込口数は")
    print("  200口のすぐ近くにあって、産駒側の小さなブレで行ったり来たりしている。")
    ups = {dm for dm, y, x, z in pairs if x["hit"] == 0 and z["hit"] == 1}
    dws = {dm for dm, y, x, z in pairs if x["hit"] == 1 and z["hit"] == 0}
    both = sorted(ups & dws)
    for dm in both:
        v = by[dm]
        traj = " → ".join(f"{y}:{'埋' if v[y]['hit'] else '余'}" for y in sorted(v))
        print(f"    {dm:<12}（{v[sorted(v)[0]]['foal_year']}年産） {traj}")
    nu = sum(1 for dm, y, x, z in pairs
             if x["hit"] == 0 and z["hit"] == 1 and dm in both)
    nd = sum(1 for dm, y, x, z in pairs
             if x["hit"] == 1 and z["hit"] == 0 and dm in both)
    print(f"    → {len(both)}頭。反転のうち{nu}件、悪化のうち{nd}件が"
          "この『往復組』から出ている。")
    print()
    print("  3年以上続けて産駒が募集された母馬の推移：")
    for dm, v in sorted(by.items(), key=lambda x: -len(x[1])):
        if len(v) < 3:
            continue
        ys = sorted(v)
        traj = " ".join(f"{y % 100:02d}:{'●' if v[y]['hit'] else '○'}" for y in ys)
        up = any(v[ys[i]]["hit"] == 0 and v[ys[i + 1]]["hit"] == 1
                 for i in range(len(ys) - 1))
        dn = any(v[ys[i]]["hit"] == 1 and v[ys[i + 1]]["hit"] == 0
                 for i in range(len(ys) - 1))
        mark = "   ← 途中で反転" if up else ("   ← 途中で脱落" if dn else "")
        print(f"    {dm:<12}({v[ys[0]]['foal_year']}) {traj}{mark}")
    print("      ●＝母馬優先枠が埋まった／○＝余った")
    print()

    print("=" * 78)
    print("■ 2. 母馬要因と産駒要因の分解（テトラコリック相関）")
    print("=" * 78)
    rho = tetrachoric(a, b, c, d)
    print("  「枠が埋まるか」の背後に連続量 log D があり")
    print("      log D =（母馬固有の水準）＋（その年の産駒固有のブレ）")
    print("  と分解できると考えると、同一母馬の2年の相関 ρ が母馬要因の分散比になる。")
    print()
    print(f"  推定 ρ = {rho:.2f}")
    print(f"    母馬要因（有資格者数・母系の格）… {rho:.0%}")
    print(f"    産駒要因（父・馬体・価格・性別・上の仔の成績）… {1-rho:.0%}")
    print()
    print(f"  → {rho:.0%}は母馬側で決まるが、残る{1-rho:.0%}はその年の仔次第。")
    print("     この産駒側のブレが、退会による右肩下がりを押し戻して反転を起こす。")
    print()

    print("=" * 78)
    print("■ 3. 反転に必要な『権利行使率 × 口数』の倍率")
    print("=" * 78)
    mu = fitted_mu()
    print(f"  D ~ 対数正規（σ={SIGMA_D}）、P(D≧{POOL}口)={P_EXCEED:.0%} → 中央値 {math.exp(mu):.0f}口")
    print(f"  E は退会で年 {CHURN:.1%} 減るので、その分も取り返す必要がある。")
    print()
    print(f"{'前年の位置（枠が余った馬の中で）':<28}{'前年のD':>10}{'必要な倍率':>12}")
    for q, lab in [(0.9, "上位10%（あと一歩）"), (0.75, "上位25%"), (0.5, "中央値"),
                   (0.25, "下位25%"), (0.1, "下位10%（かなり遠い）")]:
        dp = d_at_quantile(q, mu)
        print(f"{lab:<28}{dp:>9.0f}口{required_ratio(dp):>11.2f}倍")
    print()
    print("  → 閾値のすぐ下でも1.2〜1.3倍、中央値なら2倍強、不人気なら3〜5倍。")
    print("     『じわじわ増えて越える』のではなく、産駒側で何かが起きないと反転しない。")
    print()

    print("=" * 78)
    print("■ 4. 産駒の人気を揃えたときの、母馬の馬齢の効き方")
    print("=" * 78)
    print("  枠外ランク＝母馬優先権を持たない層からの人気")
    print("  （A/B/C＝最優先の段階で埋まる＝人気　D＝一般枠で抽選　E＝全口確定＝不人気）")
    print()
    g = defaultdict(lambda: [0, 0])
    mod = rows
    for r in mod:
        grp = "young" if r["age"] <= 10 else "old"
        g[(out_rank(r), grp)][0] += r["hit"]
        g[(out_rank(r), grp)][1] += 1
    print(f"{'枠外ランク':<12}{'母馬 5〜10歳':>18}{'母馬 11歳〜':>18}")
    for o in "ABCDE":
        cells = []
        for grp in ("young", "old"):
            h, t = g[(o, grp)]
            cells.append(f"{h}/{t} = {h/t:.0%}" if t else "  −")
        print(f"{o:<12}{cells[0]:>18}{cells[1]:>18}")
    ty = [sum(g[(o, "young")][i] for o in "ABCDE") for i in (0, 1)]
    to = [sum(g[(o, "old")][i] for o in "ABCDE") for i in (0, 1)]
    print(f"{'合計':<12}{f'{ty[0]}/{ty[1]} = {ty[0]/ty[1]:.0%}':>18}{f'{to[0]}/{to[1]} = {to[0]/to[1]:.0%}':>18}")
    print()
    dy, do = g[("D", "young")], g[("D", "old")]
    ry, ro = dy[0] / dy[1], do[0] / do[1]
    print(f"  → 産駒の人気が同じ『D』でも、母馬が10歳以下なら{ry:.0%}、"
          f"11歳以上なら{ro:.0%}。")
    print(f"     産駒の人気を揃えても母馬の馬齢が{ry/ro:.0f}倍効く。")
    print("  ※ 注意：母馬優先枠が余ると余剰が一般枠へ回る可能性があり、")
    print("     枠内と枠外のランクは完全に独立ではない。この表は目安として読む。")
    print()

    print("=" * 78)
    print("■ 5. 反転はどの年齢で起きるか")
    print("=" * 78)
    r2 = defaultdict(lambda: [0, 0])
    for dam, y, p, q in pairs:
        if p["hit"] == 0:
            grp = "7〜9歳" if q["age"] <= 9 else "10〜12歳" if q["age"] <= 12 else "13歳〜"
            r2[grp][0] += q["hit"]
            r2[grp][1] += 1
    print(f"{'翌年時点の母馬の馬齢':<22}{'前年に余ったペア':>16}{'うち反転':>10}{'反転率':>9}")
    for grp in ("7〜9歳", "10〜12歳", "13歳〜"):
        h, t = r2[grp]
        print(f"{grp:<22}{t:>15}件{h:>9}件{(h/t if t else 0):>9.0%}")
    print()
    print("  → 13歳以上の母馬からの反転はゼロ。反転の窓は12歳までで閉じる。")
    print()

    print("=" * 78)
    print("■ 5b. 前年のどこを見れば、翌年の反転を読めるか")
    print("=" * 78)
    print("  前年に枠が余った馬を、前年の『枠外ランク』（＝優先権を持たない層からの人気）で分ける。")
    print()
    left = [(dm, y, x, z) for dm, y, x, z in pairs if x["hit"] == 0]
    g2 = defaultdict(lambda: [0, 0])
    for dm, y, x, z in left:
        g2[out_rank(x)][0] += z["hit"]
        g2[out_rank(x)][1] += 1
    print(f"{'  前年の枠外ランク':<20}{'ペア':>8}{'翌年に反転':>12}{'反転率':>9}")
    lab = {"A": "A（最優先×2で抽選＝最上位人気）", "B": "B（最優先×1で抽選）",
           "C": "C（最優先で抽選）", "D": "D（一般枠で抽選）",
           "E": "E（全口確定＝不人気）"}
    for o in "ABCDE":
        h, t = g2[o]
        if t:
            print(f"  {lab[o]:<26}{t:>4}件{h:>8}件{h/t:>9.0%}")
    print()
    print("  もうひとつの切り口：翌年に産駒の一般人気が上がったか（枠外ランクが改善したか）")
    ORD = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}
    g3 = defaultdict(lambda: [0, 0])
    for dm, y, x, z in left:
        d_out = ORD[out_rank(z)] - ORD[out_rank(x)]
        k = "改善" if d_out < 0 else ("不変" if d_out == 0 else "悪化")
        g3[k][0] += z["hit"]
        g3[k][1] += 1
    for k in ("改善", "不変", "悪化"):
        h, t = g3[k]
        if t:
            print(f"    枠外が{k}した {t:>3}件中 {h:>2}件が反転 = {h/t:>4.0%}")
    print()
    print("  → 予想と逆。**前年の枠外ランクが悪い（＝その年の仔が不人気だった）馬ほど反転しやすい。**")
    print("     前年に枠外Ｅ（全口確定＝どこも抽選なし）だった19件のうち4件（21%）が翌年に反転、")
    print("     前年に枠外Ｄだった50件では10%、Ｃ以上では0/3。")
    print()
    print("     読み方：枠外Ｄ以上なのに枠内が余ったということは、")
    print("     『産駒には一般の需要があったのに母馬優先の層だけが薄かった』＝ E が本当に小さい。")
    print("     一方 枠外Ｅ は『その年の仔がたまたま外れだった』だけかもしれず、E の大小は分からない。")
    print("     つまり **枠外Ｅからの反転は平均への回帰**、**枠外Ｄからの余りは本物の枯渇**。")
    print()
    print("     実務的には、前年に枠外Ｄ以上で枠内が余った母馬は翌年も安全度が高く、")
    print("     前年にどこも抽選が起きなかった母馬（枠外Ｅ）のほうが、翌年に化ける余地を残している。")
    print("     枠外ランクが1段階以上改善した22件では反転率23%、不変42件では10%、悪化8件では0%。")
    print()

    print("=" * 78)
    print("■ 6. 上の仔の成績が効くタイミング（制度カレンダーの制約）")
    print("=" * 78)
    print("""
  第1次募集の締切は9月上旬。ある年の募集で参照できる「上の仔の成績」は
  前年産駒の2歳夏まで。

     2024年度募集（2023年産）… 2024年9月に出資確定
       → 2025年6〜8月にデビュー可能
       → 2025年度募集（2025年9月締切）の判断材料になるのは
          この夏にデビューできた早期組だけ

  つまり「上の仔が走ったから下の仔に人が集まる」経路は
  **早期デビュー組に限って1年で効き、それ以外は2年遅れで効く**。
  反転をこの経路で説明するなら、その母馬の1つ上の仔が
  6〜8月にデビューして好走しているはず——という検証可能な予測が立つ。
""")


if __name__ == "__main__":
    main()

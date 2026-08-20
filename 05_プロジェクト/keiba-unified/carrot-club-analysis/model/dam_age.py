#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
母馬の馬齢と「母馬優先枠で抽選が発生したか」の関係を調べる。

仮説
----
母馬優先枠（200口）が埋まるのは有資格者が多い馬。
有資格者は E = S × (1-退会率)^t で、t（母馬の募集から産駒の募集までの年数）が
短いほど多い。t は母馬の馬齢とほぼ 1:1 で対応する（t ＝ 馬齢 − 1）。
→ **若い母馬ほど母馬優先枠が埋まりやすい**はず。

データ
------
`data/dam_age_rank.csv`
  2024年度・2025年度 第1次募集の母馬優先対象馬 112頭について
    ・クラブ公表の抽選ランク（数字＝母馬優先枠がどの段階で埋まったか）
    ・母馬の生年（一口馬主DBのキャロット所属馬一覧を年産別に突き合わせて特定）

  抽選ランクの数字が 5 なら母馬優先枠は余った（＝申込 < 200口）、
  1〜4 なら母馬優先枠が埋まって母馬優先者どうしの抽選になった（＝申込 ≧ 200口）。

使い方
------
  python3 dam_age.py
"""

from __future__ import annotations

import csv
import math
import os
from collections import defaultdict

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "dam_age_rank.csv")


def load() -> list[dict]:
    rows = []
    with open(DATA, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({
                "season": int(r["募集年度"]),
                "dam": r["母馬名"],
                "foal_year": int(r["母馬の生年"]),
                "age": int(r["母馬の馬齢"]),
                "t": int(r["経過年数t"]),
                "rank": r["抽選ランク"],
                "hit": int(r["母馬優先枠で抽選"]),
            })
    return rows


# ---------------------------------------------------------------------------
# ロジスティック回帰（バッチ勾配法）
# ---------------------------------------------------------------------------

def fit_logistic(xs: list[float], ys: list[int],
                 iters: int = 300_000, lr: float = 0.02) -> tuple[float, float]:
    a = b = 0.0
    n = len(xs)
    for _ in range(iters):
        ga = gb = 0.0
        for x, y in zip(xs, ys):
            p = 1 / (1 + math.exp(-(a + b * x)))
            ga += y - p
            gb += (y - p) * x
        a += lr * ga / n
        b += lr * gb / n
    return a, b


# ---------------------------------------------------------------------------
# プロビット回帰（モデルとの対応がとりやすい）
#   母馬優先枠が埋まる ⇔ E×u×m ≧ 200
#   ⇔ log u ≧ c + t·λ      （λ = −log(1−退会率)）
#   log u ~ N(μ, σ) とすると P(t) = Φ((μ−c−tλ)/σ)
#   → プロビットの傾き = −λ/σ
# ---------------------------------------------------------------------------

def _phi(z: float) -> float:
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def fit_probit(xs: list[float], ys: list[int],
               iters: int = 300_000, lr: float = 0.02) -> tuple[float, float]:
    a = b = 0.0
    n = len(xs)
    for _ in range(iters):
        ga = gb = 0.0
        for x, y in zip(xs, ys):
            z = a + b * x
            p = min(max(_phi(z), 1e-9), 1 - 1e-9)
            dens = math.exp(-z * z / 2) / math.sqrt(2 * math.pi)
            w = (y - p) * dens / (p * (1 - p))
            ga += w
            gb += w * x
        a += lr * ga / n
        b += lr * gb / n
    return a, b


# ---------------------------------------------------------------------------
# 出力
# ---------------------------------------------------------------------------

def main() -> None:
    rows = load()

    print("=" * 74)
    print("■ 年度ごとの確認（母馬優先対象馬のうち、母馬優先枠で抽選になった割合）")
    print("=" * 74)
    for s in sorted({r["season"] for r in rows}):
        sub = [r for r in rows if r["season"] == s]
        h = sum(r["hit"] for r in sub)
        print(f"  {s}年度  対象 {len(sub):>3}頭 中 {h:>3}頭 = {h/len(sub):>4.0%}")
    h = sum(r["hit"] for r in rows)
    print(f"  合算    対象 {len(rows):>3}頭 中 {h:>3}頭 = {h/len(rows):>4.0%}")
    print()

    print("=" * 74)
    print("■ 母馬の馬齢別の分布")
    print("=" * 74)
    b = defaultdict(lambda: [0, 0])
    for r in rows:
        b[r["age"]][0] += r["hit"]
        b[r["age"]][1] += 1
    print(f"{'母馬の馬齢':>10}{'対象':>7}{'枠内抽選':>9}{'割合':>7}")
    for a in sorted(b):
        hit, tot = b[a]
        print(f"{a:>9}歳{tot:>6}頭{hit:>8}頭{hit/tot:>7.0%}  {'█'*round(hit/tot*22)}")
    print()

    print("=" * 74)
    print("■ 年齢帯でまとめる")
    print("=" * 74)
    for lo, hi, lab in [(5, 8, "5〜8歳（若い）"), (9, 10, "9〜10歳"),
                        (11, 12, "11〜12歳"), (13, 30, "13歳以上（高齢）")]:
        sub = [r for r in rows if lo <= r["age"] <= hi]
        if not sub:
            continue
        hit = sum(r["hit"] for r in sub)
        print(f"  {lab:<16}{len(sub):>4}頭中 {hit:>3}頭 = {hit/len(sub):>4.0%}")
    old = [r for r in rows if r["age"] >= 14]
    print(f"\n  ※ 14歳以上の母馬は {len(old)}頭すべてで母馬優先枠が余っている"
          f"（枠内抽選 {sum(r['hit'] for r in old)}頭）")
    print()

    print("=" * 74)
    print("■ 回帰")
    print("=" * 74)
    xs = [float(r["t"]) for r in rows]
    ys = [r["hit"] for r in rows]
    a, bb = fit_logistic(xs, ys)
    print(f"  ロジスティック  logit(P) = {a:.3f} + ({bb:.4f})×t")
    print(f"    経過年数1年あたりのオッズ比 = {math.exp(bb):.3f}"
          f"（オッズが年 {(1-math.exp(bb))*100:.0f}% ずつ低下）")
    print(f"{'  t（年）':>10}{'母馬の馬齢':>11}{'予測確率':>10}")
    for t in (5, 7, 9, 11, 13, 15, 18):
        p = 1 / (1 + math.exp(-(a + bb * t)))
        print(f"{t:>9}{t+1:>10}歳{p:>10.0%}")
    print()

    pa, pb = fit_probit(xs, ys)
    lam_over_sigma = -pb
    print(f"  プロビット  P = Φ({pa:.3f} + ({pb:.4f})×t)  →  λ/σ = {lam_over_sigma:.3f}")
    print()
    print("  λ = −log(1−退会率)、σ = 産駒ごとの権利行使率のばらつき（対数）")
    print("  観測された減衰は「退会」と「産次が進むほど行使率が下がる効果」の合計。")
    print(f"{'  σの仮定':>10}{'合計の年減衰率':>16}{'（うち退会3〜6%なら残りが行使率低下）':>0}")
    for sg in (0.20, 0.30, 0.40, 0.50):
        d = 1 - math.exp(-lam_over_sigma * sg)
        rest = d - 0.045
        print(f"{sg:>9.2f}{d:>15.1%}      行使率の低下分 ≒ 年 {max(rest,0):.1%}")
    print()

    print("=" * 74)
    print("■ 同一母馬の連年産駒（S が固定されるので比較が効く）")
    print("=" * 74)
    by = defaultdict(dict)
    for r in rows:
        by[r["dam"]][r["season"]] = r
    pairs = {k: v for k, v in by.items() if len(v) == 2}
    up = down = same = 0
    for k, v in sorted(pairs.items(), key=lambda x: -x[1][2024]["foal_year"]):
        p, q = v[2024], v[2025]
        if p["hit"] == 1 and q["hit"] == 0:
            down += 1
        elif p["hit"] == 0 and q["hit"] == 1:
            up += 1
        else:
            same += 1
    n1 = sum(v[2024]["hit"] for v in pairs.values())
    n2 = sum(v[2025]["hit"] for v in pairs.values())
    print(f"  2年連続で産駒が募集された母馬 {len(pairs)}頭")
    print(f"    枠内抽選になった数：2024年度 {n1}頭 → 2025年度 {n2}頭")
    print(f"    悪化（枠内→枠余り）{down}頭 / 改善（枠余り→枠内）{up}頭 / 変化なし {same}頭")
    print("  ※ 1年の経過に加えて産次も1つ進むので、退会だけの効果ではない。")


if __name__ == "__main__":
    main()

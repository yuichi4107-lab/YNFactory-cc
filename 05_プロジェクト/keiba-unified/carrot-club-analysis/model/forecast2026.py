#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026年度募集（2025年産）の母馬優先対象馬について、
母馬優先枠への申込口数 D と「枠が埋まって抽選になる確率」を予測する。

考え方
------
母馬優先枠への申込口数を対数正規で表す。

    log D(母馬, 年) = m(母馬) − λ·(年 − 2026) + ε      ε ~ N(0, σ_f)

  m(母馬) … その母馬の水準（有資格者数 E と母系の格で決まる。2026年基準）
  λ       … 1年あたりの減衰（退会 ＋ 産次が進むことによる権利行使率の低下）
  σ_f     … その年の産駒しだいのブレ（父・性別・馬体・価格・厩舎）

母馬優先枠が埋まる ⇔ D ≧ 200口（地方入厩予定馬は総口数100口なので 50口）。

m(母馬) を過去の観測から推定して2026年に外挿する。観測は2種類ある。

  (1) 中間発表の申込口数（2024・2025年度）… D の直接観測。強い情報
  (2) 抽選ランク（2021〜2025年度）      … D ≧ 200 か否かの打ち切り観測。弱い情報

観測が無い母馬（初仔など）は、母馬の馬齢だけから決まる事前分布をそのまま使う。

パラメータの出どころ
--------------------
  σ_tot = 1.0   母馬をまたいだ log D のばらつき（members.py と共通）
  ρ     = 0.73  同一母馬の連年相関（reversal.py のテトラコリック相関）
                 → σ_dam = σ_tot·√ρ = 0.854、σ_f = σ_tot·√(1−ρ) = 0.520
  λ     = 0.085 同一母馬の連年ペア103組の遷移表から。
                 前年に埋まった割合 30.1% → 翌年 27.2% のシフトを
                 プロビットで読むと λ/σ_tot = 0.085。
                 ※ 馬齢をまたいだ横断的な勾配（0.237）よりずっと小さい。
                    横断的な勾配には世代効果（昔の募集は安く1人あたり口数が多い）
                    が乗っているため。1年先の予測には within の 0.085 を使う。
  g     = 3.2   中間発表（締切24時間前）から最終値への伸び。interim.py の較正値
  σ_m   = 0.35  その伸びのばらつき（1.5〜3.8倍に開く）

  中間発表がある年も、抽選ランク（最終的に200口を超えたか）は独立した情報として
  併用する。中間で口数が多くても最終的に枠が余る馬があるため（マルシュロレーヌ）。

事前分布
--------
  dam_age.py のプロビット  P(埋まる) = Φ(1.909 − 0.2372·t)  を
  log D の水準に読み替える：  m_prior = log(200) + σ_tot·(1.909 − 0.2372·t)
  ばらつきは σ_dam。

使い方
------
  python3 forecast2026.py            # 予測一覧
  python3 forecast2026.py --lambda 0.237   # 減衰を横断的な勾配にして感度を見る
"""

from __future__ import annotations

import argparse
import csv
import math
import os
from collections import defaultdict

HERE = os.path.dirname(__file__)
D_LIST = os.path.join(HERE, "..", "data", "bosyu_2026.csv")
D_RANK = os.path.join(HERE, "..", "data", "dam_age_rank.csv")
D_INT = os.path.join(HERE, "..", "data", "carrot_interim.csv")

SIGMA_TOT = 1.0
RHO = 0.73
SIGMA_DAM = SIGMA_TOT * math.sqrt(RHO)
SIGMA_F = SIGMA_TOT * math.sqrt(1 - RHO)
LAMBDA = 0.085
GROWTH = 3.2
SIGMA_M = 0.35
POOL_CHUO = 200
POOL_CHIHO = 50
YEAR = 2026

# dam_age.py のプロビット
PROBIT_A, PROBIT_B = 1.909, -0.2372


def w(s: str, n: int) -> str:
    """全角を2桁として数え、表示幅 n に右詰めパディングする。"""
    import unicodedata
    ln = sum(2 if unicodedata.east_asian_width(c) in "WFA" else 1 for c in str(s))
    return str(s) + " " * max(1, n - ln)


def Phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


# ---------------------------------------------------------------------------
# データ
# ---------------------------------------------------------------------------

def load():
    horses = []
    with open(D_LIST, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["母馬優先対象"] != "1":
                continue
            r["dam"] = r["母馬名"]
            r["age"] = int(r["母馬の馬齢"])
            r["t"] = int(r["経過年数t"])
            r["pool"] = POOL_CHIHO if r["入厩"] == "地方" else POOL_CHUO
            horses.append(r)

    ranks = defaultdict(list)
    with open(D_RANK, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            ranks[r["母馬名"]].append((int(r["募集年度"]), int(r["母馬優先枠で抽選"]),
                                       r["抽選ランク"]))

    inter = defaultdict(list)
    with open(D_INT, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["区分"] != "対象":
                continue
            dam = r["馬名"].rsplit("の", 1)[0]
            inter[dam].append((int(r["募集年度"]),
                               int(r["母優かつ最優先"]) + int(r["母優一般"])))
    return horses, ranks, inter


# ---------------------------------------------------------------------------
# m(母馬) の事後分布 — グリッド上で数値的に
# ---------------------------------------------------------------------------

GRID = [3.0 + 0.02 * i for i in range(300)]      # log D の水準 2026年基準


def posterior(h, ranks, inter, lam: float, year: int = YEAR, upto: int | None = None):
    """母馬の水準 m の事後分布（GRID 上の重み）を返す。

    year … 基準年（m はこの年の水準）
    upto … この年以前の観測だけを使う（バックテスト用）。None なら全部使う。
    """
    t = h["t"] - (YEAR - year)
    prior_mu = math.log(h["pool"]) + SIGMA_TOT * (PROBIT_A + PROBIT_B * t)
    w = [math.exp(-((m - prior_mu) ** 2) / (2 * SIGMA_DAM ** 2)) for m in GRID]

    # 同じ年の「中間発表の口数」と「抽選ランク」は、どちらも同じ年の潜在量
    #   L_y = m − λ(y−基準年) + ε_y    ε_y ~ N(0, σ_f)
    # についての情報なので、年ごとに L_y を積分して1回の尤度にまとめる。
    # （別々の観測として掛けると σ_f を二重に数えて過信になる）
    obs_by_year = defaultdict(dict)
    for y, d in inter.get(h["dam"], []):
        if upto is None or y <= upto:
            obs_by_year[y]["D"] = d
    for y, hit, _ in ranks.get(h["dam"], []):
        if upto is None or y <= upto:
            obs_by_year[y]["hit"] = hit

    n_int = sum(1 for v in obs_by_year.values() if "D" in v)
    n_rank = sum(1 for v in obs_by_year.values() if "hit" in v)
    thr = math.log(h["pool"])
    LG = [thr - 3.0 + 0.06 * i for i in range(100)]      # L_y のグリッド

    for y, o in sorted(obs_by_year.items()):
        base_shift = lam * (y - year)
        # L_y ごとの観測尤度（m に依存しない部分）
        lik_L = []
        for L in LG:
            v = 1.0
            if "D" in o:
                z = (math.log(o["D"] * GROWTH) - L) / SIGMA_M
                v *= math.exp(-z * z / 2)
            if "hit" in o:
                v *= 1.0 if (L >= thr) == bool(o["hit"]) else 0.0
            lik_L.append(v)
        for i, m in enumerate(GRID):
            mu = m - base_shift
            tot = 0.0
            for L, v in zip(LG, lik_L):
                if v:
                    z = (L - mu) / SIGMA_F
                    tot += v * math.exp(-z * z / 2)
            w[i] *= max(tot, 1e-300)

    s = sum(w)
    w = [x / s for x in w]
    mean = sum(m * x for m, x in zip(GRID, w))
    var = sum((m - mean) ** 2 * x for m, x in zip(GRID, w))
    return mean, math.sqrt(var), n_int, n_rank


def predict(h, ranks, inter, lam: float, year: int = YEAR, upto=None):
    mu, sd, n_int, n_rank = posterior(h, ranks, inter, lam, year, upto)
    sd_pred = math.sqrt(sd ** 2 + SIGMA_F ** 2)
    p_fill = 1 - Phi((math.log(h["pool"]) - mu) / sd_pred)
    return {
        "dam": h["dam"], "age": h["age"], "t": h["t"], "pool": h["pool"],
        "sire": h["父"], "sex": h["性別"], "price": h["募集総額_万円"],
        "stable": h["厩舎"], "east": h["入厩"],
        "mu": mu, "sd": sd_pred, "D": math.exp(mu),
        "lo": math.exp(mu - 1.28 * sd_pred), "hi": math.exp(mu + 1.28 * sd_pred),
        "p": p_fill, "n_int": n_int, "n_rank": n_rank,
    }


# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lambda", dest="lam", type=float, default=LAMBDA)
    a = ap.parse_args()
    lam = a.lam

    horses, ranks, inter = load()
    res = [predict(h, ranks, inter, lam) for h in horses]
    res.sort(key=lambda r: -r["p"])

    print("=" * 96)
    print(f"■ 2026年度募集（2025年産）母馬優先枠への申込口数の予測   λ={lam:.3f}")
    print("=" * 96)
    print(f"  対象 {len(res)}頭（うち地方入厩予定 {sum(1 for r in res if r['pool']==POOL_CHIHO)}頭）")
    print(f"  観測の内訳：中間発表の口数あり {sum(1 for r in res if r['n_int'])}頭 / "
          f"抽選ランクのみ {sum(1 for r in res if not r['n_int'] and r['n_rank'])}頭 / "
          f"観測なし（馬齢だけ）{sum(1 for r in res if not r['n_int'] and not r['n_rank'])}頭")
    print()
    print(w("母馬", 16) + w("馬齢", 6) + w("父", 15) + w("性", 4)
          + w("総額", 8) + w("予測D", 9) + w("8割の幅", 16)
          + w("埋まる確率", 12) + "  根拠")
    print("-" * 96)
    for r in res:
        src = (f"中間{r['n_int']}年") if r["n_int"] else (
            (f"ランク{r['n_rank']}年") if r["n_rank"] else "馬齢のみ")
        chiho = "(地方50口)" if r["pool"] == POOL_CHIHO else ""
        band = f"{r['lo']:.0f}〜{r['hi']:.0f}口"
        print(w(r["dam"], 16) + w(f"{r['age']}歳", 6) + w(r["sire"][:11], 15)
              + w("牡" if r["sex"] == "牡馬" else "牝", 4)
              + w(r["price"], 8) + w(f"{r['D']:.0f}口", 9) + w(band, 16)
              + w(f"{r['p']:.0%}", 8) + ("★  " if r["p"] >= 0.5 else "   ")
              + src + chiho)
    print("-" * 96)
    outp = os.path.join(HERE, "..", "data", "forecast_2026.csv")
    with open(outp, "w", encoding="utf-8", newline="") as f:
        cw = csv.writer(f)
        cw.writerow(["母馬名", "母馬の馬齢", "経過年数t", "入厩", "父", "性別",
                     "募集総額_万円", "厩舎", "枠の口数", "予測D_口",
                     "予測D_下位10%", "予測D_上位10%", "枠が埋まる確率",
                     "中間発表の観測年数", "抽選ランクの観測年数"])
        for r in res:
            cw.writerow([r["dam"], r["age"], r["t"], r["east"], r["sire"],
                         r["sex"], r["price"], r["stable"], r["pool"],
                         f"{r['D']:.0f}", f"{r['lo']:.0f}", f"{r['hi']:.0f}",
                         f"{r['p']:.3f}", r["n_int"], r["n_rank"]])
    exp = sum(r["p"] for r in res)
    print(f"  枠が埋まる（母馬優先者どうしの抽選になる）と見込まれる頭数 "
          f"= {exp:.1f}頭 / {len(res)}頭 = {exp/len(res):.0%}")
    print(f"  実測の推移：2021年度40% → 2022年度39% → 2023年度24% → "
          f"2024年度34% → 2025年度34%")
    print()
    print(f"  確率50%以上 {sum(1 for r in res if r['p']>=.5)}頭 / "
          f"25〜50% {sum(1 for r in res if .25<=r['p']<.5)}頭 / "
          f"25%未満 {sum(1 for r in res if r['p']<.25)}頭")
    print()
    # 頭数の不確実性：個々の独立分散 ＋ 年ごとの共通ショック
    v_ind = sum(r["p"] * (1 - r["p"]) for r in res)
    YEAR_SHOCK = 0.06                      # 実測の年ごとブレ（24〜40%）から
    v_yr = (YEAR_SHOCK * len(res)) ** 2
    sd = math.sqrt(v_ind + v_yr)
    print(f"  頭数の不確実性： 個々のばらつき √{v_ind:.1f} = ±{math.sqrt(v_ind):.1f}頭")
    print(f"                  年ごとの共通ショック（実測24〜40%の幅）= ±{math.sqrt(v_yr):.1f}頭")
    print(f"  → 8割の幅で **{exp-1.28*sd:.0f}〜{exp+1.28*sd:.0f}頭**"
          f"（{(exp-1.28*sd)/len(res):.0%}〜{(exp+1.28*sd)/len(res):.0%}）")
    print()

    print("=" * 96)
    print("■ 母馬の馬齢帯ごと")
    print("=" * 96)
    for lo, hi, lab in [(5, 8, "5〜8歳"), (9, 10, "9〜10歳"),
                        (11, 12, "11〜12歳"), (13, 99, "13歳以上")]:
        s = [r for r in res if lo <= r["age"] <= hi]
        if not s:
            continue
        print(f"  {lab:<12}{len(s):>3}頭   予測Dの中央値 "
              f"{sorted(r['D'] for r in s)[len(s)//2]:>5.0f}口   "
              f"埋まる期待頭数 {sum(r['p'] for r in s):>4.1f}頭 "
              f"= {sum(r['p'] for r in s)/len(s):>4.0%}")
    print()

    print("=" * 96)
    print("■ なぜ例年より高めに出るのか — 母馬の顔ぶれの違い")
    print("=" * 96)
    hist_rows = []
    with open(D_RANK, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            hist_rows.append((int(r["募集年度"]), int(r["母馬の馬齢"]),
                              int(r["母馬優先枠で抽選"])))
    print(f"{w('募集年度', 12)}{w('対象', 8)}{w('母馬の馬齢の中央値', 22)}"
          f"{w('5〜10歳の割合', 16)}{w('枠が埋まった割合', 0)}")
    for y in (2021, 2022, 2023, 2024, 2025):
        sub = [x for x in hist_rows if x[0] == y]
        ages = sorted(x[1] for x in sub)
        yng = sum(1 for x in sub if x[1] <= 10) / len(sub)
        print(f"{w(f'{y}年度', 12)}{w(f'{len(sub)}頭', 8)}"
              f"{w(f'{ages[len(ages)//2]}歳', 22)}{w(f'{yng:.0%}', 16)}"
              f"{sum(x[2] for x in sub)/len(sub):.0%}")
    ages = sorted(r["age"] for r in res)
    yng = sum(1 for r in res if r["age"] <= 10) / len(res)
    print(f"{w('2026年度', 12)}{w(f'{len(res)}頭', 8)}"
          f"{w(f'{ages[len(ages)//2]}歳', 22)}{w(f'{yng:.0%}', 16)}"
          f"（予測 {exp/len(res):.0%}）")
    print()
    rep = sum(1 for r in res if r["n_int"] or r["n_rank"])
    strong = sum(1 for r in res if r["n_rank"] >= 2)
    print(f"  2026年度の特徴：57頭中 {rep}頭（{rep/len(res):.0%}）が過去5年にも産駒を出している"
          f"常連の母馬で、うち {strong}頭は2年以上の実績がある。")
    print("  過去に枠を埋めた実績のある母馬が多いぶん、平均予測が上がっている。")
    print("  ただし年ごとの共通ショック（2023年度は24%まで落ちた）は読めない。")
    print()

    print("=" * 96)
    print("■ バックテスト：同じ手順で過去の年を当てにいく")
    print("=" * 96)
    print("  その年より前の観測だけを使って予測し、実際の結果と突き合わせる。")
    print()
    hist = []
    with open(D_RANK, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            hist.append({"season": int(r["募集年度"]), "dam": r["母馬名"],
                         "age": int(r["母馬の馬齢"]), "t": int(r["経過年数t"]),
                         "hit": int(r["母馬優先枠で抽選"]), "pool": POOL_CHUO,
                         "父": "", "性別": "", "募集総額_万円": "", "厩舎": "",
                         "入厩": ""})
    print(f"{w('対象年', 10)}{w('頭数', 8)}{w('予測の平均', 12)}"
          f"{w('実際', 8)}{w('AUC', 8)}{w('ブライアスコア', 14)}")
    for ty in (2023, 2024, 2025):
        sub = [x for x in hist if x["season"] == ty]
        # その母馬の t は ty 時点のもの。基準年を ty にして予測する
        pr = []
        for x in sub:
            hh = dict(x)
            hh["t"] = x["t"] + (YEAR - ty)     # posterior 側で year 補正するため
            pr.append(predict(hh, ranks, inter, lam, year=ty, upto=ty - 1)["p"])
        act = [x["hit"] for x in sub]
        n = len(sub)
        pos = [p for p, a in zip(pr, act) if a]
        neg = [p for p, a in zip(pr, act) if not a]
        auc = (sum((p > q) + 0.5 * (p == q) for p in pos for q in neg)
               / (len(pos) * len(neg))) if pos and neg else float("nan")
        brier = sum((p - a) ** 2 for p, a in zip(pr, act)) / n
        print(f"{w(f'{ty}年度', 10)}{w(f'{n}頭', 8)}"
              f"{w(f'{sum(pr)/n:.0%}', 12)}{w(f'{sum(act)/n:.0%}', 8)}"
              f"{w(f'{auc:.2f}', 8)}{w(f'{brier:.3f}', 14)}")
    print()
    print("  AUC 0.5＝でたらめ、1.0＝完全。ブライアスコアは小さいほど良い")
    print("  （全頭に 0.34 と答えるだけのモデルなら 0.34×0.66 = 0.224）")
    print()

    print("=" * 96)
    print("■ 感度：減衰 λ を変えるとどうなるか")
    print("=" * 96)
    print(f"{'  λ':<10}{'意味':<34}{'埋まる期待頭数':>16}{'割合':>8}")
    for l, lab in [(0.000, "減衰なし（退会も行使率低下も無し）"),
                   (0.046, "退会4.5%だけ"),
                   (0.085, "連年ペアの遷移から（既定）"),
                   (0.150, "中間"),
                   (0.237, "馬齢の横断的勾配をそのまま使う")]:
        rr = [predict(h, ranks, inter, l) for h in horses]
        e = sum(x["p"] for x in rr)
        print(f"  {l:<8.3f}{lab:<34}{e:>13.1f}頭{e/len(rr):>8.0%}")
    print()
    print("  → 減衰の置き方で期待頭数は数頭しか動かない。")
    print("     個々の母馬の過去の観測のほうが効いている。")


if __name__ == "__main__":
    main()

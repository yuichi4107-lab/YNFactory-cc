#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
キャロットクラブ 母馬出資者優先制度 有資格者数 推計モデル

推計式
------
    E(母馬, 産駒募集年) = S(母馬) × R(t) × P_active

    S       : 母馬に出資した「実人数」（400口を何人で分けたか）
    R(t)    : 母馬募集年から t 年後の会員残存率（退会していない確率）
    P_active: その年に母馬優先権を行使できる状態にある率（遅延歴による失権を除く）
    t       : 産駒の募集年度 － 母馬の募集年度

S の推計
--------
    S = 400 / m̄     （m̄ = 出資者1人あたりの平均口数）

    m̄ は「1頭あたりに投じる予算 B」と「1口価格 p」から決まると考える。
        k = clip(round(B / p), 1, cap)
        m̄ = E[k]
    B は会員ごとにばらつくので対数正規分布とする。
    cap は出資可能口数の制限（抽選発生馬は5口、非抽選馬はもっと大きい）。

    馬代金が高騰する一方で会員の予算はそこまで伸びないため、
    p が上がると m̄ が下がり、S（＝実人数）は増える。
    → 新しい母馬ほど有資格者の「母数」は多い。

使い方
------
    python3 estimate.py              # 代表ケースの一覧表を出力
    python3 estimate.py --scan       # 母馬募集年度 × 人気度 のマトリクス
"""

from __future__ import annotations

import argparse
import math
import random
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# 1. 制度上の定数（キャロットクラブ公式Q&A・約款より）
# ---------------------------------------------------------------------------

UNITS_CENTRAL = 400        # 中央入厩予定馬の総口数
UNITS_LOCAL = 100          # 地方入厩予定馬の総口数
DAM_PRIORITY_UNITS = 200   # 母馬優先枠（400口の半分）
CAP_WHEN_LOTTERY = 5       # 募集口数を超える申込があった場合の減口上限
CAP_MAX = 199              # 抽選が発生しない場合の1人あたり上限（募集口数の半数未満）

# ---------------------------------------------------------------------------
# 2. キャロットの1口価格の推移（万円）
#    2023〜2025年産は募集馬リストから実測。それ以前は全中央クラブ平均の
#    伸び率（2013年産2324万円→2022年産3118万円＝年率3.3%）で後方推計。
# ---------------------------------------------------------------------------

MEASURED_UNIT_PRICE = {   # キー＝年産（募集年度 = 年産 + 1）
    2023: 10.75,
    2024: 12.34,
    2025: 13.22,
}
BACKCAST_RATE = 0.033     # 2022年産以前に適用する年率


def unit_price(foal_year: int) -> float:
    """年産から中央募集馬の1口平均価格（万円）を返す。"""
    if foal_year in MEASURED_UNIT_PRICE:
        return MEASURED_UNIT_PRICE[foal_year]
    if foal_year < 2023:
        return MEASURED_UNIT_PRICE[2023] / ((1 + BACKCAST_RATE) ** (2023 - foal_year))
    # 2026年産以降は直近2年の伸び率を延長
    growth = MEASURED_UNIT_PRICE[2025] / MEASURED_UNIT_PRICE[2023]
    per_year = growth ** 0.5
    return MEASURED_UNIT_PRICE[2025] * (per_year ** (foal_year - 2025))


def price_by_season(season: int) -> float:
    """募集年度から1口平均価格（万円）を返す。募集年度は1歳時＝年産+1。"""
    return unit_price(season - 1)


# ---------------------------------------------------------------------------
# 3. 人気度カテゴリ → 1人あたり口数の上限
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Popularity:
    key: str
    label: str
    cap: int          # 1人あたり口数の上限
    budget_mult: float  # 申込者層の予算の中央値倍率
    sigma_mult: float   # 申込者層の予算のばらつき倍率


# 人気馬ほど「1人5口まで」の減口ルールが効き、かつ薄く広く多人数が集まる
# → 平均口数 m̄ が小さく、出資者実人数 S は大きくなる。
# 逆に売れ残る馬は、口数制限がかからないまま少数の大口出資者が吸収する
# → m̄ が大きく、S は小さくなる。
POPULARITY = {
    "lottery": Popularity(
        "lottery", "1次で抽選（人気馬）", CAP_WHEN_LOTTERY, 1.00, 1.00),
    "full1st": Popularity(
        "full1st", "1次で満口（抽選なし）", 12, 1.15, 1.15),
    "full15th": Popularity(
        "full15th", "1.5次・2次で満口", 30, 1.45, 1.40),
    "leftover": Popularity(
        "leftover", "通常募集まで残った", CAP_MAX, 2.00, 1.70),
}

# ---------------------------------------------------------------------------
# 4. パラメータ（シナリオ）
# ---------------------------------------------------------------------------

@dataclass
class Params:
    # 1頭あたり投下予算の中央値（万円, 2025年度時点）
    budget_median_2025: float = 20.0
    # 予算の年成長率（馬代金の伸びより低いと仮定）
    budget_growth: float = 0.03
    # 予算のばらつき（対数正規のσ）
    budget_sigma: float = 0.62
    # 年間退会率
    churn: float = 0.07
    # 遅延歴などで母馬優先権を行使できない会員の割合
    inactive_rate: float = 0.03
    n_sim: int = 200_000
    seed: int = 20260820


def budget_median(season: int, p: Params) -> float:
    return p.budget_median_2025 * ((1 + p.budget_growth) ** (season - 2025))


# ---------------------------------------------------------------------------
# 5. 平均口数 m̄ と 出資者実人数 S
# ---------------------------------------------------------------------------

def mean_units(season: int, popularity: str, p: Params) -> float:
    """募集年度と人気度から、出資者1人あたりの平均口数 m̄ を求める。"""
    pop = POPULARITY[popularity]
    price = price_by_season(season)
    med = budget_median(season, p) * pop.budget_mult
    mu = math.log(med)
    sigma = p.budget_sigma * pop.sigma_mult

    rng = random.Random(p.seed + season)
    total = 0
    for _ in range(p.n_sim):
        b = math.exp(rng.gauss(mu, sigma))
        k = int(b / price + 0.5)
        total += min(max(k, 1), pop.cap)
    return total / p.n_sim


def n_investors(season: int, popularity: str, p: Params,
                units: int = UNITS_CENTRAL) -> float:
    """母馬の出資者実人数 S。"""
    return units / mean_units(season, popularity, p)


# ---------------------------------------------------------------------------
# 6. 残存率と有資格者数
# ---------------------------------------------------------------------------

def survival(t: int, churn: float) -> float:
    return (1 - churn) ** t


def eligible(dam_season: int, foal_season: int, popularity: str,
             p: Params, units: int = UNITS_CENTRAL) -> float:
    """母馬優先の有資格者数 E。"""
    s = n_investors(dam_season, popularity, p, units)
    t = foal_season - dam_season
    return s * survival(t, p.churn) * (1 - p.inactive_rate)


def eligible_range(dam_season: int, foal_season: int, popularity: str,
                   units: int = UNITS_CENTRAL) -> tuple[float, float, float]:
    """低位・中位・高位シナリオの有資格者数を返す。"""
    low = Params(churn=0.10, budget_median_2025=25.0, budget_growth=0.045)
    mid = Params()
    high = Params(churn=0.05, budget_median_2025=16.0, budget_growth=0.015)
    return (
        eligible(dam_season, foal_season, popularity, low, units),
        eligible(dam_season, foal_season, popularity, mid, units),
        eligible(dam_season, foal_season, popularity, high, units),
    )


# ---------------------------------------------------------------------------
# 7. 母馬優先枠（200口）が埋まるかの判定
# ---------------------------------------------------------------------------

def dam_priority_demand(e_mid: float, foal_season: int,
                        exercise_rate: float, p: Params | None = None) -> float:
    """有資格者のうち exercise_rate が権利を行使したときの申込口数。"""
    p = p or Params()
    # 産駒に申し込む側の1人あたり口数は、産駒の1口価格で決まる（抽選が起きる前提で5口上限）
    m = mean_units(foal_season, "lottery", p)
    return e_mid * exercise_rate * m


# ---------------------------------------------------------------------------
# 8. 出力
# ---------------------------------------------------------------------------

def fmt(x: float) -> str:
    return f"{x:,.0f}"


def print_price_table() -> None:
    print("■ キャロット中央募集馬の1口平均価格の推移（万円 / ★=実測、他は後方推計）")
    print(f"{'年産':>6} {'募集年度':>8} {'1口価格':>9} {'総額(400口)':>12}")
    for y in range(2012, 2027):
        star = "★" if y in MEASURED_UNIT_PRICE else " "
        pr = unit_price(y)
        print(f"{y:>6} {y+1:>8} {pr:>8.2f}{star} {fmt(pr*400):>11}万円")
    print()


def print_investor_table() -> None:
    p = Params()
    print("■ 母馬1頭（中央400口）の出資者実人数 S の推計")
    print(f"{'募集年度':>8} {'1口価格':>8}", end="")
    for k in POPULARITY:
        print(f" | {POPULARITY[k].label:>22}", end="")
    print()
    for season in (2013, 2016, 2019, 2022, 2025, 2026):
        print(f"{season:>8} {price_by_season(season):>7.2f}万", end="")
        for k in POPULARITY:
            m = mean_units(season, k, p)
            s = UNITS_CENTRAL / m
            print(f" | {fmt(s):>8}人(平均{m:>4.1f}口)", end="")
        print()
    print()


def print_eligible_table() -> None:
    print("■ 母馬優先 有資格者数 E の推計（中央400口の母馬）")
    print("   低位＝退会率10%/予算高め、中位＝退会率7%、高位＝退会率5%/予算低め")
    print()
    rows = [
        ("2016年度募集の人気牝馬", 2016, "lottery"),
        ("2016年度募集の並の牝馬", 2016, "full1st"),
        ("2016年度募集の不人気牝馬", 2016, "leftover"),
        ("2019年度募集の人気牝馬", 2019, "lottery"),
        ("2019年度募集の並の牝馬", 2019, "full1st"),
        ("2019年度募集の不人気牝馬", 2019, "leftover"),
        ("2022年度募集の人気牝馬", 2022, "lottery"),
        ("2022年度募集の並の牝馬", 2022, "full1st"),
    ]
    foal_season = 2026
    print(f"{'ケース':<26} {'S(実人数)':>10} {'経過':>5} "
          f"{'低位':>7} {'中位':>7} {'高位':>7}")
    for label, dam_season, pop in rows:
        s = n_investors(dam_season, pop, Params())
        lo, mid, hi = eligible_range(dam_season, foal_season, pop)
        t = foal_season - dam_season
        print(f"{label:<26} {fmt(s):>9}人 {t:>4}年 "
              f"{fmt(lo):>6}人 {fmt(mid):>6}人 {fmt(hi):>6}人")
    print()


def print_quota_table() -> None:
    print("■ 母馬優先枠（200口）が埋まるか＝母馬優先どうしの抽選になるか")
    print("   行使率＝有資格者のうち実際にその産駒に申し込む人の割合")
    print()
    foal_season = 2026
    m = mean_units(foal_season, "lottery", Params())
    print(f"   産駒側の1人あたり平均申込口数 m = {m:.2f}口"
          f"（1口{price_by_season(foal_season):.2f}万円・5口上限）")
    print()
    header = f"{'母馬の募集年度/人気':<28}{'E(中位)':>9}"
    for r in (0.2, 0.35, 0.5, 0.7, 1.0):
        header += f"{'行使'+str(int(r*100))+'%':>10}"
    print(header)
    for dam_season, pop, label in [
        (2016, "lottery", "2016年度・人気"),
        (2016, "full1st", "2016年度・並"),
        (2019, "lottery", "2019年度・人気"),
        (2019, "full1st", "2019年度・並"),
        (2022, "lottery", "2022年度・人気"),
        (2022, "full1st", "2022年度・並"),
    ]:
        _, e_mid, _ = eligible_range(dam_season, foal_season, pop)
        line = f"{label:<28}{fmt(e_mid):>8}人"
        for r in (0.2, 0.35, 0.5, 0.7, 1.0):
            d = e_mid * r * m
            mark = "★" if d >= DAM_PRIORITY_UNITS else " "
            line += f"{fmt(d)+'口'+mark:>10}"
        print(line)
    print("   ★＝200口超＝母馬優先者どうしで抽選（＝優先権を使っても落ちうる）")
    print()


def print_scan() -> None:
    print("■ 母馬募集年度 × 人気度 → 2026年度募集での有資格者数（中位シナリオ）")
    print(f"{'母馬募集年度':>12}", end="")
    for k in POPULARITY:
        print(f"{POPULARITY[k].key:>12}", end="")
    print()
    for season in range(2012, 2024):
        print(f"{season:>12}", end="")
        for k in POPULARITY:
            _, mid, _ = eligible_range(season, 2026, k)
            print(f"{fmt(mid)+'人':>12}", end="")
        print()
    print()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", action="store_true")
    args = ap.parse_args()

    print_price_table()
    print_investor_table()
    print_eligible_table()
    print_quota_table()
    if args.scan:
        print_scan()


if __name__ == "__main__":
    main()

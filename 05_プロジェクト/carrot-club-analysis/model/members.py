#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
キャロットクラブ 会員数・退会率の推計

考え方
------
【会員数】
  「最優先希望枠は必ず1頭だけ選ばなければならない」というルールを使う。
  → 第1次募集に参加した人数 N ＝ 全馬の最優先申込「人数」の合計
  → 全馬の最優先申込「口数」の合計 Σ = N × m1（m1 = 最優先馬への平均申込口数）
  → N = Σ / m1

  Σ は直接は公表されないが、クラブが毎年公表する「抽選ランク」から復元できる。
  ランクは各馬について「どの段階で枠が埋まったか」を示すので、
  「最優先申込がプール口数を超えたか否か」という打ち切り観測になる。
  この打ち切り率から対数正規分布を当てはめて期待値を出す。

【退会率】
  キャンセル募集の口数は、クラブが「すべて出資者の退会によって生じたもの」と明記している。
  ただし対象は最新世代の馬だけなので、
  「現役の出資馬を持ったまま辞めた人」しか捕捉できない（＝退会率の下限）。
  全馬引退後に静かに辞める人は口数を残さないので観測できない。
  そこで下限（キャンセル募集）と上限（定常状態モデル）の両側から挟む。

使い方
------
  python3 members.py
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# 1. 抽選ランクの実データ（2025年度 第1次募集・92頭）
#
#    ランク記号の意味（クラブ公表の説明文より）
#      数字  = ≪母馬優先枠≫（200口）がどの段階で埋まったか
#              1: 最優先×2 内で抽選 / 2: 最優先×1 内で抽選
#              3: 最優先×なし 内で抽選 / 4: 一般出資枠 内で抽選
#              5: 一般出資枠の全ての口数が出資確定（＝枠が余った）
#      英字  = ≪母馬優先枠外≫（母馬優先対象馬は200口、非対象馬は400口）
#              A: 最優先×2 内で抽選 / B: 最優先×1 内で抽選
#              C: 最優先×なし 内で抽選 / D: 一般出資枠 内で抽選
#              E: 一般出資枠で全口出資確定
# ---------------------------------------------------------------------------

RANK_2025_DAM_PRIORITY = {   # 母馬優先対象馬
    "3B": 1, "4A": 1, "4B": 1, "4C": 5, "4D": 10,
    "5A": 2, "5B": 2, "5C": 6, "5D": 16, "5E": 9,
}
RANK_2025_NO_DAM = {          # 母馬優先非対象馬
    "B": 2, "C": 5, "D": 17, "E": 14,
}

POOL_FULL = 400      # 母馬優先非対象馬のプール
POOL_HALF = 200      # 母馬優先対象馬の「母馬優先枠」「枠外」それぞれのプール


# ---------------------------------------------------------------------------
# 2. 打ち切り観測から対数正規分布を当てはめる
# ---------------------------------------------------------------------------

def _inv_norm(p: float) -> float:
    """標準正規分布の分位点（Acklam の近似）。"""
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    pl, ph = 0.02425, 1 - 0.02425
    if p < pl:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > ph:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
                ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
           (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def lognormal_from_censoring(threshold: float, p_exceed: float,
                             sigma: float) -> tuple[float, float]:
    """「閾値を超えた割合」から対数正規分布の中央値と期待値を返す。

    X ~ LogNormal(mu, sigma) で P(X >= threshold) = p_exceed となる mu を解く。
    """
    z = _inv_norm(1 - p_exceed)
    mu = math.log(threshold) - z * sigma
    median = math.exp(mu)
    mean = math.exp(mu + sigma ** 2 / 2)
    return median, mean


# ---------------------------------------------------------------------------
# 3. ランクから「最優先申込がプールを超えた割合」を数える
# ---------------------------------------------------------------------------

@dataclass
class RankSummary:
    n_dam: int              # 母馬優先対象馬の頭数
    n_nodam: int            # 非対象馬の頭数
    p_nodam_pri: float      # 非対象馬で最優先申込 >= 400口 の割合
    p_dam_out_pri: float    # 対象馬の枠外で最優先申込 >= 200口 の割合
    p_dam_in_full: float    # 対象馬の母馬優先枠が埋まった割合（>= 200口）


def summarize(dam: dict[str, int], nodam: dict[str, int]) -> RankSummary:
    n_dam = sum(dam.values())
    n_nodam = sum(nodam.values())

    # 非対象馬：英字が A/B/C なら最優先の段階で400口に到達している
    nodam_pri = sum(v for k, v in nodam.items() if k in ("A", "B", "C"))

    # 対象馬・枠外：2文字目が A/B/C なら枠外の最優先で200口に到達
    dam_out_pri = sum(v for k, v in dam.items() if k[1] in ("A", "B", "C"))

    # 対象馬・母馬優先枠：1文字目が 5 以外なら枠内で抽選＝200口に到達
    dam_in_full = sum(v for k, v in dam.items() if k[0] != "5")

    return RankSummary(
        n_dam=n_dam,
        n_nodam=n_nodam,
        p_nodam_pri=nodam_pri / n_nodam,
        p_dam_out_pri=dam_out_pri / n_dam,
        p_dam_in_full=dam_in_full / n_dam,
    )


# ---------------------------------------------------------------------------
# 4. 会員数の推計
# ---------------------------------------------------------------------------

@dataclass
class MemberParams:
    sigma: float = 1.0           # 最優先申込口数のばらつき（対数正規のσ）
    m1: float = 2.5              # 最優先希望馬への1人あたり平均申込口数
    phi: float = 0.20            # 母馬優先枠の申込のうち「最優先も併用」した割合
    join_rate: float = 0.75      # 会員のうち第1次募集に参加する割合


def estimate_members(rs: RankSummary, p: MemberParams) -> dict:
    _, mean_nodam = lognormal_from_censoring(POOL_FULL, rs.p_nodam_pri, p.sigma)
    med_out, mean_out = lognormal_from_censoring(POOL_HALF, rs.p_dam_out_pri, p.sigma)
    med_in, mean_in = lognormal_from_censoring(POOL_HALF, rs.p_dam_in_full, p.sigma)

    # 全馬の最優先申込口数の合計
    total_priority_units = (
        rs.n_nodam * mean_nodam
        + rs.n_dam * (mean_out + p.phi * mean_in)
    )
    n_applicants = total_priority_units / p.m1
    n_members = n_applicants / p.join_rate

    return {
        "mean_nodam": mean_nodam,
        "mean_out": mean_out,
        "median_in": med_in,
        "mean_in": mean_in,
        "total_priority_units": total_priority_units,
        "n_applicants": n_applicants,
        "n_members": n_members,
    }


# ---------------------------------------------------------------------------
# 5. キャンセル募集（＝退会）からの退会数の推計
#
#    クラブ公表の案内文：
#      「本募集におけるキャンセル口数は、すべて出資者の退会によって生じたものとなります」
# ---------------------------------------------------------------------------

@dataclass
class CancelRound:
    season: int        # 募集年度
    label: str
    horses: int
    units: int
    months_after: int  # 出資確定からの経過月数（概算）


CANCEL_DATA = [
    CancelRound(2024, "2024年度 第1回（2025/01）", 57, 129, 4),
    CancelRound(2025, "2025年度 第1回（2026/01）", 61, 106, 4),
    CancelRound(2025, "2025年度 第2回（2026/04）", 30, 61, 7),
]

# 世代あたりの総口数（中央88頭×400口 ＋ 地方4頭×100口）
UNITS_PER_SEASON = 88 * 400 + 4 * 100


def estimate_quit_from_cancel(units_per_person_per_season: float,
                              months: int = 7) -> dict:
    """最新世代のキャンセル口数から「現役馬を持ったまま辞めた人数」を出す。"""
    units = sum(c.units for c in CANCEL_DATA if c.season == 2025)
    people = units / units_per_person_per_season
    annualized = people * 12 / months
    return {
        "units": units,
        "months": months,
        "people": people,
        "annualized": annualized,
        "share_of_season_units": units / UNITS_PER_SEASON,
    }


# ---------------------------------------------------------------------------
# 6. 定常状態モデルからの退会率
#    設立からの年数と現在の会員数、年間新規入会数から退会率 d を逆算する。
#      N = A * (1 - (1-d)^T) / d
# ---------------------------------------------------------------------------

FOUNDED_YEAR = 1998


def members_after(years: int, new_per_year: float, churn: float) -> float:
    if churn <= 0:
        return new_per_year * years
    return new_per_year * (1 - (1 - churn) ** years) / churn


def solve_churn(target_members: float, years: int, new_per_year: float) -> float | None:
    """会員数と年間新規入会数から退会率を二分法で解く。"""
    lo, hi = 0.0005, 0.40
    if members_after(years, new_per_year, lo) < target_members:
        return None   # 新規が少なすぎてその会員数に到達しない
    if members_after(years, new_per_year, hi) > target_members:
        return None   # 退会率が大きくても会員数が多すぎる
    for _ in range(200):
        mid = (lo + hi) / 2
        if members_after(years, new_per_year, mid) > target_members:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ---------------------------------------------------------------------------
# 7. 母馬優先枠のデータから「退会率」と「権利行使率」を同時に見る
# ---------------------------------------------------------------------------

@dataclass
class ExerciseParams:
    s_dam: float = 175.0     # 母馬の出資者実人数（estimate.py の推計より）
    t_years: int = 8         # 母馬募集から産駒募集までの平均経過年数
    m_dam: float = 2.2       # 母馬優先で申し込むときの1人あたり口数
    inactive: float = 0.03   # 遅延歴などで権利を行使できない割合


def implied_exercise_rate(median_in_units: float, churn: float,
                          p: ExerciseParams) -> float:
    """観測された母馬優先枠の申込口数（中央値）と整合する権利行使率 u。"""
    e = p.s_dam * (1 - churn) ** p.t_years * (1 - p.inactive)
    return median_in_units / (e * p.m_dam)


def eligible_at(churn: float, p: ExerciseParams) -> float:
    return p.s_dam * (1 - churn) ** p.t_years * (1 - p.inactive)


# ---------------------------------------------------------------------------
# 8. 出力
# ---------------------------------------------------------------------------

def fmt(x: float) -> str:
    return f"{x:,.0f}"


def main() -> None:
    rs = summarize(RANK_2025_DAM_PRIORITY, RANK_2025_NO_DAM)

    print("=" * 78)
    print("■ STEP A  抽選ランクから「最優先申込がプールを超えた割合」を数える")
    print("=" * 78)
    print(f"  2025年度 第1次募集  母馬優先対象馬 {rs.n_dam}頭 / 非対象馬 {rs.n_nodam}頭"
          f" ＝ 計{rs.n_dam + rs.n_nodam}頭")
    print()
    print(f"  非対象馬（プール400口）  最優先だけで400口を超えた馬"
          f"  … {rs.p_nodam_pri:.1%}")
    print(f"  対象馬・枠外（200口）    最優先だけで200口を超えた馬"
          f"  … {rs.p_dam_out_pri:.1%}")
    print(f"  対象馬・母馬優先枠（200口）枠が埋まって抽選になった馬"
          f" … {rs.p_dam_in_full:.1%}")
    print()

    print("=" * 78)
    print("■ STEP B  最優先申込口数の分布を復元する（対数正規・打ち切り推定）")
    print("=" * 78)
    print(f"{'σ':>5} {'非対象馬の平均':>16} {'対象馬枠外の平均':>18} "
          f"{'母馬優先枠の中央値':>20} {'同・平均':>12}")
    for sg in (0.7, 1.0, 1.3):
        _, mn = lognormal_from_censoring(POOL_FULL, rs.p_nodam_pri, sg)
        _, mo = lognormal_from_censoring(POOL_HALF, rs.p_dam_out_pri, sg)
        mi_med, mi = lognormal_from_censoring(POOL_HALF, rs.p_dam_in_full, sg)
        print(f"{sg:>5.1f} {fmt(mn)+'口':>16} {fmt(mo)+'口':>18} "
              f"{fmt(mi_med)+'口':>20} {fmt(mi)+'口':>12}")
    print("  → σ を変えても平均はあまり動かない（打ち切り推定が効いている）")
    print()

    print("=" * 78)
    print("■ STEP C  会員数の推計")
    print("=" * 78)
    base = MemberParams()
    r = estimate_members(rs, base)
    print(f"  全馬の最優先申込口数の合計 Σ … 約 {fmt(r['total_priority_units'])}口")
    print()
    print("  N（第1次募集の参加人数）＝ Σ ÷ m1")
    print(f"{'m1（最優先馬への平均口数）':>26} {'参加人数 N':>12} "
          f"{'会員数(参加率75%)':>18} {'会員数(参加率85%)':>18}")
    for m1 in (2.0, 2.5, 3.0, 3.5):
        rr = estimate_members(rs, MemberParams(m1=m1))
        n = rr["n_applicants"]
        print(f"{m1:>24.1f}口 {fmt(n)+'人':>12} "
              f"{fmt(n/0.75)+'人':>18} {fmt(n/0.85)+'人':>18}")
    print()
    print("  検算：第1次募集で確定した口数は約32,000口。参加者1人あたりの当選口数は")
    for m1 in (2.0, 2.5, 3.0, 3.5):
        rr = estimate_members(rs, MemberParams(m1=m1))
        print(f"        m1={m1:.1f} → {32000/rr['n_applicants']:.1f}口/人"
              f"（1頭2口なら {32000/rr['n_applicants']/2:.1f}頭当選）")
    print()

    print("=" * 78)
    print("■ STEP D  キャンセル募集（＝退会）から退会数を測る")
    print("=" * 78)
    print("  クラブ公表：「本募集におけるキャンセル口数は、すべて出資者の退会によって"
          "生じたものとなります」")
    print()
    print(f"{'募集回':<28}{'頭数':>8}{'口数':>8}{'確定後':>8}")
    for c in CANCEL_DATA:
        print(f"{c.label:<28}{c.horses:>7}頭{c.units:>7}口{c.months_after:>6}ヶ月")
    print()
    for upp in (2.0, 3.2, 4.5):
        q = estimate_quit_from_cancel(upp)
        print(f"  退会者1人が最新世代に平均{upp:>4.1f}口持っていたとすると"
              f" → {fmt(q['people'])}人 / 7ヶ月 ＝ 年 {fmt(q['annualized'])}人")
    q = estimate_quit_from_cancel(3.2)
    print()
    print(f"  最新世代の総口数 {fmt(UNITS_PER_SEASON)}口 に対する"
          f"キャンセル口数の比率 … {q['share_of_season_units']:.2%}（7ヶ月）")
    print("  ※ これは「現役の出資馬を持ったまま辞めた人」しか捕捉していない。")
    print("     全馬引退後に静かに辞める人は口数を残さないので、これは退会率の下限。")
    print()

    print("=" * 78)
    print("■ STEP E  定常状態モデルで退会率を挟む（1998年設立・28年経過）")
    print("=" * 78)
    years = 2026 - FOUNDED_YEAR
    print(f"{'年間新規入会':>14}", end="")
    for target in (9000, 12000, 15000):
        print(f"{'会員'+fmt(target)+'人':>16}", end="")
    print()
    for a in (300, 500, 800, 1200):
        print(f"{fmt(a)+'人':>14}", end="")
        for target in (9000, 12000, 15000):
            d = solve_churn(target, years, a)
            cell = "到達せず" if d is None else f"退会率 {d:.1%}"
            print(f"{cell:>16}", end="")
        print()
    print("  → 新規入会が年500〜1,200人なら、退会率は概ね 1〜7% のレンジに収まる")
    print()

    print("=" * 78)
    print("■ STEP F  母馬優先枠の実測と突き合わせて退会率を絞る")
    print("=" * 78)
    _, _ = lognormal_from_censoring(POOL_HALF, rs.p_dam_in_full, 1.0)
    med_in, _ = lognormal_from_censoring(POOL_HALF, rs.p_dam_in_full, 1.0)
    ep = ExerciseParams()
    print(f"  観測：母馬優先枠への申込口数の中央値 ≒ {fmt(med_in)}口")
    print(f"  仮定：母馬の出資者実人数 S={fmt(ep.s_dam)}人、経過 {ep.t_years}年、"
          f"母馬優先での平均申込 {ep.m_dam}口")
    print()
    print("  ○＝権利行使率が常識的な40〜60%に収まる／△＝30〜75%／×＝それ以外")
    print(f"{'退会率':>8}{'有資格者数 E':>16}{'整合する権利行使率 u':>24}{'妥当性':>10}")
    for d in (0.02, 0.03, 0.045, 0.06, 0.08, 0.10, 0.13):
        e = eligible_at(d, ep)
        u = implied_exercise_rate(med_in, d, ep)
        judge = "○" if 0.40 <= u <= 0.60 else ("△" if 0.30 <= u <= 0.75 else "×")
        print(f"{d:>7.1%}{fmt(e)+'人':>16}{u:>22.0%}{judge:>10}")
    print()
    print("  → 権利行使率が40〜60%に収まるのは退会率 3〜6% のとき。")
    print("     退会率10%以上だと行使率が8割超になり、母馬に出資していた人がほぼ全員")
    print("     その仔にも申し込む計算になってしまい不自然。")
    print()
    print("  ただし『母馬優先での平均申込口数 m』の置き方に敏感なので、感度も見る：")
    print(f"{'m（口）':>8}", end="")
    for d in (0.03, 0.045, 0.06, 0.08):
        print(f"{'退会'+format(d,'.1%'):>12}", end="")
    print()
    for m in (1.8, 2.2, 2.6, 3.0):
        print(f"{m:>8.1f}", end="")
        for d in (0.03, 0.045, 0.06, 0.08):
            u = implied_exercise_rate(med_in, d, ExerciseParams(m_dam=m))
            print(f"{u:>11.0%} ", end="")
        print()
    print("  （表の中身は整合する権利行使率 u。40〜60%あたりが自然）")
    print()


if __name__ == "__main__":
    main()

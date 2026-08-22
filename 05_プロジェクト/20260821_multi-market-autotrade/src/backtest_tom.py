"""CR-33 ターン・オブ・ザ・マンス効果のバックテスト（MVP-0 S0）。

問い: 「この効果は2022年以降も効いているのか」
論文の検証期間は2015-08〜2021-08。したがって 2022-08 以降が真のアウトオブサンプルになる。

依存は標準ライブラリのみ。データは data/ohlcv_btc_jpy.json（スナップショット）だけを読む。
"""
import json
import os
from datetime import date, timedelta

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "ohlcv_btc_jpy.json")

IS_END = "2022-07-31"      # 論文の対象期間の外側に境界を置く
OOS_START = "2022-08-01"

ONE_WAY_COST = 0.0005      # テイカー 0.05%（往復 0.1%）
STOP_PCT = 0.08            # SF-1: 建値から -8%


def load_bars():
    with open(DATA) as f:
        snap = json.load(f)
    return snap, snap["bars"]


def quality_check(bars):
    """BACKTEST_PROTOCOL §1.2 の品質チェック。"""
    issues = []
    dates = [b["date"] for b in bars]

    if dates != sorted(dates):
        issues.append("日付が昇順でない")
    if len(set(dates)) != len(dates):
        issues.append("日付の重複がある")

    # 欠損日
    d0 = date.fromisoformat(dates[0])
    d1 = date.fromisoformat(dates[-1])
    expected = set()
    d = d0
    while d <= d1:
        expected.add(d.isoformat())
        d += timedelta(days=1)
    missing = sorted(expected - set(dates))

    # 異常値（前日終値比 ±30% 超）
    spikes = []
    for i in range(1, len(bars)):
        prev, cur = bars[i - 1]["close"], bars[i]["close"]
        if prev > 0 and abs(cur / prev - 1) > 0.30:
            spikes.append((bars[i]["date"], round((cur / prev - 1) * 100, 1)))

    # OHLC の整合
    bad_ohlc = [b["date"] for b in bars
                if not (b["low"] <= b["open"] <= b["high"] and b["low"] <= b["close"] <= b["high"])]

    return {
        "件数": len(bars),
        "期間": f"{dates[0]} 〜 {dates[-1]}",
        "欠損日数": len(missing),
        "欠損日の例": missing[:5],
        "急変（±30%超）": spikes,
        "OHLC不整合": bad_ohlc,
        "構造的な問題": issues,
    }


def build_calendar(bars):
    """各バーに「その月の何日目か」「月末まで何日か」を付与する。

    暗号資産は24/7なので、データに存在する日を営業日とみなす。
    """
    by_month = {}
    for i, b in enumerate(bars):
        ym = b["date"][:7]
        by_month.setdefault(ym, []).append(i)
    meta = {}
    for ym, idxs in by_month.items():
        n = len(idxs)
        for pos, i in enumerate(idxs):
            meta[i] = {"ym": ym, "day_of_month": pos + 1, "days_to_end": n - pos - 1}
    return meta, by_month


def run(bars, n_before, m_day, cost_mult, use_stop, start=None, end=None):
    """N: 月末の何日前に買うか（0=月末当日） / M: 翌月の何日目に売るか"""
    meta, by_month = build_calendar(bars)
    months = sorted(by_month)
    cost = ONE_WAY_COST * cost_mult

    trades = []
    holding = None
    equity = 1.0
    curve = []
    peak = 1.0
    max_dd = 0.0

    for i, b in enumerate(bars):
        d = b["date"]
        if start and d < start:
            continue
        if end and d > end:
            break

        m = meta[i]

        # --- 保有中の処理 ---
        if holding:
            entry_px = holding["entry_px"]
            stop_px = entry_px * (1 - STOP_PCT) if use_stop else None
            exit_px = None
            reason = None

            # 損切り（ギャップは寄り値で約定させる／FR-BT-008）
            if stop_px is not None and b["low"] <= stop_px:
                exit_px = min(b["open"], stop_px)
                reason = "stop"
            # 予定の決済日
            elif m["ym"] > holding["entry_ym"] and m["day_of_month"] >= m_day:
                exit_px = b["close"]
                reason = "exit"

            if exit_px is not None:
                gross = exit_px / entry_px
                net = gross * (1 - cost) ** 2
                equity *= net
                trades.append({
                    "entry": holding["entry_date"], "exit": d,
                    "entry_px": entry_px, "exit_px": exit_px,
                    "ret": net - 1, "reason": reason,
                })
                holding = None
            else:
                equity_mtm = equity * (b["close"] / entry_px) * (1 - cost)
                peak = max(peak, equity_mtm)
                max_dd = max(max_dd, 1 - equity_mtm / peak)
                curve.append((d, equity_mtm))
                continue

        # --- 新規エントリー（カレンダーのみで決まる＝先読みなし） ---
        if holding is None and m["days_to_end"] == n_before:
            holding = {"entry_date": d, "entry_px": b["close"], "entry_ym": m["ym"]}

        peak = max(peak, equity)
        max_dd = max(max_dd, 1 - equity / peak)
        curve.append((d, equity))

    if not curve:
        return None

    years = (date.fromisoformat(curve[-1][0]) - date.fromisoformat(curve[0][0])).days / 365.25
    total = equity - 1
    cagr = (equity ** (1 / years) - 1) if years > 0 and equity > 0 else float("nan")
    wins = [t for t in trades if t["ret"] > 0]

    return {
        "N": n_before, "M": m_day, "cost_mult": cost_mult, "stop": use_stop,
        "期間": f"{curve[0][0]} 〜 {curve[-1][0]}",
        "年数": round(years, 2),
        "トレード数": len(trades),
        "累積リターン": round(total * 100, 2),
        "年率": round(cagr * 100, 2),
        "最大DD": round(max_dd * 100, 2),
        "勝率": round(len(wins) / len(trades) * 100, 1) if trades else 0.0,
        "損切り発動": sum(1 for t in trades if t["reason"] == "stop"),
        "_trades": trades,
    }


def buy_and_hold(bars, start, end):
    sel = [b for b in bars if (not start or b["date"] >= start) and (not end or b["date"] <= end)]
    if len(sel) < 2:
        return None
    ratio = sel[-1]["close"] / sel[0]["close"]
    years = (date.fromisoformat(sel[-1]["date"]) - date.fromisoformat(sel[0]["date"])).days / 365.25
    peak, max_dd, eq = sel[0]["close"], 0.0, sel[0]["close"]
    for b in sel:
        eq = b["close"]
        peak = max(peak, eq)
        max_dd = max(max_dd, 1 - eq / peak)
    return {
        "累積リターン": round((ratio - 1) * 100, 2),
        "年率": round((ratio ** (1 / years) - 1) * 100, 2),
        "最大DD": round(max_dd * 100, 2),
    }

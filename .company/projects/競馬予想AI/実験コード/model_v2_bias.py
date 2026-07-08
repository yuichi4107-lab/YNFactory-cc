# -*- coding: utf-8 -*-
"""馬場バイアス特徴量の実験モジュール（model_v2のラッパー、本番無改変）

同一競馬場×同一馬場種別の「直近45日・target_date未満」のレースから
  - bias_draw:  内枠(相対1/3以内) と 外枠(相対2/3以降) の複勝率差
  - bias_front: 先行(1角3番手以内) と 後方(8番手以降) の複勝率差
を推定し、各馬の枠順・脚質(既存early_pace)との適合度を掛け合わせる。

追加5特徴量: bias_draw / bias_front / bias_draw_fit / bias_front_fit / bias_samples
リーク防止: バイアス集計SQLは ra.date < target_date のみ。leak_check() で機械検証可能。
"""
import math
import sys
import os

sys.path.insert(0, "/opt/keiba-unified/jra/scripts")
import model_v2

BIAS_COLS = ["bias_draw", "bias_front", "bias_draw_fit", "bias_front_fit", "bias_samples"]
FEATURE_COLS_FULL = list(model_v2.FEATURE_COLS_FULL) + BIAS_COLS
FEATURE_COLS_NO_ODDS = list(model_v2.FEATURE_COLS_NO_ODDS) + BIAS_COLS

WINDOW_DAYS = 45
MIN_SIDE = 15          # 内/外・先行/後方それぞれの最小標本数（未満はバイアス0=中立）
_CACHE = {}

# venue_code -> venue名 の逆引き（dfにはvenue_codeしか残らないため）
_CODE2VENUE = {v: k for k, v in model_v2.VENUE_CODE.items()}


def _venue_bias(conn, venue, surface, target_date):
    key = (venue, surface, target_date)
    if key in _CACHE:
        return _CACHE[key]
    c = conn.cursor()
    c.execute("""SELECT r.horse_number, ra.head_count, r.passing, r.finish_position
                 FROM results r JOIN races ra ON ra.race_id = r.race_id
                 WHERE ra.venue = ? AND ra.surface = ?
                   AND ra.date < ? AND ra.date >= date(?, ?)
                   AND r.finish_position > 0""",
              (venue, surface, target_date, target_date, f"-{WINDOW_DAYS} day"))
    inner, outer, front, back = [], [], [], []
    n = 0
    for hn, hc, passing, fin in c.fetchall():
        if not hn or not hc or hc < 8:
            continue
        n += 1
        top3 = 1 if fin <= 3 else 0
        rel = (hn - 1) / (hc - 1)
        if rel <= 1 / 3:
            inner.append(top3)
        elif rel >= 2 / 3:
            outer.append(top3)
        if passing:
            try:
                fc = int(str(passing).split("-")[0])
            except (ValueError, IndexError):
                fc = None
            if fc is not None:
                if fc <= 3:
                    front.append(top3)
                elif fc >= 8:
                    back.append(top3)
    bias_draw = (sum(inner) / len(inner) - sum(outer) / len(outer)) \
        if len(inner) >= MIN_SIDE and len(outer) >= MIN_SIDE else 0.0
    bias_front = (sum(front) / len(front) - sum(back) / len(back)) \
        if len(front) >= MIN_SIDE and len(back) >= MIN_SIDE else 0.0
    out = (bias_draw, bias_front, math.log1p(n))
    _CACHE[key] = out
    return out


def build_features_for_date(conn, target_date):
    """model_v2の特徴量に bias 5列を後付けする（既存列は無改変）"""
    df = model_v2.build_features_for_date(conn, target_date)
    if df is None or df.empty:
        return df
    draws, fronts, dfits, ffits, samples = [], [], [], [], []
    for _, row in df.iterrows():
        venue = _CODE2VENUE.get(row.get("venue_code", 0), "")
        surface = "芝" if row.get("surface_turf", 0) == 1 else "ダート"
        b_draw, b_front, b_n = _venue_bias(conn, venue, surface, target_date)
        hn = row.get("horse_number") or 0
        hc = row.get("head_count") or 14
        rel = (hn - 1) / (hc - 1) if hn and hc and hc > 1 else 0.5
        ep = row.get("early_pace")
        ep = float(ep) if ep is not None and not (isinstance(ep, float) and math.isnan(ep)) else 7.0
        draws.append(b_draw)
        fronts.append(b_front)
        dfits.append(b_draw * (1.0 - 2.0 * rel))
        ffits.append(b_front * (4.0 - min(ep, 8.0)) / 4.0)
        samples.append(b_n)
    df = df.copy()
    df["bias_draw"] = draws
    df["bias_front"] = fronts
    df["bias_draw_fit"] = dfits
    df["bias_front_fit"] = ffits
    df["bias_samples"] = samples
    return df


def leak_check(db_path, sample_dates):
    """リーク機械検証: target_date当日以降のデータを消したコピーDBで
    バイアス値が不変であることを確認する（変わればリーク）。"""
    import sqlite3
    import shutil
    import tempfile
    ok = True
    for d in sample_dates:
        _CACHE.clear()
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        venues = [r for r in conn.execute(
            "SELECT DISTINCT venue, surface FROM races WHERE date = ? AND surface IN ('芝','ダート')", (d,))]
        before = {vs: _venue_bias(conn, vs[0], vs[1], d) for vs in venues}
        conn.close()

        tmp = tempfile.mktemp(suffix=".db")
        shutil.copy(db_path, tmp)
        conn2 = sqlite3.connect(tmp)
        conn2.execute("DELETE FROM results WHERE race_id IN (SELECT race_id FROM races WHERE date >= ?)", (d,))
        conn2.execute("DELETE FROM races WHERE date >= ?", (d,))
        conn2.commit()
        _CACHE.clear()
        after = {vs: _venue_bias(conn2, vs[0], vs[1], d) for vs in venues}
        conn2.close()
        os.remove(tmp)

        for vs in venues:
            if before[vs] != after[vs]:
                print(f"LEAK DETECTED {d} {vs}: {before[vs]} != {after[vs]}")
                ok = False
        print(f"leak-check {d}: {'OK' if all(before[vs]==after[vs] for vs in venues) else 'NG'} "
              f"({len(venues)} venue-surface)")
    _CACHE.clear()
    print("LEAK CHECK", "PASSED" if ok else "FAILED")
    return ok


if __name__ == "__main__":
    # 使い方: python3 model_v2_bias.py --leak-check /tmp/jra_v3.db 2026-06-01 2026-03-15
    if "--leak-check" in sys.argv:
        args = [a for a in sys.argv[1:] if a != "--leak-check"]
        db = args[0]
        dates = args[1:] or ["2026-06-01"]
        sys.exit(0 if leak_check(db, dates) else 1)

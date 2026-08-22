"""S0: CR-33 の検証を実行し、結果を出力する。"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from backtest_tom import load_bars, run, buy_and_hold, IS_END, OOS_START

GRID_N = [1, 2, 3]   # 月末の何日前に買うか
GRID_M = [1, 3, 5]   # 翌月の何日目に売るか
TRIALS = len(GRID_N) * len(GRID_M)

snap, bars = load_bars()
last = bars[-1]["date"]

print(f"# CR-33 検証結果")
print(f"データ: {bars[0]['date']} 〜 {last}（{len(bars)}本・GMOコイン公開API）")
print(f"分割: IS {bars[0]['date']}〜{IS_END} / OOS {OOS_START}〜{last}")
print(f"探索した組合せ数: {TRIALS}（N={GRID_N} × M={GRID_M}）")
print()

def table(title, start, end, cost_mult, use_stop):
    print(f"## {title}（コスト{cost_mult}倍 / 損切り{'あり' if use_stop else 'なし'}）")
    print("| N | M | トレード | 累積% | 年率% | 最大DD% | 勝率% | 損切り |")
    print("|--:|--:|--:|--:|--:|--:|--:|--:|")
    rows = []
    for n in GRID_N:
        for m in GRID_M:
            r = run(bars, n, m, cost_mult, use_stop, start, end)
            if r:
                rows.append(r)
                print(f"| {n} | {m} | {r['トレード数']} | {r['累積リターン']} | {r['年率']} | "
                      f"{r['最大DD']} | {r['勝率']} | {r['損切り発動']} |")
    print()
    return rows

is_rows = table("IS（開発期間）", None, IS_END, 1.0, True)
oos_rows_10 = table("OOS（真のアウトオブサンプル）", OOS_START, None, 1.0, True)
oos_rows_15 = table("OOS", OOS_START, None, 1.5, True)
oos_rows_20 = table("OOS", OOS_START, None, 2.0, True)
oos_nostop = table("OOS（損切りなし・参考）", OOS_START, None, 1.0, False)

print("## バイ・アンド・ホールドとの比較")
for label, s, e in [("IS", None, IS_END), ("OOS", OOS_START, None)]:
    bh = buy_and_hold(bars, s, e)
    print(f"- {label} B&H: 累積 {bh['累積リターン']}% / 年率 {bh['年率']}% / 最大DD {bh['最大DD']}%")
print()

best_is = max(is_rows, key=lambda r: r["年率"])
print(f"## ISで最良のパラメータ: N={best_is['N']}, M={best_is['M']}（年率 {best_is['年率']}%）")
for cm, rows in [(1.0, oos_rows_10), (1.5, oos_rows_15), (2.0, oos_rows_20)]:
    r = next(x for x in rows if x["N"] == best_is["N"] and x["M"] == best_is["M"])
    print(f"- そのパラメータのOOS（コスト{cm}倍）: 年率 {r['年率']}% / 最大DD {r['最大DD']}% / トレード {r['トレード数']}回")
print()

pos = [r for r in oos_rows_20 if r["年率"] > 0]
print(f"## 判定材料")
print(f"- OOS・コスト2.0倍で年率がプラスの組合せ: {len(pos)}/{TRIALS}")
print(f"- OOS・コスト2.0倍の年率の中央値: {sorted(r['年率'] for r in oos_rows_20)[TRIALS//2]}%")

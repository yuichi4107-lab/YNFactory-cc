# -*- coding: utf-8 -*-
"""配当均等再検証の分析（2026-07-11・現行レジーム）

入力: stake_v4_{label}.json（combos=[(nums, est_odds, payout|null)]）
出力: 全期間/3⁄14-15除外の両方で flat/配当均等/穴厚め のROI・95%CI・
      利益上位3日丸ごと除外ROI（投資も除外する正しい計算）・月次
"""
import io
import json
import random
import sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BUDGET = 5000.0
SCHEMES = ("flat", "payout_eq", "odds_prop")
EXCLUDE = ("2026-03-14", "2026-03-15")


def settle(r, scheme):
    combos = r["combos"]
    n = len(combos)
    if scheme == "flat":
        ws = [1.0] * n
    elif scheme == "payout_eq":
        ws = [1.0 / max(eo, 1.01) for _, eo, _ in combos]
    else:
        ws = [max(eo, 1.01) for _, eo, _ in combos]
    tw = sum(ws)
    stakes = [BUDGET * w / tw for w in ws]
    inv = sum(stakes)
    pay = sum((po or 0) / 100.0 * s for (_, eo, po), s in zip(combos, stakes))
    return inv, pay


def block(title, races):
    print(f"\n--- {title} (n={len(races)}) ---")
    if not races:
        return
    for scheme in SCHEMES:
        pl = [settle(r, scheme) for r in races]
        inv = sum(x[0] for x in pl)
        pay = sum(x[1] for x in pl)
        hits = sum(1 for _, p in pl if p > 0)
        # 利益上位3日を投資ごと除外
        day = defaultdict(lambda: [0.0, 0.0])
        for r, (i, p) in zip(races, pl):
            day[r["date"]][0] += i
            day[r["date"]][1] += p
        top3 = sorted(day, key=lambda d: -(day[d][1] - day[d][0]))[:3]
        inv3 = inv - sum(day[d][0] for d in top3)
        pay3 = pay - sum(day[d][1] for d in top3)
        # bootstrap CI (レース単位・1500回)
        rng = random.Random(7)
        rois = []
        for _ in range(1500):
            s = [pl[rng.randrange(len(pl))] for _ in range(len(pl))]
            si = sum(x[0] for x in s)
            rois.append(100 * sum(x[1] for x in s) / si)
        rois.sort()
        print(f"  {scheme:10s}: ROI={100*pay/inv:6.1f}%  hit={100*hits/len(pl):4.1f}%  "
              f"95%CI=[{rois[37]:.0f},{rois[1462]:.0f}]  利益上位3日除外={100*pay3/inv3 if inv3 else 0:6.1f}%")


def monthly(races):
    mon = defaultdict(list)
    for r in races:
        mon[r["date"][:7]].append(r)
    line1, line2 = "  月次 flat     :", "  月次 配当均等 :"
    for mo in sorted(mon):
        for scheme, _ in (("flat", line1), ("payout_eq", line2)):
            pass
        pf = [settle(r, "flat") for r in mon[mo]]
        pe = [settle(r, "payout_eq") for r in mon[mo]]
        line1 += f" {mo[-2:]}月={100*sum(p for _,p in pf)/sum(i for i,_ in pf):5.1f}%"
        line2 += f" {mo[-2:]}月={100*sum(p for _,p in pe)/sum(i for i,_ in pe):5.1f}%"
    print(line1)
    print(line2)


def main():
    for label in ("C5b_morning", "FULL_prodOLD", "FULL_B"):
        races = json.load(open(f"stake_v4_{label}.json", encoding="utf-8"))
        print(f"\n===== {label} =====")
        block("全期間", races)
        ex = [r for r in races if r["date"] not in EXCLUDE]
        block("3/14-15除外（標準プロトコル）", ex)
        monthly(ex)


if __name__ == "__main__":
    main()

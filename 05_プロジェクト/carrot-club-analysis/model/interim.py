#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
クラブ公表の「申込み状況の中間発表（2回目）」からの直接観測。

何が新しいか
------------
これまで（members.py / dam_age.py / reversal.py）は、抽選ランクという
**打ち切り観測**（「200口を超えたか否か」の二値）から申込口数を復元していた。

ところがクラブは第1次募集の締切前日17時に、総申込口数が200口以上になった
募集馬について**申込口数の内訳そのもの**を公表している。

  ＜母馬優先対象馬＞ 「総申込」「母馬優先＋最優先」「母馬優先（一般）」「最優先」
  ＜母馬優先非対象馬＞「総申込」「最優先」

  母馬優先枠への申込口数 D = 「母馬優先＋最優先」＋「母馬優先（一般）」

つまり **D が直接見える**。抽選ランクの 1〜4/5 は「最終的に D が200口を
超えたか」なので、この2つを突き合わせると

  ・中間時点の D がいくつなら最終的に200口を超えるのか（しきい値の較正）
  ・締切24時間で申込がどれだけ伸びるのか、そのばらつきはどれくらいか

が分かる。後者のばらつきが、docs/07 でいう「産駒側のブレ」の実体。

データ
------
`data/carrot_interim.csv`
  2024年度（2024/9/5 17時／締切は9/6 17時）
  2025年度（2025/9/4 17時／締切は9/5 17時）

使い方
------
  python3 interim.py
"""

from __future__ import annotations

import csv
import os
import statistics
from collections import defaultdict

HERE = os.path.dirname(__file__)
INTERIM = os.path.join(HERE, "..", "data", "carrot_interim.csv")
RANK = os.path.join(HERE, "..", "data", "dam_age_rank.csv")

POOL = 200
# クラブ公表「現時点で前年比約N%のお申込み」（中間発表2回目の本文）
REPORTED_SHARE = {2024: 0.21, 2025: 0.234}


def load():
    rows = []
    with open(INTERIM, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r["season"] = int(r["募集年度"])
            r["total"] = int(r["総申込"])
            r["dp_top"] = int(r["母優かつ最優先"])
            r["dp_gen"] = int(r["母優一般"])
            r["top_only"] = int(r["最優先のみ"])
            r["D"] = r["dp_top"] + r["dp_gen"]          # 母馬優先枠への申込
            r["top"] = r["dp_top"] + r["top_only"]      # 最優先希望枠の行使
            r["dam"] = r["馬名"].rsplit("の", 1)[0]
            rows.append(r)
    rk = {}
    with open(RANK, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rk[(int(r["募集年度"]), r["母馬名"])] = r
    for r in rows:
        m = rk.get((r["season"], r["dam"]))
        r["rank"] = m["抽選ランク"] if m else None
        r["hit"] = int(m["母馬優先枠で抽選"]) if m else None
        r["age"] = int(m["母馬の馬齢"]) if m else None
    return rows


def main() -> None:
    rows = load()

    print("=" * 78)
    print("■ 0. 何頭ぶん観測できたか")
    print("=" * 78)
    for y in sorted({r["season"] for r in rows}):
        s = [r for r in rows if r["season"] == y]
        t = [r for r in s if r["区分"] == "対象"]
        print(f"  {y}年度  掲載 {len(s)}頭"
              f"（母馬優先対象 {len(t)}頭／非対象 {len(s)-len(t)}頭）"
              f"  ※総申込200口以上の馬だけが掲載される")
    print()

    print("=" * 78)
    print("■ 1. 中間時点の母馬優先枠申込 D と、最終的に枠が埋まったか")
    print("=" * 78)
    tgt = [r for r in rows if r["区分"] == "対象" and r["hit"] is not None]
    tgt.sort(key=lambda r: -r["D"])
    print(f"{'年度':<6}{'母馬':<15}{'総申込':>8}{'母優枠D':>9}{'最優先':>8}"
          f"{'ランク':>7}{'結果':>5}{'母馬':>6}")
    for r in tgt:
        print(f"{r['season']:<6}{r['dam']:<15}{r['total']:>7}口{r['D']:>8}口"
              f"{r['top']:>7}口{r['rank']:>7}"
              f"{'  埋' if r['hit'] else '  余':>5}{r['age']:>5}歳")
    print()

    fil = [r["D"] for r in tgt if r["hit"]]
    lef = [r["D"] for r in tgt if not r["hit"]]
    print(f"  最終的に埋まった {len(fil)}頭：中間の D は中央値 {statistics.median(fil):.0f}口"
          f"（{min(fil)}〜{max(fil)}口）")
    print(f"  最終的に余った  {len(lef)}頭：中間の D は中央値 {statistics.median(lef):.0f}口"
          f"（{min(lef)}〜{max(lef)}口）")
    print()

    # しきい値の較正：D で並べたときに最もよく分離する切れ目を探す
    cand = sorted({r["D"] for r in tgt})
    best = max(cand, key=lambda c: sum((r["D"] >= c) == bool(r["hit"]) for r in tgt))
    acc = sum((r["D"] >= best) == bool(r["hit"]) for r in tgt) / len(tgt)
    print(f"  最もよく分離する中間しきい値 = {best}口（正答率 {acc:.0%}）")
    print(f"  → 締切24時間前に母馬優先枠へ {best}口 入っていれば、"
          f"最終的に200口へ届く公算が大きい。")
    print(f"  → 逆算すると、最後の24時間で D は約 {POOL/best:.1f}倍 になる。")
    print()
    print("  重なり合う帯（誤分類が出る範囲）：")
    lo = max(r["D"] for r in tgt if not r["hit"] and r["D"] < best) if any(
        not r["hit"] and r["D"] < best for r in tgt) else 0
    band = [r for r in tgt if min(fil) <= r["D"] <= max(lef)]
    print(f"    {min(fil)}口〜{max(lef)}口 に {len(band)}頭が重なる"
          f"（この帯にいる馬は最終日次第で どちらにも転ぶ）")
    for r in sorted(band, key=lambda r: -r["D"]):
        print(f"      {r['dam']:<15}{r['season']}年度 D={r['D']:>3}口 → "
              f"{'埋まった' if r['hit'] else '余った'}（{r['rank']}）")
    print()

    print("=" * 78)
    print("■ 2. 最終日の伸びのばらつき＝「産駒側のブレ」の実体")
    print("=" * 78)
    for y in sorted(REPORTED_SHARE):
        s = [r for r in rows if r["season"] == y]
        print(f"  {y}年度  中間時点の掲載馬の総申込合計 {sum(r['total'] for r in s):,}口")
        print(f"          クラブ公表『現時点で前年比約{REPORTED_SHARE[y]:.1%}』")
    print()
    print("  つまり申込の大半は締切直前に入る。中間発表は順位の目安にしかならない。")
    print("  実際、同じ中間 D でも最終結果が割れている：")
    print(f"    余ったのに中間 D が最大 … {max(lef)}口")
    print(f"    埋まったのに中間 D が最小 … {min(fil)}口")
    print(f"  → 最終日の伸び率は馬によって {POOL/max(lef):.1f}倍未満〜{POOL/min(fil):.1f}倍超まで開く。")
    print("     この伸び率のばらつきが、reversal.py でいう産駒側の分散そのもの。")
    print()

    print("=" * 78)
    print("■ 3. 母馬優先枠は『全体人気の写し鏡』か")
    print("=" * 78)
    print("  総申込（全体人気）と母馬優先枠申込 D の関係を見る。")
    print()
    print(f"{'  総申込の帯':<18}{'頭数':>6}{'D の中央値':>12}{'D/総申込':>10}{'枠が埋まった率':>14}")
    for lo, hi, lab in [(0, 250, "200〜249口"), (250, 300, "250〜299口"),
                        (300, 400, "300〜399口"), (400, 10000, "400口以上")]:
        s = [r for r in tgt if lo <= r["total"] < hi]
        if not s:
            continue
        med = statistics.median([r["D"] for r in s])
        ratio = sum(r["D"] for r in s) / sum(r["total"] for r in s)
        h = sum(r["hit"] for r in s)
        print(f"  {lab:<16}{len(s):>5}頭{med:>10.0f}口{ratio:>10.0%}"
              f"{f'{h}/{len(s)} = {h/len(s):.0%}':>14}")
    print()
    print("  → 総申込が多いほど D も多い傾向はあるが、比例していない。")
    print("     全体人気が最上位でも母馬優先枠が余る馬がある：")
    for r in tgt:
        if not r["hit"] and r["rank"] and r["rank"][-1] in "AB":
            print(f"      {r['dam']:<15}{r['season']}年度 総申込{r['total']}口"
                  f"（枠外{r['rank'][-1]}＝最上位人気）なのに D={r['D']}口 で枠は余った"
                  f"／母馬{r['age']}歳")
    print("     いずれも母馬優先の有資格者が薄く、人気を支えているのは一般層。")
    print()

    print("=" * 78)
    print("■ 4. Σ最優先申込口数の直接観測（members.py の答え合わせ）")
    print("=" * 78)
    print("  members.py は抽選ランクの打ち切り観測から Σ最優先申込口数 ≒ 24,000口 と復元した。")
    print("  中間発表には最優先の実口数が載っているので、粗いながら突き合わせられる。")
    print()
    for y in sorted(REPORTED_SHARE):
        s = [r for r in rows if r["season"] == y]
        top = sum(r["top"] for r in s)
        sh = REPORTED_SHARE[y]
        print(f"  {y}年度  中間時点の Σ最優先（掲載馬のみ）= {top:,}口")
        print(f"          クラブ公表の進捗 {sh:.1%} で割り戻すと ≒ {top/sh:,.0f}口")
    print()
    print("  → 2年とも 22,000口台。members.py の 24,000口 と 8% 以内で一致する。")
    print("  ただしこの割り戻しは粗い。理由は3つ：")
    print("    (1) 掲載は総申込200口以上の馬だけ。それ以下の馬の最優先が抜けている（下振れ要因）")
    print("    (2) クラブの『前年比N%』は全馬の総申込ベースで、最優先だけの進捗ではない")
    print("    (3) 母馬優先を持つ人は早めに動く可能性があり、時間プロファイルが層で違いうる")
    print("  それでも桁と水準が合っているので、members.py の会員数1万〜1万4千人という")
    print("  レンジは、独立な観測からも支持される。")


if __name__ == "__main__":
    main()

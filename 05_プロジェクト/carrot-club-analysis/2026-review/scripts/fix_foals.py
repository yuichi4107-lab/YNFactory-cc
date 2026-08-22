# -*- coding: utf-8 -*-
"""産駒数（何番仔）を取り直す。

netkeibaの /horse/mare/{id}/ は現在その馬自身のページへ転送されるようになっており、
fetch_foals.py の産駒一覧の取得が空振りして全頭「1番仔」になっていた。
母名検索（horse_list&mare=）の結果はキャッシュ済みなので、そこから数え直す。

  何番仔 = その馬より前に生まれた同じ母の産駒の数 + 1

クラブのカタログ由来の産駒数（roster.csv・2020〜2022年度）と突き合わせて
数え方が合っているかを先に確かめる。
"""
import csv
import io
import json
import os
import re
import sys

from scrape_results import search_dam

BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def alias():
    p = os.path.join(DS, 'dam_alias.csv')
    if not os.path.exists(p):
        return {}
    return {r['name']: r['dam_alias'] for r in csv.DictReader(open(p, encoding='utf-8'))}


def count_before(dam, born, cache, al=None, name=''):
    """母名検索の結果から、born年より前に生まれた産駒の数を数える。"""
    keys = [dam]
    if 'Ⅱ' in dam:
        keys = [dam.replace('Ⅱ', 'II'), dam.replace('Ⅱ', ''), dam]
    a = (al or {}).get(name)
    if a:
        keys.insert(0, a)
    years = []
    for k in keys:
        if k not in cache:
            try:
                cache[k] = search_dam(k)
            except Exception:
                cache[k] = []
        if cache[k]:
            years = [int(h[:4]) for h, _ in cache[k] if h[:4].isdigit()]
            break
    return sum(1 for y in years if y < born) + 1, len(years)


def main():
    rows = list(csv.DictReader(open(os.path.join(DS, 'panel5.csv'), encoding='utf-8-sig')))
    al = alias()
    cache = {}

    # まず 2020〜2022年度（クラブのカタログ由来の正解がある）で数え方を検算する
    hit = miss = 0
    diffs = []
    old = [r for r in rows if r['year'] <= '2022' and r['n_foals']]
    sample = old[::4]          # 4頭に1頭を抜いて検算（母ページの取得に時間がかかるため）
    for r in sample:
        n, listed = count_before(r['dam'], int(r['born']), cache, al, r['name'])
        truth = int(float(r['n_foals']))
        if listed == 0:
            miss += 1
            continue
        if n == truth:
            hit += 1
        else:
            diffs.append((r['year'], r['name'], truth, n, listed))
    print(f'検算（2020〜2022年度から{len(sample)}頭を抽出）: 一致 {hit} / 不一致 {len(diffs)} / 母の産駒が引けず {miss}')
    for d in diffs[:10]:
        print('   ', d)

    # 検算の一致率が7割弱しかない（母名検索は同名の別馬や、クラブが数えない産駒も拾う）。
    # 表示する数値として使えないので、参考値として残しつつ n_foals は空にする。
    out = {}
    for r in rows:
        if r['year'] < '2023':
            continue
        n, listed = count_before(r['dam'], int(r['born']), cache, al, r['name'])
        out[r['year'] + '#' + r['no']] = {
            'n_foals': None, 'n_foals_rough': n if listed else None, 'n_listed': listed,
            'note': '母名検索からの概算。クラブのカタログ値と7割弱しか一致しないため未採用',
        }
    json.dump(out, open(os.path.join(DS, 'foal_order.json'), 'w', encoding='utf-8'),
              ensure_ascii=False)
    from collections import Counter
    print('2023・2024年度は n_foals=null（概算のみ n_foals_rough に保持）')
    print('  概算の分布:', dict(sorted(Counter(v['n_foals_rough'] for v in out.values()).items(),
                                    key=lambda x: (x[0] is None, x[0]))))


if __name__ == '__main__':
    main()

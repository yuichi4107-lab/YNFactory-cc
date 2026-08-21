# -*- coding: utf-8 -*-
"""母の産駒一覧から「何番仔か」を数える（既存ロスターの産駒数と同じ意味）。

netkeibaの繁殖牝馬ページ /horse/mare/{dam_id}/ に産駒が年順で並ぶ。
その馬より前に生まれた産駒の数＋1 を産駒数（何番仔）とする。

出力: datasets/foal_order.json  { key: {"dam_id":..., "n_foals":n, "n_listed":m} }
"""
import csv
import io
import json
import os
import re
import sys

from scrape_results import get

BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')
OUT = os.path.join(DS, 'foal_order.json')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def foal_years(dam_id):
    html = get(f'https://db.netkeiba.com/horse/mare/{dam_id}/')
    years = []
    for m in re.finditer(r'<a href="/horse/(\w+)/?"[^>]*title="[^"]*"', html):
        hid = m.group(1)
        if hid[:4].isdigit():
            years.append(int(hid[:4]))
    return years


def main():
    panel = list(csv.DictReader(open(os.path.join(DS, 'panel5.csv'), encoding='utf-8-sig')))
    res = {}
    for line in open(os.path.join(DS, 'results_new.jsonl'), encoding='utf-8'):
        d = json.loads(line)
        if d.get('dam_id'):
            res[d['key']] = d['dam_id']
    out = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}
    todo = [r for r in panel if r['year'] in ('2023', '2024')
            and (r['year'] + '#' + r['no']) not in out]
    print('対象', len(todo), '頭', flush=True)
    cache = {}
    for i, r in enumerate(todo):
        key = r['year'] + '#' + r['no']
        dam_id = res.get(key)
        if not dam_id:
            out[key] = {'dam_id': '', 'n_foals': None}
            continue
        try:
            if dam_id not in cache:
                cache[dam_id] = foal_years(dam_id)
            ys = cache[dam_id]
            born = int(r['born'])
            out[key] = {'dam_id': dam_id, 'n_foals': sum(1 for y in ys if y < born) + 1,
                        'n_listed': len(ys)}
        except Exception as e:
            out[key] = {'dam_id': dam_id, 'n_foals': None, 'error': str(e)}
        if (i + 1) % 20 == 0:
            json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
            print(f'{i+1}/{len(todo)}', flush=True)
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
    print('DONE', len(out))


if __name__ == '__main__':
    main()

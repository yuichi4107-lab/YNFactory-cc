# -*- coding: utf-8 -*-
"""2020〜2022年度募集274頭の成績を取り直して、新2年ぶんと取得日を揃える。

final_results.json の horse_id をそのまま使うので突合はやり直さない。
出力: datasets/final_results_2026-08.json
"""
import io
import json
import os
import sys

from scrape_results import parse_horse

BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')
OUT = os.path.join(DS, 'final_results_2026-08.json')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

old = json.load(open(os.path.join(DS, 'final_results.json'), encoding='utf-8'))
new = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}

for i, (k, v) in enumerate(old.items()):
    if k in new:
        continue
    hid = v.get('horse_id')
    d = dict(v)
    if hid:
        try:
            d.update(parse_horse(hid))
        except Exception as e:
            d['refresh_error'] = str(e)
    new[k] = d
    if (i + 1) % 20 == 0:
        json.dump(new, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
        print(f'{i+1}/{len(old)}', flush=True)
json.dump(new, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
print('DONE', len(new))

# -*- coding: utf-8 -*-
"""獲得賞金を、キャッシュ済みのnetkeibaページから読み直す。

「5億963万円」表記の億の桁を落としていたので、全頭を parse_horse でやり直す。
ページはキャッシュにあるので通信は発生しない（無い場合だけ取りに行く）。
"""
import io
import json
import os
import sys

from scrape_results import parse_horse

BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def repair_json(path):
    d = json.load(open(path, encoding='utf-8'))
    n = 0
    for k, v in d.items():
        hid = v.get('horse_id')
        if not hid:
            continue
        before = (v.get('prize_jra') or 0) + (v.get('prize_nar') or 0)
        v.update(parse_horse(hid))
        after = (v.get('prize_jra') or 0) + (v.get('prize_nar') or 0)
        if abs(after - before) > 0.01:
            n += 1
    json.dump(d, open(path, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'{os.path.basename(path)}: {len(d)}頭中 {n}頭を修正')


def repair_jsonl(path):
    rows = [json.loads(line) for line in open(path, encoding='utf-8')]
    n = 0
    for v in rows:
        hid = v.get('horse_id')
        if not hid:
            continue
        before = (v.get('prize_jra') or 0) + (v.get('prize_nar') or 0)
        v.update(parse_horse(hid))
        after = (v.get('prize_jra') or 0) + (v.get('prize_nar') or 0)
        if abs(after - before) > 0.01:
            n += 1
    with open(path, 'w', encoding='utf-8') as f:
        for v in rows:
            f.write(json.dumps(v, ensure_ascii=False) + '\n')
    print(f'{os.path.basename(path)}: {len(rows)}行中 {n}行を修正')


if __name__ == '__main__':
    repair_json(os.path.join(DS, 'final_results_2026-08.json'))
    repair_jsonl(os.path.join(DS, 'results_new.jsonl'))

# -*- coding: utf-8 -*-
"""roster_new_raw.csv の各馬を netkeiba に突合し、成績・生産者・母の生年を取る。

  母名で産駒検索 → 生年一致で候補 → 血統ページの父名で確定
出力: datasets/results_new.jsonl（1行1頭・追記式なので中断しても再開できる）
"""
import csv
import json
import os
import re
import sys

from nkextra import parse_extra  # noqa: F401  （生産者用）
from scrape_results import get, parse_horse, search_dam

BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')
OUT = os.path.join(DS, 'results_new.jsonl')


def ped(hid):
    html = get(f'https://db.netkeiba.com/horse/ped/{hid}/')
    out = {}
    for m in re.finditer(r'<td[^>]*rowspan="16"[^>]*class="(b_ml|b_fml)"[^>]*>(.*?)</td>', html, re.S):
        blk = m.group(2)
        a = re.search(r'/horse/(\w+)/"[^>]*>\s*([^<\r\n]+)', blk)
        y = re.search(r'<br\s*/?>\s*(\d{4})', blk)
        key = 'sire' if m.group(1) == 'b_ml' else 'dam'
        if a:
            out[key + '_id'] = a.group(1)
            out[key + '_nk'] = a.group(2).strip()
        if y:
            out[key + '_born'] = int(y.group(1))
    return out


def breeder(hid):
    html = get(f'https://db.netkeiba.com/horse/{hid}/')
    m = re.search(r'生産者</th>\s*<td[^>]*>(.*?)</td>', html, re.S)
    return re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else ''


def variants(dam):
    v = [dam]
    if 'Ⅱ' in dam:
        v = [dam.replace('Ⅱ', 'II'), dam.replace('Ⅱ', ''), dam.replace('Ⅱ', '2')]
    return v


def norm_sire(s):
    return (s or '').replace('　', '').replace(' ', '').strip()


def main():
    rows = list(csv.DictReader(open(os.path.join(DS, 'roster_new_raw.csv'), encoding='utf-8')))
    done = set()
    if os.path.exists(OUT):
        for line in open(OUT, encoding='utf-8'):
            try:
                done.add(json.loads(line)['key'])
            except Exception:
                pass
    dam_cache = {}
    for i, r in enumerate(rows):
        key = f"{r['year']}#{r['no']}"
        if key in done:
            continue
        name = r['name']
        dam = re.sub(r'の\d\d$', '', name)
        born = r['born']
        out = {'key': key, 'year': r['year'], 'no': r['no'], 'boshu_name': name,
               'dam': dam, 'status': ''}
        try:
            cands = []
            seen = set()
            for v in variants(dam):
                if v not in dam_cache:
                    dam_cache[v] = search_dam(v)
                for hid, nm in dam_cache[v]:
                    if hid.startswith(str(born)) and hid not in seen:
                        seen.add(hid)
                        cands.append((hid, nm))
            picked = None
            if len(cands) == 1:
                picked = cands[0][0]
                out['status'] = 'ok'
            elif len(cands) > 1:
                for hid, nm in cands:
                    p = ped(hid)
                    if norm_sire(p.get('sire_nk')) == norm_sire(r['sire']):
                        picked = hid
                        out['status'] = 'ok_by_sire'
                        break
                if picked is None:
                    out['status'] = 'ambiguous:' + ';'.join(f'{h}:{n}' for h, n in cands)
            else:
                out['status'] = 'not_found'
            if picked:
                out.update(parse_horse(picked))
                out.update(ped(picked))
                out['breeder'] = breeder(picked)
                if norm_sire(out.get('sire_nk')) != norm_sire(r['sire']):
                    out['status'] += '+sire_mismatch'
        except Exception as e:
            out['status'] = f'error:{e}'
        with open(OUT, 'a', encoding='utf-8') as f:
            f.write(json.dumps(out, ensure_ascii=False) + '\n')
        print(f"[{i+1}/{len(rows)}] {key} {name} -> {out['status']}", flush=True)


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""まだ突合できていない馬を、生年での絞り込みを緩めて拾い直す。

外国産（持込）の産駒は netkeiba の馬IDが生年で始まらないことがあるので、
ID の頭4桁ではなく血統ページの生年で判定する。
"""
import csv
import io
import json
import os
import re
import sys
import urllib.parse

from match_new import ped, breeder
from scrape_results import get, parse_horse

BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')
OUT = os.path.join(DS, 'results_new.jsonl')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROMAN = {'Ⅱ': 'II', 'Ⅲ': 'III', 'Ⅳ': 'IV'}


def alias_table():
    p = os.path.join(DS, 'dam_alias.csv')
    if not os.path.exists(p):
        return {}
    return {r['name']: r['dam_alias'] for r in csv.DictReader(open(p, encoding='utf-8'))}


def variants(dam, name='', alias=None):
    v = [dam]
    for k, r in ROMAN.items():
        if k in dam:
            v = [dam.replace(k, r), dam.replace(k, ''), dam.replace(k, ' ' + r)]
    a = (alias or {}).get(name)
    if a:
        v.insert(0, a)      # 外国産は母名が英字で登録されている
    return v


def search(dam):
    try:
        q = dam.encode('euc-jp')
    except UnicodeEncodeError:
        return []
    params = {'pid': 'horse_list', 'mare': q, 'list': '100'}
    html = get('https://db.netkeiba.com/?' + urllib.parse.urlencode(params))
    hits = re.findall(r'href="/horse/(\w+)/?"[^>]*>([^<]+)</a>', html)
    m = re.search(r'og:url"\s+content="https://db\.netkeiba\.com/horse/(\w+)/?"', html)
    if m:
        hits.append((m.group(1), ''))
    seen, out = set(), []
    for hid, nm in hits:
        if hid not in seen and not hid.startswith('sire'):
            seen.add(hid)
            out.append((hid, nm))
    return out


def main():
    rows = {r['year'] + '#' + r['no']: r for r in
            csv.DictReader(open(os.path.join(DS, 'roster_new_raw.csv'), encoding='utf-8'))}
    best = {}
    for line in open(OUT, encoding='utf-8'):
        d = json.loads(line)
        if d['key'] not in best or d['status'].startswith('ok'):
            best[d['key']] = d
    bad = [k for k, d in best.items() if not d['status'].startswith('ok')]
    bad += [k for k in rows if k not in best]
    alias = alias_table()
    print('残り:', bad)
    for key in sorted(set(bad)):
        r = rows[key]
        dam = re.sub(r'の\d\d$', '', r['name'])
        born = int(r['born'])
        picked = None
        for v in variants(dam, r['name'], alias):
            for hid, nm in search(v):
                p = ped(hid)
                if p.get('dam_born') is None:
                    continue
                h = parse_horse(hid)
                y = re.search(r'(\d{4})年', h.get('birth_full', '') or '')
                if y and int(y.group(1)) == born:
                    picked = (hid, h, p)
                    break
            if picked:
                break
        out = {'key': key, 'year': r['year'], 'no': r['no'], 'boshu_name': r['name'],
               'dam': dam, 'status': 'not_found_final'}
        if picked:
            hid, h, p = picked
            out.update(h)
            out.update(p)
            out['breeder'] = breeder(hid)
            out['status'] = 'ok_fixup2'
        print(key, r['name'], '->', out['status'], out.get('reg_name', ''), out.get('dam_nk', ''))
        with open(OUT, 'a', encoding='utf-8') as f:
            f.write(json.dumps(out, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""match_new.py が not_found にした馬を拾い直す。

netkeibaの母名検索は、該当が1頭しかないとその馬のページへリダイレクトする。
その場合 horse_list のリンクが無いので search_dam が空を返す。og:url から拾う。

出力: datasets/results_new.jsonl へ追記（キー重複は後勝ちで読む側が処理）
"""
import csv
import io
import json
import os
import re
import sys
import urllib.parse

from match_new import ped, breeder, variants
from scrape_results import get, parse_horse

BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')
OUT = os.path.join(DS, 'results_new.jsonl')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def single_hit(dam):
    """母名検索が1頭に絞られてリダイレクトした場合の馬IDを返す。"""
    params = {'pid': 'horse_list', 'mare': dam.encode('euc-jp'), 'list': '100'}
    html = get('https://db.netkeiba.com/?' + urllib.parse.urlencode(params))
    m = re.search(r'og:url"\s+content="https://db\.netkeiba\.com/horse/(\w+)/?"', html)
    return m.group(1) if m else None


def main():
    rows = {r['year'] + '#' + r['no']: r for r in
            csv.DictReader(open(os.path.join(DS, 'roster_new_raw.csv'), encoding='utf-8'))}
    bad = []
    for line in open(OUT, encoding='utf-8'):
        d = json.loads(line)
        if d['status'].startswith(('not_found', 'ambiguous', 'error')):
            bad.append(d['key'])
    print('拾い直す:', bad)
    for key in bad:
        r = rows[key]
        dam = re.sub(r'の\d\d$', '', r['name'])
        picked = None
        for v in variants(dam):
            hid = single_hit(v)
            if hid:
                p = ped(hid)
                if p.get('dam_nk', '').replace(' ', '') in (v, dam, v.replace('Ⅱ', ''),
                                                            dam.replace('Ⅱ', '')):
                    picked = hid
                    break
                print('  候補の母が違う:', key, hid, p.get('dam_nk'))
        out = {'key': key, 'year': r['year'], 'no': r['no'], 'boshu_name': r['name'],
               'dam': dam, 'status': 'not_found_again'}
        if picked:
            out.update(parse_horse(picked))
            out.update(ped(picked))
            out['breeder'] = breeder(picked)
            out['status'] = 'ok_fixup'
        print(key, r['name'], '->', out['status'], out.get('reg_name', ''))
        with open(OUT, 'a', encoding='utf-8') as f:
            f.write(json.dumps(out, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()

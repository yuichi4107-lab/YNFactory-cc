# -*- coding: utf-8 -*-
"""2023年度募集（22年産）を、クラブ公式の一次情報で埋める。

  募集馬カタログ・動画ページ … 予定厩舎・総額・1口・性・毛色・生月日・母の父
    https://carrotclub.net/movie/bosyuba2023LineupAll.html
  測尺・予定育成牧場一覧表PDF … 体高・胸囲・管囲・馬体重・育成牧場
    https://carrotclub.net/pdf/202308Size.pdf

出力: datasets/club_2023.csv
"""
import csv
import io
import os
import re
import sys
import urllib.request

import pdfplumber

from srcfetch import get, tables

BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')
PDF = os.path.join(BASE, 'src_cache', 'pdf', '2023_size.pdf')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def norm_name(s):
    s = s.replace('　', '').replace(' ', '').strip()
    s = re.sub(r'^[（(]?[外地][）)]', '', s)
    s = s.replace('II', 'Ⅱ')
    return re.sub(r'の20(\d\d)$', r'の\1', s)


def catalog():
    out = {}
    for rows in tables(get('https://carrotclub.net/movie/bosyuba2023LineupAll.html'), min_rows=2):
        hdr = rows[0]
        if not hdr or hdr[0] != 'No.':
            continue
        for r in rows[1:]:
            if len(r) < 9 or not r[0].strip().isdigit():
                continue
            sire_bms = r[2]
            m = re.match(r'(.+?)[（(](.+)[）)]\s*$', sire_bms)
            sire, bms = (m.group(1), m.group(2)) if m else (sire_bms, '')
            md = re.match(r'(\d+)/(\d+)', r[5])
            # 価格は「総額」「1口」の2セル。行によって位置がずれるので数字セルを拾う
            nums = [c.replace(',', '') for c in r[7:] if re.fullmatch(r'[\d,]+\.?\d*', c.strip())]
            total = float(nums[0]) if nums else None
            unit = float(nums[1]) if len(nums) > 1 else None
            out[norm_name(r[1])] = {
                'no': r[0].strip(), 'sire': sire.lstrip('*'), 'bms': bms.lstrip('*'),
                'sex': '牡' if r[3].strip() == '牡' else 'メス', 'coat': r[4].strip(),
                'birth': '2022-%02d-%02d' % (int(md.group(1)), int(md.group(2))) if md else '',
                'trainer': r[6].strip(), 'total_man': total, 'unit_man': unit,
                'kuchi': round(total / unit) if (total and unit) else '',
            }
    return out


def size_pdf():
    if not os.path.exists(PDF):
        os.makedirs(os.path.dirname(PDF), exist_ok=True)
        req = urllib.request.Request('https://carrotclub.net/pdf/202308Size.pdf',
                                     headers={'User-Agent': 'Mozilla/5.0'})
        open(PDF, 'wb').write(urllib.request.urlopen(req, timeout=60).read())
    out = {}
    with pdfplumber.open(PDF) as pdf:
        for page in pdf.pages:
            for tb in page.extract_tables():
                for r in tb:
                    if not r or not (r[0] or '').strip().isdigit():
                        continue
                    out[norm_name(r[1])] = {
                        'height': r[2], 'girth': r[3], 'cannon': r[4],
                        'weight': r[5], 'ikusei': (r[6] or '').strip(),
                    }
    return out


def main():
    cat = catalog()
    siz = size_pdf()
    print('カタログ表', len(cat), '頭 / 測尺PDF', len(siz), '頭')
    print('カタログのみ:', sorted(set(cat) - set(siz)))
    print('測尺のみ:', sorted(set(siz) - set(cat)))
    fields = ['name', 'no', 'sire', 'bms', 'sex', 'coat', 'birth', 'trainer', 'total_man',
              'unit_man', 'kuchi', 'height', 'girth', 'cannon', 'weight', 'ikusei']
    out = os.path.join(DS, 'club_2023.csv')
    names = sorted(set(cat) | set(siz), key=lambda n: int((cat.get(n) or {}).get('no') or 999))
    with open(out, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        for n in names:
            d = {'name': n}
            d.update(cat.get(n) or {})
            d.update(siz.get(n) or {})
            w.writerow({k: d.get(k, '') for k in fields})
    print('書き出し:', out, len(names), '頭')
    k = [d['kuchi'] for d in cat.values()]
    from collections import Counter
    print('口数:', Counter(k))


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""2023・2024年度募集（22年産・23年産）の募集馬ロスターを組む。

背骨（＝実際に募集された馬）は「なんでも競馬レビュー」の確定リスト。
  2023年度(8/10版) … 募集名・父・性・総額・一口
  2024年度(9/9版)  … 募集名・父・性・提供・一口・厩舎・体高・胸囲・管囲・体重
クラブ公式の「募集予定馬一覧（7/1現在）」から母の父・毛色・生月日・提供牧場を補う。
公式は予定版なので、確定リストと入れ替わった馬は突合レポートに出す。

出力: datasets/roster_new_raw.csv
"""
import csv
import io
import os
import re
import sys

from srcfetch import get, tables

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')

CLUB = {2023: 'https://carrotclub.net/club/2023_bosyuyoteiba.html',
        2024: 'https://carrotclub.net/club/2024_bosyuyoteiba.html'}
SK = {2023: 'https://sports-keiba.com/2023/08/10/23car_list/',
      2024: 'https://sports-keiba.com/2024/09/09/24car_list0701/'}
BORN = {2023: 2022, 2024: 2023}


def norm_name(s):
    """募集名を『母名の22』形式に揃える。外国産の (外) 表記と II/Ⅱ 揺れを吸収。"""
    s = s.replace('　', '').replace(' ', '').strip()
    s = re.sub(r'^[（(]?外[）)]', '', s)
    s = s.replace('II', 'Ⅱ').replace('Ⅱ', 'Ⅱ')
    s = re.sub(r'の20(\d\d)$', r'の\1', s)
    return s


def club_rows(year):
    out = {}
    for r in tables(get(CLUB[year]))[0][1:]:
        if len(r) < 8 or not r[0].isdigit():
            continue
        m = re.match(r'(\d+)月(\d+)日', r[6])
        out[norm_name(r[1])] = {
            'club_no': r[0], 'club_name': r[1], 'bms': r[3], 'coat': r[5],
            'birth': f'{BORN[year]}-{int(m.group(1)):02d}-{int(m.group(2)):02d}' if m else '',
            'farm': r[7],
        }
    return out


def sk_rows(year):
    rows = tables(get(SK[year]))[0]
    hdr = rows[0]
    out = []
    for r in rows[1:]:
        if len(r) < len(hdr) or not r[0].strip().isdigit():
            continue
        d = dict(zip(hdr, r))
        rec = {'no': d['No.'].strip(), 'name': norm_name(d['募集予定']),
               'raw_name': d['募集予定'].strip(), 'sire': d['父'].strip(),
               'sex': '牡' if d['性'].strip() == '牡' else 'メス'}
        if '総額' in d:
            rec['total_man'] = d['総額'].replace(',', '').strip()
        if '一口' in d:
            rec['unit_man'] = d['一口'].replace(',', '').strip()
        for a, b in [('厩舎', 'trainer'), ('体高', 'height'), ('胸囲', 'girth'),
                     ('管囲', 'cannon'), ('体重', 'weight'), ('提供', 'farm_sk')]:
            if a in d:
                rec[b] = d[a].strip()
        out.append(rec)
    return out


FIELDS = ['year', 'born', 'no', 'name', 'raw_name', 'sire', 'bms', 'sex', 'coat', 'birth',
          'farm', 'farm_sk', 'total_man', 'unit_man', 'trainer', 'height', 'girth',
          'cannon', 'weight', 'club_no', 'src_note']

rows_all = []
for year in (2023, 2024):
    club = club_rows(year)
    sk = sk_rows(year)
    hit = 0
    for r in sk:
        d = {'year': year, 'born': BORN[year], 'src_note': ''}
        d.update(r)
        c = club.get(r['name'])
        if c:
            hit += 1
            d.update({k: v for k, v in c.items() if k in FIELDS})
        else:
            d['src_note'] = 'クラブ7/1一覧に無し(生月日・母父・提供牧場はnetkeibaで補完)'
        rows_all.append(d)
    dropped = sorted(set(club) - {r['name'] for r in sk})
    print(f'--- {year}年度募集（{BORN[year]}年産） 確定リスト {len(sk)}頭 / '
          f'クラブ7/1一覧 {len(club)}頭 / 突合 {hit}頭')
    print('   確定リストに無い（＝募集取り下げ等）:', dropped)
    print('   クラブ7/1一覧に無い（＝差し替え・追加）:',
          sorted({r['name'] for r in sk} - set(club)))

with open(os.path.join(DS, 'roster_new_raw.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction='ignore')
    w.writeheader()
    for d in rows_all:
        w.writerow({k: d.get(k, '') for k in FIELDS})
print('\n書き出し:', os.path.join(DS, 'roster_new_raw.csv'), len(rows_all), '頭')

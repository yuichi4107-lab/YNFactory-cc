# -*- coding: utf-8 -*-
"""募集総額を一口馬主DB（umadb）と突き合わせて検算する。

2024年度募集は「なんでも競馬レビュー」の一口価格しか無く、総額を
  中央 = 一口 × 400口 ／ 地方 = 一口 × 100口
で復元している。この復元が正しいかを、別ソースの募集価格で確かめる。
"""
import csv
import io
import os
import re
import sys

from srcfetch import get

BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def umadb(born):
    """馬名 → 募集価格(万円)。"""
    html = get(f'https://www.umadb.com/umalist/c105/y{born}/')
    out = {}
    for tr in re.findall(r'<tr.*?</tr>', html, re.S):
        cells = [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', c)).replace('\xa0', ' ').strip()
                 for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.S)]
        # [順位, 回収率, クラブ名, 馬名, 性齢, 募集価格, 獲得金, 戦績, クラス, 厩舎, 生産牧場]
        if len(cells) < 11 or 'キャロット' not in cells[2]:
            continue
        m = re.fullmatch(r'([\d,]+)万', cells[5])
        if m:
            out[cells[3]] = float(m.group(1).replace(',', ''))
    return out


def main():
    panel = list(csv.DictReader(open(os.path.join(DS, 'panel5.csv'), encoding='utf-8-sig')))
    for year, born in [(2023, 2022), (2024, 2023), (2022, 2021)]:
        ref = umadb(born)
        rows = [r for r in panel if r['year'] == str(year) and r['reg_name']]
        hit = ok = 0
        bad = []
        for r in rows:
            nm = r['reg_name'].split(' (')[0].strip()
            if nm not in ref:
                continue
            hit += 1
            if abs(ref[nm] - float(r['total_man'])) < 1:
                ok += 1
            else:
                bad.append((r['name'], nm, r['total_man'], ref[nm]))
        print(f'{year}年度募集: umadbと突合できた {hit}頭 / 総額一致 {ok}頭')
        for b in bad[:10]:
            print('   相違', b)


if __name__ == '__main__':
    main()

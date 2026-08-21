# -*- coding: utf-8 -*-
"""netkeiba 馬ページから 父・母・生産者 を追加で取る。"""
import re

from scrape_results import get


def parse_extra(hid):
    html = get(f'https://db.netkeiba.com/horse/{hid}/')

    def field(label):
        m = re.search(re.escape(label) + r'</th>\s*<td[^>]*>(.*?)</td>', html, re.S)
        return re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else ''

    sire = sire_id = dam = dam_id = ''
    m = re.search(r'<td[^>]*rowspan="2"[^>]*class="b_ml"[^>]*>\s*<a href="/horse/(\w+)/?"[^>]*>([^<]+)', html)
    if m:
        sire_id, sire = m.group(1), m.group(2).strip()
    m = re.search(r'<td[^>]*rowspan="2"[^>]*class="b_fml"[^>]*>\s*<a href="/horse/(\w+)/?"[^>]*>([^<]+)', html)
    if m:
        dam_id, dam = m.group(1), m.group(2).strip()
    return {'sire_nk': sire, 'sire_id': sire_id, 'dam_nk': dam, 'dam_id': dam_id,
            'breeder': field('生産者'), 'birth_nk': field('生年月日'),
            'sex_nk': '', 'sale': field('セリ取引価格')}


def dam_born(dam_id):
    """母の生年。netkeibaのIDは日本産なら先頭4桁が生年。"""
    if not dam_id:
        return None
    if dam_id[:4].isdigit():
        return int(dam_id[:4])
    html = get(f'https://db.netkeiba.com/horse/{dam_id}/')
    m = re.search(r'生年月日</th>\s*<td[^>]*>(.*?)</td>', html, re.S)
    if m:
        y = re.search(r'(\d{4})年', re.sub(r'<[^>]+>', '', m.group(1)))
        if y:
            return int(y.group(1))
    return None

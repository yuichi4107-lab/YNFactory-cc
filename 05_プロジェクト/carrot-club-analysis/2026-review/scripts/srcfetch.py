# -*- coding: utf-8 -*-
"""外部ソースのHTML取得とテーブル抽出（キャッシュ付き）。"""
import hashlib
from html import unescape
import os
import re
import time
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, 'src_cache')
os.makedirs(CACHE, exist_ok=True)


def get(url):
    p = os.path.join(CACHE, hashlib.md5(url.encode()).hexdigest() + '.html')
    if os.path.exists(p):
        return open(p, encoding='utf-8').read()
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    raw = urllib.request.urlopen(req, timeout=60).read()
    html = None
    for enc in ('utf-8', 'cp932', 'euc-jp'):
        try:
            html = raw.decode(enc)
            break
        except Exception:
            pass
    if html is None:
        html = raw.decode('utf-8', 'replace')
    open(p, 'w', encoding='utf-8').write(html)
    time.sleep(1.0)
    return html


def tables(html, min_rows=5):
    out = []
    for tb in re.findall(r'<table.*?</table>', html, re.S):
        rows = []
        for tr in re.findall(r'<tr.*?</tr>', tb, re.S):
            cells = [re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]+>', '', c))).replace('\xa0', ' ').strip()
                     for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.S)]
            if cells:
                rows.append(cells)
        if len(rows) >= min_rows:
            out.append(rows)
    return out

# -*- coding: utf-8 -*-
"""厩舎名の表記を年度またぎで揃える。

クラブの募集資料は姓だけ（『木村』『奥村武』）、なんでも競馬レビューは
フルネーム（『木村 哲也』）。同じ厩舎が別物として集計されないように、
姓 → フルネーム の対応表を作って寄せる。

対応表の作り方
  1. 2024年度募集（レビュー＝フルネーム）と2026年度募集リストのフルネームを集める
  2. netkeiba の現厩舎名も候補に入れる（転厩していない馬に限る）
  3. 姓に対してフルネーム候補が1つに決まるものだけ寄せる。複数残るものは姓のまま
"""
import csv
import os
import re
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')
DATA = os.path.join(BASE, '..', '..', 'data')


def full_name_pool():
    pool = set()
    p = os.path.join(DATA, 'bosyu_2026.csv')
    if os.path.exists(p):
        for r in csv.DictReader(open(p, encoding='utf-8-sig')):
            t = (r.get('厩舎') or '').replace(' ', '').strip()
            if t and len(t) >= 3:
                pool.add(t)
    p = os.path.join(DS, 'roster_new_raw.csv')
    if os.path.exists(p):
        for r in csv.DictReader(open(p, encoding='utf-8')):
            t = (r.get('trainer') or '').replace(' ', '').strip()
            if t and len(t) >= 3 and not re.search(r'門別|南関|地方', t):
                pool.add(t)
    return pool


def build_map(panel_rows):
    """姓 → フルネーム。panel_rows は panel5.csv の辞書リスト。"""
    pool = full_name_pool()
    # netkeibaの現厩舎も候補に足す（予定厩舎の姓で始まるものだけ＝転厩していない馬）
    for r in panel_rows:
        planned = (r.get('trainer_planned') or '').replace(' ', '')
        now = (r.get('trainer') or '').replace(' ', '')
        if planned and now and now.startswith(planned) and len(now) >= 3:
            pool.add(now)
    cand = defaultdict(set)
    for full in pool:
        for n in range(1, len(full)):
            cand[full[:n]].add(full)
    m = {sur: sorted(fs)[0] for sur, fs in cand.items() if len(fs) == 1}
    m.update({full: full for full in pool})   # フルネームはそのまま通す
    return m


def resolve(name, mapping, now=''):
    """姓をフルネームに寄せる。now は同じ馬のnetkeiba現厩舎（あれば手掛かりに使う）。"""
    n = (name or '').replace(' ', '').strip()
    if not n:
        return ''
    if re.search(r'門別|南関|地方', n):
        return '地方'
    if n in mapping:
        return mapping[n]
    now = (now or '').replace(' ', '').strip()
    if now.startswith(n) and len(now) > len(n):
        return now          # 転厩していない馬なら現厩舎名がそのまま答え
    return n


def resolve_all(rows, mapping):
    """パネル全体を2周して、同姓が1人に決まるものを後から埋める。"""
    first = [resolve(r.get('trainer_planned'), mapping, r.get('trainer')) for r in rows]
    learned = {}
    for r, v in zip(rows, first):
        sur = (r.get('trainer_planned') or '').replace(' ', '').strip()
        if sur and v != sur and v.startswith(sur):
            learned.setdefault(sur, set()).add(v)
    extra = {s: next(iter(v)) for s, v in learned.items() if len(v) == 1}
    done = set(mapping.values()) | {'地方'}
    return [v if v in done else extra.get(v, v) for v in first]

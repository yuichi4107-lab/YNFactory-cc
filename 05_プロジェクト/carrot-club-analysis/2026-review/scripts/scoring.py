# -*- coding: utf-8 -*-
"""スコア基準の定義を1か所に置く。

datasets/criteria.json を読んで、募集馬1頭ぶんの辞書から点数と内訳を出す。
分析側（derive/backtest）と成果物側（Excel更新）で同じ定義を使うためのもの。
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')
PATH = os.path.join(DS, 'criteria.json')


def load_criteria(path=PATH):
    return json.load(open(path, encoding='utf-8'))


def value(row, col):
    """パネル／2026募集リストの両方から同じ意味の値を取り出す。"""
    if col == 'male':
        return 1 if str(row.get('sex', '')).startswith('牡') else 0
    if col == 'nf':
        return 1 if 'ノーザン' in str(row.get('farm', '')) else 0
    v = row.get(col)
    if v in (None, ''):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def score(row, criteria=None):
    """(点数, 内訳文字列, 欠測の基準数) を返す。"""
    crit = criteria or load_criteria()
    pts, hits, missing = 0, [], 0
    for c in crit['criteria']:
        v = value(row, c['col'])
        if v is None:
            missing += 1
            continue
        if c['lo'] <= v <= c['hi']:
            pts += 1
            hits.append(c['short'])
    return pts, '・'.join(hits), missing

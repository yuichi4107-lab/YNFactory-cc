# -*- coding: utf-8 -*-
"""2020〜2024年度募集の5年ぶんを1枚のパネルに束ねる。

  2020〜2022年度 … datasets/roster.csv ＋ final_results(_2026-08).json
  2023〜2024年度 … datasets/roster_new_raw.csv ＋ results_new.jsonl

出力: datasets/panel5.csv
"""
import csv
import io
import json
import os
import re
import sys
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

FIELDS = ['year', 'born', 'no', 'name', 'reg_name', 'horse_id', 'sire', 'sex', 'birth',
          'month', 'farm', 'farm_src', 'dam', 'dam_age', 'total_man', 'unit_man', 'weight',
          'height', 'girth', 'cannon', 'kuchi', 'n_foals', 'trainer_planned', 'trainer', 'district', 'starts',
          'wins', 'prize_jra', 'prize_nar', 'prize', 'ret', 'main_wins', 'graded', 'status']


def split_trainer(s):
    """netkeibaの『萩原清 (美浦)』を氏名と所属に割る。"""
    m = re.match(r'\s*([^\s(（]+)\s*[（(]([^）)]*)[）)]', s or '')
    if m:
        return m.group(1), m.group(2)
    return (s or '').strip(), ''


def num(v, d=None):
    try:
        return float(str(v).replace(',', '').strip())
    except Exception:
        return d


def is_graded(main):
    """主な勝鞍が重賞かどうか。netkeibaの表記は (G1) (GIII) (JpnII) など。"""
    return bool(re.search(r'\((G|Jpn|L)\s*[IV0-9]', main or ''))


def norm_farm(s):
    s = (s or '').replace('＊', '').replace('*', '').strip()
    for key, label in [('ノーザン', 'ノーザンＦ'), ('白老', '白老Ｆ'), ('追分', '追分Ｆ'),
                       ('レイクヴィラ', 'レイクヴィラＦ')]:
        if key in s:
            return label
    return s or '不明'


rows = []

# ---- 2020〜2022年度 -------------------------------------------------
base_path = os.path.join(DS, 'final_results.json')
res_path = os.path.join(DS, 'final_results_2026-08.json')
base = json.load(open(base_path, encoding='utf-8'))
res = base
if os.path.exists(res_path):
    fresh = json.load(open(res_path, encoding='utf-8'))
    if len(fresh) == len(base):        # 取り直しが途中のファイルは使わない
        res = fresh
    else:
        print(f'※ 取り直しが途中（{len(fresh)}/{len(base)}）なので旧ファイルを使う')
        res_path = base_path
print('旧3年の成績ソース:', os.path.basename(res_path))
for r in csv.DictReader(open(os.path.join(DS, 'roster.csv'), encoding='utf-8')):
    key = r['year'] + '#' + r['no']
    v = res.get(key) or {}
    tot = num(r['total_man'])
    prize = (v.get('prize_jra') or 0) + (v.get('prize_nar') or 0)
    rows.append({
        'year': r['year'], 'born': r['born'], 'no': r['no'], 'name': r['name'],
        'reg_name': v.get('reg_name', ''), 'horse_id': v.get('horse_id', ''),
        'sire': r['sire'], 'sex': '牡' if r['sex'] == '牡' else 'メス',
        'birth': r['birth'], 'month': int(r['birth'][5:7]),
        'farm': norm_farm(r['farm']), 'farm_src': 'クラブ提供牧場',
        'dam': r['dam'], 'dam_age': num(r['dam_age']), 'total_man': tot,
        'unit_man': num(r['unit_yen'], 0) / 10000 if r['unit_yen'] else '',
        'weight': num(r['weight']), 'height': num(r['height']), 'girth': num(r['girth']),
        'cannon': num(r['cannon']),
        'kuchi': round(tot * 10000 / num(r['unit_yen'])) if num(r['unit_yen']) else '',
        'n_foals': num(r['n_foals']),
        'trainer_planned': r['trainer'],
        'trainer': split_trainer(v.get('trainer_now', ''))[0],
        'district': split_trainer(v.get('trainer_now', ''))[1],
        'starts': v.get('starts'), 'wins': v.get('wins'),
        'prize_jra': v.get('prize_jra'), 'prize_nar': v.get('prize_nar'),
        'prize': prize, 'ret': prize / tot if tot else '',
        'main_wins': v.get('main_wins', ''), 'graded': int(is_graded(v.get('main_wins'))),
        'status': v.get('status', ''),
    })

# ---- 2023〜2024年度 -------------------------------------------------
# 2023年度はクラブ公式のカタログ表と測尺PDFがあるので、そちらを優先する
club23 = {}
p23 = os.path.join(DS, 'club_2023.csv')
if os.path.exists(p23):
    for r in csv.DictReader(open(p23, encoding='utf-8-sig')):
        club23[r['name']] = r

foals = {}
pf = os.path.join(DS, 'foal_order.json')
if os.path.exists(pf):
    foals = json.load(open(pf, encoding='utf-8'))

newres = {}
p = os.path.join(DS, 'results_new.jsonl')
if os.path.exists(p):
    for line in open(p, encoding='utf-8'):
        try:
            d = json.loads(line)
            newres[d['key']] = d
        except Exception:
            pass
for r in csv.DictReader(open(os.path.join(DS, 'roster_new_raw.csv'), encoding='utf-8')):
    key = r['year'] + '#' + r['no']
    v = newres.get(key) or {}
    c = club23.get(r['name']) if r['year'] == '2023' else None
    if c:
        # クラブ公式（カタログ表＋測尺PDF）で上書き。空欄は元のまま残す。
        for src, dst in [('trainer', 'trainer'), ('total_man', 'total_man'),
                         ('unit_man', 'unit_man'), ('height', 'height'), ('girth', 'girth'),
                         ('cannon', 'cannon'), ('weight', 'weight'), ('birth', 'birth'),
                         ('sex', 'sex'), ('coat', 'coat'), ('bms', 'bms'), ('sire', 'sire')]:
            if c.get(src):
                r[dst] = c[src]
        # 育成牧場(ikusei)は提供・生産牧場とは別物なので farm には流用しない
    unit = num(r['unit_man'])
    tot = num(r['total_man'])
    if tot is None and unit is not None:
        # 地方入厩予定馬は100口、中央は400口。厩舎欄が門別・南関なら地方とみなす。
        chihou = re.search(r'門別|南関|地方', r.get('trainer') or '')
        tot = unit * (100 if chihou else 400)
    dam_born = v.get('dam_born')
    dam_age = (int(r['born']) - dam_born) if dam_born else None
    prize = (v.get('prize_jra') or 0) + (v.get('prize_nar') or 0)
    farm = r['farm'] or r['farm_sk'] or v.get('breeder', '')
    if r['farm']:
        farm_src = 'クラブ提供牧場'
    elif r['farm_sk']:
        farm_src = 'レビュー提供欄'
    else:
        farm_src = 'netkeiba生産者'
    rows.append({
        'year': r['year'], 'born': r['born'], 'no': r['no'], 'name': r['name'],
        'reg_name': v.get('reg_name', ''), 'horse_id': v.get('horse_id', ''),
        'sire': r['sire'], 'sex': r['sex'],
        'birth': r['birth'] or v.get('birth_full', ''), 'month': '',
        'farm': norm_farm(farm), 'farm_src': farm_src,
        'dam': re.sub(r'の\d\d$', '', r['name']), 'dam_age': dam_age, 'total_man': tot,
        'unit_man': unit, 'weight': num(r['weight']), 'height': num(r['height']),
        'girth': num(r['girth']), 'cannon': num(r['cannon']),
        'kuchi': round(tot / unit) if (tot and unit) else '',
        'n_foals': (foals.get(key) or {}).get('n_foals'),
        'trainer_planned': (r.get('trainer') or '').replace(' ', ''),
        'trainer': split_trainer(v.get('trainer_now', ''))[0],
        'district': split_trainer(v.get('trainer_now', ''))[1],
        'starts': v.get('starts'), 'wins': v.get('wins'),
        'prize_jra': v.get('prize_jra'), 'prize_nar': v.get('prize_nar'),
        'prize': prize, 'ret': prize / tot if tot else '',
        'main_wins': v.get('main_wins', ''), 'graded': int(is_graded(v.get('main_wins'))),
        'status': v.get('status', ''),
    })

# 生月：クラブ一覧に載っていない馬は netkeiba の生年月日から埋める
for d in rows:
    if not d['month']:
        b = str(d['birth'])
        m = re.search(r'(\d{4})年(\d+)月(\d+)日', b) or re.search(r'(\d{4})-(\d+)-(\d+)', b)
        if m:
            d['month'] = int(m.group(2))
            d['birth'] = '%s-%02d-%02d' % (m.group(1), int(m.group(2)), int(m.group(3)))

out = os.path.join(DS, 'panel5.csv')
with open(out, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction='ignore')
    w.writeheader()
    for d in rows:
        w.writerow({k: d.get(k, '') for k in FIELDS})

print('書き出し:', out, len(rows), '頭')
print('年度別:', dict(sorted(Counter(d['year'] for d in rows).items())))
print('未突合:', sum(1 for d in rows if not d['horse_id']))
for f in ('weight', 'dam_age', 'total_man', 'month', 'trainer', 'trainer_planned'):
    print('  %s 欠測: %d' % (f, sum(1 for d in rows if d.get(f) in (None, '', 0))))

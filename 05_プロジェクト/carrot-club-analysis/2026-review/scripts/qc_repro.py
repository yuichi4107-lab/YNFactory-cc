# -*- coding: utf-8 -*-
"""既存3年（2020〜2022年度募集）の公表値を再現できるか確かめる。"""
import csv
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def num(v, d=None):
    try:
        return float(str(v).replace(',', ''))
    except Exception:
        return d


roster = {f"{r['year']}#{r['no']}": r for r in
          csv.DictReader(open(os.path.join(DS, 'roster.csv'), encoding='utf-8'))}
res = json.load(open(os.path.join(DS, 'final_results.json'), encoding='utf-8'))

rows = []
for k, r in roster.items():
    v = res.get(k) or {}
    tot = num(r['total_man'])
    prize = (v.get('prize_jra') or 0) + (v.get('prize_nar') or 0)
    rows.append(dict(year=r['year'], name=r['name'], sex=r['sex'], month=int(r['birth'][5:7]),
                     farm=r['farm'], dam_age=num(r['dam_age']), total=tot,
                     weight=num(r['weight']), wins=v.get('wins') or 0,
                     starts=v.get('starts') or 0, prize=prize,
                     ret=prize / tot if tot else None, trainer=r['trainer'],
                     matched=bool(v.get('horse_id')), main=v.get('main_wins', '')))

print('roster', len(rows), '/ netkeiba突合済み', sum(1 for x in rows if x['matched']))
print('馬体重欠測', sum(1 for x in rows if x['weight'] is None),
      '/ 母年齢欠測', sum(1 for x in rows if x['dam_age'] is None))


def rate(sub, f):
    return f'{100 * sum(1 for x in sub if f(x)) / len(sub):.0f}% (n={len(sub)})' if sub else '-'


win = lambda x: x['wins'] >= 1          # noqa: E731
ret1 = lambda x: x['ret'] is not None and x['ret'] >= 1   # noqa: E731

print('\n■全体   勝ち上がり', rate(rows, win), ' 回収≥1', rate(rows, ret1),
      ' 重賞', sum(1 for x in rows if 'Ｇ' in (x['main'] or '') or 'G' in (x['main'] or '')))
print('\n■性別')
for key, f in [('牡', lambda x: x['sex'] == '牡'), ('メス', lambda x: x['sex'] != '牡')]:
    s = [x for x in rows if f(x)]
    print(' ', key, rate(s, win), rate(s, ret1))
print('\n■生まれ月')
for m in range(1, 7):
    s = [x for x in rows if x['month'] == m]
    if s:
        print(f'  {m}月', rate(s, win), rate(s, ret1))
print('\n■生産')
for key, f in [('ノーザンＦ系', lambda x: 'ノーザン' in x['farm']),
               ('その他', lambda x: 'ノーザン' not in x['farm'])]:
    s = [x for x in rows if f(x)]
    print(' ', key, rate(s, win), rate(s, ret1))
print('\n■母年齢')
for lo, hi in [(0, 7), (8, 11), (12, 15), (16, 30)]:
    s = [x for x in rows if x['dam_age'] is not None and lo <= x['dam_age'] <= hi]
    print(f'  {lo}-{hi}歳', rate(s, win), rate(s, ret1))
print('\n■募集総額')
for lo, hi in [(0, 2499), (2500, 3999), (4000, 5999), (6000, 7999), (8000, 999999)]:
    s = [x for x in rows if lo <= x['total'] <= hi]
    print(f'  {lo}-{hi}万', rate(s, win), rate(s, ret1))
print('\n■募集時馬体重')
for lo, hi in [(0, 429.9), (430, 459.9), (460, 9999)]:
    s = [x for x in rows if x['weight'] is not None and lo <= x['weight'] <= hi]
    print(f'  {lo}-{hi}kg', rate(s, win), rate(s, ret1))
print('\n■年度別')
for y in ('2020', '2021', '2022'):
    s = [x for x in rows if x['year'] == y]
    print(' ', y, rate(s, win), rate(s, ret1))

# -*- coding: utf-8 -*-
"""母の競走成績と、クラブ外を含む全兄姉の実績を取る。

いまのパネルは母について「産駒誕生時の馬齢」しか持っておらず、
母の質を測る変数が無い。7方向の洗い直しでも、母まわりの候補が軒並み
「母年齢という代理変数が粗すぎる」で終わっていた。そこを埋める。

取るもの
  1. 各馬の母ID・父ID（2020〜2022年度は血統ページから。2023〜2024年度は取得済み）
  2. 母自身の競走成績（母の馬ページ）
  3. 母の全産駒＝兄姉（母名検索。1リクエストで全産駒の生年・父・総賞金が返る）

出力: datasets/family.json
  {"dams": {dam_id: {...母の成績..., "sibs": [{name, sex, born, sire, prize}]}},
   "horses": {"2020#1": {"dam_id":..., "sire_id":..., "sire_name":...}}}

注意: 外国産の母は netkeiba に日本での戦績しか無く、海外で走っていても
0戦0勝に見える。foreign フラグを立てて分析側で「未出走」と区別する。
"""
import csv
import io
import json
import os
import re
import sys
import urllib.parse

from scrape_results import get, parse_horse

BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')
OUT = os.path.join(DS, 'family.json')
if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def ped(hid):
    html = get(f'https://db.netkeiba.com/horse/ped/{hid}/')
    out = {}
    for m in re.finditer(r'<td[^>]*rowspan="16"[^>]*class="(b_ml|b_fml)"[^>]*>(.*?)</td>', html, re.S):
        blk = m.group(2)
        a = re.search(r'/horse/(\w+)/"[^>]*>\s*([^<\r\n]+)', blk)
        y = re.search(r'<br\s*/?>\s*(\d{4})', blk)
        key = 'sire' if m.group(1) == 'b_ml' else 'dam'
        if a:
            out[key + '_id'] = a.group(1)
            out[key + '_name'] = a.group(2).strip()
        if y:
            out[key + '_born'] = int(y.group(1))
    return out


def mare_rows(name):
    """母名検索。産駒1頭1行で 馬名・性・生年・父・母・母父・総賞金 が返る。"""
    try:
        q = name.encode('euc-jp')
    except UnicodeEncodeError:
        return []
    url = 'https://db.netkeiba.com/?' + urllib.parse.urlencode(
        {'pid': 'horse_list', 'mare': q, 'list': '100'})
    html = get(url)
    out = []
    for tr in re.findall(r'<tr.*?</tr>', html, re.S):
        c = [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', x)).replace('\xa0', ' ').strip()
             for x in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.S)]
        if len(c) < 13 or not re.fullmatch(r'\d{4}', c[4] or ''):
            continue
        try:
            prize = float(c[12].replace(',', ''))
        except ValueError:
            prize = None
        out.append({'name': c[2], 'sex': c[3], 'born': int(c[4]), 'sire': c[7],
                    'dam': c[8], 'bms': c[9], 'prize': prize})
    return out


def is_graded(main):
    return bool(re.search(r'\((G|Jpn)\s*[IV0-9]', main or ''))


def main():
    panel = list(csv.DictReader(open(os.path.join(DS, 'panel5.csv'), encoding='utf-8-sig')))
    newres = {}
    p = os.path.join(DS, 'results_new.jsonl')
    for line in open(p, encoding='utf-8'):
        d = json.loads(line)
        if d.get('dam_id'):
            newres[d['key']] = d
    alias = {}
    pa = os.path.join(DS, 'dam_alias.csv')
    if os.path.exists(pa):
        alias = {r['name']: r['dam_alias'] for r in csv.DictReader(open(pa, encoding='utf-8'))}

    data = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {'dams': {}, 'horses': {}}
    dams, horses = data['dams'], data['horses']

    # ---- 1. 各馬の母ID・父ID ------------------------------------------
    todo = [r for r in panel if r['horse_id'] and (r['year'] + '#' + r['no']) not in horses]
    print('母ID・父IDを引く:', len(todo), '頭', flush=True)
    for i, r in enumerate(todo):
        key = r['year'] + '#' + r['no']
        v = newres.get(key)
        try:
            if v and v.get('dam_id'):
                info = {'dam_id': v['dam_id'], 'dam_name': v.get('dam_nk', r['dam']),
                        'dam_born': v.get('dam_born'), 'sire_id': v.get('sire_id'),
                        'sire_name': v.get('sire_nk', r['sire'])}
            else:
                pd_ = ped(r['horse_id'])
                info = {'dam_id': pd_.get('dam_id'), 'dam_name': pd_.get('dam_name', r['dam']),
                        'dam_born': pd_.get('dam_born'), 'sire_id': pd_.get('sire_id'),
                        'sire_name': pd_.get('sire_name', r['sire'])}
            horses[key] = info
        except Exception as e:
            horses[key] = {'error': str(e)}
        if (i + 1) % 25 == 0:
            json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
            print(f'  {i+1}/{len(todo)}', flush=True)
    json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)

    # ---- 2. 母の競走成績 と 3. 兄姉 ------------------------------------
    need = {}
    for r in panel:
        key = r['year'] + '#' + r['no']
        h = horses.get(key) or {}
        did = h.get('dam_id')
        if did and did not in dams:
            need[did] = (h.get('dam_name') or r['dam'], alias.get(r['name']) or r['dam'])
    print('母を引く:', len(need), '頭', flush=True)
    for i, (did, (nk_name, search_name)) in enumerate(need.items()):
        rec = {'dam_id': did, 'name': nk_name, 'foreign': not did[:4].isdigit()}
        try:
            d = parse_horse(did)
            rec.update({'starts': d.get('starts'), 'wins': d.get('wins'),
                        'prize_jra': d.get('prize_jra'), 'prize_nar': d.get('prize_nar'),
                        'main_wins': d.get('main_wins'), 'graded': int(is_graded(d.get('main_wins'))),
                        'birth': d.get('birth_full')})
        except Exception as e:
            rec['error_dam'] = str(e)
        try:
            sibs = mare_rows(search_name) or mare_rows(nk_name)
            rec['sibs'] = sibs
            rec['n_bms'] = len({s['bms'] for s in sibs}) if sibs else 0
        except Exception as e:
            rec['error_sibs'] = str(e)
            rec['sibs'] = []
        dams[did] = rec
        if (i + 1) % 20 == 0:
            json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
            print(f'  {i+1}/{len(need)}', flush=True)
    json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
    print('DONE 母', len(dams), '頭 / 馬', len(horses), '頭')


if __name__ == '__main__':
    main()

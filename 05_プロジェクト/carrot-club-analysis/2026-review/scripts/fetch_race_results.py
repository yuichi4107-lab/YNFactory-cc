# -*- coding: utf-8 -*-
"""各馬の出走履歴（db.netkeiba.com/horse/result/）を取り、レース単位の要約を作る。

netkeibaの「通算成績」は中央と地方を合算しているので、それだけだと
「中央では1勝もできず地方へ移って勝った馬」も勝ち上がり扱いになる。
中央だけの勝ち上がりを数えられるようにレース単位まで降りる。

出力: datasets/race_summary.json
  { key: {jra_starts, jra_wins, nar_starts, nar_wins, first_win_date,
          first_jra_win_date, last_date, starts_by3, wins_by3, prize_by3} }
"""
import io
import json
import os
import re
import sys

from scrape_results import get

BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')
OUT = os.path.join(DS, 'race_summary.json')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

JRA = ('札幌', '函館', '福島', '新潟', '東京', '中山', '中京', '京都', '阪神', '小倉')


def cells(tr):
    return [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', c)).strip()
            for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.S)]


def summarize(hid, born):
    html = get(f'https://db.netkeiba.com/horse/result/{hid}/')
    m = re.search(r'<table[^>]*class="[^"]*db_h_race_results[^"]*".*?</table>', html, re.S)
    d = dict(jra_starts=0, jra_wins=0, nar_starts=0, nar_wins=0, first_win_date='',
             first_jra_win_date='', last_date='', starts_by3=0, wins_by3=0, prize_by3=0.0,
             rows=0)
    if not m:
        return d
    trs = re.findall(r'<tr.*?</tr>', m.group(0), re.S)
    hdr = cells(trs[0]) if trs else []
    idx = {name: i for i, name in enumerate(hdr)}
    for tr in trs[1:]:
        c = cells(tr)
        if len(c) < 12:
            continue
        date = c[idx.get('日付', 0)]
        place = c[idx.get('開催', 1)]
        rank = c[idx.get('着 順', idx.get('着順', 11))]
        prize = c[-1]
        d['rows'] += 1
        is_jra = any(p in place for p in JRA)
        won = rank.strip() == '1'
        if is_jra:
            d['jra_starts'] += 1
            d['jra_wins'] += int(won)
        else:
            d['nar_starts'] += 1
            d['nar_wins'] += int(won)
        if won:
            if not d['first_win_date'] or date < d['first_win_date']:
                d['first_win_date'] = date
            if is_jra and (not d['first_jra_win_date'] or date < d['first_jra_win_date']):
                d['first_jra_win_date'] = date
        if date > d['last_date']:
            d['last_date'] = date
        # 3歳いっぱい（＝生年+3年の12/31）までの実績
        y = int(date[:4]) if re.match(r'\d{4}', date) else 0
        if y and y <= born + 3:
            d['starts_by3'] += 1
            d['wins_by3'] += int(won)
            try:
                d['prize_by3'] += float(prize.replace(',', '')) if prize.strip() else 0.0
            except ValueError:
                pass
    return d


def main():
    import csv
    panel = list(csv.DictReader(open(os.path.join(DS, 'panel5.csv'), encoding='utf-8-sig')))
    out = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}
    todo = [r for r in panel if r['horse_id'] and f"{r['year']}#{r['no']}" not in out]
    print('対象', len(todo), '頭', flush=True)
    for i, r in enumerate(todo):
        key = f"{r['year']}#{r['no']}"
        try:
            out[key] = summarize(r['horse_id'], int(r['born']))
        except Exception as e:
            out[key] = {'error': str(e)}
        if (i + 1) % 20 == 0:
            json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
            print(f'{i+1}/{len(todo)}', flush=True)
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
    print('DONE', len(out))


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""種牡馬リーディング（年度別）を取る。父の格をクラブ外を含む母集団で測るため。

クラブ内の産駒は1父あたり中央値4〜7頭しかなく、それで作った「父の過去実績」は
z=+0.14 で潰れた。JRA全体の産駒成績なら1父あたり数十〜数百頭あるので、
同じ考え方が生き返るかを確かめられる。

リークを避けるため、募集年度Yの馬には「Y-1年の」リーディングを当てる
（募集はYの夏なので、その時点で完結している直近の年はY-1）。

出力: datasets/sire_leading.json  {year: {sire_name: {...}}}
"""
import io
import json
import os
import re
import sys

from scrape_results import get

BASE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(BASE, '..', 'datasets')
OUT = os.path.join(DS, 'sire_leading.json')
if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

YEARS = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]


def num(s):
    try:
        return float(str(s).replace(',', ''))
    except Exception:
        return None


def page(year, p):
    url = f'https://db.netkeiba.com/?pid=sire_leading&year={year}'
    if p > 1:
        url += f'&page={p}'
    html = get(url)
    out = {}
    for tr in re.findall(r'<tr.*?</tr>', html, re.S):
        c = [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', x)).replace('\xa0', ' ').strip()
             for x in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.S)]
        # [順位, 馬名, 出走頭数, 勝馬頭数, 出走回数, 勝利回数, 重賞出走, 重賞勝利, ...]
        if len(c) < 16 or not c[0].isdigit():
            continue
        runners, winners = num(c[2]), num(c[3])
        out[c[1]] = {
            'rank': int(c[0]), 'runners': runners, 'winners': winners,
            'win_horse_rate': round(winners / runners, 4) if runners else None,
            'graded_wins': num(c[7]),
        }
    return out


def main():
    data = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}
    for y in YEARS:
        key = str(y)
        if key in data and len(data[key]) >= 100:
            continue
        got = {}
        for p in (1, 2, 3):
            try:
                rows = page(y, p)
            except Exception as e:
                print(y, 'page', p, 'NG', e)
                break
            if not rows:
                break
            before = len(got)
            got.update(rows)
            if len(got) == before:      # ページ送りが効いていない
                break
        data[key] = got
        print(f'{y}年: 種牡馬 {len(got)}頭', flush=True)
        json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
    print('DONE', {k: len(v) for k, v in data.items()})


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vol3 CSV Part3: P53-P55 後付け（著者紹介・奥付）"""
import csv

def text_page(content):
    return f"◆【テキストページ】このページは画像生成不要。EPUB製本時にテキストとして直接レンダリングする。\n{content}"

pages = []

# P53: 著者紹介
pages.append([53, "テキストページ",
text_page("""◆【著者紹介】
著者紹介　Yuichi

キャリアコンサルタント／AIビジネスアドバイザー

人事と採用の分野で20年以上の経験を積み、転職・成長・転職管理に従事。

国家資格キャリアコンサルタントとして、これまで100名以上のキャリア支援を実施。

現在は、転職・育児・AIを主なテーマに情報発信を行うほか、中小企業の経営者に対してのAI活用・副業起業の支援を行っている。

非エンジニア向けのAI活用と、身近で使える「稼ぎ方のヒント」の提供を使命として、同分野の知識・ノウハウを提供している。

最新情報: info@ynfactory.online"""),
"[]", ""])

# P54: 奥付
pages.append([54, "テキストページ",
text_page("""◆【奥付】

【書名】
出産でキャリアを失った元事務職ママが、AIで初めて稼ぐまで　第3巻

【著者】
Yuichi

【発行所】
YN出版

【発行日】
2026年5月

本書の内容を無断で複製・転載・配信することを禁じます。
本書はフィクションです。登場する人名・団体の名はすべて架空のものであり、実在のものとは一切関係ありません。

© 2026 Yuichi / YN出版"""),
"[]", ""])

OUT = r"G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\vol3\panels\part3.csv"
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, quoting=csv.QUOTE_ALL)
    w.writerow(["ページ番号", "使用するコマ割りテンプレ", "漫画作成のプロンプト", "コマ別テキストJSON", "outfit_id"])
    for p in pages:
        w.writerow(p)
print(f"Part3 done: {len(pages)} pages -> {OUT}")

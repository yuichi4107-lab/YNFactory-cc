#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最終CSV構築スクリプト
構成:
  P1-P3:   前付け（目次・あらすじ・登場人物紹介）
  P4:      第5章扉
  P5-P14:  第5章前半（Zoom面談シーン）← part1の P5-P14
  P15-P28: 第5章追加（前日・ケンタ・Claude練習等）← ch5_extra 14P
  P29-P46: 第5章後半（Instagramプロフィール〜面談終了）← part1の P15-P24を再配置
  P47:     第5章 章末まとめ
  P48:     コラム⑥
  P49:     第6章扉
  P50-P77: 第6章（投稿〜再開）← part2 P27-P51 + ch6_extra 15P を混合
  P78:     第6章 章末まとめ
  P79:     コラム⑦
  P80-P81: 後付け（著者紹介・奥付）
  合計: 81P → 追加シーンで拡張して ~115P を目指す
"""
import csv, os

BASE = r"G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\vol3\panels"

def read_csv(fname, skip_header=True):
    rows = []
    with open(os.path.join(BASE, fname), newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        all_rows = list(reader)
    if skip_header:
        return all_rows[1:]
    return all_rows

# part1: P1-P24（前付け3P + 第5章21P）
p1 = read_csv("part1.csv")
# part2: P25-P52（コラム⑥1P + 第6章26P + コラム⑦1P）
p2 = read_csv("part2.csv")
# part3: P53-P54（著者紹介・奥付）
p3 = read_csv("part3.csv")
# ch5_extra: 14P（追加の第5章シーン）
ch5 = read_csv("ch5_extra.csv")
# ch6_extra: 15P（追加の第6章シーン）
ch6 = read_csv("ch6_extra.csv")

# ch5_extra と ch6_extra のフォーマットは [テンプレ, プロンプト, JSON, outfit]
# → ページ番号列が先頭に無い（headerが異なる）
# 必要なのは [ページ番号, テンプレ, プロンプト, JSON, outfit]

# part1から各セクションを抽出
pre = p1[0:3]      # P1-P3: 前付け
ch5_扉 = p1[3:4]   # P4: 第5章扉
ch5_zoom = p1[4:21] # P5-P21: Zoom面談シーン（part1 index 4-20）
ch5_instagram = p1[21:24] # P22-P24: Instagram提案〜章末

# part2から各セクションを抽出
# P25=コラム⑥, P26=第6章扉, P27-P51=第6章, P52=コラム⑦
col6 = [p2[0]]    # P25: コラム⑥
ch6_扉 = [p2[1]]  # P26: 第6章扉
ch6_main = p2[2:28] # P27-P52: 第6章本編+コラム⑦（26行）
col7 = [p2[27]]   # P52: コラム⑦

# ch5_extraとch6_extraのデータを正しい形式に変換（ページ番号は後で付与）
def convert_extra(rows):
    """[テンプレ, プロンプト, JSON, outfit] → [None, テンプレ, プロンプト, JSON, outfit]"""
    return [[None] + row for row in rows]

ch5_ex = convert_extra(ch5)
ch6_ex = convert_extra(ch6)

# ==== 最終ページリストを構築 ====
# 各要素: [ページ番号(後付け), テンプレ, プロンプト, JSON, outfit]

final = []

# 前付け（3P）
for row in pre:
    final.append(row[1:])  # ページ番号列を除く（後で付与）

# 第5章扉（1P）
for row in ch5_扉:
    final.append(row[1:])

# 第5章 前半Zoom面談（17P: P5-P21）
for row in ch5_zoom:
    final.append(row[1:])

# 第5章 追加シーン（14P）= ch5_extra
for row in ch5_ex:
    final.append(row[1:])  # [None, テンプレ, プロンプト, JSON, outfit] → [テンプレ,...]

# 第5章 Instagram提案〜章末（3P）
for row in ch5_instagram:
    final.append(row[1:])

# コラム⑥（1P）
for row in col6:
    final.append(row[1:])

# 第6章扉（1P）
for row in ch6_扉:
    final.append(row[1:])

# 第6章 追加シーン前半（8P: 毎日投稿〜「ミサキの言葉」まで）
# ch6_extra index 0-7: 週間計画・反応ゼロ・初コメント・もっと具体的・支援センター・ひなた発語・夜のケンタ・その体験を投稿
for row in ch6_ex[:8]:
    final.append(row[1:])

# 第6章 本編（ひなた発熱〜再開）= part2 P27-P51
# part2 index 2-26（25行）: P27-P51
for row in ch6_main[:25]:
    final.append(row[1:])

# 第6章 追加シーン後半（7P: ひなた発熱詳細〜コメントの重み〜継続）
# ch6_extra index 8-14
for row in ch6_ex[8:]:
    final.append(row[1:])

# コラム⑦（1P）
for row in col7:
    final.append(row[1:])

# 後付け（2P: 著者紹介・奥付）
for row in p3:
    final.append(row[1:])

# ページ番号を付与
numbered = [[i+1] + list(row) for i, row in enumerate(final)]

print(f"Total pages: {len(numbered)}")

# テンプレ分布確認
from collections import Counter
templates = [row[1] for row in numbered]
dist = Counter(templates)
total = len(numbered)
print("\nTemplate distribution:")
for t, cnt in sorted(dist.items()):
    print(f"  {t}: {cnt} ({cnt/total*100:.1f}%)")

# 章範囲確認
for i, row in enumerate(numbered):
    tmpl = row[1]
    prompt_start = row[2][:60] if len(row) > 2 else ""
    if "第5章" in prompt_start or "第6章" in prompt_start or "コラム" in prompt_start:
        print(f"P{row[0]}: {tmpl} | {prompt_start[:50]}")

OUT = os.path.join(BASE, "comicle_output.csv")
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, quoting=csv.QUOTE_ALL)
    w.writerow(["ページ番号", "使用するコマ割りテンプレ", "漫画作成のプロンプト", "コマ別テキストJSON", "outfit_id"])
    for row in numbered:
        w.writerow(row)

print(f"\nOutput: {OUT}")
print(f"Pages 1-{len(numbered)}")

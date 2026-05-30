#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merge part1.csv + part2.csv + part3.csv into comicle_output.csv"""
import csv, os

BASE = r"G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\vol3\panels"
parts = ["part1.csv", "part2.csv", "part3.csv"]
OUT = os.path.join(BASE, "comicle_output.csv")

all_rows = []
header = None
for fname in parts:
    fpath = os.path.join(BASE, fname)
    with open(fpath, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if header is None:
        header = rows[0]
    all_rows.extend(rows[1:])  # skip header for subsequent parts

print(f"Total data rows: {len(all_rows)}")

# Verify page numbers are sequential
for i, row in enumerate(all_rows):
    expected = i + 1
    actual = int(row[0])
    if actual != expected:
        print(f"WARNING: row {i} has page {actual}, expected {expected}")

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, quoting=csv.QUOTE_ALL)
    w.writerow(header)
    for row in all_rows:
        w.writerow(row)

print(f"Merged -> {OUT}")
print(f"Pages: 1 - {len(all_rows)}")

# Template distribution
from collections import Counter
templates = [r[1] for r in all_rows]
dist = Counter(templates)
total = len(all_rows)
print("\nTemplate distribution:")
for t, cnt in sorted(dist.items()):
    print(f"  {t}: {cnt} pages ({cnt/total*100:.1f}%)")

"""vol4 専用テキストページレンダラー。

vol4 の comicle_output.csv は、目次・前巻あらすじ・コラム⑧⑨⑩・著者紹介・奥付の
本文を「漫画作成のプロンプト」列に直接保持している（コラムは CSV 側で
「Nページ目」に分割済み）。本スクリプトは各テキストページ行を vol3 と同等の
整形品質（コラム番号=h2 / サブタイトル=h3 / キャリコン行=subtitle / 奥付=colophon）で
XHTML にレンダリングする。

build_vol_epub.py が text_pages/page_NNN.xhtml を取り込むため、出力先は vol4/text_pages。
"""
from __future__ import annotations

import argparse
import csv
import html
import re
import shutil
from pathlib import Path

# 行頭の指示／セクションマーカー（◆ 始まり）
INSTRUCTION_RE = re.compile(r"^◆【テキストページ】")
SECTION_RE = re.compile(r"^◆【(.+?)】")
# 「【コラム⑧】タイトル……」のように 】 の後に本文が続く見出し行
COLUMN_TITLE_RE = re.compile(r"^【(コラム[①-⑳0-9]+)】(.+)$")
# 「【書名】」「【著者】」のように 】 で閉じる単独見出し
BRACKET_HEADING_RE = re.compile(r"^【(.+?)】$")


def classify_section(prompt: str) -> tuple[str, list[str]]:
    """指示行・セクションマーカー行を除去し、(セクション種別, 本文行リスト) を返す。"""
    lines = [ln.rstrip() for ln in prompt.replace("\r\n", "\n").split("\n")]
    section = ""
    body: list[str] = []
    for ln in lines:
        if INSTRUCTION_RE.match(ln):
            continue
        m = SECTION_RE.match(ln)
        if m and not section:
            section = m.group(1)  # 例: 目次 / 前巻までのあらすじ / コラム⑧ 1ページ目 / 著者紹介 / 奥付
            continue
        body.append(ln)
    # 先頭・末尾の空行を除去
    while body and not body[0].strip():
        body.pop(0)
    while body and not body[-1].strip():
        body.pop()
    return section, body


def render_blocks(body: list[str], section: str) -> list[str]:
    is_colophon = section.startswith("奥付")
    is_author = section.startswith("著者紹介")
    blocks: list[str] = []
    for raw in body:
        line = raw.strip()
        if not line:
            continue
        esc = html.escape(line)

        col = COLUMN_TITLE_RE.match(line)
        if col:
            # 例: 【コラム⑧】承認と自己効力感——「できる」という感覚を取り戻すために
            blocks.append(f"<h2>{html.escape(col.group(1))}</h2>")
            blocks.append(f"<h3>{html.escape(col.group(2))}</h3>")
            continue

        brk = BRACKET_HEADING_RE.match(line)
        if brk:
            # 例: 【目次】【前巻（第1〜3巻）までのあらすじ】【書名】【著者】 など
            blocks.append(f"<h2>{html.escape(brk.group(1))}</h2>")
            continue

        if line.startswith("キャリアコンサルタント") and not is_author:
            blocks.append(f'<p class="subtitle">{esc}</p>')
            continue

        if is_author and line.startswith("著者紹介"):
            blocks.append(f"<h2>{esc}</h2>")
            continue

        blocks.append(f"<p>{esc}</p>")
    return blocks


def write_xhtml(out_path: Path, page_label: str, section: str, blocks: list[str]) -> None:
    klass = "colophon" if section.startswith("奥付") else "text-page"
    body_html = "\n".join(blocks)
    xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" lang="ja">
<head>
  <meta name="viewport" content="width=1024, height=1536"/>
  <link rel="stylesheet" type="text/css" href="../styles/style.css"/>
  <title>ページ {html.escape(page_label)}</title>
</head>
<body>
  <div class="{klass}">
{body_html}
  </div>
</body>
</html>
"""
    out_path.write_text(xhtml, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv-file", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    # 旧 page_*.xhtml（旧版の番号付きファイル）を一掃
    for old in out_dir.glob("page_*.xhtml"):
        old.unlink()

    count = 0
    with args.csv_file.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("使用するコマ割りテンプレ") != "テキストページ":
                continue
            page_num = int(row["ページ番号"])
            section, body = classify_section(row.get("漫画作成のプロンプト", ""))
            blocks = render_blocks(body, section)
            write_xhtml(out_dir / f"page_{page_num:03d}.xhtml", str(page_num), section, blocks)
            count += 1
            print(f"  P{page_num:>3} [{section}] -> {len(blocks)} blocks")

    print(f"TEXT_PAGES_WRITTEN: {count}")
    print(f"OUT_DIR: {out_dir}")


if __name__ == "__main__":
    main()

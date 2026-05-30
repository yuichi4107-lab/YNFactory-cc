from __future__ import annotations

import argparse
import csv
import html
import re
import shutil
from pathlib import Path


def extract_body(prompt: str) -> tuple[str, str]:
    markers = ["◆【目次】", "◆【前巻までのあらすじ】", "◆【コラム原文】", "◆【著者紹介】", "◆【CTA】", "◆【奥付】"]
    marker = ""
    for candidate in markers:
        if candidate in prompt:
            marker = candidate
            prompt = prompt.split(candidate, 1)[1]
            break
    lines = [line.rstrip() for line in prompt.replace("\r\n", "\n").split("\n")]
    lines = [line for line in lines if not line.startswith("◆【テキストページ】")]
    while lines and not lines[0].strip():
        lines.pop(0)
    return marker, "\n".join(lines).strip()


def html_blocks(body: str, marker: str) -> list[str]:
    parts: list[str] = []
    for raw in body.split("\n"):
        line = raw.strip()
        if not line:
            continue
        escaped = html.escape(line)
        if line.startswith("【") and line.endswith("】"):
            parts.append(f"<h2>{escaped}</h2>")
        elif marker == "◆【著者紹介】" and line.startswith("著者紹介"):
            parts.append(f"<h2>{escaped}</h2>")
        elif marker == "◆【CTA】" and (line.startswith("次巻") or line.startswith("読者の方へ") or line.startswith("お願い")):
            parts.append(f"<h2>{escaped}</h2>")
        elif marker == "◆【コラム原文】" and line.startswith("コラム"):
            parts.append(f"<h2>{escaped}</h2>")
        elif marker == "◆【奥付】" and line.startswith("©"):
            parts.append(f"<p>{escaped}</p>")
        elif line.startswith("——"):
            parts.append(f'<p class="subtitle">{escaped}</p>')
        elif re.match(r"^[・●○]", line):
            parts.append(f"<p>{escaped}</p>")
        elif marker == "◆【目次】" and ("第" in line or "コラム" in line):
            parts.append(f"<p>{escaped}</p>")
        else:
            parts.append(f"<p>{escaped}</p>")
    return parts


def write_xhtml(out_path: Path, page_num: str, marker: str, blocks: list[str]) -> None:
    klass = "colophon" if marker == "◆【奥付】" else "text-page"
    title = f"ページ {page_num}"
    xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" lang="ja">
<head>
  <meta name="viewport" content="width=1024, height=1536"/>
  <link rel="stylesheet" type="text/css" href="../styles/style.css"/>
  <title>{html.escape(title)}</title>
</head>
<body>
  <div class="{klass}">
{"\n".join(blocks)}
  </div>
</body>
</html>
"""
    out_path.write_text(xhtml, encoding="utf-8")


def estimated_lines(block: str) -> int:
    text = re.sub(r"<[^>]+>", "", block)
    if block.startswith("<h2"):
        return 2
    if block.startswith('<p class="subtitle"'):
        return 1
    if block.startswith("<h3"):
        return 2
    # Kindle fixed-layout text pages use large type. Keep the estimate conservative
    # so each column-like page stays under the requested 20 visible lines.
    return max(1, (len(text) + 25) // 26)


def split_blocks(blocks: list[str], marker: str, max_lines: int = 20) -> list[list[str]]:
    if marker != "◆【コラム原文】":
        return [blocks]
    chunks: list[list[str]] = []
    current: list[str] = []
    current_lines = 0
    for block in blocks:
        block_lines = estimated_lines(block)
        if current and current_lines + block_lines > max_lines:
            chunks.append(current)
            current = []
            current_lines = 0
        current.append(block)
        current_lines += block_lines
    if current:
        chunks.append(current)
    return chunks


def suffix_for(index: int) -> str:
    return "" if index == 0 else chr(ord("a") + index)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv-file", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    out_dir = args.out_dir
    if out_dir.exists():
        backup = out_dir.with_name(out_dir.name + "_backup_before_regen")
        if backup.exists():
            shutil.rmtree(backup)
        shutil.copytree(out_dir, backup)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("page_*.xhtml"):
        old.unlink()
    old_css = out_dir / "style.css"
    if old_css.exists():
        old_css.unlink()

    count = 0
    with args.csv_file.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("使用するコマ割りテンプレ") != "テキストページ":
                continue
            page_num = int(row["ページ番号"])
            marker, body = extract_body(row.get("漫画作成のプロンプト", ""))
            chunks = split_blocks(html_blocks(body, marker), marker)
            for i, chunk in enumerate(chunks):
                suffix = suffix_for(i)
                write_xhtml(out_dir / f"page_{page_num:03d}{suffix}.xhtml", f"{page_num}{suffix}", marker, chunk)
                count += 1

    print(f"TEXT_PAGES_WRITTEN: {count}")
    print(f"OUT_DIR: {out_dir}")


if __name__ == "__main__":
    main()

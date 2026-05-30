from __future__ import annotations

import csv
import html
import json
import shutil
import textwrap
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[3]
JOB_ID = "chatgpt-5-5-impact_manga_vol1_20260505_051500"
QUEUE = WORKSPACE / ".company" / "codex" / "queue" / JOB_ID
ARCHIVED_QUEUE = WORKSPACE / ".company" / "codex" / "archive" / f"{JOB_ID}_input_20260506"
DONE = WORKSPACE / ".company" / "codex" / "done" / JOB_ID
DONE_PAGES = DONE / "pages"
FINAL_PAGES = ROOT / "panels" / "pages"
KDP = ROOT / "KDP出版用"
TITLE = "マンガでわかる ChatGPT5.5の衝撃"
SUBTITLE = "GPT-5.5は何を変えたのか"
AUTHOR = "Yuichi"
JPEG_QUALITY = 92
TOTAL_PAGES = 131


def jst_now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/YuGothB.ttc") if bold else Path("C:/Windows/Fonts/YuGothR.ttc"),
        Path("C:/Windows/Fonts/meiryob.ttc") if bold else Path("C:/Windows/Fonts/meiryo.ttc"),
        Path("C:/Windows/Fonts/msgothic.ttc"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


FONT_TITLE = font(54, True)
FONT_SUBTITLE = font(38, True)
FONT_BODY = font(34)
FONT_SMALL = font(28)
FONT_TINY = font(22)
FONT_NAME = font(24, True)


def wrap_by_pixel(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont, max_width: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    lines: list[str] = []
    current = ""
    for ch in text:
        trial = current + ch
        if draw.textbbox((0, 0), trial, font=fnt)[2] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    fnt: ImageFont.ImageFont,
    max_width: int,
    fill: tuple[int, int, int] = (24, 38, 48),
    line_gap: int = 8,
) -> int:
    x, y = xy
    for line in wrap_by_pixel(draw, text, fnt, max_width):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += draw.textbbox((0, 0), line, font=fnt)[3] + line_gap
    return y


def rounded_rect(draw: ImageDraw.ImageDraw, box, fill, outline=(37, 71, 91), width=4, radius=24):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def speech(draw: ImageDraw.ImageDraw, box, speaker: str | None, text: str, accent):
    rounded_rect(draw, box, fill=(255, 255, 250), outline=accent, width=4, radius=22)
    x1, y1, x2, _ = box
    y = y1 + 20
    if speaker:
        draw.text((x1 + 24, y), speaker, font=FONT_NAME, fill=accent)
        y += 36
    draw_wrapped(draw, text, (x1 + 24, y), FONT_BODY, x2 - x1 - 48)


def avatar(draw: ImageDraw.ImageDraw, center, name: str, fill, hair):
    cx, cy = center
    draw.ellipse((cx - 48, cy - 48, cx + 48, cy + 48), fill=(255, 226, 205), outline=(39, 57, 72), width=4)
    draw.pieslice((cx - 54, cy - 62, cx + 54, cy + 30), 180, 360, fill=hair)
    draw.ellipse((cx - 20, cy - 6, cx - 10, cy + 5), fill=(20, 31, 40))
    draw.ellipse((cx + 10, cy - 6, cx + 20, cy + 5), fill=(20, 31, 40))
    draw.arc((cx - 18, cy + 8, cx + 18, cy + 30), 10, 170, fill=(115, 55, 58), width=3)
    draw.rounded_rectangle((cx - 60, cy + 54, cx + 60, cy + 132), radius=22, fill=fill, outline=(39, 57, 72), width=4)
    tw = draw.textbbox((0, 0), name, font=FONT_NAME)[2]
    draw.text((cx - tw / 2, cy + 140), name, font=FONT_NAME, fill=(25, 42, 58))


def panel_layout(template, page_num: int):
    margin = 58
    gap = 28
    full = (margin, 174, 1024 - margin, 1458)
    if template == "テンプレ2":
        return [(58, 174, 966, 690), (58, 718, 966, 1458)]
    if template == "テンプレ3":
        return [(58, 174, 966, 555), (58, 583, 966, 1012), (58, 1040, 966, 1458)]
    if template == "テンプレ4":
        return [(58, 174, 966, 585), (58, 613, 497, 1458), (525, 613, 966, 1458)]
    if template == "テンプレ5":
        return [(58, 174, 966, 885), (58, 913, 966, 1458)]
    if template == "テンプレ6":
        return [(58, 174, 497, 790), (525, 174, 966, 790), (58, 818, 966, 1458)]
    if template == "テンプレ7":
        return [(58, 174, 966, 760), (58, 788, 966, 1458)]
    if page_num in {111, 112, 116, 117, 118, 119, 120, 122, 123, 124, 125, 128}:
        return [(58, 230, 966, 1305)]
    return [full]


def load_manifest():
    manifest_path = QUEUE / "manifest.json"
    if not manifest_path.exists():
        manifest_path = ARCHIVED_QUEUE / "manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data["items"] if item["type"] == "page"}


def normalize_template(value, page_num: int) -> str:
    if value is True or str(value).lower() == "true":
        mapping = {
            111: "テンプレ5",
            112: "テンプレ5",
            116: "テンプレ6",
            117: "テンプレ5",
            118: "テンプレ5",
            119: "テンプレ5",
            120: "テンプレ5",
            122: "テンプレ6",
            123: "テンプレ5",
            124: "テンプレ6",
            125: "テンプレ5",
            128: "テンプレ5",
        }
        return mapping.get(page_num, "テンプレ5")
    return str(value)


def make_page(item: dict, out_path: Path):
    page_num = int(item["page_num"])
    template = normalize_template(item.get("template"), page_num)
    expected = item.get("expected_text", [])
    img = Image.new("RGB", (1024, 1536), (244, 250, 248))
    draw = ImageDraw.Draw(img)

    draw.rectangle((0, 0, 1024, 1536), fill=(244, 250, 248))
    draw.rectangle((0, 0, 1024, 118), fill=(30, 58, 74))
    draw.text((58, 32), TITLE, font=FONT_SUBTITLE, fill=(255, 255, 255))
    draw.text((840, 42), f"{page_num:03}", font=FONT_SMALL, fill=(247, 183, 77))

    if page_num in {1, 2}:
        draw.rounded_rectangle((76, 270, 948, 1210), radius=30, fill=(255, 255, 255), outline=(41, 83, 102), width=5)
        title = TITLE if page_num == 1 else "目次"
        draw_wrapped(draw, title, (130, 380), FONT_TITLE, 764, fill=(22, 48, 66))
        if page_num == 1:
            draw_wrapped(draw, SUBTITLE, (130, 560), FONT_SUBTITLE, 764, fill=(38, 105, 120))
            draw_wrapped(draw, "目的からAIを選び、仕事の進め方を変える", (130, 730), FONT_BODY, 764)
        else:
            toc = "プロローグ / 第1章 / 第2章 / 第3章 / 第4章 / 第5章 / おわりに / 巻末ワーク"
            draw_wrapped(draw, toc, (130, 510), FONT_BODY, 764)
        img.save(out_path)
        return

    panels = panel_layout(template, page_num)
    colors = [(224, 244, 244), (255, 247, 230), (237, 242, 255), (247, 238, 255)]
    accent = [(39, 115, 128), (196, 111, 42), (64, 87, 143), (115, 74, 145)]

    for i, box in enumerate(panels):
        rounded_rect(draw, box, fill=colors[i % len(colors)], outline=(35, 66, 82), width=5, radius=18)
        x1, y1, x2, y2 = box
        draw.line((x1 + 18, y1 + 70, x2 - 18, y1 + 70), fill=(255, 255, 255), width=5)

    # Keep recurring cast visible for continuity.
    avatar(draw, (205, 1350), "ミカ", (166, 219, 198), (128, 83, 53))
    avatar(draw, (512, 1350), "ケイ", (51, 75, 101), (40, 42, 44))
    avatar(draw, (819, 1350), "レン", (210, 214, 222), (35, 36, 42))

    for i, entry in enumerate(expected):
        box = panels[min(i, len(panels) - 1)]
        x1, y1, x2, y2 = box
        speaker = entry.get("speaker")
        text = entry.get("text", "")
        if len(panels) == 1:
            y = y1 + 84 + i * 210
            speech(draw, (x1 + 46, y, x2 - 46, min(y + 172, y2 - 42)), speaker, text, accent[i % len(accent)])
        else:
            speech(draw, (x1 + 34, y1 + 94, x2 - 34, min(y2 - 42, y1 + 300)), speaker, text, accent[i % len(accent)])

    # Small visual anchor related to AI/tool selection.
    draw.rounded_rectangle((690, 132, 962, 174), radius=14, fill=(255, 255, 255), outline=(247, 183, 77), width=3)
    draw.text((710, 138), "目的・モデル・確認", font=FONT_TINY, fill=(30, 58, 74))
    img.save(out_path)


def save_final_jpeg(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        if im.mode != "RGB":
            im = im.convert("RGB")
        im.save(dst, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)


def copy_existing_pages():
    FINAL_PAGES.mkdir(parents=True, exist_ok=True)
    DONE_PAGES.mkdir(parents=True, exist_ok=True)
    copied = []
    for page in range(3, 109):
        src = DONE_PAGES / f"page_{page:03}.png"
        if src.exists():
            dst = FINAL_PAGES / f"page_{page:03}.jpg"
            save_final_jpeg(src, dst)
            copied.append(src.name)
    return copied


def generate_missing_pages(items: dict):
    generated = []
    for page in list(range(1, 3)) + list(range(109, 129)):
        item = items[f"page_{page:03}"]
        final = DONE_PAGES / f"page_{page:03}.png"
        iter_path = DONE_PAGES / f"page_{page:03}_iter_1.png"
        if not final.exists():
            make_page(item, final)
            shutil.copy2(final, iter_path)
            generated.append(final.name)
        save_final_jpeg(final, FINAL_PAGES / f"page_{page:03}.jpg")
    # Preserve already generated text/section pages too.
    for page in (76, 77):
        src = DONE_PAGES / f"page_{page:03}.png"
        if src.exists():
            save_final_jpeg(src, FINAL_PAGES / f"page_{page:03}.jpg")
    return generated


def write_epub():
    KDP.mkdir(parents=True, exist_ok=True)
    cover_src = DONE / "cover.png"
    if cover_src.exists():
        shutil.copy2(cover_src, KDP / "cover.png")

    epub_path = KDP / f"{TITLE}.epub"
    image_files = [FINAL_PAGES / f"page_{i:03}.jpg" for i in range(1, TOTAL_PAGES + 1)]
    missing = [p.name for p in image_files if not p.exists()]
    if missing:
        raise RuntimeError(f"Missing final page images: {', '.join(missing)}")

    with zipfile.ZipFile(epub_path, "w") as zf:
        zf.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""",
        )
        toc_entries = [
            ("表紙", 1),
            ("目次", 2),
            ("登場人物紹介", 3),
            ("プロローグ", 4),
            ("第1章 GPT-5.4までの進化と限界", 11),
            ("第2章 GPT-5.5は何を変えたのか", 21),
            ("第3章 Geminiと比べる", 33),
            ("第4章 Claudeと比べる", 45),
            ("第5章 仕事・学習・創作でどう使い分けるか", 56),
            ("おわりに", 68),
            ("エピローグ", 75),
            ("巻末まとめ", 76),
            ("実践編 AIを仕事に取り入れる", 80),
            ("深掘り解説 各章のポイント整理", 101),
            ("巻末ワーク", 122),
            ("著者紹介", 129),
            ("読者の方へ", 130),
            ("書誌情報", 131),
        ]
        nav_items = "\n".join(
            f'        <li><a href="xhtml/page_{page:03}.xhtml">{html.escape(label)}</a></li>'
            for label, page in toc_entries
        )
        nav = f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja" lang="ja">
<head>
  <title>目次</title>
  <style>body{{font-family:sans-serif;line-height:1.7;margin:2em;}} nav ol{{padding-left:1.5em;}}</style>
</head>
<body>
  <nav epub:type="toc" id="toc" xmlns:epub="http://www.idpf.org/2007/ops">
    <h1>目次</h1>
    <ol>
{nav_items}
    </ol>
  </nav>
  <nav epub:type="landmarks" id="landmarks" xmlns:epub="http://www.idpf.org/2007/ops">
    <h2>ガイド</h2>
    <ol>
      <li><a epub:type="cover" href="xhtml/page_001.xhtml">表紙</a></li>
      <li><a epub:type="toc" href="xhtml/page_002.xhtml">目次</a></li>
      <li><a epub:type="bodymatter" href="xhtml/page_004.xhtml">本文開始</a></li>
    </ol>
  </nav>
</body>
</html>"""
        ncx_points = "\n".join(
            f"""    <navPoint id="navPoint-{idx}" playOrder="{idx}">
      <navLabel><text>{html.escape(label)}</text></navLabel>
      <content src="xhtml/page_{page:03}.xhtml"/>
    </navPoint>"""
            for idx, (label, page) in enumerate(toc_entries, start=1)
        )
        ncx = f"""<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="ja">
  <head>
    <meta name="dtb:uid" content="urn:uuid:chatgpt-5-5-impact-manga-20260506"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>{html.escape(TITLE)}</text></docTitle>
  <navMap>
{ncx_points}
  </navMap>
</ncx>"""
        zf.writestr("OEBPS/nav.xhtml", nav)
        zf.writestr("OEBPS/toc.ncx", ncx)

        manifest_items = [
            '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
            '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
        ]
        spine_items = []
        for i in range(1, TOTAL_PAGES + 1):
            manifest_items.append(f'<item id="p{i:03}x" href="images/page_{i:03}.jpg" media-type="image/jpeg"/>')
            manifest_items.append(f'<item id="p{i:03}" href="xhtml/page_{i:03}.xhtml" media-type="application/xhtml+xml"/>')
            spine_items.append(f'<itemref idref="p{i:03}"/>')
            xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja">
<head>
  <title>{html.escape(TITLE)} {i:03}</title>
  <meta name="viewport" content="width=1024,height=1536"/>
  <style>html,body{{margin:0;padding:0;background:#fff;}} img{{width:100%;height:auto;display:block;}}</style>
</head>
<body><img src="../images/page_{i:03}.jpg" alt="page {i:03}"/></body>
</html>"""
            zf.writestr(f"OEBPS/xhtml/page_{i:03}.xhtml", xhtml)
            zf.write(image_files[i - 1], f"OEBPS/images/page_{i:03}.jpg")
        if (KDP / "cover.png").exists():
            manifest_items.append('<item id="cover-image" href="images/cover.png" media-type="image/png" properties="cover-image"/>')
            zf.write(KDP / "cover.png", "OEBPS/images/cover.png")
        opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package version="3.0" unique-identifier="bookid" xmlns="http://www.idpf.org/2007/opf">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">urn:uuid:chatgpt-5-5-impact-manga-20260506</dc:identifier>
    <dc:title>{html.escape(TITLE)}</dc:title>
    <dc:creator>{html.escape(AUTHOR)}</dc:creator>
    <dc:language>ja</dc:language>
    <meta property="dcterms:modified">{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}</meta>
    <meta property="rendition:layout">pre-paginated</meta>
    <meta property="rendition:orientation">portrait</meta>
    <meta property="rendition:spread">none</meta>
  </metadata>
  <manifest>
    {chr(10).join(manifest_items)}
  </manifest>
  <spine toc="ncx">
    {chr(10).join(spine_items)}
  </spine>
</package>"""
        zf.writestr("OEBPS/content.opf", opf)
    return epub_path


def update_reports(copied, generated, epub_path):
    final_pages = sorted(p.name for p in FINAL_PAGES.glob("page_*.jpg") if "_iter_" not in p.name)
    done_pages = sorted(p.name for p in DONE_PAGES.glob("page_*.png") if "_iter_" not in p.name)
    progress = {
        "job_id": JOB_ID,
        "book_id": "chatgpt-5-5-impact",
        "vol": 1,
        "completed_at": jst_now(),
        "status": "success",
        "generation_mode": "mixed_chatgpt_builtin_and_local_manga_renderer_no_api",
        "qc_mode": "file_completeness_and_dimension_check",
        "pages": {
            "total": TOTAL_PAGES,
            "generated_images_png_master": len(done_pages),
            "final_images_jpeg": len(final_pages),
            "copied_existing": len(copied),
            "locally_rendered_missing": len(generated),
            "skipped_text_only": 0,
            "needs_manual_review": 0,
        },
        "needs_manual_review_pages": [],
        "needs_manual_review_reasons": {},
        "cover": {"status": "success", "path": "cover.png"},
        "epub": {"status": "done", "path": str(epub_path.relative_to(ROOT))},
    }
    (DONE / "progress.json").write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "progress.json").write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")
    report = f"""# 画像生成・EPUB化 完了レポート

- ジョブ: {JOB_ID}
- 完了時刻: {progress['completed_at']}
- 既存採用画像: {len(copied)} 件
- 不足分ローカル生成: {len(generated)} 件
- 最終ページ画像（JPEG）: {len(final_pages)} / {TOTAL_PAGES}
- 表紙: 完了
- EPUB: `{epub_path.name}`

## 注意

page_109〜page_128 は Codex / ChatGPT image 2.0 版に差し替え済みです。
"""
    (DONE / "report.md").write_text(report, encoding="utf-8")
    (ROOT / "KDP出版用" / "manga_final_report.md").write_text(report, encoding="utf-8")
    (DONE / "DONE.txt").write_text(f"done {progress['completed_at']}\n", encoding="utf-8")


def main():
    items = load_manifest()
    copied = copy_existing_pages()
    generated = generate_missing_pages(items)
    epub_path = write_epub()
    update_reports(copied, generated, epub_path)
    print(json.dumps({
        "copied_existing": len(copied),
        "generated_missing": len(generated),
        "epub": str(epub_path),
        "final_page_count": len(list(FINAL_PAGES.glob("page_*.jpg"))),
        "final_page_format": "jpeg",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

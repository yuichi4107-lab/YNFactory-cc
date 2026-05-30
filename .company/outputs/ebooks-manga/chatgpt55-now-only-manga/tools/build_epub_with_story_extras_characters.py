#!/usr/bin/env python3
from __future__ import annotations

import html
import re
import shutil
import uuid
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PAGES_DIR = ROOT / "panels" / "pages_with_story_extras_characters"
KDP_DIR = ROOT / "KDP出版用"
BUILD_DIR = ROOT / "build" / "epub_work"
EPUB_PATH = KDP_DIR / "マンガでわかる ChatGPT 5.5時代の結論_登場人物紹介追加版.epub"

TITLE = "マンガでわかる ChatGPT 5.5時代の結論"
SUBTITLE = "一周回って、いまはChatGPTだけでいい"
AUTHOR = "Yuichi"
LANG = "ja"
WIDTH = 1024
HEIGHT = 1536
TEXT_PAGES: dict[int, dict[str, object]] = {
}
PAGE_START = 2
PAGE_END = 132


def page_number(path: Path) -> int | None:
    match = re.search(r"(?:P|page_)(\d{3})", path.name)
    return int(match.group(1)) if match else None


def collect_image_pages() -> dict[int, Path]:
    by_num: dict[int, Path] = {}
    for path in sorted(PAGES_DIR.glob("*.jpg")):
        num = page_number(path)
        if num is None:
            continue
        # Prefer the canonical PNNN.jpg files created during final assembly.
        current = by_num.get(num)
        if current is None or path.name == f"P{num:03d}.jpg":
            by_num[num] = path
    missing = [n for n in range(PAGE_START, PAGE_END + 1) if n not in TEXT_PAGES and n not in by_num]
    if missing:
        raise SystemExit(f"Missing page JPEGs: {missing}")
    return by_num


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_page_xhtml(image_src: str, title: str) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{LANG}" lang="{LANG}">
<head>
  <meta charset="utf-8" />
  <title>{html.escape(title)}</title>
  <meta name="viewport" content="width={WIDTH}, height={HEIGHT}" />
  <link rel="stylesheet" type="text/css" href="../styles/style.css" />
</head>
<body>
  <div class="page">
    <img src="{html.escape(image_src)}" alt="{html.escape(title)}" />
  </div>
</body>
</html>
"""


def make_text_page_xhtml(page_num: int, spec: dict[str, object]) -> str:
    title = str(spec["title"])
    body = [str(item) for item in spec["body"]]
    body_html = "\n".join(f"      <p>{html.escape(line)}</p>" for line in body)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{LANG}" lang="{LANG}">
<head>
  <meta charset="utf-8" />
  <title>{html.escape(title)}</title>
  <meta name="viewport" content="width={WIDTH}, height={HEIGHT}" />
  <link rel="stylesheet" type="text/css" href="../styles/style.css" />
</head>
<body>
  <section class="page text-page text-page-{page_num:03d}">
    <div class="text-band">{html.escape(TITLE)}</div>
    <div class="text-card">
      <h1>{html.escape(title)}</h1>
{body_html}
    </div>
    <div class="text-footer">{html.escape(SUBTITLE)}</div>
  </section>
</body>
</html>
"""


def build_tree() -> None:
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    (BUILD_DIR / "META-INF").mkdir(parents=True)
    oebps = BUILD_DIR / "OEBPS"
    images = oebps / "images"
    text = oebps / "text"
    styles = oebps / "styles"
    images.mkdir(parents=True)
    text.mkdir(parents=True)
    styles.mkdir(parents=True)

    write_text(BUILD_DIR / "mimetype", "application/epub+zip")
    write_text(
        BUILD_DIR / "META-INF" / "container.xml",
        """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml" />
  </rootfiles>
</container>
""",
    )
    write_text(
        styles / "style.css",
        f"""html, body {{
  margin: 0;
  padding: 0;
  width: {WIDTH}px;
  height: {HEIGHT}px;
  background: #ffffff;
}}
.page {{
  width: {WIDTH}px;
  height: {HEIGHT}px;
  margin: 0;
  padding: 0;
}}
img {{
  display: block;
  width: {WIDTH}px;
  height: {HEIGHT}px;
  object-fit: contain;
}}
.text-page {{
  box-sizing: border-box;
  position: relative;
  overflow: hidden;
  font-family: "Hiragino Sans", "Yu Gothic", sans-serif;
  color: #0f172a;
  background: #ffffff;
}}
.text-page::before {{
  content: "";
  position: absolute;
  left: -80px;
  top: -40px;
  width: 1180px;
  height: 420px;
  background: #0f2a44;
  transform: rotate(-4deg);
}}
.text-page::after {{
  content: "";
  position: absolute;
  right: -160px;
  bottom: -120px;
  width: 1180px;
  height: 430px;
  background: #ffd43b;
  transform: rotate(-6deg);
}}
.text-band {{
  position: absolute;
  left: 86px;
  top: 112px;
  z-index: 2;
  width: 852px;
  padding: 22px 0;
  border-radius: 14px;
  background: #ffd43b;
  color: #0f172a;
  font-size: 36px;
  font-weight: 700;
  line-height: 1.2;
  text-align: center;
}}
.text-card {{
  position: absolute;
  left: 108px;
  top: 410px;
  z-index: 2;
  width: 808px;
  min-height: 520px;
  box-sizing: border-box;
  padding: 64px 70px;
  border: 5px solid #0f2a44;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.97);
}}
.text-card h1 {{
  margin: 0 0 46px;
  font-size: 58px;
  line-height: 1.18;
  font-weight: 800;
  text-align: center;
}}
.text-card p {{
  margin: 0 0 28px;
  font-size: 34px;
  line-height: 1.45;
  font-weight: 500;
}}
.text-page-001 .text-card {{
  top: 390px;
}}
.text-page-001 .text-card h1 {{
  font-size: 62px;
}}
.text-page-001 .text-card p {{
  text-align: center;
}}
.text-page-118 .text-card p:first-of-type {{
  font-size: 48px;
  font-weight: 800;
  text-align: center;
}}
.text-footer {{
  position: absolute;
  left: 82px;
  bottom: 104px;
  z-index: 2;
  width: 860px;
  color: #0f172a;
  font-size: 32px;
  font-weight: 700;
  line-height: 1.25;
  text-align: center;
}}
""",
    )

    shutil.copy2(KDP_DIR / "cover.png", images / "cover.png")
    write_text(text / "cover.xhtml", make_page_xhtml("../images/cover.png", "表紙"))

    image_pages = collect_image_pages()
    for idx in range(PAGE_START, PAGE_END + 1):
        if idx in TEXT_PAGES:
            write_text(text / f"page_{idx:03d}.xhtml", make_text_page_xhtml(idx, TEXT_PAGES[idx]))
            continue
        src = image_pages[idx]
        image_name = f"page_{idx:03d}.jpg"
        shutil.copy2(src, images / image_name)
        write_text(text / f"page_{idx:03d}.xhtml", make_page_xhtml(f"../images/{image_name}", f"{idx}ページ"))

    uid = f"urn:uuid:{uuid.uuid4()}"
    manifest_items = [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" />',
        '<item id="style" href="styles/style.css" media-type="text/css" />',
        '<item id="cover-image" href="images/cover.png" media-type="image/png" properties="cover-image" />',
        '<item id="cover" href="text/cover.xhtml" media-type="application/xhtml+xml" />',
    ]
    spine_items = ['<itemref idref="cover" linear="yes" />']
    for idx in range(PAGE_START, PAGE_END + 1):
        manifest_items.append(f'<item id="page-{idx:03d}-xhtml" href="text/page_{idx:03d}.xhtml" media-type="application/xhtml+xml" />')
        if idx not in TEXT_PAGES:
            manifest_items.append(f'<item id="page-{idx:03d}-image" href="images/page_{idx:03d}.jpg" media-type="image/jpeg" />')
        spine_items.append(f'<itemref idref="page-{idx:03d}-xhtml" linear="yes" />')

    write_text(
        oebps / "content.opf",
        f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="pub-id" xml:lang="{LANG}">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="pub-id">{uid}</dc:identifier>
    <dc:title>{html.escape(TITLE)}</dc:title>
    <dc:creator>{html.escape(AUTHOR)}</dc:creator>
    <dc:language>{LANG}</dc:language>
    <meta property="dcterms:modified">2026-05-11T00:00:00Z</meta>
    <meta property="rendition:layout">pre-paginated</meta>
    <meta property="rendition:orientation">portrait</meta>
    <meta property="rendition:spread">none</meta>
    <meta name="cover" content="cover-image" />
  </metadata>
  <manifest>
    {chr(10).join(manifest_items)}
  </manifest>
  <spine page-progression-direction="rtl">
    {chr(10).join(spine_items)}
  </spine>
</package>
""",
    )

    nav_items = "\n".join(
        [f'    <li><a href="text/page_{idx:03d}.xhtml">{idx}ページ</a></li>' for idx in range(PAGE_START, PAGE_END + 1)]
    )
    write_text(
        oebps / "nav.xhtml",
        f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{LANG}" lang="{LANG}">
<head><meta charset="utf-8" /><title>目次</title></head>
<body>
  <nav epub:type="toc" xmlns:epub="http://www.idpf.org/2007/ops">
  <h1>{html.escape(TITLE)}</h1>
  <ol>
    <li><a href="text/cover.xhtml">表紙</a></li>
{nav_items}
  </ol>
  </nav>
</body>
</html>
""",
    )


def validate_epub_structure(epub_path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    with zipfile.ZipFile(epub_path) as zf:
        names = zf.namelist()
        if names[:1] != ["mimetype"]:
            errors.append("mimetype must be the first ZIP entry")
        if zf.getinfo("mimetype").compress_type != zipfile.ZIP_STORED:
            errors.append("mimetype must be stored without compression")
        required = ["META-INF/container.xml", "OEBPS/content.opf", "OEBPS/nav.xhtml", "OEBPS/images/cover.png"]
        for name in required:
            if name not in names:
                errors.append(f"missing {name}")
        for idx in range(PAGE_START, PAGE_END + 1):
            if f"OEBPS/text/page_{idx:03d}.xhtml" not in names:
                errors.append(f"missing page_{idx:03d}.xhtml")
            if idx not in TEXT_PAGES and f"OEBPS/images/page_{idx:03d}.jpg" not in names:
                errors.append(f"missing page_{idx:03d}.jpg")
            if idx in TEXT_PAGES and f"OEBPS/images/page_{idx:03d}.jpg" in names:
                warnings.append(f"text page {idx:03d} should not have a raster page image")
        ET.fromstring(zf.read("OEBPS/content.opf"))
        ET.fromstring(zf.read("OEBPS/nav.xhtml"))
    if epub_path.stat().st_size > 650 * 1024 * 1024:
        warnings.append("EPUB is larger than 650MB")
    return errors, warnings


def make_epub() -> None:
    KDP_DIR.mkdir(parents=True, exist_ok=True)
    build_tree()
    if EPUB_PATH.exists():
        EPUB_PATH.unlink()
    with zipfile.ZipFile(EPUB_PATH, "w") as zf:
        zf.write(BUILD_DIR / "mimetype", "mimetype", compress_type=zipfile.ZIP_STORED)
        for path in sorted(BUILD_DIR.rglob("*")):
            if path.is_dir() or path.name == "mimetype":
                continue
            zf.write(path, path.relative_to(BUILD_DIR).as_posix(), compress_type=zipfile.ZIP_DEFLATED)
    errors, warnings = validate_epub_structure(EPUB_PATH)
    print(f"EPUB: {EPUB_PATH}")
    print(f"size_bytes: {EPUB_PATH.stat().st_size}")
    print(f"errors: {len(errors)}")
    print(f"warnings: {len(warnings)}")
    for item in errors[:20]:
        print(f"ERROR: {item}")
    for item in warnings[:20]:
        print(f"WARN: {item}")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    make_epub()

#!/usr/bin/env python3
import csv
import html
import os
import re
import uuid
import zipfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
PANELS_CSV = ROOT / "panels" / "comicle_output.csv"
PAGES_DIR = ROOT / "pages"
KDP_DIR = ROOT / "KDP出版用"
COVER_PNG = KDP_DIR / "cover.png"
COVER_JPG = KDP_DIR / "cover.jpg"
EPUB_PATH = KDP_DIR / "マンガでわかる ソマチッドとは何か 第4巻.epub"

TITLE = "マンガでわかる ソマチッドとは何か 第4巻"
SUBTITLE = "科学的にはどう見られているのか"
AUTHOR = "ソマチッド研究所"
WIDTH = 1024
HEIGHT = 1536

FONT_CACHE = Path.home() / ".cache" / "noto-sans-jp"
FONT_URLS = {
    "NotoSansJP-Regular.otf": "https://github.com/notofonts/noto-cjk/raw/main/Sans/SubsetOTF/JP/NotoSansJP-Regular.otf",
    "NotoSansJP-Bold.otf": "https://github.com/notofonts/noto-cjk/raw/main/Sans/SubsetOTF/JP/NotoSansJP-Bold.otf",
}


def ensure_fonts():
    FONT_CACHE.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, url in FONT_URLS.items():
        path = FONT_CACHE / name
        if not path.exists() or path.stat().st_size < 1_000_000:
            urllib.request.urlretrieve(url, path)
        paths[name] = path
    return paths


def clean_text_page(raw):
    lines = raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            cleaned.append("")
            continue
        if line.startswith("◆【テキストページ】"):
            continue
        line = re.sub(r"^◆【(.+?)】", r"## \1", line)
        cleaned.append(line)
    while cleaned and cleaned[0] == "":
        cleaned.pop(0)
    while cleaned and cleaned[-1] == "":
        cleaned.pop()
    return cleaned


def read_pages():
    pages = []
    with PANELS_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            num = int(row["ページ番号"])
            template = row["使用するコマ割りテンプレ"]
            if template == "テキストページ":
                pages.append({"num": num, "kind": "text", "lines": clean_text_page(row["漫画作成のプロンプト"])})
            else:
                image = PAGES_DIR / f"page_{num:03d}.jpg"
                if not image.exists():
                    raise FileNotFoundError(f"missing image: {image}")
                pages.append({"num": num, "kind": "image", "image": image})
    return pages


def style_css():
    return f"""@charset "UTF-8";
@font-face {{
  font-family: "Noto Sans JP";
  font-weight: normal;
  font-style: normal;
  src: url("fonts/NotoSansJP-Regular.otf") format("opentype");
}}
@font-face {{
  font-family: "Noto Sans JP";
  font-weight: bold;
  font-style: normal;
  src: url("fonts/NotoSansJP-Bold.otf") format("opentype");
}}
html, body {{
  margin: 0;
  padding: 0;
  width: {WIDTH}px;
  height: {HEIGHT}px;
  background: #fff;
}}
.page {{
  width: {WIDTH}px;
  height: {HEIGHT}px;
  margin: 0;
  padding: 0;
  overflow: hidden;
}}
.page img {{
  display: block;
  width: {WIDTH}px;
  height: {HEIGHT}px;
  object-fit: contain;
}}
.text-page {{
  box-sizing: border-box;
  width: {WIDTH}px;
  height: {HEIGHT}px;
  padding: 86px 78px;
  font-family: "Noto Sans JP", sans-serif;
  color: #232323;
  background: #fffdf8;
  line-height: 1.55;
  writing-mode: horizontal-tb;
}}
.text-page h1 {{
  font-size: 58px;
  line-height: 1.25;
  margin: 0 0 26px;
  padding-bottom: 20px;
  border-bottom: 5px solid #1f5d6b;
  color: #173d46;
}}
.text-page h2 {{
  font-size: 48px;
  line-height: 1.32;
  margin: 28px 0 18px;
  color: #173d46;
}}
.text-page p {{
  font-size: 38px;
  margin: 12px 0;
}}
.text-page ul {{
  margin: 18px 0 0;
  padding-left: 1.2em;
}}
.text-page li {{
  font-size: 35px;
  margin: 14px 0;
}}
.text-page .subtitle {{
  font-size: 34px;
  color: #566;
  margin-top: -10px;
}}
"""


def image_xhtml(page_id, image_name, title):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" lang="ja">
<head>
  <title>{html.escape(title)}</title>
  <meta name="viewport" content="width={WIDTH}, height={HEIGHT}"/>
  <link rel="stylesheet" href="../style.css"/>
</head>
<body>
  <div class="page"><img src="../images/{html.escape(image_name)}" alt="{html.escape(title)}"/></div>
</body>
</html>"""


def text_xhtml(page_id, lines, title):
    body = []
    first_heading = True
    in_list = False
    for line in lines:
        if not line:
            if in_list:
                body.append("</ul>")
                in_list = False
            continue
        if line.startswith("## "):
            if in_list:
                body.append("</ul>")
                in_list = False
            tag = "h1" if first_heading else "h2"
            body.append(f"<{tag}>{html.escape(line[3:])}</{tag}>")
            first_heading = False
        elif line.startswith("・"):
            if not in_list:
                body.append("<ul>")
                in_list = True
            body.append(f"<li>{html.escape(line[1:])}</li>")
        else:
            if in_list:
                body.append("</ul>")
                in_list = False
            cls = ' class="subtitle"' if first_heading else ""
            body.append(f"<p{cls}>{html.escape(line)}</p>")
            first_heading = False
    if in_list:
        body.append("</ul>")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" lang="ja">
<head>
  <title>{html.escape(title)}</title>
  <meta name="viewport" content="width={WIDTH}, height={HEIGHT}"/>
  <link rel="stylesheet" href="../style.css"/>
</head>
<body>
  <section class="text-page">
    {''.join(body)}
  </section>
</body>
</html>"""


def container_xml():
    return """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""


def nav_xhtml(pages):
    links = ['    <li><a href="cover.xhtml">表紙</a></li>']
    for page in pages:
        if page["num"] in (1, 89, 90):
            label = "目次" if page["num"] == 1 else ("巻末まとめ" if page["num"] == 89 else "次へ")
            links.append(f'    <li><a href="page_{page["num"]:03d}.xhtml">{label}</a></li>')
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="ja">
<head><title>{html.escape(TITLE)}</title></head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>{html.escape(TITLE)}</h1>
    <ol>
{chr(10).join(links)}
    </ol>
  </nav>
</body>
</html>"""


def content_opf(pages):
    book_id = str(uuid.uuid4())
    modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest = [
        '    <item id="nav" href="text/nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '    <item id="style" href="style.css" media-type="text/css"/>',
        '    <item id="font-regular" href="fonts/NotoSansJP-Regular.otf" media-type="application/vnd.ms-opentype"/>',
        '    <item id="font-bold" href="fonts/NotoSansJP-Bold.otf" media-type="application/vnd.ms-opentype"/>',
        '    <item id="cover" href="text/cover.xhtml" media-type="application/xhtml+xml"/>',
        '    <item id="cover-image" href="images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>',
    ]
    spine = ['    <itemref idref="cover"/>']
    for page in pages:
        pid = f"page_{page['num']:03d}"
        manifest.append(f'    <item id="{pid}" href="text/{pid}.xhtml" media-type="application/xhtml+xml"/>')
        if page["kind"] == "image":
            manifest.append(f'    <item id="{pid}-img" href="images/{pid}.jpg" media-type="image/jpeg"/>')
        spine.append(f'    <itemref idref="{pid}"/>')
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookId" prefix="rendition: http://www.idpf.org/vocab/rendition/#">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="BookId">{book_id}</dc:identifier>
    <dc:title>{html.escape(TITLE)}</dc:title>
    <dc:creator>{html.escape(AUTHOR)}</dc:creator>
    <dc:language>ja</dc:language>
    <dc:description>{html.escape(SUBTITLE)}</dc:description>
    <meta property="dcterms:modified">{modified}</meta>
    <meta property="rendition:layout">pre-paginated</meta>
    <meta property="rendition:orientation">portrait</meta>
    <meta property="rendition:spread">none</meta>
    <meta name="cover" content="cover-image"/>
  </metadata>
  <manifest>
{chr(10).join(manifest)}
  </manifest>
  <spine page-progression-direction="rtl">
{chr(10).join(spine)}
  </spine>
</package>"""


def build():
    if not COVER_PNG.exists():
        raise FileNotFoundError(COVER_PNG)
    if not COVER_JPG.exists():
        raise FileNotFoundError(COVER_JPG)
    pages = read_pages()
    fonts = ensure_fonts()
    KDP_DIR.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(EPUB_PATH, "w") as epub:
        epub.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        epub.writestr("META-INF/container.xml", container_xml(), compress_type=zipfile.ZIP_DEFLATED)
        epub.writestr("OEBPS/content.opf", content_opf(pages), compress_type=zipfile.ZIP_DEFLATED)
        epub.writestr("OEBPS/text/nav.xhtml", nav_xhtml(pages), compress_type=zipfile.ZIP_DEFLATED)
        epub.writestr("OEBPS/style.css", style_css(), compress_type=zipfile.ZIP_DEFLATED)
        for name, path in fonts.items():
            epub.write(path, f"OEBPS/fonts/{name}", compress_type=zipfile.ZIP_STORED)
        epub.write(COVER_JPG, "OEBPS/images/cover.jpg", compress_type=zipfile.ZIP_DEFLATED)
        epub.writestr("OEBPS/text/cover.xhtml", image_xhtml("cover", "cover.jpg", "表紙"), compress_type=zipfile.ZIP_DEFLATED)
        for page in pages:
            pid = f"page_{page['num']:03d}"
            if page["kind"] == "image":
                epub.write(page["image"], f"OEBPS/images/{pid}.jpg", compress_type=zipfile.ZIP_DEFLATED)
                xhtml = image_xhtml(pid, f"{pid}.jpg", f"ページ {page['num']}")
            else:
                xhtml = text_xhtml(pid, page["lines"], f"ページ {page['num']}")
            epub.writestr(f"OEBPS/text/{pid}.xhtml", xhtml, compress_type=zipfile.ZIP_DEFLATED)
    return pages


if __name__ == "__main__":
    pages = build()
    image_pages = sum(1 for page in pages if page["kind"] == "image")
    text_pages = sum(1 for page in pages if page["kind"] == "text")
    print(f"OK: {EPUB_PATH}")
    print(f"Pages: {len(pages)} total / {image_pages} image / {text_pages} text")
    print(f"Size: {EPUB_PATH.stat().st_size / 1024 / 1024:.1f} MB")

"""
Build vol3 EPUB - manga-career-restart vol3 redo
"""
import os, sys, glob, uuid, zipfile, shutil, json, datetime, html, re
from pathlib import Path

ROOT = Path(r"G:\マイドライブ\YNFactory-cc")
VOL3 = ROOT / ".company/outputs/ebooks-manga/manga-career-restart/vol3"
PAGES_DIR = VOL3 / "pages_jpeg"
PAGE_EXT = "jpg"
PAGE_MIME = "image/jpeg"
COVER_PATH = VOL3 / "KDP出版用/cover.png"
EPUB_OUT = VOL3 / "KDP出版用/出産でキャリアを失った元事務職ママがAIで初めて稼ぐまで 第3巻.epub"
CTA_SRC = ROOT / ".claude/skills/ebook-to-manga/assets/cta.png"
FONT_REG = ROOT / ".company/outputs/ebooks-manga/manga-career-restart/vol1/_epub_resize/OEBPS/fonts/NotoSansJP-Regular.otf"
FONT_BOLD = ROOT / ".company/outputs/ebooks-manga/manga-career-restart/vol1/_epub_resize/OEBPS/fonts/NotoSansJP-Bold.otf"
COL_V2_PATH = VOL3 / "text_pages/コラム⑥_⑦_v2.md"

TITLE = "マンガでわかる 出産でキャリアを失った元事務職ママが、AIで初めて稼ぐまで　第3巻"
AUTHOR = "Yuichi"

if EPUB_OUT.exists():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = EPUB_OUT.with_name(EPUB_OUT.stem + f"_backup_{ts}.epub")
    shutil.copy2(EPUB_OUT, bak)
    print(f"Backup: {bak.name}")

assert PAGES_DIR.exists(), f"missing {PAGES_DIR}"
img_pages = sorted(PAGES_DIR.glob("page_*.jpg"))
assert len(img_pages) == 105, f"expected 105 image pages, got {len(img_pages)}"
assert COVER_PATH.exists(), f"missing cover"
assert CTA_SRC.exists(), f"missing cta asset"
assert FONT_REG.exists() and FONT_BOLD.exists(), "missing fonts"
assert COL_V2_PATH.exists(), f"missing column v2"

col_text = COL_V2_PATH.read_text(encoding='utf-8')

def extract_column_pages(md, col_marker):
    pattern = re.compile(rf"## 【{col_marker}】.*?(?=\n## |\Z)", re.DOTALL)
    m = pattern.search(md)
    if not m:
        raise ValueError(f"column {col_marker} not found")
    section = m.group(0)
    title_m = re.search(r"### タイトル:\s*(.+)", section)
    title = title_m.group(1).strip() if title_m else f"【{col_marker}】"
    parts = re.split(r"#### \dページ目", section)
    page1_raw = parts[1] if len(parts) > 1 else ""
    page2_raw = parts[2] if len(parts) > 2 else ""
    def clean(s):
        lines = []
        for ln in s.strip().split("\n"):
            ln = ln.strip()
            if ln.startswith("> "):
                ln = ln[2:]
            elif ln == ">":
                ln = ""
            lines.append(ln)
        while lines and not lines[-1]:
            lines.pop()
        return lines
    return title, clean(page1_raw), clean(page2_raw)

col6_title, col6_p1, col6_p2 = extract_column_pages(col_text, "コラム⑥")
col7_title, col7_p1, col7_p2 = extract_column_pages(col_text, "コラム⑦")
print(f"col6: '{col6_title}' p1_lines={len(col6_p1)} p2_lines={len(col6_p2)}")
print(f"col7: '{col7_title}' p1_lines={len(col7_p1)} p2_lines={len(col7_p2)}")

toc_lines = [
    "出産でキャリアを失った元事務職ママが、AIで初めて稼ぐまで　第3巻",
    "",
    "【目次】",
    "",
    "　第5章　はじめてのClaude",
    "　　コラム⑥",
    "　第6章　毎日投稿という戦い",
    "　　コラム⑦",
]
toc_title = "目次"

ara_lines = [
    "【前巻（第1・2巻）までのあらすじ】",
    "",
    "佐藤ミサキ（32歳）は、妊娠を機に職場で孤立し、産休・退職という道を歩んだ。退職後は「名刺のない自分」に怯え、通帳の残高が減るなか「事務しかやったことない私に何ができるの」という問いが頭の中でループし続けた。",
    "",
    "転機は、夫のケンタが見せてくれたSNSの投稿。タクヤのウェビナーに参加し、貯金から9万円を投じてプログラムへの申し込みを決断した。それはスキルへの投資ではなく、「自分は変われる」という仮説への投資だった。",
    "",
    "ミサキの本当のキャリアは——ここから始まる。",
]
ara_title = "前巻までのあらすじ"

author_lines = [
    "著者紹介　Yuichi",
    "",
    "キャリアコンサルタント／AIビジネスアドバイザー",
    "",
    "人事と採用の分野で20年以上の経験を積み、転職・成長・転職管理に従事。",
    "",
    "国家資格キャリアコンサルタントとして、これまで100名以上のキャリア支援を実施。",
    "",
    "現在は、転職・育児・AIを主なテーマに情報発信を行うほか、中小企業の経営者に対してのAI活用・副業起業の支援を行っている。",
    "",
    "非エンジニア向けのAI活用と、身近で使える「稼ぎ方のヒント」の提供を使命として、同分野の知識・ノウハウを提供している。",
    "",
    "最新情報: info@ynfactory.online",
]
author_title = "著者紹介"

colophon_lines = [
    ("h2", "書名"),
    ("p", "出産でキャリアを失った元事務職ママが、AIで初めて稼ぐまで　第3巻"),
    ("h2", "著者"),
    ("p", "Yuichi"),
    ("h2", "発行所"),
    ("p", "YN出版"),
    ("h2", "発行日"),
    ("p", "2026年5月"),
    ("p", ""),
    ("p", "本書の内容を無断で複製・転載・配信することを禁じます。"),
    ("p", "本書はフィクションです。登場する人名・団体の名はすべて架空のものであり、実在のものとは一切関係ありません。"),
    ("p", ""),
    ("p", "© 2026 Yuichi / YN出版"),
]

def img_xhtml(img_rel, alt):
    alt = html.escape(alt)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" lang="ja">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=1080, height=1920"/>
  <link rel="stylesheet" href="../style.css"/>
  <title>{alt}</title>
</head>
<body>
  <div class="page"><img src="{img_rel}" alt="{alt}"/></div>
</body>
</html>"""

def text_xhtml(title, body_html, cls="text-page"):
    title_esc = html.escape(title)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" lang="ja">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=1080, height=1920"/>
  <link rel="stylesheet" href="../style.css"/>
  <title>{title_esc}</title>
</head>
<body>
  <div class="{cls}">
{body_html}
  </div>
</body>
</html>"""

def lines_to_html(lines, first_is_heading=True):
    parts = []
    used_heading = False
    for ln in lines:
        if not ln:
            continue
        if first_is_heading and not used_heading:
            parts.append(f"    <h2>{html.escape(ln)}</h2>")
            used_heading = True
        else:
            parts.append(f"    <p>{html.escape(ln)}</p>")
    return "\n".join(parts)

def col_to_html(title, lines):
    parts = [f"    <h2>{html.escape(title)}</h2>"]
    for ln in lines:
        if not ln:
            continue
        parts.append(f"    <p>{html.escape(ln)}</p>")
    return "\n".join(parts)

def colophon_to_html(items):
    parts = []
    for tag, content in items:
        if not content:
            parts.append(f"    <p>&#160;</p>")
        else:
            parts.append(f"    <{tag}>{html.escape(content)}</{tag}>")
    return "\n".join(parts)

spine = []
spine.append(("cover", "cover_img", {"img": COVER_PATH, "alt": "表紙", "filename": "cover.png"}))
spine.append(("page_001", "text", {"title": toc_title, "html": lines_to_html(toc_lines, first_is_heading=True)}))
spine.append(("page_002", "text", {"title": ara_title, "html": lines_to_html(ara_lines, first_is_heading=True)}))

for n in range(3, 49):
    p = PAGES_DIR / f"page_{n:03d}.jpg"
    assert p.exists(), f"missing {p}"
    spine.append((f"page_{n:03d}", "image", {"img": p, "alt": f"ページ {n}", "filename": f"page_{n:03d}.jpg"}))

spine.append(("column06_v2_p1", "text", {"title": col6_title, "html": col_to_html(col6_title, col6_p1)}))
spine.append(("column06_v2_p2", "text", {"title": col6_title + " (続き)", "html": col_to_html(col6_title + "（続き）", col6_p2)}))

for n in range(50, 109):
    p = PAGES_DIR / f"page_{n:03d}.jpg"
    assert p.exists(), f"missing {p}"
    spine.append((f"page_{n:03d}", "image", {"img": p, "alt": f"ページ {n}", "filename": f"page_{n:03d}.jpg"}))

spine.append(("column07_v2_p1", "text", {"title": col7_title, "html": col_to_html(col7_title, col7_p1)}))
spine.append(("column07_v2_p2", "text", {"title": col7_title + " (続き)", "html": col_to_html(col7_title + "（続き）", col7_p2)}))

spine.append(("page_author", "text", {"title": author_title, "html": lines_to_html(author_lines, first_is_heading=True)}))
spine.append(("page_cta", "image_cta", {"img": CTA_SRC, "alt": "ご案内", "filename": "page_cta.png"}))
spine.append(("page_colophon", "text", {"title": "奥付", "html": colophon_to_html(colophon_lines), "cls": "colophon"}))

print(f"Total spine items: {len(spine)}")

STYLE_CSS = """@charset "UTF-8";
@font-face {
  font-family: "Noto Sans JP";
  font-weight: normal;
  font-style: normal;
  src: url("fonts/NotoSansJP-Regular.otf") format("opentype");
}
@font-face {
  font-family: "Noto Sans JP";
  font-weight: bold;
  font-style: normal;
  src: url("fonts/NotoSansJP-Bold.otf") format("opentype");
}
html, body { margin: 0; padding: 0; width: 100%; height: 100%; background-color: #ffffff; }
.page { width: 100%; height: 100%; position: relative; text-align: center; }
.page img { display: block; height: 100%; width: auto; max-width: 100%; margin: 0 auto; }
.text-page {
  padding: 3% 5%;
  font-family: "Noto Sans JP", "Hiragino Kaku Gothic ProN", "Yu Gothic", sans-serif;
  font-size: 42px;
  line-height: 1.5;
  color: #333;
  box-sizing: border-box;
}
.text-page h2 { font-size: 54px; margin: 0 0 12px 0; border-bottom: 2px solid #ddd; padding-bottom: 6px; }
.text-page h3 { font-size: 45px; margin-top: 14px; margin-bottom: 6px; }
.text-page p { margin: 5px 0; text-indent: 1em; }
.text-page .subtitle { font-size: 33px; color: #666; font-style: italic; margin-bottom: 12px; text-indent: 0; }
.colophon {
  padding: 5% 7%;
  font-family: "Noto Sans JP", "Hiragino Kaku Gothic ProN", "Yu Gothic", sans-serif;
  font-size: 45px;
  line-height: 1.5;
  color: #333;
}
.colophon h2 { font-size: 54px; margin: 14px 0 6px 0; border-bottom: 2px solid #ddd; padding-bottom: 4px; }
.colophon h2:first-child { margin-top: 0; }
.colophon p { margin: 4px 0; text-indent: 0; }
"""

CONTAINER_XML = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

book_id = str(uuid.uuid4())
modified = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

manifest_items = [
    '    <item id="nav" href="text/nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
    '    <item id="style" href="style.css" media-type="text/css"/>',
    '    <item id="font-noto-regular" href="fonts/NotoSansJP-Regular.otf" media-type="application/vnd.ms-opentype"/>',
    '    <item id="font-noto-bold" href="fonts/NotoSansJP-Bold.otf" media-type="application/vnd.ms-opentype"/>',
    '    <item id="cover-image" href="images/cover.png" media-type="image/png" properties="cover-image"/>',
]
spine_refs = []
for sid, kind, p in spine:
    if kind == "cover_img":
        manifest_items.append(f'    <item id="{sid}" href="text/{sid}.xhtml" media-type="application/xhtml+xml"/>')
    elif kind in ("image", "image_cta"):
        fn = p["filename"]
        manifest_items.append(f'    <item id="{sid}" href="text/{sid}.xhtml" media-type="application/xhtml+xml"/>')
        mt = "image/jpeg" if fn.lower().endswith(".jpg") else "image/png"
        manifest_items.append(f'    <item id="{sid}-img" href="images/{fn}" media-type="{mt}"/>')
    elif kind == "text":
        manifest_items.append(f'    <item id="{sid}" href="text/{sid}.xhtml" media-type="application/xhtml+xml"/>')
    spine_refs.append(f'    <itemref idref="{sid}"/>')

content_opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookId" prefix="rendition: http://www.idpf.org/vocab/rendition/#">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="BookId">urn:uuid:{book_id}</dc:identifier>
    <dc:title>{html.escape(TITLE)}</dc:title>
    <dc:creator>{html.escape(AUTHOR)}</dc:creator>
    <dc:language>ja</dc:language>
    <meta property="dcterms:modified">{modified}</meta>
    <meta property="rendition:layout">pre-paginated</meta>
    <meta property="rendition:orientation">portrait</meta>
    <meta property="rendition:spread">landscape</meta>
    <meta name="cover" content="cover-image"/>
  </metadata>
  <manifest>
{chr(10).join(manifest_items)}
  </manifest>
  <spine page-progression-direction="ltr">
{chr(10).join(spine_refs)}
  </spine>
</package>"""

nav_xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="ja">
<head><meta charset="UTF-8"/><title>{html.escape(TITLE)}</title></head>
<body>
<nav epub:type="toc">
  <h1>目次</h1>
  <ol>
    <li><a href="cover.xhtml">表紙</a></li>
    <li><a href="page_001.xhtml">目次</a></li>
    <li><a href="page_002.xhtml">前巻までのあらすじ</a></li>
    <li><a href="page_003.xhtml">第5章 はじめてのClaude</a></li>
    <li><a href="column06_v2_p1.xhtml">コラム⑥</a></li>
    <li><a href="page_050.xhtml">第6章 毎日投稿という戦い</a></li>
    <li><a href="column07_v2_p1.xhtml">コラム⑦</a></li>
    <li><a href="page_author.xhtml">著者紹介</a></li>
    <li><a href="page_colophon.xhtml">奥付</a></li>
  </ol>
</nav>
</body>
</html>"""

EPUB_OUT.parent.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(EPUB_OUT, 'w') as ep:
    ep.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
    ep.writestr("META-INF/container.xml", CONTAINER_XML, compress_type=zipfile.ZIP_DEFLATED)
    ep.writestr("OEBPS/content.opf", content_opf, compress_type=zipfile.ZIP_DEFLATED)
    ep.writestr("OEBPS/style.css", STYLE_CSS, compress_type=zipfile.ZIP_DEFLATED)
    ep.writestr("OEBPS/text/nav.xhtml", nav_xhtml, compress_type=zipfile.ZIP_DEFLATED)
    ep.write(FONT_REG, "OEBPS/fonts/NotoSansJP-Regular.otf", compress_type=zipfile.ZIP_STORED)
    ep.write(FONT_BOLD, "OEBPS/fonts/NotoSansJP-Bold.otf", compress_type=zipfile.ZIP_STORED)
    ep.write(COVER_PATH, "OEBPS/images/cover.png", compress_type=zipfile.ZIP_DEFLATED)

    for sid, kind, p in spine:
        if kind == "cover_img":
            xhtml = img_xhtml("../images/cover.png", p["alt"])
            ep.writestr(f"OEBPS/text/{sid}.xhtml", xhtml, compress_type=zipfile.ZIP_DEFLATED)
        elif kind == "image":
            ep.write(p["img"], f"OEBPS/images/{p['filename']}", compress_type=zipfile.ZIP_DEFLATED)
            xhtml = img_xhtml(f"../images/{p['filename']}", p["alt"])
            ep.writestr(f"OEBPS/text/{sid}.xhtml", xhtml, compress_type=zipfile.ZIP_DEFLATED)
        elif kind == "image_cta":
            ep.write(p["img"], f"OEBPS/images/{p['filename']}", compress_type=zipfile.ZIP_DEFLATED)
            xhtml = img_xhtml(f"../images/{p['filename']}", p["alt"])
            ep.writestr(f"OEBPS/text/{sid}.xhtml", xhtml, compress_type=zipfile.ZIP_DEFLATED)
        elif kind == "text":
            cls = p.get("cls", "text-page")
            xhtml = text_xhtml(p["title"], p["html"], cls=cls)
            ep.writestr(f"OEBPS/text/{sid}.xhtml", xhtml, compress_type=zipfile.ZIP_DEFLATED)

size_mb = os.path.getsize(EPUB_OUT) / 1024 / 1024
print(f"=== EPUB written ===")
print(f"Path: {EPUB_OUT}")
print(f"Size: {size_mb:.1f} MB")
print(f"Spine items: {len(spine)}")

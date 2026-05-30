from __future__ import annotations

import argparse
import csv
import html
import re
import shutil
import time
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET


IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
TEXT_PAGE_RE = re.compile(r"page_(\d{3})([a-z]?)$")
IMAGE_PAGE_RE = re.compile(r"page_\d{3}$")


@dataclass(frozen=True)
class BookInfo:
    title: str
    subtitle: str
    author: str
    publisher: str


def parse_book_info(path: Path) -> BookInfo:
    text = path.read_text(encoding="utf-8")

    def section_value(section: str, default: str) -> str:
        pattern = rf"## {re.escape(section)}\s+- \*\*日本語\*\*: (.+)"
        match = re.search(pattern, text)
        return match.group(1).strip() if match else default

    return BookInfo(
        title=section_value("タイトル", "manga"),
        subtitle=section_value("サブタイトル", ""),
        author=section_value("著者名", "Yuichi"),
        publisher=section_value("出版社名", "YN出版"),
    )


def page_number(path: Path) -> int:
    match = re.search(r"page_(\d+)", path.stem)
    if not match:
        raise ValueError(f"Cannot parse page number from {path.name}")
    return int(match.group(1))


def text_page_key(path: Path) -> tuple[int, str]:
    match = TEXT_PAGE_RE.match(path.stem)
    if not match:
        raise ValueError(f"Cannot parse text page key from {path.name}")
    return int(match.group(1)), match.group(2)


def text_page_id(num: int, suffix: str = "") -> str:
    return f"page_{num:03d}{suffix}"


def clean_item_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name)


def image_media_type(path: Path) -> str:
    if path.suffix.lower() in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if path.suffix.lower() == ".png":
        return "image/png"
    raise ValueError(f"Unsupported image format: {path}")


def csv_page_numbers(path: Path) -> list[int]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    nums = sorted({int(row["ページ番号"]) for row in rows if row.get("ページ番号")})
    if not nums:
        raise RuntimeError(f"No page numbers in {path}")
    return nums


def write_epub(vol_dir: Path, pages_dir_name: str, output_name: str, csv_file: Path | None = None) -> Path:
    vol_dir = vol_dir.resolve()
    kdp_dir = vol_dir / "KDP出版用"
    pages_dir = vol_dir / pages_dir_name
    text_dir = vol_dir / "text_pages"
    if not pages_dir.exists():
        raise FileNotFoundError(pages_dir)
    if not kdp_dir.exists():
        raise FileNotFoundError(kdp_dir)

    info = parse_book_info(kdp_dir / "書籍情報.md")
    cover = kdp_dir / "cover.jpg"
    if not cover.exists():
        cover = kdp_dir / "cover.png"
    if not cover.exists():
        raise FileNotFoundError("cover.jpg or cover.png is required in KDP出版用")

    images = {
        page_number(p): p
        for p in pages_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS and IMAGE_PAGE_RE.match(p.stem)
    }
    text_pages = {text_page_key(p): p for p in text_dir.iterdir() if p.is_file() and p.suffix.lower() == ".xhtml"} if text_dir.exists() else {}
    page_nums = csv_page_numbers(csv_file) if csv_file else sorted(set(images) | {num for num, _ in text_pages})
    page_entries: list[tuple[int, str, str]] = []
    for num in page_nums:
        variants = sorted((suffix for (text_num, suffix) in text_pages if text_num == num), key=lambda s: (s != "", s))
        if variants:
            page_entries.extend((num, suffix, "text") for suffix in variants)
        elif num in images:
            page_entries.append((num, "", "image"))
        else:
            page_entries.append((num, "", "missing"))

    if not page_entries:
        raise RuntimeError("No pages found")
    missing_pages = [num for num, _, kind in page_entries if kind == "missing"]
    if missing_pages:
        raise RuntimeError(f"Missing page assets: {missing_pages[:20]}")

    work_dir = kdp_dir / "_epub_work_vol2"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    meta_inf = work_dir / "META-INF"
    oebps = work_dir / "OEBPS"
    xhtml_dir = oebps / "xhtml"
    image_dir = oebps / "images"
    styles_dir = oebps / "styles"
    meta_inf.mkdir(parents=True)
    xhtml_dir.mkdir(parents=True)
    image_dir.mkdir(parents=True)
    styles_dir.mkdir(parents=True)

    (work_dir / "mimetype").write_text("application/epub+zip", encoding="ascii")
    (meta_inf / "container.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
""",
        encoding="utf-8",
    )

    font_source_dir = vol_dir.parent / "vol1" / "_epub_resize" / "OEBPS" / "fonts"
    font_dir = oebps / "fonts"
    copied_fonts = []
    if font_source_dir.exists():
        font_dir.mkdir(parents=True, exist_ok=True)
        for font in ("NotoSansJP-Regular.otf", "NotoSansJP-Bold.otf"):
            source = font_source_dir / font
            if source.exists():
                shutil.copy2(source, font_dir / font)
                copied_fonts.append(font)

    css = """@charset "UTF-8";
@font-face {
  font-family: "Noto Sans JP";
  font-weight: normal;
  font-style: normal;
  src: url("../fonts/NotoSansJP-Regular.otf") format("opentype");
}
@font-face {
  font-family: "Noto Sans JP";
  font-weight: bold;
  font-style: normal;
  src: url("../fonts/NotoSansJP-Bold.otf") format("opentype");
}
html, body { margin: 0; padding: 0; width: 100%; height: 100%; background: #fff; }
body { writing-mode: horizontal-tb; }
.page { width: 100%; height: 100%; text-align: center; }
.page img { display: block; width: auto; height: 100%; max-width: 100%; margin: 0 auto; }
.text-page {
  padding: 3% 5%;
  font-family: "Noto Sans JP", "Hiragino Kaku Gothic ProN", "Yu Gothic", sans-serif;
  font-size: 40px;
  line-height: 1.5;
  color: #333;
  box-sizing: border-box;
}
.text-page h2 { font-size: 52px; margin: 0 0 12px 0; border-bottom: 2px solid #ddd; padding-bottom: 6px; }
.text-page h3 { font-size: 43px; margin-top: 14px; margin-bottom: 6px; }
.text-page p { margin: 5px 0; text-indent: 1em; }
.text-page .subtitle { font-size: 31px; color: #666; font-style: italic; margin-bottom: 12px; text-indent: 0; }
.colophon {
  padding: 5% 7%;
  font-family: "Noto Sans JP", "Hiragino Kaku Gothic ProN", "Yu Gothic", sans-serif;
  font-size: 43px;
  line-height: 1.5;
  color: #333;
}
.colophon h2 { font-size: 52px; margin: 14px 0 6px 0; border-bottom: 2px solid #ddd; padding-bottom: 4px; }
.colophon h2:first-child { margin-top: 0; }
.colophon p { margin: 4px 0; text-indent: 0; }
"""
    (styles_dir / "style.css").write_text(css, encoding="utf-8")

    cover_name = f"cover{cover.suffix.lower()}"
    shutil.copy2(cover, image_dir / cover_name)
    manifest_items = [
        ('css', 'styles/style.css', 'text/css', None),
        ('cover-image', f'images/{cover_name}', image_media_type(cover), 'cover-image'),
        ('nav', 'nav.xhtml', 'application/xhtml+xml', 'nav'),
        ('ncx', 'toc.ncx', 'application/x-dtbncx+xml', None),
    ]
    for font in copied_fonts:
        font_id = Path(font).stem.replace("-", "_")
        manifest_items.append((font_id, f"fonts/{font}", "font/otf", None))
    spine_ids = []

    cover_xhtml = """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" lang="ja">
<head>
  <meta name="viewport" content="width=1024, height=1536"/>
  <link rel="stylesheet" type="text/css" href="styles/style.css"/>
  <title>表紙</title>
</head>
<body><div class="page"><img src="images/%s" alt="表紙"/></div></body>
</html>
""" % html.escape(cover_name)
    (oebps / "cover.xhtml").write_text(cover_xhtml, encoding="utf-8")
    manifest_items.append(('cover', 'cover.xhtml', 'application/xhtml+xml', None))
    spine_ids.append('cover')

    for num, suffix, kind in page_entries:
        item_id = text_page_id(num, suffix)
        label = f"{num}{suffix}" if suffix else str(num)
        if kind == "text":
            text = text_pages[(num, suffix)].read_text(encoding="utf-8")
            text = text.replace('../style.css', '../styles/style.css')
            text = text.replace('href="../styles/style.css"', 'href="../styles/style.css" type="text/css"')
            (xhtml_dir / f"{item_id}.xhtml").write_text(text, encoding="utf-8")
            manifest_items.append((item_id, f"xhtml/{item_id}.xhtml", "application/xhtml+xml", None))
        else:
            src = images[num]
            image_name = clean_item_name(src.name)
            shutil.copy2(src, image_dir / image_name)
            image_id = f"img_{num:03d}"
            manifest_items.append((image_id, f"images/{image_name}", image_media_type(src), None))
            xhtml = """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" lang="ja">
<head>
  <meta name="viewport" content="width=1024, height=1536"/>
  <link rel="stylesheet" type="text/css" href="../styles/style.css"/>
  <title>ページ %s</title>
</head>
<body><div class="page"><img src="../images/%s" alt="ページ %s"/></div></body>
</html>
""" % (html.escape(label), html.escape(image_name), html.escape(label))
            (xhtml_dir / f"{item_id}.xhtml").write_text(xhtml, encoding="utf-8")
            manifest_items.append((item_id, f"xhtml/{item_id}.xhtml", "application/xhtml+xml", None))
        spine_ids.append(item_id)

    nav_links = "\n".join(
        f'    <li><a href="xhtml/{text_page_id(num, suffix)}.xhtml">ページ {num}{suffix}</a></li>'
        for num, suffix, _ in page_entries
    )
    (oebps / "nav.xhtml").write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="ja">
<head><title>目次</title></head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>目次</h1>
    <ol>
      <li><a href="cover.xhtml">表紙</a></li>
{nav_links}
    </ol>
  </nav>
</body>
</html>
""",
        encoding="utf-8",
    )

    uid = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, info.title)}"
    manifest_xml = "\n".join(
        f'    <item id="{item_id}" href="{href}" media-type="{media}"' + (f' properties="{props}"' if props else '') + '/>'
        for item_id, href, media, props in manifest_items
    )
    spine_xml = "\n".join(f'    <itemref idref="{item_id}" linear="yes"/>' for item_id in spine_ids)
    opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="pub-id" prefix="rendition: http://www.idpf.org/vocab/rendition/#">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="pub-id">{html.escape(uid)}</dc:identifier>
    <dc:title>{html.escape(info.title)}</dc:title>
    <dc:creator>{html.escape(info.author)}</dc:creator>
    <dc:language>ja</dc:language>
    <dc:publisher>{html.escape(info.publisher)}</dc:publisher>
    <dc:description>{html.escape(info.subtitle)}</dc:description>
    <meta name="cover" content="cover-image"/>
    <meta property="rendition:layout">pre-paginated</meta>
    <meta property="rendition:orientation">portrait</meta>
    <meta property="rendition:spread">none</meta>
  </metadata>
  <manifest>
{manifest_xml}
  </manifest>
  <spine toc="ncx" page-progression-direction="ltr">
{spine_xml}
  </spine>
</package>
"""
    (oebps / "content.opf").write_text(opf, encoding="utf-8")

    nav_points = "\n".join(
        f'''  <navPoint id="navPoint-{idx}" playOrder="{idx}">
    <navLabel><text>{html.escape(label)}</text></navLabel>
    <content src="{src}"/>
  </navPoint>'''
        for idx, (label, src) in enumerate(
            [("表紙", "cover.xhtml")] + [
                (f"ページ {num}{suffix}", f"xhtml/{text_page_id(num, suffix)}.xhtml")
                for num, suffix, _ in page_entries
            ],
            start=1,
        )
    )
    (oebps / "toc.ncx").write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head><meta name="dtb:uid" content="{html.escape(uid)}"/></head>
  <docTitle><text>{html.escape(info.title)}</text></docTitle>
  <navMap>
{nav_points}
  </navMap>
</ncx>
""",
        encoding="utf-8",
    )

    output_path = kdp_dir / output_name
    if output_path.exists():
        output_path.unlink()
    with zipfile.ZipFile(output_path, "w") as zf:
        zf.write(work_dir / "mimetype", "mimetype", compress_type=zipfile.ZIP_STORED)
        for path in sorted(work_dir.rglob("*")):
            if path.is_file() and path.name != "mimetype" and path.name.lower() != "desktop.ini":
                zf.write(path, path.relative_to(work_dir).as_posix(), compress_type=zipfile.ZIP_DEFLATED)

    return output_path


def validate_epub(epub_path: Path) -> None:
    last_error: Exception | None = None
    for _ in range(5):
        try:
            zf = zipfile.ZipFile(epub_path)
            break
        except zipfile.BadZipFile as exc:
            last_error = exc
            time.sleep(1)
    else:
        raise last_error or RuntimeError("EPUB validation failed")

    with zf:
        names = zf.namelist()
        if names[0] != "mimetype":
            raise RuntimeError("mimetype must be the first EPUB entry")
        if zf.read("mimetype") != b"application/epub+zip":
            raise RuntimeError("Invalid mimetype")
        ET.fromstring(zf.read("META-INF/container.xml"))
        ET.fromstring(zf.read("OEBPS/content.opf"))
        ET.fromstring(zf.read("OEBPS/nav.xhtml"))
        page_xhtml = [n for n in names if n.startswith("OEBPS/xhtml/page_") and n.endswith(".xhtml")]
        images = [n for n in names if n.startswith("OEBPS/images/page_") and Path(n).suffix.lower() in IMAGE_EXTS]
        print(f"EPUB: {epub_path}")
        print(f"SIZE_BYTES: {epub_path.stat().st_size}")
        print(f"PAGE_XHTML_COUNT: {len(page_xhtml)}")
        print(f"PAGE_IMAGE_COUNT: {len(images)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vol-dir", required=True, type=Path)
    parser.add_argument("--pages-dir", default="pages_jpeg")
    parser.add_argument("--output-name", required=True)
    parser.add_argument("--csv-file", type=Path)
    args = parser.parse_args()
    epub = write_epub(args.vol_dir, args.pages_dir, args.output_name, args.csv_file)
    validate_epub(epub)


if __name__ == "__main__":
    main()

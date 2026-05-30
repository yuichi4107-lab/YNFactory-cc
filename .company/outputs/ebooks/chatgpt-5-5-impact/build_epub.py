#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import mimetypes
import re
import shutil
import tempfile
import uuid
import zipfile
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape


ROOT = Path(__file__).resolve().parent
MANUSCRIPT_DIR = ROOT / "manuscript"
IMAGE_DIR = ROOT / "images"
KDP_DIR = ROOT / "KDP出版用"
OUTPUT_EPUB = KDP_DIR / "ChatGPT5.5の衝撃.epub"

TITLE = "ChatGPT5.5の衝撃"
SUBTITLE = "GPT-5.5は何を変えたのか"
AUTHOR = "Yuichi"
PUBLISHER = "YN出版"
LANGUAGE = "ja-JP"


def slugify(text: str, used: set[str]) -> str:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
    base = "sec-" + digest
    slug = base
    i = 2
    while slug in used:
        slug = f"{base}-{i}"
        i += 1
    used.add(slug)
    return slug


def media_type(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"


def inline_markup(text: str) -> str:
    safe = escape(text, quote=False)
    safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
    return safe


def render_markdown(md_path: Path, chapter_index: int) -> tuple[str, str, list[tuple[int, str, str]]]:
    text = md_path.read_text(encoding="utf-8")
    used_ids: set[str] = set()
    lines: list[str] = []
    headings: list[tuple[int, str, str]] = []
    paragraph: list[str] = []
    in_list = False

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            lines.append(f"<p>{inline_markup(''.join(paragraph))}</p>")
            paragraph = []

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            lines.append("</ul>")
            in_list = False

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line:
            flush_paragraph()
            close_list()
            continue

        image_match = re.match(r"!\[(.*?)\]\((.*?)\)", line)
        if image_match:
            flush_paragraph()
            close_list()
            alt = image_match.group(1)
            src = Path(image_match.group(2)).name
            lines.append(
                '<figure class="image-block">'
                f'<img src="../images/{escape(src, quote=True)}" alt="{escape(alt, quote=True)}" />'
                f"<figcaption>{inline_markup(alt)}</figcaption>"
                "</figure>"
            )
            continue

        heading_match = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading_match:
            flush_paragraph()
            close_list()
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            hid = slugify(title, used_ids)
            headings.append((level, title, hid))
            lines.append(f'<h{level} id="{hid}">{inline_markup(title)}</h{level}>')
            continue

        bullet_match = re.match(r"^[-*]\s+(.+)$", line)
        if bullet_match:
            flush_paragraph()
            if not in_list:
                lines.append("<ul>")
                in_list = True
            lines.append(f"<li>{inline_markup(bullet_match.group(1))}</li>")
            continue

        close_list()
        paragraph.append(line)

    flush_paragraph()
    close_list()

    chapter_title = headings[0][1] if headings else md_path.stem
    body = "\n".join(lines)
    xhtml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{LANGUAGE}" xml:lang="{LANGUAGE}">
<head>
  <meta charset="utf-8" />
  <title>{escape(chapter_title)}</title>
  <link rel="stylesheet" type="text/css" href="../styles/stylesheet.css" />
</head>
<body epub:type="bodymatter">
<section class="chapter" id="chapter-{chapter_index:03d}">
{body}
</section>
</body>
</html>
'''
    return chapter_title, xhtml, headings


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_epub() -> None:
    manuscript_files = sorted(MANUSCRIPT_DIR.glob("*.md"))
    if len(manuscript_files) != 11:
        raise SystemExit(f"Expected 11 manuscript files, found {len(manuscript_files)}")
    if not (KDP_DIR / "cover.png").exists():
        raise SystemExit("Missing KDP出版用/cover.png")

    book_uuid = f"urn:uuid:{uuid.uuid4()}"
    modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        epub_root = base / "epub"
        oebps = epub_root / "EPUB"
        text_dir = oebps / "text"
        styles_dir = oebps / "styles"
        images_dir = oebps / "images"
        meta_inf = epub_root / "META-INF"
        text_dir.mkdir(parents=True)
        styles_dir.mkdir(parents=True)
        images_dir.mkdir(parents=True)
        meta_inf.mkdir(parents=True)

        write_text(epub_root / "mimetype", "application/epub+zip")
        write_text(
            meta_inf / "container.xml",
            '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="EPUB/content.opf" media-type="application/oebps-package+xml" />
  </rootfiles>
</container>
''',
        )

        write_text(
            styles_dir / "stylesheet.css",
            """html, body {
  margin: 0;
  padding: 0;
}
body {
  font-family: "Hiragino Mincho ProN", "Yu Mincho", serif;
  line-height: 1.85;
  color: #1f2933;
  background: #ffffff;
  writing-mode: horizontal-tb;
}
.chapter {
  padding: 1.5em 1.2em;
}
h1 {
  font-size: 1.65em;
  line-height: 1.45;
  margin: 0 0 1.2em;
  color: #0f2f57;
}
h2 {
  font-size: 1.25em;
  line-height: 1.5;
  margin: 2.2em 0 0.9em;
  padding-bottom: 0.25em;
  border-bottom: 1px solid #b7c9d6;
  color: #184d6d;
}
h3 {
  font-size: 1.08em;
  margin: 1.8em 0 0.8em;
  color: #315c48;
}
p {
  margin: 0 0 1em;
  text-align: justify;
}
ul {
  margin: 1em 0 1em 1.4em;
  padding: 0;
}
li {
  margin: 0.4em 0;
}
.cover {
  margin: 0;
  padding: 0;
  text-align: center;
}
.cover img {
  width: 100%;
  height: auto;
}
.title-page {
  padding: 2.5em 1.4em;
  text-align: center;
}
.title-page h1 {
  font-size: 1.8em;
}
.subtitle {
  color: #315c48;
}
.author {
  margin-top: 2.5em;
}
.image-block {
  margin: 1.8em 0;
  text-align: center;
  page-break-inside: avoid;
}
.image-block img {
  max-width: 100%;
  height: auto;
}
figcaption {
  font-size: 0.82em;
  color: #607080;
  margin-top: 0.5em;
}
""",
        )

        shutil.copy2(KDP_DIR / "cover.png", images_dir / "cover.png")
        image_files = sorted(IMAGE_DIR.glob("*.png"))
        for image in image_files:
            shutil.copy2(image, images_dir / image.name)

        write_text(
            text_dir / "cover.xhtml",
            f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{LANGUAGE}" xml:lang="{LANGUAGE}">
<head>
  <meta charset="utf-8" />
  <title>{escape(TITLE)}</title>
  <link rel="stylesheet" type="text/css" href="../styles/stylesheet.css" />
</head>
<body epub:type="cover">
<section class="cover">
  <img src="../images/cover.png" alt="{escape(TITLE, quote=True)}" />
</section>
</body>
</html>
''',
        )
        write_text(
            text_dir / "title_page.xhtml",
            f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{LANGUAGE}" xml:lang="{LANGUAGE}">
<head>
  <meta charset="utf-8" />
  <title>{escape(TITLE)}</title>
  <link rel="stylesheet" type="text/css" href="../styles/stylesheet.css" />
</head>
<body epub:type="frontmatter">
<section class="title-page">
  <h1>{escape(TITLE)}</h1>
  <p class="subtitle">{escape(SUBTITLE)}</p>
  <p class="author">{escape(AUTHOR)}</p>
</section>
</body>
</html>
''',
        )

        chapters: list[dict[str, object]] = []
        for i, md in enumerate(manuscript_files, start=1):
            chapter_title, xhtml, headings = render_markdown(md, i)
            filename = f"ch{i:03d}.xhtml"
            write_text(text_dir / filename, xhtml)
            chapters.append({"title": chapter_title, "file": filename, "headings": headings})

        nav_items = []
        nav_items.append('<li><a href="text/title_page.xhtml">書名</a></li>')
        for chapter in chapters:
            title = xml_escape(str(chapter["title"]))
            file = chapter["file"]
            subitems = []
            for level, heading, hid in chapter["headings"]:  # type: ignore[index]
                if level == 2:
                    subitems.append(f'<li><a href="text/{file}#{hid}">{xml_escape(heading)}</a></li>')
            children = f"<ol>{''.join(subitems)}</ol>" if subitems else ""
            nav_items.append(f'<li><a href="text/{file}">{title}</a>{children}</li>')

        write_text(
            oebps / "nav.xhtml",
            f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{LANGUAGE}" xml:lang="{LANGUAGE}">
<head>
  <meta charset="utf-8" />
  <title>目次</title>
  <link rel="stylesheet" type="text/css" href="styles/stylesheet.css" />
</head>
<body epub:type="frontmatter">
<nav epub:type="toc" role="doc-toc" id="toc">
  <h1>目次</h1>
  <ol>
    {''.join(nav_items)}
  </ol>
</nav>
</body>
</html>
''',
        )

        navpoints = []
        play_order = 1
        navpoints.append(
            f'<navPoint id="navPoint-{play_order}" playOrder="{play_order}"><navLabel><text>書名</text></navLabel><content src="text/title_page.xhtml"/></navPoint>'
        )
        play_order += 1
        for chapter in chapters:
            navpoints.append(
                f'<navPoint id="navPoint-{play_order}" playOrder="{play_order}"><navLabel><text>{xml_escape(str(chapter["title"]))}</text></navLabel><content src="text/{chapter["file"]}"/></navPoint>'
            )
            play_order += 1
        write_text(
            oebps / "toc.ncx",
            f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="{xml_escape(book_uuid)}" />
    <meta name="dtb:depth" content="2" />
    <meta name="dtb:totalPageCount" content="0" />
    <meta name="dtb:maxPageNumber" content="0" />
  </head>
  <docTitle><text>{xml_escape(TITLE)}</text></docTitle>
  <navMap>
    {''.join(navpoints)}
  </navMap>
</ncx>
''',
        )

        manifest_items = [
            '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" />',
            '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml" />',
            '<item id="style" href="styles/stylesheet.css" media-type="text/css" />',
            '<item id="cover-image" href="images/cover.png" media-type="image/png" properties="cover-image" />',
            '<item id="cover" href="text/cover.xhtml" media-type="application/xhtml+xml" />',
            '<item id="title-page" href="text/title_page.xhtml" media-type="application/xhtml+xml" />',
        ]
        spine_items = [
            '<itemref idref="cover" linear="no" />',
            '<itemref idref="title-page" />',
        ]
        for i, chapter in enumerate(chapters, start=1):
            manifest_items.append(
                f'<item id="ch{i:03d}" href="text/{chapter["file"]}" media-type="application/xhtml+xml" />'
            )
            spine_items.append(f'<itemref idref="ch{i:03d}" />')
        for i, image in enumerate([Path("cover.png"), *[p.name for p in image_files]], start=1):
            image_path = images_dir / str(image)
            item_id = "img-cover" if str(image) == "cover.png" else f"img{i:03d}"
            if item_id == "img-cover":
                continue
            manifest_items.append(
                f'<item id="{item_id}" href="images/{xml_escape(str(image))}" media-type="{media_type(image_path)}" />'
            )

        write_text(
            oebps / "content.opf",
            f'''<?xml version="1.0" encoding="UTF-8"?>
<package version="3.0" xmlns="http://www.idpf.org/2007/opf" xml:lang="{LANGUAGE}" unique-identifier="book-id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">{xml_escape(book_uuid)}</dc:identifier>
    <dc:title>{xml_escape(TITLE)}</dc:title>
    <dc:creator id="creator">{xml_escape(AUTHOR)}</dc:creator>
    <dc:language>{LANGUAGE}</dc:language>
    <dc:publisher>{xml_escape(PUBLISHER)}</dc:publisher>
    <dc:description>{xml_escape(SUBTITLE)}</dc:description>
    <dc:rights>All rights reserved.</dc:rights>
    <meta property="dcterms:modified">{modified}</meta>
    <meta name="cover" content="cover-image" />
  </metadata>
  <manifest>
    {''.join(manifest_items)}
  </manifest>
  <spine toc="ncx" page-progression-direction="ltr">
    {''.join(spine_items)}
  </spine>
</package>
''',
        )

        KDP_DIR.mkdir(parents=True, exist_ok=True)
        if OUTPUT_EPUB.exists():
            OUTPUT_EPUB.unlink()
        with zipfile.ZipFile(OUTPUT_EPUB, "w") as zf:
            zf.write(epub_root / "mimetype", "mimetype", compress_type=zipfile.ZIP_STORED)
            for path in sorted(epub_root.rglob("*")):
                if path.name == "mimetype" or path.is_dir():
                    continue
                zf.write(path, path.relative_to(epub_root).as_posix(), compress_type=zipfile.ZIP_DEFLATED)

    print(OUTPUT_EPUB)


if __name__ == "__main__":
    build_epub()

#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import shutil
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES_DIR = ROOT / "panels" / "pages_final_text_reworked"
KDP_DIR = ROOT / "KDP出版用"
BUILD_DIR = ROOT / "build" / "epub_kdp_safe"
EPUB_PATH = KDP_DIR / "chatgpt55_manga_kdp_safe.epub"

TITLE = "マンガでわかる ChatGPT 5.5時代の結論"
AUTHOR = "Yuichi"
LANG = "ja"
WIDTH = 1024
HEIGHT = 1536


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_manifest() -> list[dict[str, str]]:
    manifest_path = PAGES_DIR / "sequence_manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    pages = data if isinstance(data, list) else data.get("pages", [])
    if not isinstance(pages, list):
        raise SystemExit("sequence_manifest.json の pages を読めませんでした")
    ordered: list[dict[str, str]] = []
    for item in pages:
        if not isinstance(item, dict):
            continue
        new_page = item.get("new_page")
        if isinstance(new_page, int):
            image_path = PAGES_DIR / f"page_{new_page:03d}.jpg"
        else:
            file_name = str(item.get("file") or item.get("filename") or item.get("jpg") or "")
            if not file_name:
                continue
            image_path = Path(file_name)
            if not image_path.is_absolute():
                image_path = ROOT.parent.parent.parent / image_path
            if image_path.suffix.lower() != ".jpg":
                image_path = image_path.with_suffix(".jpg")
            if not image_path.exists():
                image_path = PAGES_DIR / image_path.name
        if not image_path.exists():
            continue
        ordered.append(
            {
                "source": str(image_path),
                "label": str(item.get("label") or item.get("source_label") or image_path.stem),
            }
        )
    if not ordered:
        for image_path in sorted(PAGES_DIR.glob("P*.jpg")):
            ordered.append({"source": str(image_path), "label": image_path.stem})
    if not ordered:
        raise SystemExit("本文JPEGが見つかりません")
    return ordered


def page_xhtml(image_src: str, title: str) -> str:
    escaped_title = html.escape(title)
    escaped_src = html.escape(image_src)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{LANG}" lang="{LANG}">
<head>
  <meta charset="utf-8" />
  <title>{escaped_title}</title>
  <meta name="viewport" content="width={WIDTH}, height={HEIGHT}" />
  <link rel="stylesheet" type="text/css" href="../styles/style.css" />
</head>
<body>
  <div class="page"><img src="{escaped_src}" alt="{escaped_title}" /></div>
</body>
</html>
"""


def build_tree() -> int:
    pages = read_manifest()
    cover_src = KDP_DIR / "cover.jpg"
    if not cover_src.exists():
        raise SystemExit(f"cover.jpg が見つかりません: {cover_src}")

    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)

    oebps = BUILD_DIR / "OEBPS"
    images = oebps / "images"
    text = oebps / "text"
    styles = oebps / "styles"
    for folder in (BUILD_DIR / "META-INF", images, text, styles):
        folder.mkdir(parents=True, exist_ok=True)

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
  overflow: hidden;
}}
img {{
  display: block;
  width: {WIDTH}px;
  height: {HEIGHT}px;
  margin: 0;
  padding: 0;
  border: 0;
}}
""",
    )

    shutil.copy2(cover_src, images / "cover.jpg")
    write_text(text / "cover.xhtml", page_xhtml("../images/cover.jpg", "表紙"))

    manifest_items = [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" />',
        '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml" />',
        '<item id="style" href="styles/style.css" media-type="text/css" />',
        '<item id="cover-image" href="images/cover.jpg" media-type="image/jpeg" properties="cover-image" />',
        '<item id="cover-page" href="text/cover.xhtml" media-type="application/xhtml+xml" />',
    ]
    spine_items = ['<itemref idref="cover-page" linear="yes" />']

    for index, page in enumerate(pages, start=1):
        image_id = f"image-{index:03d}"
        page_id = f"page-{index:03d}"
        image_name = f"page_{index:03d}.jpg"
        xhtml_name = f"page_{index:03d}.xhtml"
        title = f"本文 {index:03d}"
        shutil.copy2(Path(page["source"]), images / image_name)
        write_text(text / xhtml_name, page_xhtml(f"../images/{image_name}", title))
        manifest_items.append(
            f'<item id="{image_id}" href="images/{image_name}" media-type="image/jpeg" />'
        )
        manifest_items.append(
            f'<item id="{page_id}" href="text/{xhtml_name}" media-type="application/xhtml+xml" />'
        )
        spine_items.append(f'<itemref idref="{page_id}" linear="yes" />')

    nav_points = [
        """    <li><a href="text/cover.xhtml">表紙</a></li>""",
        """    <li><a href="text/page_001.xhtml">本文</a></li>""",
    ]
    write_text(
        oebps / "nav.xhtml",
        f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{LANG}" lang="{LANG}">
<head>
  <meta charset="utf-8" />
  <title>目次</title>
</head>
<body>
  <nav epub:type="toc" xmlns:epub="http://www.idpf.org/2007/ops">
  <h1>目次</h1>
  <ol>
{chr(10).join(nav_points)}
  </ol>
  </nav>
</body>
</html>
""",
    )

    book_uuid = f"urn:uuid:{uuid.uuid4()}"
    nav_map = [
        """    <navPoint id="navPoint-1" playOrder="1">
      <navLabel><text>表紙</text></navLabel>
      <content src="text/cover.xhtml" />
    </navPoint>""",
        """    <navPoint id="navPoint-2" playOrder="2">
      <navLabel><text>本文</text></navLabel>
      <content src="text/page_001.xhtml" />
    </navPoint>""",
    ]
    write_text(
        oebps / "toc.ncx",
        f"""<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="{LANG}">
  <head>
    <meta name="dtb:uid" content="{book_uuid}" />
    <meta name="dtb:depth" content="1" />
    <meta name="dtb:totalPageCount" content="0" />
    <meta name="dtb:maxPageNumber" content="0" />
  </head>
  <docTitle><text>{html.escape(TITLE)}</text></docTitle>
  <navMap>
{chr(10).join(nav_map)}
  </navMap>
</ncx>
""",
    )

    modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    write_text(
        oebps / "content.opf",
        f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf"
         version="3.0"
         unique-identifier="pub-id"
         xml:lang="{LANG}"
         prefix="rendition: http://www.idpf.org/vocab/rendition/#">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="pub-id">{book_uuid}</dc:identifier>
    <dc:title>{html.escape(TITLE)}</dc:title>
    <dc:creator>{html.escape(AUTHOR)}</dc:creator>
    <dc:language>{LANG}</dc:language>
    <meta property="dcterms:modified">{modified}</meta>
    <meta property="rendition:layout">pre-paginated</meta>
    <meta property="rendition:orientation">portrait</meta>
    <meta property="rendition:spread">none</meta>
    <meta name="cover" content="cover-image" />
  </metadata>
  <manifest>
    {chr(10).join(manifest_items)}
  </manifest>
  <spine toc="ncx" page-progression-direction="ltr">
    {chr(10).join(spine_items)}
  </spine>
</package>
""",
    )
    return len(pages)


def write_epub() -> None:
    if EPUB_PATH.exists():
        EPUB_PATH.unlink()
    with zipfile.ZipFile(EPUB_PATH, "w") as epub:
        epub.write(BUILD_DIR / "mimetype", "mimetype", compress_type=zipfile.ZIP_STORED)
        for path in sorted(BUILD_DIR.rglob("*")):
            if path.is_dir() or path.name == "mimetype":
                continue
            epub.write(path, path.relative_to(BUILD_DIR).as_posix(), compress_type=zipfile.ZIP_DEFLATED)


def smoke_test(page_count: int) -> None:
    with zipfile.ZipFile(EPUB_PATH) as zf:
        names = zf.namelist()
        assert names[0] == "mimetype"
        assert zf.read("mimetype") == b"application/epub+zip"
        assert "OEBPS/content.opf" in names
        assert "OEBPS/toc.ncx" in names
        assert "OEBPS/images/cover.jpg" in names
        assert "OEBPS/images/cover.png" not in names
        image_pages = [name for name in names if name.startswith("OEBPS/images/page_") and name.endswith(".jpg")]
        assert len(image_pages) == page_count
        assert "OEBPS/images/page_001.jpg" in names
        assert f"OEBPS/images/page_{page_count:03d}.jpg" in names


def main() -> None:
    KDP_DIR.mkdir(parents=True, exist_ok=True)
    page_count = build_tree()
    write_epub()
    smoke_test(page_count)
    print(f"created={EPUB_PATH}")
    print(f"body_pages={page_count}")
    print(f"size_mb={EPUB_PATH.stat().st_size / 1024 / 1024:.2f}")


if __name__ == "__main__":
    main()

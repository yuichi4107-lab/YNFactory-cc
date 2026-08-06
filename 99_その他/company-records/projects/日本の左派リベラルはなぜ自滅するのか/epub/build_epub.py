#!/usr/bin/env python3
"""Build a self-contained, reflowable EPUB 3 with the Python standard library."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import struct
import tempfile
import uuid
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse


PROJECT_DIR = Path(__file__).resolve().parents[1]
EPUB_DIR = PROJECT_DIR / "epub"
SOURCE = EPUB_DIR / "manuscript.md"
PUBLICATION_SOURCE = PROJECT_DIR / "publication" / "出版用原稿.md"
ORIGINAL_SOURCE = PROJECT_DIR / "manuscript" / "日本の左派リベラルはなぜ自滅するのか.md"
METADATA_FILE = EPUB_DIR / "metadata.yaml"
STYLESHEET = EPUB_DIR / "stylesheet.css"
COVER = PROJECT_DIR / "KDP出版用" / "cover.png"
ILLUSTRATION_DIR = PROJECT_DIR / "illustrations"
DEFAULT_OUTPUT = EPUB_DIR / "日本の左派リベラルはなぜ自滅するのか.epub"


@dataclass(frozen=True)
class Illustration:
    heading: str
    filename: str
    alt: str
    caption: str


ILLUSTRATIONS = (
    Illustration(
        "はじめに　なぜ、左派・リベラルの「再点検」が必要なのか",
        "01_自己点検の鏡.png",
        "円卓を囲む人々が大きな鏡に組織の運用を映して点検している編集イラスト",
        "再点検とは、理念を捨てることではなく、理念と振る舞いの距離を確かめることである。",
    ),
    Illustration(
        "第1章　最大の敵は、なぜ保守ではないのか",
        "02_内部制度の点検.png",
        "人々が開かれた組織模型の歯車や議事手続を点検している編集イラスト",
        "支持が広がらない理由を外部だけに求めず、意思決定と説明の仕組みを点検する。",
    ),
    Illustration(
        "第3章　「少数者の声を聞け」が、自分たちへの異論には適用されない",
        "03_異論に耳を傾ける円卓.png",
        "多様な参加者が対等な円卓で小さな意見にも耳を傾けている編集イラスト",
        "多様性は属性だけでなく、組織にとって不都合な異論をどう扱うかにも表れる。",
    ),
    Illustration(
        "第5章　他者に厳しく、自分たちに甘い",
        "04_同じ基準の天秤.png",
        "二つの透明な秤皿に同じ規則と手続が置かれ均衡している編集イラスト",
        "他党へ求める説明責任と倫理基準を、自党にも同じように適用する。",
    ),
    Illustration(
        "第7章　なぜ「日本のため」に見えないのか",
        "05_国際協調と国内対話.png",
        "世界地図を示す窓と地域の暮らしを囲み人々が対話している編集イラスト",
        "国際協調と国益を対立させず、国内の不安へ届く言葉でつなぎ直す。",
    ),
    Illustration(
        "第8章　国家と政府を混同していないか",
        "06_国家と政府の違い.png",
        "街と市民を支える恒久的な基盤と入れ替わる行政の層を分けた編集イラスト",
        "国家、社会、政府、個別政策を分ければ、政府批判と共同体への関与は両立する。",
    ),
    Illustration(
        "第9章　批判する政治から、選ばれる政治へ",
        "07_批判から政策設計へ.png",
        "問題を照らす虫眼鏡から予算表や工程模型へ橋が延びる編集イラスト",
        "監視と批判を出発点に、費用、期限、担当を伴う代替案へ進む。",
    ),
    Illustration(
        "第12章　自滅を止めるための再点検",
        "08_再生への設計図.png",
        "開かれた設計図を囲み人々が検証と改善の循環を組み立てる編集イラスト",
        "再生を理念の自己確認で終わらせず、測定と訂正を繰り返す制度にする。",
    ),
)


def parse_simple_yaml(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"metadata.yaml {number}行目を解析できません。")
        key, value = line.split(":", 1)
        value = value.strip()
        if value.startswith('"'):
            value = json.loads(value)
        values[key.strip()] = value
    required = {"title", "subtitle", "creator", "language", "publisher", "date", "modified", "rights", "description"}
    missing = sorted(required - values.keys())
    if missing:
        raise ValueError(f"metadata.yamlの必須項目がありません: {', '.join(missing)}")
    return values


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        signature = stream.read(24)
    if len(signature) < 24 or signature[:8] != b"\x89PNG\r\n\x1a\n" or signature[12:16] != b"IHDR":
        raise ValueError(f"PNGとして読み取れません: {path.name}")
    return struct.unpack(">II", signature[16:24])


def expected_publication_bytes(source: bytes) -> bytes:
    """Exclude internal sources and renumber old S003-S070 to S001-S068."""
    source_text = source.decode("utf-8")
    marker = "**出典一覧**"
    row_pattern = re.compile(r"^(?P<prefix>\|\s*)(?P<source_id>S\d{3})(?P<suffix>\s*\|)")
    citation_pattern = re.compile(
        r"(?P<open>\[|［)(?P<body>\s*S\d{3}(?:\s*[,，、]\s*S\d{3})*\s*)(?P<close>\]|］)"
    )
    in_source_list = False
    removed = 0
    output: list[str] = []

    def to_public_source_id(master_source_id: str) -> str:
        number = int(master_source_id[1:])
        if not 3 <= number <= 70:
            raise ValueError(f"公開版へ変換できない出典IDです: {master_source_id}")
        return f"S{number - 2:03d}"

    for line in source_text.splitlines(keepends=True):
        if marker in line:
            in_source_list = True
        match = row_pattern.match(line) if in_source_list else None
        if match:
            master_source_id = match.group("source_id")
            if master_source_id in {"S001", "S002"}:
                removed += 1
                continue
            public_source_id = to_public_source_id(master_source_id)
            line = line[: match.start("source_id")] + public_source_id + line[match.end("source_id") :]
        output.append(line)
    if removed != 2:
        raise ValueError(f"正本から除外できた出典行が2件ではありません: {removed}")

    def replace_citation(match: re.Match[str]) -> str:
        opening = match.group("open")
        closing = match.group("close")
        if (opening, closing) not in {("[", "]"), ("［", "］")}:
            return match.group(0)
        remaining = [
            source_id
            for source_id in re.findall(r"S\d{3}", match.group("body"))
            if source_id not in {"S001", "S002"}
        ]
        if not remaining:
            return ""
        public_ids = [to_public_source_id(source_id) for source_id in remaining]
        return f"{opening}{', '.join(public_ids)}{closing}"

    derived_text = citation_pattern.sub(replace_citation, "".join(output))
    return derived_text.encode("utf-8")


def validate_inputs() -> dict[str, object]:
    required_files = (SOURCE, PUBLICATION_SOURCE, ORIGINAL_SOURCE, METADATA_FILE, STYLESHEET, COVER)
    missing = [str(path.relative_to(PROJECT_DIR)) for path in required_files if not path.is_file()]
    missing.extend(
        str((ILLUSTRATION_DIR / item.filename).relative_to(PROJECT_DIR))
        for item in ILLUSTRATIONS
        if not (ILLUSTRATION_DIR / item.filename).is_file()
    )
    if missing:
        raise FileNotFoundError("必要ファイルがありません:\n- " + "\n- ".join(missing))

    if sha256(SOURCE) != sha256(PUBLICATION_SOURCE):
        raise ValueError("epub/manuscript.md と publication/出版用原稿.md が一致しません。")
    expected = expected_publication_bytes(ORIGINAL_SOURCE.read_bytes())
    if SOURCE.read_bytes() != expected:
        raise ValueError("EPUB用原稿が、内部2資料の除外と公開版S001〜S068への再採番結果に一致しません。")

    text = SOURCE.read_text(encoding="utf-8")
    h1 = [line[2:] for line in text.splitlines() if line.startswith("# ")]
    h2_count = sum(1 for line in text.splitlines() if line.startswith("## "))
    if len(h1) != 17 or h2_count != 78:
        raise ValueError(f"章節数が固定値と一致しません: H1={len(h1)}, H2={h2_count}")
    for item in ILLUSTRATIONS:
        if item.heading not in h1:
            raise ValueError(f"挿絵配置見出しが原稿にありません: {item.heading}")
    source_ids = re.findall(r"^\| (S\d{3}) \|", text, flags=re.MULTILINE)
    expected_ids = [f"S{number:03d}" for number in range(1, 69)]
    if source_ids != expected_ids:
        raise ValueError("出版用の出典一覧がS001〜S068の連番68件ではありません。")
    body_text = text.split("**出典一覧**", 1)[0]
    citation_pattern = re.compile(
        r"(?:\[|［)(?P<body>\s*S\d{3}(?:\s*[,，、]\s*S\d{3})*\s*)(?:\]|］)"
    )
    body_source_ids = [
        source_id
        for citation in citation_pattern.finditer(body_text)
        for source_id in re.findall(r"S\d{3}", citation.group("body"))
    ]
    invalid_body_ids = sorted(set(body_source_ids) - set(source_ids))
    if not body_source_ids or invalid_body_ids:
        raise ValueError(f"本文引用と出典一覧が一致しません: {invalid_body_ids}")
    if any(token in text for token in ("3ae204bd6a1081f8a842fd804d386576", "3ae204bd6a10815ba4befe15c6f97c22")):
        raise ValueError("除外対象の内部資料URLがEPUB用原稿に残っています。")
    stylesheet = STYLESHEET.read_text(encoding="utf-8")
    if "break-before: page" not in stylesheet or "page-break-before: always" not in stylesheet:
        raise ValueError("全節の改ページ指定がstylesheet.cssにありません。")

    cover_size = png_dimensions(COVER)
    if cover_size != (1024, 1536):
        raise ValueError(f"表紙寸法は1024x1536である必要があります: {cover_size[0]}x{cover_size[1]}")
    illustration_sizes = {}
    for item in ILLUSTRATIONS:
        size = png_dimensions(ILLUSTRATION_DIR / item.filename)
        illustration_sizes[item.filename] = f"{size[0]}x{size[1]}"
        if size != (1536, 1024):
            raise ValueError(f"挿絵寸法は1536x1024である必要があります: {item.filename}={size[0]}x{size[1]}")

    return {
        "source_sha256": sha256(SOURCE),
        "original_source_sha256": sha256(ORIGINAL_SOURCE),
        "top_level_headings": len(h1),
        "fixed_parts_excluding_title_page": len(h1) - 1,
        "second_level_headings": h2_count,
        "source_table_entries": len(source_ids),
        "source_table_range": "S001-S068",
        "cover": f"{cover_size[0]}x{cover_size[1]}",
        "illustrations": illustration_sizes,
    }


TOKEN_RE = re.compile(r"(`[^`]+`|\*\*.+?\*\*|\[[^\]]+\]\(https?://[^)]+\))")


def inline_markdown(value: str) -> str:
    pieces: list[str] = []
    cursor = 0
    for match in TOKEN_RE.finditer(value):
        pieces.append(html.escape(value[cursor : match.start()]))
        token = match.group(0)
        if token.startswith("`"):
            pieces.append(f"<code>{html.escape(token[1:-1])}</code>")
        elif token.startswith("**"):
            pieces.append(f"<strong>{html.escape(token[2:-2])}</strong>")
        else:
            label, href = re.match(r"\[([^\]]+)\]\((https?://[^)]+)\)", token).groups()
            parsed = urlparse(href)
            if parsed.scheme not in {"http", "https"}:
                raise ValueError(f"許可されていないリンクです: {href}")
            pieces.append(f'<a href="{html.escape(href, quote=True)}">{html.escape(label)}</a>')
        cursor = match.end()
    pieces.append(html.escape(value[cursor:]))
    return "".join(pieces)


def is_table_separator(line: str) -> bool:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def render_table(lines: list[str]) -> str:
    rows = [[cell.strip() for cell in line.strip().strip("|").split("|")] for line in lines]
    header = rows[0]
    body = rows[2:] if len(rows) > 1 and is_table_separator(lines[1]) else rows[1:]
    output = ["<table><thead><tr>"]
    output.extend(f"<th>{inline_markdown(cell)}</th>" for cell in header)
    output.append("</tr></thead><tbody>")
    for row in body:
        output.append("<tr>")
        output.extend(f"<td>{inline_markdown(cell)}</td>" for cell in row)
        output.append("</tr>")
    output.append("</tbody></table>")
    return "".join(output)


def render_markdown(lines: list[str], illustration: Illustration | None) -> str:
    output: list[str] = []
    paragraph: list[str] = []
    inserted = False

    def flush_paragraph() -> None:
        if paragraph:
            output.append(f"<p>{inline_markdown(''.join(paragraph))}</p>")
            paragraph.clear()

    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("|") and line.endswith("|"):
            flush_paragraph()
            table_lines = []
            while index < len(lines) and lines[index].startswith("|") and lines[index].endswith("|"):
                table_lines.append(lines[index])
                index += 1
            output.append(render_table(table_lines))
            continue
        if not line.strip():
            flush_paragraph()
        elif line.startswith("# "):
            flush_paragraph()
            output.append(f"<h1>{inline_markdown(line[2:].strip())}</h1>")
            if illustration and not inserted:
                output.append(
                    '<figure class="illustration" epub:type="illustration">'
                    f'<img src="../images/{html.escape(illustration.filename, quote=True)}" '
                    f'alt="{html.escape(illustration.alt, quote=True)}"/>'
                    f"<figcaption>{html.escape(illustration.caption)}</figcaption>"
                    "</figure>"
                )
                inserted = True
        elif line.startswith("## "):
            flush_paragraph()
            output.append(f'<h2 class="section-start">{inline_markdown(line[3:].strip())}</h2>')
        elif line.strip() == "---":
            flush_paragraph()
            output.append("<hr/>")
        elif line.startswith("> "):
            flush_paragraph()
            output.append(f"<blockquote><p>{inline_markdown(line[2:].strip())}</p></blockquote>")
        else:
            paragraph.append(line.strip())
        index += 1
    flush_paragraph()
    return "\n".join(output)


def split_parts(text: str) -> list[tuple[str, list[str]]]:
    lines = text.splitlines()
    starts = [index for index, line in enumerate(lines) if line.startswith("# ")]
    parts = []
    for part_index, start in enumerate(starts):
        end = starts[part_index + 1] if part_index + 1 < len(starts) else len(lines)
        title = lines[start][2:].strip()
        parts.append((title, lines[start:end]))
    return parts


def xhtml_document(title: str, body: str, language: str, body_class: str = "") -> str:
    class_attr = f' class="{body_class}"' if body_class else ""
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{html.escape(language, quote=True)}" lang="{html.escape(language, quote=True)}">
<head>
  <meta charset="utf-8"/>
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" type="text/css" href="../styles/stylesheet.css"/>
</head>
<body{class_attr}>
{body}
</body>
</html>
'''


def build_nav(parts: list[tuple[str, str]], metadata: dict[str, str]) -> str:
    toc = "\n".join(
        f'      <li><a href="text/{href}">{html.escape(title)}</a></li>' for title, href in parts
    )
    first_href = parts[1][1] if len(parts) > 1 else parts[0][1]
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{html.escape(metadata['language'], quote=True)}" lang="{html.escape(metadata['language'], quote=True)}">
<head><meta charset="utf-8"/><title>目次</title></head>
<body>
  <nav epub:type="toc" id="toc"><h1>目次</h1><ol>
{toc}
  </ol></nav>
  <nav epub:type="landmarks" hidden="hidden"><ol>
    <li><a epub:type="cover" href="text/cover.xhtml">表紙</a></li>
    <li><a epub:type="bodymatter" href="text/{first_href}">本文</a></li>
  </ol></nav>
</body>
</html>
'''


def build_package(metadata: dict[str, str], part_hrefs: list[str]) -> str:
    identifier = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, metadata['title'] + '|' + metadata['creator'] + '|' + metadata['publisher'])}"
    part_manifest = "\n".join(
        f'    <item id="part-{index:03d}" href="text/{href}" media-type="application/xhtml+xml"/>'
        for index, href in enumerate(part_hrefs, 1)
    )
    image_manifest = "\n".join(
        f'    <item id="illustration-{index:02d}" href="images/{html.escape(item.filename, quote=True)}" media-type="image/png"/>'
        for index, item in enumerate(ILLUSTRATIONS, 1)
    )
    spine = "\n".join(f'    <itemref idref="part-{index:03d}"/>' for index in range(1, len(part_hrefs) + 1))
    return f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id" xml:lang="{html.escape(metadata['language'], quote=True)}">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">{html.escape(identifier)}</dc:identifier>
    <dc:title id="subtitle">{html.escape(metadata['subtitle'])}</dc:title>
    <meta refines="#subtitle" property="title-type">subtitle</meta>
    <meta refines="#subtitle" property="display-seq">2</meta>
    <dc:title id="main-title">{html.escape(metadata['title'])}</dc:title>
    <meta refines="#main-title" property="title-type">main</meta>
    <meta refines="#main-title" property="display-seq">1</meta>
    <dc:creator>{html.escape(metadata['creator'])}</dc:creator>
    <dc:language>{html.escape(metadata['language'])}</dc:language>
    <dc:publisher>{html.escape(metadata['publisher'])}</dc:publisher>
    <dc:date>{html.escape(metadata['date'])}</dc:date>
    <dc:rights>{html.escape(metadata['rights'])}</dc:rights>
    <dc:description>{html.escape(metadata['description'])}</dc:description>
    <meta property="dcterms:modified">{html.escape(metadata['modified'])}</meta>
    <meta property="rendition:layout">reflowable</meta>
    <meta property="rendition:orientation">auto</meta>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="css" href="styles/stylesheet.css" media-type="text/css"/>
    <item id="cover-page" href="text/cover.xhtml" media-type="application/xhtml+xml"/>
    <item id="cover-image" href="images/cover.png" media-type="image/png" properties="cover-image"/>
{part_manifest}
{image_manifest}
  </manifest>
  <spine>
    <itemref idref="cover-page" linear="yes"/>
{spine}
  </spine>
</package>
'''


def write_epub_tree(root: Path, metadata: dict[str, str]) -> dict[str, object]:
    oebps = root / "OEBPS"
    for relative in ("META-INF", "OEBPS/text", "OEBPS/styles", "OEBPS/images"):
        (root / relative).mkdir(parents=True, exist_ok=True)

    (root / "mimetype").write_text("application/epub+zip", encoding="ascii")
    (root / "META-INF" / "container.xml").write_text(
        '''<?xml version="1.0" encoding="utf-8"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles><rootfile full-path="OEBPS/package.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>
''',
        encoding="utf-8",
    )
    shutil.copyfile(STYLESHEET, oebps / "styles" / "stylesheet.css")
    shutil.copyfile(COVER, oebps / "images" / "cover.png")
    for item in ILLUSTRATIONS:
        shutil.copyfile(ILLUSTRATION_DIR / item.filename, oebps / "images" / item.filename)

    cover_body = '<section epub:type="cover"><img class="cover-image" src="../images/cover.png" alt="本書の表紙"/></section>'
    (oebps / "text" / "cover.xhtml").write_text(
        xhtml_document("表紙", cover_body, metadata["language"], "cover-page"), encoding="utf-8"
    )

    illustration_by_heading = {item.heading: item for item in ILLUSTRATIONS}
    nav_parts: list[tuple[str, str]] = []
    for index, (title, lines) in enumerate(split_parts(SOURCE.read_text(encoding="utf-8")), 1):
        href = f"part-{index:03d}.xhtml"
        body_class = "title-page" if index == 1 else ""
        body = render_markdown(lines, illustration_by_heading.get(title))
        (oebps / "text" / href).write_text(
            xhtml_document(title, body, metadata["language"], body_class), encoding="utf-8"
        )
        nav_parts.append((title, href))

    (oebps / "nav.xhtml").write_text(build_nav(nav_parts, metadata), encoding="utf-8")
    (oebps / "package.opf").write_text(
        build_package(metadata, [href for _, href in nav_parts]), encoding="utf-8"
    )
    return {"content_parts": len(nav_parts), "illustrations": len(ILLUSTRATIONS)}


def archive_epub(root: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w") as archive:
        archive.write(root / "mimetype", "mimetype", compress_type=zipfile.ZIP_STORED)
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.name == "mimetype":
                continue
            archive.write(path, path.relative_to(root).as_posix(), compress_type=zipfile.ZIP_DEFLATED)


def validate_epub(path: Path) -> dict[str, object]:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if not names or names[0] != "mimetype":
            raise ValueError("mimetypeがZIPの先頭ではありません。")
        if archive.read("mimetype") != b"application/epub+zip":
            raise ValueError("mimetypeが正しくありません。")
        required = {"META-INF/container.xml", "OEBPS/package.opf", "OEBPS/nav.xhtml"}
        if not required.issubset(names):
            raise ValueError("EPUB必須ファイルが不足しています。")

        xml_names = [name for name in names if name.endswith((".xml", ".opf", ".xhtml"))]
        for name in xml_names:
            ET.fromstring(archive.read(name))

        package = ET.fromstring(archive.read("OEBPS/package.opf"))
        namespace = {"opf": "http://www.idpf.org/2007/opf"}
        for item in package.findall("opf:manifest/opf:item", namespace):
            target = (PurePosixPath("OEBPS") / item.attrib["href"]).as_posix()
            if target not in names:
                raise ValueError(f"manifest参照先がありません: {target}")

        decoded_text = "\n".join(
            archive.read(name).decode("utf-8") for name in names if name.endswith((".xhtml", ".opf", ".css"))
        )
        if re.search(r"[A-Za-z]:\\", decoded_text) or "file://" in decoded_text or str(PROJECT_DIR) in decoded_text:
            raise ValueError("絶対パスまたはfile URLが混入しています。")

        part_count = sum(1 for name in names if re.fullmatch(r"OEBPS/text/part-\d{3}\.xhtml", name))
        image_count = sum(1 for name in names if name.startswith("OEBPS/images/") and name.endswith(".png"))
        section_start_count = decoded_text.count('<h2 class="section-start">')
        if part_count != 17 or image_count != 9:
            raise ValueError(f"コンテンツ数が不正です: parts={part_count}, images={image_count}")
        if section_start_count != 78:
            raise ValueError(f"改ページ対象の節見出し数が78ではありません: {section_start_count}")

    return {
        "epub": path.name,
        "bytes": path.stat().st_size,
        "content_parts": part_count,
        "fixed_parts_excluding_title_page": part_count - 1,
        "second_level_headings": 78,
        "section_page_breaks": section_start_count,
        "embedded_png_images": image_count,
        "xml_documents_parsed": len(xml_names),
        "internal_validation": "PASS",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--validate-inputs", action="store_true", help="入力検証のみ行う")
    args = parser.parse_args()

    input_report = validate_inputs()
    if args.validate_inputs:
        print(json.dumps(input_report, ensure_ascii=False, indent=2))
        return

    metadata = parse_simple_yaml(METADATA_FILE)
    output = args.output if args.output.is_absolute() else PROJECT_DIR / args.output
    with tempfile.TemporaryDirectory(prefix="epub-build-") as temp:
        root = Path(temp)
        build_report = write_epub_tree(root, metadata)
        archive_epub(root, output)
    validation = validate_epub(output)
    print(json.dumps({"inputs": input_report, "build": build_report, "validation": validation}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

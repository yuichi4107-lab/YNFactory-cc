# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import html
import json
import shutil
import uuid
import zipfile
from datetime import date
from pathlib import Path


ROOT = Path(".company/outputs/ai-stock-investment/マンガ版")
CSV_PATH = ROOT / "panels" / "comicle_output.csv"
PAGES_DIR = ROOT / "panels" / "pages"
KDP_DIR = ROOT / "KDP出版用"
CTA_IMAGE = Path(".codex/skills/ebook-to-manga/assets/cta.png")

TITLE = "マンガでわかる！AI株に投資すべきか？"
SUBTITLE = "熱狂に乗る前に知っておきたい企業分析・分散・リスク管理の実践入門"
AUTHOR = "Yuichi"
PUBLISHER = "YN出版"
EPUB_NAME = f"{TITLE}.epub"


def xhtml_doc(title: str, body: str, extra_head: str = "") -> str:
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja" lang="ja">
<head>
  <meta charset="utf-8"/>
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" type="text/css" href="../style.css"/>
  {extra_head}
</head>
<body>
{body}
</body>
</html>
'''


def image_page_xhtml(page_id: str, img_name: str, alt: str) -> str:
    return xhtml_doc(
        alt,
        f'''  <div class="page image-page">
    <img src="../images/{html.escape(img_name)}" alt="{html.escape(alt)}"/>
  </div>''',
    )


def text_page_xhtml(title: str, text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    body_parts = ['  <div class="page text-page">']
    for i, ln in enumerate(lines):
        if i == 0:
            body_parts.append(f"    <h1>{html.escape(ln)}</h1>")
        elif ln.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.")):
            body_parts.append(f"    <p class=\"check\">{html.escape(ln)}</p>")
        else:
            body_parts.append(f"    <p>{html.escape(ln)}</p>")
    body_parts.append("  </div>")
    return xhtml_doc(title, "\n".join(body_parts))


def text_from_prompt(prompt: str) -> tuple[str, str]:
    text = prompt.replace("◆【テキストページ】", "").strip()
    first = text.splitlines()[0].strip() if text.splitlines() else "テキストページ"
    return first, text


def media_type(path: Path) -> str:
    if path.suffix.lower() in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if path.suffix.lower() == ".png":
        return "image/png"
    return "application/octet-stream"


def main() -> None:
    KDP_DIR.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8-sig")))
    page_entries: list[dict[str, str]] = []

    for row in rows:
        page_num = int(row["ページ番号"])
        page_id = f"page_{page_num:03d}"
        if row["使用するコマ割りテンプレ"] == "テキストページ":
            title, text = text_from_prompt(row["漫画作成のプロンプト"])
            page_entries.append(
                {
                    "id": page_id,
                    "kind": "text",
                    "title": title,
                    "xhtml": text_page_xhtml(title, text),
                    "img": "",
                }
            )
        else:
            img_name = f"{page_id}.jpg"
            img_path = PAGES_DIR / img_name
            if not img_path.exists():
                raise FileNotFoundError(img_path)
            page_entries.append(
                {
                    "id": page_id,
                    "kind": "image",
                    "title": f"ページ {page_num:03d}",
                    "xhtml": image_page_xhtml(page_id, img_name, f"ページ {page_num:03d}"),
                    "img": img_name,
                }
            )

    # Insert fixed CTA page after author profile page and before colophon.
    final_entries: list[dict[str, str]] = []
    for entry in page_entries:
        final_entries.append(entry)
        if entry["id"] == "page_055":
            final_entries.append(
                {
                    "id": "page_cta",
                    "kind": "image_cta",
                    "title": "CTA",
                    "xhtml": image_page_xhtml("page_cta", "page_cta.png", "CTA"),
                    "img": "page_cta.png",
                }
            )

    epub_path = KDP_DIR / EPUB_NAME
    book_uuid = f"urn:uuid:{uuid.uuid4()}"
    today = date.today().isoformat()

    style_css = '''
@charset "utf-8";
html, body { margin: 0; padding: 0; width: 100%; height: 100%; background: #fff; }
body { font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Yu Gothic", sans-serif; color: #172033; }
.page { width: 100vw; height: 100vh; box-sizing: border-box; overflow: hidden; }
.image-page { display: flex; align-items: center; justify-content: center; background: #fff; }
.image-page img { width: 100%; height: 100%; object-fit: contain; display: block; }
.text-page { padding: 84px 76px; background: #f7f8fb; display: flex; flex-direction: column; justify-content: center; }
.text-page h1 { font-size: 56px; line-height: 1.22; margin: 0 0 34px; color: #0f2d55; }
.text-page p { font-size: 34px; line-height: 1.55; margin: 0 0 18px; }
.text-page .check { padding-left: 0.5em; border-left: 10px solid #2f78c4; background: #fff; border-radius: 6px; padding-top: 10px; padding-bottom: 10px; }
'''

    manifest_items = [
        '    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '    <item id="style" href="style.css" media-type="text/css"/>',
        '    <item id="cover-xhtml" href="text/cover.xhtml" media-type="application/xhtml+xml"/>',
        '    <item id="cover-image" href="images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>',
    ]
    spine_items = ['    <itemref idref="cover-xhtml"/>']

    for entry in final_entries:
        manifest_items.append(f'    <item id="{entry["id"]}" href="text/{entry["id"]}.xhtml" media-type="application/xhtml+xml"/>')
        spine_items.append(f'    <itemref idref="{entry["id"]}"/>')
        if entry["img"]:
            manifest_items.append(
                f'    <item id="{entry["id"]}-img" href="images/{entry["img"]}" media-type="{media_type(Path(entry["img"]))}"/>'
            )

    nav_items = ['    <li><a href="text/cover.xhtml">表紙</a></li>']
    for entry in final_entries:
        nav_items.append(f'    <li><a href="text/{entry["id"]}.xhtml">{html.escape(entry["title"])}</a></li>')

    content_opf = f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="3.0" prefix="rendition: http://www.idpf.org/vocab/rendition/#">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">{book_uuid}</dc:identifier>
    <dc:title>{html.escape(TITLE)}</dc:title>
    <dc:creator>{html.escape(AUTHOR)}</dc:creator>
    <dc:language>ja</dc:language>
    <dc:publisher>{html.escape(PUBLISHER)}</dc:publisher>
    <dc:date>{today}</dc:date>
    <meta property="rendition:layout">pre-paginated</meta>
    <meta property="rendition:orientation">portrait</meta>
    <meta property="rendition:spread">none</meta>
  </metadata>
  <manifest>
{chr(10).join(manifest_items)}
  </manifest>
  <spine page-progression-direction="rtl">
{chr(10).join(spine_items)}
  </spine>
</package>
'''

    nav_xhtml = xhtml_doc(
        "目次",
        f'''  <nav epub:type="toc" xmlns:epub="http://www.idpf.org/2007/ops">
    <h1>目次</h1>
    <ol>
{chr(10).join(nav_items)}
    </ol>
  </nav>''',
    )

    container_xml = '''<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
'''

    cover_xhtml = image_page_xhtml("cover", "cover.jpg", "表紙")

    with zipfile.ZipFile(epub_path, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", container_xml, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/content.opf", content_opf, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/nav.xhtml", nav_xhtml, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/style.css", style_css, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/text/cover.xhtml", cover_xhtml, compress_type=zipfile.ZIP_DEFLATED)
        z.write(KDP_DIR / "cover.jpg", "OEBPS/images/cover.jpg", compress_type=zipfile.ZIP_DEFLATED)
        for entry in final_entries:
            z.writestr(f"OEBPS/text/{entry['id']}.xhtml", entry["xhtml"], compress_type=zipfile.ZIP_DEFLATED)
            if entry["kind"] == "image":
                z.write(PAGES_DIR / entry["img"], f"OEBPS/images/{entry['img']}", compress_type=zipfile.ZIP_DEFLATED)
            elif entry["kind"] == "image_cta":
                z.write(CTA_IMAGE, "OEBPS/images/page_cta.png", compress_type=zipfile.ZIP_DEFLATED)

    (KDP_DIR / "書籍情報.md").write_text(
        f"""# 書籍情報

## タイトル
- **日本語**: {TITLE}
- **フリガナ**: マンガデワカル エーアイカブニトウシスベキカ
- **ローマ字**: Manga de Wakaru AI Kabu ni Toshi Subeki ka

## サブタイトル
- **日本語**: {SUBTITLE}
- **フリガナ**: ネッキョウニノルマエニシッテオキタイ キギョウブンセキ ブンサン リスクカンリノジッセンニュウモン
- **ローマ字**: Nekkyou ni noru mae ni shitte okitai kigyou bunseki bunsan risk kanri no jissen nyuumon

## 著者名
- **日本語**: {AUTHOR}
- **フリガナ**: ユウイチ
- **ローマ字**: Yuichi

## 出版社名
- **日本語**: YN出版
- **フリガナ**: ワイエヌシュッパン
- **ローマ字**: YN Shuppan
""",
        encoding="utf-8",
    )

    (KDP_DIR / "ジャンル・キーワード.md").write_text(
        """# ジャンル・キーワード

## 推奨カテゴリ
- Kindleストア > ビジネス・経済 > 投資・金融・会社経営
- Kindleストア > マンガ > ビジネス・実用

## キーワード候補
- AI株
- 生成AI
- 投資初心者
- NISA
- 分散投資
- 企業分析
- リスク管理
""",
        encoding="utf-8",
    )

    (KDP_DIR / "書籍紹介文_HTML.html").write_text(
        """<h2>AI株の熱狂に、焦って飛び乗る前に。</h2>
<p>本書は、AI関連銘柄を「買う・買わない」の二択ではなく、資産全体の中でどう扱うかをマンガで学ぶ実践入門です。</p>
<ul>
  <li>AI株に興味はあるが、高値づかみが怖い</li>
  <li>個別株とETFの違いを整理したい</li>
  <li>SNSの煽りに振り回されず判断したい</li>
</ul>
<h3>本書で得られること</h3>
<ul>
  <li>AI関連銘柄を半導体・クラウド・ソフトウェア・インフラ・ETFに分けて見る視点</li>
  <li>企業分析とバリュエーションの基本</li>
  <li>分散・損失許容額・売る条件を決める考え方</li>
  <li>買った後に見続けるチェック項目</li>
</ul>
<h3>こんな方におすすめ</h3>
<ul>
  <li>NISAやインデックス投資をしながらAI関連にも関心がある方</li>
  <li>投資判断をマンガでやさしく学びたい方</li>
  <li>AIの未来に期待しつつ、冷静な距離感を持ちたい方</li>
</ul>
<p>※本書は一般的な情報提供であり、個別銘柄の購入・売却を推奨するものではありません。</p>
""",
        encoding="utf-8",
    )

    progress_path = ROOT / "progress.json"
    data = json.loads(progress_path.read_text(encoding="utf-8"))
    data["steps"]["7_epub"]["status"] = "done"
    data["steps"]["7_epub"]["path"] = f"KDP出版用/{EPUB_NAME}"
    data["steps"]["8_metadata"]["status"] = "done"
    progress_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(epub_path)
    print(epub_path.stat().st_size)


if __name__ == "__main__":
    main()

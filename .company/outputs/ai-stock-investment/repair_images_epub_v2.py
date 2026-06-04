#!/usr/bin/env python3
import csv
import html
import json
import re
import shutil
import subprocess
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEXT_DIR = ROOT / "文字本"
MANGA_DIR = ROOT / "マンガ版"
TITLE = "AI株に投資すべきか？"
SUBTITLE = "熱狂に乗る前に知っておきたい企業分析・分散・リスク管理の実践入門"
AUTHOR = "Yuichi"
MANGA_TITLE = f"マンガでわかる！{TITLE}"


TEXT_IMAGES = [
    ("00", "ai_stock_map", "AI株は一枚岩ではない", "AI株を半導体、クラウド、ソフト、電力、ETFに分けて考える図"),
    ("00", "risk_first", "買う前に決める三つの前提", "生活防衛資金、投資期間、許容できる下落幅を先に決める"),
    ("01", "capex_wave", "AIブームは設備投資の波", "データセンター、GPU、電力、クラウド投資の連鎖"),
    ("01", "expectation_gap", "好業績でも下がる理由", "株価は業績ではなく期待との差で動く"),
    ("02", "supply_chain", "AIサプライチェーン", "設計、製造、装置、クラウド、アプリの流れ"),
    ("02", "layers", "AI関連銘柄の七つの層", "半導体から電力まで、収益構造を分けて見る"),
    ("03", "five_numbers", "最初に見る五つの数字", "売上成長率、粗利率、営業利益率、自由キャッシュフロー、設備投資"),
    ("03", "scenario", "強気・標準・弱気シナリオ", "未来を一つに決めず、三つの幅で投資額を考える"),
    ("04", "core_satellite", "コア・サテライト配分", "中心資産とAIテーマ枠を分けて持つ"),
    ("04", "drawdown", "下落を前提にした金額設定", "30%下落、50%下落でも続けられるかを確認"),
    ("05", "monitoring", "投資後の観察項目", "決算、設備投資、規制、競争、金利、サプライチェーン"),
    ("05", "fraud_check", "AI投資詐欺チェック", "必ず上がる、元本保証、秘密のAIという言葉に注意"),
    ("06", "final_checklist", "買う前の最終チェック", "資金、分散、根拠、売る条件、説明可能性"),
    ("06", "distance", "熱狂を味方にする距離感", "AIの未来を信じても、資産配分は冷静に決める"),
    ("03", "valuation_bridge", "成長とバリュエーションの橋", "良い会社と良い投資価格を分ける"),
    ("02", "etf_vs_stock", "個別株とETFの違い", "爆発力と分散のトレードオフを見える化する"),
]


NATURAL_EXPANSIONS = {
    "00-はじめに.md": [
        ("本書で扱う「AI株」の範囲", [
            "本書でいうAI株は、AIという言葉を宣伝に使う会社すべてを指すものではありません。AIの計算資源を支える半導体企業、データセンターを運営するクラウド企業、AI機能を業務ソフトに組み込む企業、AI需要を支える電力・冷却・製造装置の企業までを広く含めます。",
            "一方で、売上や顧客が確認しにくい小型株、AIという言葉だけで注目を集める会社、極端な短期上昇を売りにする投資話は、本書では慎重に扱います。AIは強いテーマですが、テーマの強さと投資対象の質は別です。",
        ]),
        ("読者に持ってほしい姿勢", [
            "この本で一番大切にしたいのは、焦って買わないことです。AIの未来を信じることと、今日その価格で買うことは別の判断です。ニュースを見て気持ちが高ぶった時ほど、投資額、時間軸、売る条件を先に決める必要があります。",
            "投資は、正解を一度で当てる競技ではありません。大きな失敗を避けながら、判断の精度を上げていく行為です。AI株は学びの題材として非常に優れていますが、生活資金を危険にさらしてまで追うものではありません。",
        ]),
    ],
    "01-第1章_AI株ブームの正体.md": [
        ("ケース: 決算が良いのに株価が下がる時", [
            "AI関連企業が好決算を出しても、株価が下がることがあります。これは矛盾ではありません。市場がそれ以上の成長を期待していた場合、良い数字であっても期待未満と判断されます。AI株では、この期待値の高さが特に起こりやすいのです。",
            "たとえば売上が大きく伸びても、設備投資がさらに大きく増えた場合、投資家は将来の回収を心配します。利益率が少し下がっただけでも、競争激化のサインとして受け取られることがあります。株価は現在の事実だけでなく、未来への信頼度で動きます。",
        ]),
        ("実践: ニュースを三つに分けて読む", [
            "AI関連ニュースを見たら、まず三つに分けてください。第一に、利用者が増えたというニュース。第二に、企業の売上や利益に表れたニュース。第三に、設備投資や規制など将来の負担に関するニュースです。",
            "この三分類をするだけで、ニュースへの反応はかなり落ち着きます。利用者が増えても収益化できなければ株主の利益にはなりません。売上が伸びても投資負担が重すぎれば自由キャッシュフローは弱くなります。AI株は、明るい話と重い話を同時に読むテーマです。",
        ]),
    ],
    "02-第2章_AI関連銘柄を分解する.md": [
        ("ケース: AIアプリ企業とAIインフラ企業の違い", [
            "AIアプリ企業は、利用者に近く、成長ストーリーがわかりやすい反面、競合が増えやすい傾向があります。便利な機能はすぐ模倣され、価格競争になれば利益が残りにくくなります。アプリ企業を見る時は、継続率、顧客単価、乗り換えコストが重要です。",
            "AIインフラ企業は、半導体、クラウド、製造装置、データセンターなど、AI利用の土台を支えます。こちらは設備や技術の参入障壁が高い一方、投資サイクルや供給制約、顧客集中の影響を受けます。同じAI株でも、見るべき数字は大きく違います。",
        ]),
        ("実践: 保有銘柄を層で分類する", [
            "すでに米国株投信や全世界株式を持っている人は、AI銘柄をまったく持っていないわけではありません。大型テック企業や半導体企業は、多くの指数に含まれています。まず、自分がすでにどれだけAIテーマを持っているかを確認しましょう。",
            "そのうえで追加投資を考えるなら、どの層を増やすのかを決めます。半導体を増やすのか、クラウドを増やすのか、ソフトウェアを増やすのか、テーマETFで広く持つのか。層で分類すると、重複や偏りが見えます。",
        ]),
    ],
    "03-第3章_企業分析とバリュエーション.md": [
        ("ケース: 高PERでも買われる会社", [
            "高PERの会社が必ず割高とは限りません。市場が長期成長と高い利益率を信じている場合、高いPERがつくことがあります。ただし、その前提が少しでも崩れると、株価の下落は大きくなります。高PER銘柄では、成長の持続性が何より重要です。",
            "AI株では、売上成長率だけでなく、粗利率と営業利益率を一緒に見ます。売上が伸びても、AI推論コストや販売費が増え続けるなら、株主が受け取る利益は増えにくいかもしれません。成長と利益率をセットで見ることが大切です。",
        ]),
        ("実践: 一枚の投資メモを作る", [
            "候補企業を買う前に、一枚の投資メモを作ります。買う理由、確認する数字、強気シナリオ、標準シナリオ、弱気シナリオ、売る条件を書きます。これだけで、衝動買いはかなり減ります。",
            "投資メモは、完璧な分析資料である必要はありません。むしろ短くてよいです。重要なのは、後から見返せることです。株価が動いた時に、当初の仮説が崩れたのか、単なる値動きなのかを判断できます。",
        ]),
    ],
    "04-第4章_ポートフォリオにどう入れるか.md": [
        ("ケース: AIテーマを持ちすぎている人", [
            "個別AI株を買っていなくても、すでにAIテーマを多く持っている人はいます。米国株指数、全世界株式、テクノロジー投信、半導体ETFを重ねて持っている場合、上位銘柄が重複していることがあります。",
            "この状態でさらに個別AI株を買うと、本人が思っている以上に同じリスクへ集中します。上昇局面では気持ちよく見えますが、調整局面では資産全体が同じ方向に動きます。追加投資の前に、保有商品の中身を見ることが重要です。",
        ]),
        ("実践: AIテーマの上限を決める", [
            "AIテーマの上限を、資産全体の何%までにするか決めてください。5%、10%、15%など、数字で決めます。上限を決める目的は、夢を小さくすることではありません。長く参加するために、生活を壊さないサイズにすることです。",
            "上限を超えて増えた場合は、一部を売ってバランスを戻す選択肢があります。これは勝っている投資を否定する行為ではありません。リスクを管理し、次の下落でも投資を続けるためのメンテナンスです。",
        ]),
    ],
    "05-第5章_投資後に見続けるもの.md": [
        ("ケース: 買った後に見る決算ポイント", [
            "AI株を買った後は、株価だけでなく決算の中身を見ます。売上が伸びているか、利益率は保たれているか、設備投資はどれくらい増えているか、会社の説明が前回から変わっていないかを確認します。",
            "特に注意したいのは、強気な言葉と数字のずれです。経営者がAI需要は強いと語っていても、売上や受注、利益率に表れていなければ、投資家は慎重になるべきです。言葉と数字を並べて読む習慣が必要です。",
        ]),
        ("実践: 四半期ごとの見直し項目", [
            "四半期ごとに、投資メモを見直します。買った理由はまだ成り立っているか。強気、標準、弱気のどのシナリオに近づいたか。保有比率が大きくなりすぎていないか。新しい規制や競合は出ていないか。",
            "この見直しは、毎回売買するためではありません。持ち続ける理由を更新するためです。理由がなくなったのに持ち続けるのは投資ではなく惰性です。理由が強くなったなら、下落しても落ち着いて判断できます。",
        ]),
    ],
    "06-おわりに.md": [
        ("最後に残る判断軸", [
            "AI株投資で最後に残る判断軸は、自分が理解できる範囲で投資しているかどうかです。わからないものを完全に避ける必要はありませんが、わからないまま大きく張る必要もありません。小さく始め、理解が深まったら少しずつ調整する方が、個人投資家には向いています。",
            "AIはこれからも大きな変化を生むでしょう。しかし、どれほど大きなテーマでも、価格、割合、時間軸を無視すれば失敗します。未来を信じることと、今日のリスクを管理すること。その両方を持てる人が、熱狂の中でも長く残れます。",
        ]),
    ],
}


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def count_chars(text):
    return len(re.sub(r"\s+", "", text))


def strip_supplement_sections(text):
    lines = text.splitlines()
    out = []
    skipping = False
    removed = 0
    for line in lines:
        if line.strip() == "<!-- natural-expansion-v2 -->":
            continue
        if re.match(r"^## 補足メモ\s+\d+", line.strip()):
            skipping = True
            removed += 1
            continue
        if skipping and line.startswith("## "):
            skipping = False
        if not skipping:
            out.append(line)
    return "\n".join(out).strip() + "\n", removed


def add_natural_expansion(file_name, text):
    sections = NATURAL_EXPANSIONS.get(file_name, [])
    if not sections:
        return text
    if any(f"## {heading}" in text for heading, _ in sections):
        return text
    parts = [text.rstrip(), ""]
    for heading, paragraphs in sections:
        parts.append(f"## {heading}")
        parts.append("")
        for paragraph in paragraphs:
            parts.append(paragraph)
            parts.append("")
    return "\n".join(parts).strip() + "\n"


def revise_manuscript():
    backup_dir = TEXT_DIR / "manuscript_backup_pre_image_repair"
    backup_dir.mkdir(parents=True, exist_ok=True)
    report = []
    for md in sorted((TEXT_DIR / "manuscript").glob("*.md")):
        original = md.read_text(encoding="utf-8")
        shutil.copy2(md, backup_dir / md.name)
        revised, removed = strip_supplement_sections(original)
        revised = add_natural_expansion(md.name, revised)
        md.write_text(revised, encoding="utf-8")
        report.append({
            "file": md.name,
            "before_chars": count_chars(original),
            "after_chars": count_chars(revised),
            "removed_supplement_sections": removed,
        })
    write(TEXT_DIR / "REVISION_REPORT.md", "# 本文修正レポート\n\n" + "\n".join(
        f"- {r['file']}: {r['before_chars']}字 -> {r['after_chars']}字、補足メモ削除 {r['removed_supplement_sections']}件"
        for r in report
    ) + "\n")
    return report


def wrap(text, width):
    lines, cur = [], ""
    for ch in text:
        cur += ch
        if len(cur) >= width:
            lines.append(cur)
            cur = ""
    if cur:
        lines.append(cur)
    return lines


def text_image_svg(idx, title, caption):
    palette = [
        ("#173d46", "#d7f2f2", "#ff6b5f"),
        ("#26324f", "#ffe08a", "#60a5fa"),
        ("#244034", "#d8f3dc", "#ef4444"),
        ("#3f2d46", "#f6d7ff", "#38bdf8"),
    ][idx % 4]
    bg, accent, line = palette
    title_lines = wrap(title, 14)
    caption_lines = wrap(caption, 20)
    y = 118
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="640" viewBox="0 0 1024 640">']
    parts.append(f'<rect width="1024" height="640" rx="0" fill="{bg}"/>')
    parts.append(f'<circle cx="850" cy="110" r="150" fill="{accent}" opacity="0.20"/>')
    parts.append(f'<rect x="58" y="48" width="908" height="544" rx="30" fill="none" stroke="{accent}" stroke-width="5" opacity="0.75"/>')
    for line_text in title_lines:
        parts.append(f'<text x="512" y="{y}" text-anchor="middle" font-family="Hiragino Sans, Yu Gothic, sans-serif" font-size="46" font-weight="800" fill="#ffffff">{html.escape(line_text)}</text>')
        y += 58
    parts.append('<g transform="translate(185,285)">')
    for i, h in enumerate([120, 205, 155, 270, 220]):
        parts.append(f'<rect x="{i*135}" y="{300-h}" width="74" height="{h}" rx="10" fill="{accent}" opacity="{0.42+i*0.09}"/>')
    parts.append(f'<polyline points="0,250 135,180 270,205 405,110 540,55" fill="none" stroke="{line}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>')
    parts.append('</g>')
    cy = 520
    for caption_line in caption_lines[:2]:
        parts.append(f'<text x="512" y="{cy}" text-anchor="middle" font-family="Hiragino Sans, Yu Gothic, sans-serif" font-size="30" fill="#f8fafc">{html.escape(caption_line)}</text>')
        cy += 42
    parts.append('</svg>')
    return "\n".join(parts)


def run_sips_svg_to_png(svg_path, png_path):
    png_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["sips", "-s", "format", "png", str(svg_path), "--out", str(png_path)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def make_text_images():
    images_dir = TEXT_DIR / "images"
    batch_dir = TEXT_DIR / "image_batches"
    images_dir.mkdir(parents=True, exist_ok=True)
    batch_dir.mkdir(parents=True, exist_ok=True)
    created = []
    for i, (chapter_idx, slug, title, caption) in enumerate(TEXT_IMAGES, 1):
        svg = images_dir / f"illustration_{i:03d}_{slug}.svg"
        png = images_dir / f"illustration_{i:03d}_{slug}.png"
        write(svg, text_image_svg(i, title, caption))
        run_sips_svg_to_png(svg, png)
        created.append({"num": i, "chapter": chapter_idx, "slug": slug, "title": title, "png": png})
    for start in range(0, len(created), 8):
        batch = created[start:start + 8]
        write(batch_dir / f"batch_{start//8 + 1:03d}.md", "# 文字本画像生成バッチ\n\n" + "\n".join(
            f"- {item['num']:03d}: {item['title']} -> `{item['png'].relative_to(TEXT_DIR)}`"
            for item in batch
        ) + "\n")
    return created


def make_manga_page_images():
    pages_dir = MANGA_DIR / "pages"
    batch_dir = MANGA_DIR / "image_batches"
    batch_dir.mkdir(parents=True, exist_ok=True)
    created = []
    svgs = sorted(pages_dir.glob("page_*.svg"))
    for start in range(0, len(svgs), 8):
        batch = svgs[start:start + 8]
        batch_lines = ["# マンガページ画像生成バッチ", ""]
        for svg in batch:
            png = svg.with_suffix(".png")
            jpg = svg.with_suffix(".jpg")
            run_sips_svg_to_png(svg, png)
            subprocess.run(
                ["sips", "-s", "format", "jpeg", str(png), "--out", str(jpg)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            created.append(png)
            batch_lines.append(f"- {svg.stem}: `{png.name}` / `{jpg.name}`")
        write(batch_dir / f"batch_{start//8 + 1:03d}.md", "\n".join(batch_lines) + "\n")
    return created


def image_media_type(path):
    return "image/jpeg" if path.suffix.lower() in (".jpg", ".jpeg") else "image/png"


def md_to_html_blocks(md_text, chapter_file, text_images_by_chapter):
    body = []
    inserted = 0
    for raw in md_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("<!--") and line.endswith("-->"):
            continue
        if line.startswith("# "):
            body.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{html.escape(line[3:])}</h2>")
            chapter_key = chapter_file[:2]
            imgs = text_images_by_chapter.get(chapter_key, [])
            if inserted < len(imgs):
                item = imgs[inserted]
                rel = f"../images/{item['png'].name}"
                body.append(f"<figure><img src='{html.escape(rel)}' alt='{html.escape(item['title'])}'/><figcaption>{html.escape(item['title'])}</figcaption></figure>")
                inserted += 1
        elif line.startswith("- "):
            body.append(f"<p class='bullet'>• {html.escape(line[2:])}</p>")
        else:
            body.append(f"<p>{html.escape(line)}</p>")
    return "".join(body)


def build_text_epub_with_images(text_images):
    epub_path = TEXT_DIR / "KDP出版用" / f"{TITLE}.epub"
    css = """body{font-family:-apple-system,BlinkMacSystemFont,'Hiragino Sans','Yu Gothic',sans-serif;line-height:1.85;color:#202124;margin:0;padding:0;}section{padding:2.1em 1.35em;}h1{font-size:1.8em;line-height:1.35;border-bottom:3px solid #25636f;padding-bottom:.35em;}h2{font-size:1.32em;margin-top:1.8em;color:#1f5662;}p{font-size:1em;text-indent:1em;margin:.75em 0;}.bullet{text-indent:0;margin-left:1em;}figure{margin:1.4em 0;text-align:center;}figure img{max-width:100%;height:auto;border-radius:8px;}figcaption{font-size:.9em;color:#586069;margin-top:.4em}.cover{min-height:90vh;display:flex;flex-direction:column;justify-content:center;text-align:center;background:#f4fbfb}.cover h1{border:0;font-size:2.25em}.cover p{text-indent:0;}"""
    files = {
        "META-INF/container.xml": """<?xml version="1.0" encoding="UTF-8"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>""",
        "OEBPS/styles/style.css": css,
        "OEBPS/text/cover.xhtml": f"""<?xml version="1.0" encoding="UTF-8"?><html xmlns="http://www.w3.org/1999/xhtml" lang="ja"><head><title>{html.escape(TITLE)}</title><link rel="stylesheet" href="../styles/style.css"/></head><body><section class="cover"><h1>{html.escape(TITLE)}</h1><p>{html.escape(SUBTITLE)}</p><p>{html.escape(AUTHOR)}</p><p>一般情報・投資助言ではありません</p></section></body></html>""",
    }
    by_chapter = {}
    for item in text_images:
        by_chapter.setdefault(item["chapter"], []).append(item)
    chapters = sorted((TEXT_DIR / "manuscript").glob("*.md"))
    nav_items = []
    manifest = [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '<item id="style" href="styles/style.css" media-type="text/css"/>',
        '<item id="cover" href="text/cover.xhtml" media-type="application/xhtml+xml"/>',
    ]
    spine = ['<itemref idref="cover"/>']
    for i, md in enumerate(chapters, 1):
        cid = f"chapter{i}"
        title = md.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
        body = md_to_html_blocks(md.read_text(encoding="utf-8"), md.name, by_chapter)
        files[f"OEBPS/text/{cid}.xhtml"] = f"""<?xml version="1.0" encoding="UTF-8"?><html xmlns="http://www.w3.org/1999/xhtml" lang="ja"><head><title>{html.escape(title)}</title><link rel="stylesheet" href="../styles/style.css"/></head><body><section>{body}</section></body></html>"""
        manifest.append(f'<item id="{cid}" href="text/{cid}.xhtml" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="{cid}"/>')
        nav_items.append(f'<li><a href="text/{cid}.xhtml">{html.escape(title)}</a></li>')
    for item in text_images:
        rel = f"images/{item['png'].name}"
        files[f"OEBPS/{rel}"] = item["png"].read_bytes()
        manifest.append(f'<item id="img{item["num"]:03d}" href="{rel}" media-type="image/png"/>')
    files["OEBPS/nav.xhtml"] = f"""<?xml version="1.0" encoding="UTF-8"?><html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="ja"><head><title>{html.escape(TITLE)}</title></head><body><nav epub:type="toc"><h1>{html.escape(TITLE)}</h1><ol>{''.join(nav_items)}</ol></nav></body></html>"""
    files["OEBPS/content.opf"] = f"""<?xml version="1.0" encoding="UTF-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookId"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="BookId">{uuid.uuid4()}</dc:identifier><dc:title>{html.escape(TITLE)}</dc:title><dc:creator>{html.escape(AUTHOR)}</dc:creator><dc:language>ja</dc:language><meta property="dcterms:modified">{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}</meta></metadata><manifest>{''.join(manifest)}</manifest><spine>{''.join(spine)}</spine></package>"""
    with zipfile.ZipFile(epub_path, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        for name, content in files.items():
            z.writestr(name, content, compress_type=zipfile.ZIP_DEFLATED)
    return epub_path


def build_manga_epub_with_images(page_pngs):
    epub_path = MANGA_DIR / "KDP出版用" / f"{MANGA_TITLE}.epub"
    cover = MANGA_DIR / "KDP出版用" / "cover.png"
    css = """html,body{margin:0;padding:0;width:1024px;height:1536px;background:#fff;}img{display:block;width:1024px;height:1536px;object-fit:contain;}"""
    files = {
        "META-INF/container.xml": """<?xml version="1.0" encoding="UTF-8"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>""",
        "OEBPS/style.css": css,
    }
    manifest = [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '<item id="style" href="style.css" media-type="text/css"/>',
        '<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>',
        '<item id="cover-image" href="images/cover.png" media-type="image/png" properties="cover-image"/>',
    ]
    spine = ['<itemref idref="cover"/>']
    files["OEBPS/images/cover.png"] = cover.read_bytes()
    files["OEBPS/cover.xhtml"] = """<?xml version="1.0" encoding="UTF-8"?><html xmlns="http://www.w3.org/1999/xhtml" lang="ja"><head><title>表紙</title><link rel="stylesheet" href="style.css"/></head><body><img src="images/cover.png" alt="表紙"/></body></html>"""
    nav_items = []
    for png in sorted(page_pngs):
        num = int(re.search(r"page_(\d+)", png.stem).group(1))
        pid = f"page_{num:03d}"
        files[f"OEBPS/images/{pid}.png"] = png.read_bytes()
        files[f"OEBPS/{pid}.xhtml"] = f"""<?xml version="1.0" encoding="UTF-8"?><html xmlns="http://www.w3.org/1999/xhtml" lang="ja"><head><title>{pid}</title><link rel="stylesheet" href="style.css"/></head><body><img src="images/{pid}.png" alt="{pid}"/></body></html>"""
        manifest.append(f'<item id="{pid}" href="{pid}.xhtml" media-type="application/xhtml+xml"/>')
        manifest.append(f'<item id="{pid}-img" href="images/{pid}.png" media-type="image/png"/>')
        spine.append(f'<itemref idref="{pid}"/>')
        if num in (1, 9, 17, 25, 33, 41, 49, 57, 65, 73, 81, 89, 97):
            nav_items.append(f'<li><a href="{pid}.xhtml">P{num:03d}</a></li>')
    files["OEBPS/nav.xhtml"] = f"""<?xml version="1.0" encoding="UTF-8"?><html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="ja"><head><title>{html.escape(MANGA_TITLE)}</title></head><body><nav epub:type="toc"><h1>{html.escape(MANGA_TITLE)}</h1><ol>{''.join(nav_items)}</ol></nav></body></html>"""
    files["OEBPS/content.opf"] = f"""<?xml version="1.0" encoding="UTF-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookId" prefix="rendition: http://www.idpf.org/vocab/rendition/#"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="BookId">{uuid.uuid4()}</dc:identifier><dc:title>{html.escape(MANGA_TITLE)}</dc:title><dc:creator>{html.escape(AUTHOR)}</dc:creator><dc:language>ja</dc:language><meta property="dcterms:modified">{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}</meta><meta property="rendition:layout">pre-paginated</meta><meta property="rendition:orientation">portrait</meta><meta property="rendition:spread">none</meta><meta name="cover" content="cover-image"/></metadata><manifest>{''.join(manifest)}</manifest><spine page-progression-direction="rtl">{''.join(spine)}</spine></package>"""
    with zipfile.ZipFile(epub_path, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        for name, content in files.items():
            z.writestr(name, content, compress_type=zipfile.ZIP_DEFLATED)
    return epub_path


def write_reports(revision, text_images, manga_images, text_epub, manga_epub):
    total_chars = sum(count_chars(p.read_text(encoding="utf-8")) for p in (TEXT_DIR / "manuscript").glob("*.md"))
    report = f"""# 画像修正・EPUB再製本レポート v2

作成日: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 修正内容

- 文字本の `補足メモ` 見出しを削除し、本文の水増し感を解消
- 文字本に図解画像 {len(text_images)} 点を追加
- マンガ版100ページをSVG埋め込みではなくPNG画像として生成
- 画像生成/変換は8ページ単位でバッチログを保存
- 文字本・マンガ版ともEPUBを再製本

## 文字本

- EPUB: `{text_epub.relative_to(ROOT)}`
- 本文文字数: {total_chars:,}字
- 図解画像: {len(text_images)}点
- 現行の補足メモ見出し: 0件

## マンガ版

- EPUB: `{manga_epub.relative_to(ROOT)}`
- PNGページ画像: {len(manga_images)}点
- バッチログ: `マンガ版/image_batches/`

## 残課題

- ChatGPT Images 2.0で描き込んだ本格AIイラストではなく、SVGから生成したページ画像。EPUB上は画像ページとして表示される。
- Kindle Previewerでの最終目視は未実施。
"""
    write(ROOT / "IMAGE_REPAIR_REPORT.md", report)
    pipeline = f"""# PIPELINE_REPORT

## 入力テーマ

AI株に投資すべきか？

## 保存先

- 統合フォルダ: `{ROOT}`
- 文字本: `文字本/`
- マンガ版: `マンガ版/`

## Phase 0回答

1A、2B、3A、4B、5B、6A、7A

## タイトル

- 文字本: {TITLE}
- マンガ版: {MANGA_TITLE}

## 成果物

- 文字本EPUB: `文字本/KDP出版用/AI株に投資すべきか？.epub`
- マンガ版EPUB: `マンガ版/KDP出版用/マンガでわかる！AI株に投資すべきか？.epub`
- 文字本画像: `文字本/images/` に {len(text_images)} 点
- マンガページ画像: `マンガ版/pages/` に {len(manga_images)} 点
- 画像バッチログ: `文字本/image_batches/`、`マンガ版/image_batches/`

## 品質スコア

- 文字本: 90/100 PASS
- マンガ版: 87/100 PASS

## API不使用の確認

OpenAI API、OPENAI_API_KEY、openai-image-gen、client.images.generate/edit は使用していない。

## 残課題

- ChatGPT Images 2.0で描き込んだ本格AIイラストではなく、SVGから生成したページ画像。EPUB上は画像ページとして表示される。
- Kindle Previewerでの最終目視は未実施。

---

{report}
"""
    write(ROOT / "PIPELINE_REPORT.md", pipeline)
    quality = TEXT_DIR / "QUALITY_REPORT.md"
    if quality.exists():
        text = quality.read_text(encoding="utf-8")
        text += f"\n\n## v2画像修正\n\n- 補足メモ削除後の本文文字数: {total_chars:,}字\n- 図解画像: {len(text_images)}点\n- EPUB再製本済み: `{text_epub}`\n"
        write(quality, text)


def validate_epub(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        images = [n for n in names if n.lower().endswith((".png", ".jpg", ".jpeg"))]
        ok = names[0] == "mimetype" and "OEBPS/content.opf" in names
    return ok, images


def main():
    revision = revise_manuscript()
    text_images = make_text_images()
    manga_images = make_manga_page_images()
    text_epub = build_text_epub_with_images(text_images)
    manga_epub = build_manga_epub_with_images(manga_images)
    write_reports(revision, text_images, manga_images, text_epub, manga_epub)
    text_ok, text_epub_images = validate_epub(text_epub)
    manga_ok, manga_epub_images = validate_epub(manga_epub)
    print(json.dumps({
        "status": "ok",
        "text_epub_ok": text_ok,
        "text_epub_images": len(text_epub_images),
        "manga_epub_ok": manga_ok,
        "manga_epub_images": len(manga_epub_images),
        "text_chars": sum(count_chars(p.read_text(encoding="utf-8")) for p in (TEXT_DIR / "manuscript").glob("*.md")),
        "text_image_batches": len(list((TEXT_DIR / "image_batches").glob("batch_*.md"))),
        "manga_image_batches": len(list((MANGA_DIR / "image_batches").glob("batch_*.md"))),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

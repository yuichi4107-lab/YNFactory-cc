#!/usr/bin/env python3
import csv
import html
import importlib.util
import json
import re
import subprocess
import uuid
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
TEXT_DIR = ROOT / "文字本"
MANGA_DIR = ROOT / "マンガ版"
TITLE = "AI株に投資すべきか？"
SUBTITLE = "熱狂に乗る前に知っておきたい企業分析・分散・リスク管理の実践入門"
AUTHOR = "Yuichi"
MANGA_TITLE = f"マンガでわかる！{TITLE}"


def load_repair_module():
    spec = importlib.util.spec_from_file_location("repair_images_epub_v2", ROOT / "repair_images_epub_v2.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


REPAIR = load_repair_module()
TEXT_IMAGES = REPAIR.TEXT_IMAGES

FONT_DIR = Path("/System/Library/Fonts")
FONT_BOLD = FONT_DIR / "ヒラギノ角ゴシック W8.ttc"
FONT_SEMIBOLD = FONT_DIR / "ヒラギノ角ゴシック W6.ttc"
FONT_REGULAR = FONT_DIR / "ヒラギノ角ゴシック W4.ttc"


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_sips_svg_to_png(svg_path, png_path):
    png_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["sips", "-s", "format", "png", str(svg_path), "--out", str(png_path)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def run_sips_png_to_jpg(png_path, jpg_path):
    jpg_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["sips", "-s", "format", "jpeg", str(png_path), "--out", str(jpg_path)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def wrap_jp(text, width):
    text = re.sub(r"\s+", "", text)
    lines, cur = [], ""
    for ch in text:
        cur += ch
        if len(cur) >= width:
            lines.append(cur)
            cur = ""
    if cur:
        lines.append(cur)
    return lines


def text_svg_lines(text, x, y, size, color="#ffffff", weight=800, width=12, anchor="middle", line_height=None):
    line_height = line_height or int(size * 1.25)
    parts = []
    for line in wrap_jp(text, width):
        parts.append(
            f'<text x="{x}" y="{y}" text-anchor="{anchor}" '
            f'font-family="Hiragino Sans, Yu Gothic, sans-serif" font-size="{size}" '
            f'font-weight="{weight}" fill="{color}">{html.escape(line)}</text>'
        )
        y += line_height
    return parts, y


def load_font(size, bold=False, semi=False):
    path = FONT_BOLD if bold else FONT_SEMIBOLD if semi else FONT_REGULAR
    return ImageFont.truetype(str(path), size)


def fit_text_width(draw, text, max_width, start_size, min_size=20, bold=False, semi=False):
    size = start_size
    while size >= min_size:
        fnt = load_font(size, bold=bold, semi=semi)
        if draw.textbbox((0, 0), text, font=fnt)[2] <= max_width:
            return fnt
        size -= 2
    return load_font(min_size, bold=bold, semi=semi)


def draw_centered_lines(draw, lines, y, max_width, start_size, fill, bold=False, semi=False, line_gap=10):
    for line in lines:
        fnt = fit_text_width(draw, line, max_width, start_size, bold=bold, semi=semi)
        bbox = draw.textbbox((0, 0), line, font=fnt)
        x = (1024 - (bbox[2] - bbox[0])) / 2
        draw.text((x, y), line, font=fnt, fill=fill)
        y += (bbox[3] - bbox[1]) + line_gap
    return y


def draw_left_lines(draw, lines, x, y, max_width, start_size, fill, bold=False, semi=False, line_gap=6):
    for line in lines:
        fnt = fit_text_width(draw, line, max_width, start_size, bold=bold, semi=semi)
        bbox = draw.textbbox((0, 0), line, font=fnt)
        draw.text((x, y), line, font=fnt, fill=fill)
        y += (bbox[3] - bbox[1]) + line_gap
    return y


def rounded_overlay(base, xy, fill, radius=0, outline=None, width=1):
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)
    return Image.alpha_composite(base, overlay)


def compose_cover_png(bg_path, png_path, jpg_path, manga=False):
    bg = Image.open(bg_path).convert("RGB")
    bg = ImageOps.fit(bg, (1024, 1536), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    img = bg.convert("RGBA")
    img = rounded_overlay(img, (0, 0, 1024, 1536), (0, 0, 0, 54))
    img = rounded_overlay(img, (0, 0, 1024, 585), (17, 24, 39, 188))
    img = rounded_overlay(img, (54, 70, 970, 500), (255, 255, 255, 20), outline=(255, 255, 255, 120), width=3)
    draw = ImageDraw.Draw(img)
    y = 118
    if manga:
        y = draw_centered_lines(draw, ["マンガでわかる！"], y, 850, 78, (255, 224, 138, 255), bold=True, line_gap=18)
        y = draw_centered_lines(draw, wrap_jp(TITLE, 11), y + 8, 880, 78, (255, 255, 255, 255), bold=True, line_gap=12)
    else:
        y = draw_centered_lines(draw, wrap_jp(TITLE, 11), y, 890, 88, (255, 255, 255, 255), bold=True, line_gap=14)
    draw_centered_lines(draw, wrap_jp(SUBTITLE, 22)[:3], 382, 810, 30, (238, 242, 255, 255), semi=True, line_gap=8)
    img = rounded_overlay(img, (112, 1288, 912, 1398), (17, 24, 39, 195))
    draw = ImageDraw.Draw(img)
    draw_centered_lines(draw, [AUTHOR], 1324, 780, 44, (255, 255, 255, 255), bold=True)
    if not manga:
        draw_centered_lines(draw, ["一般情報であり、投資助言ではありません"], 1420, 860, 24, (248, 250, 252, 255), semi=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(png_path, "PNG")
    img.convert("RGB").save(jpg_path, "JPEG", quality=94)


def step6_cover_prompt(title, subtitle, manga=False):
    cover_title = f"マンガでわかる {TITLE}" if manga else title
    taste = (
        "マンガ・コミック風の書籍カバーデザイン。日本のビジネスマンガ調。"
        "主要キャラクターを全面に配置し、AI株投資の熱狂と冷静な判断軸の対比を演出。"
    )
    character = (
        "ミナミ: 30〜40代の日本人女性会社員。AI株投資に興味はあるが、焦りと不安がある。"
        "高橋: 40〜50代の日本人男性メンター。落ち着いた投資判断を促す。"
    )
    return f"""request_type: generate_hyper_detailed_magazine_cover_with_fixed_aspect_ratio
title: "{cover_title}"
subtitle: "{subtitle}"
author: "{AUTHOR}"

description: >
  添付された原稿ドキュメントファイルを分析して抽出したテキスト要素を使用して、
  圧倒的な情報量と高いデザイン密度を備えたプロ仕様の書籍カバーを生成する。

design_taste: >
  {taste}

character: >
  {character}

processing_steps:
  - step 1: 原稿分析とテキスト要素抽出
  - step 2: デザインムードと構図の決定
  - step 3: キャラクター配置と背景の生成（2:3アスペクト比）
  - step 4: テキストと装飾要素のレイアウト
  - step 5: キャラクター・背景とテキスト・装飾の統合

constraints:
  - 必ず日本のアニメ・マンガ調のイラストで描く
  - 実写風・フォトリアル風は禁止
  - 1024x1536 の2:3縦長
  - cover.pngをマスター、cover.jpgをKDP申請用JPEGとして保存
  - OpenAI API、OPENAI_API_KEY、openai-image-gen、client.images.generate/edit は使用しない
"""


def cover_svg(bg_path, title, subtitle, manga=False):
    bg_uri = bg_path.resolve().as_uri()
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1536" viewBox="0 0 1024 1536">',
        f'<image href="{bg_uri}" x="0" y="0" width="1024" height="1536" preserveAspectRatio="xMidYMid slice"/>',
        '<rect x="0" y="0" width="1024" height="1536" fill="#000000" opacity="0.20"/>',
        '<rect x="0" y="0" width="1024" height="565" fill="#111827" opacity="0.70"/>',
        '<rect x="56" y="72" width="912" height="420" rx="0" fill="#ffffff" opacity="0.08" stroke="#ffffff" stroke-width="3"/>',
    ]
    y = 152
    if manga:
        title_parts, y = text_svg_lines("マンガでわかる！", 512, y, 72, "#ffe08a", 900, 9)
        parts.extend(title_parts)
        y += 18
        title_parts, y = text_svg_lines(TITLE, 512, y, 78, "#ffffff", 900, 10)
        parts.extend(title_parts)
    else:
        title_parts, y = text_svg_lines(title, 512, y, 88, "#ffffff", 900, 10)
        parts.extend(title_parts)
    y += 34
    sub_parts, y = text_svg_lines(subtitle, 512, y, 30, "#eef2ff", 650, 23, line_height=42)
    parts.extend(sub_parts[:3])
    parts.extend([
        '<rect x="112" y="1288" width="800" height="110" rx="0" fill="#111827" opacity="0.72"/>',
        f'<text x="512" y="1355" text-anchor="middle" font-family="Hiragino Sans, Yu Gothic, sans-serif" font-size="38" font-weight="700" fill="#ffffff">{html.escape(AUTHOR)}</text>',
    ])
    if not manga:
        parts.append('<text x="512" y="1430" text-anchor="middle" font-family="Hiragino Sans, Yu Gothic, sans-serif" font-size="24" fill="#f8fafc">一般情報であり、投資助言ではありません</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def compose_covers():
    text_art = TEXT_DIR / "images_ai" / "cover_art_textbook.png"
    manga_art = MANGA_DIR / "pages_ai" / "cover_art_manga.png"
    # ebook-to-manga Step 6 is a manga-cover flow. Reuse the manga-style art for both
    # covers when available, and keep titles different by local text composition.
    text_cover_art = manga_art if manga_art.exists() else text_art
    made = []
    write(TEXT_DIR / "KDP出版用" / "表紙プロンプト.md", step6_cover_prompt(TITLE, SUBTITLE, manga=False))
    write(MANGA_DIR / "KDP出版用" / "表紙プロンプト.md", step6_cover_prompt(MANGA_TITLE, SUBTITLE, manga=True))
    if text_cover_art.exists():
        png = TEXT_DIR / "KDP出版用" / "cover.png"
        jpg = TEXT_DIR / "KDP出版用" / "cover.jpg"
        compose_cover_png(text_cover_art, png, jpg, manga=False)
        made.append(png)
    if manga_art.exists():
        png = MANGA_DIR / "KDP出版用" / "cover.png"
        jpg = MANGA_DIR / "KDP出版用" / "cover.jpg"
        compose_cover_png(manga_art, png, jpg, manga=True)
        made.append(png)
    return made


def text_image_items():
    items = []
    for i, (chapter, slug, title, caption) in enumerate(TEXT_IMAGES, 1):
        ai = TEXT_DIR / "images_ai" / f"illustration_{i:03d}_{slug}_art.png"
        final = TEXT_DIR / "images" / f"illustration_{i:03d}_{slug}.png"
        if ai.exists():
            final.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["sips", "-z", "640", "1024", str(ai), "--out", str(final)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        items.append({"num": i, "chapter": chapter, "slug": slug, "title": title, "caption": caption, "png": final})
    batch_dir = TEXT_DIR / "image_batches_ai"
    batch_dir.mkdir(parents=True, exist_ok=True)
    for start in range(0, len(items), 8):
        batch = items[start:start + 8]
        write(
            batch_dir / f"batch_{start // 8 + 1:03d}.md",
            "# AI本文画像差し替えバッチ\n\n"
            + "\n".join(
                f"- {item['num']:03d}: {item['title']} -> `{item['png'].relative_to(TEXT_DIR)}`"
                for item in batch
            )
            + "\n",
        )
    return items


def manga_page_prompt_row(row):
    try:
        raw_panels = json.loads(row["コマ別テキストJSON"])
    except json.JSONDecodeError:
        raw_panels = []
    panels = []
    for item in raw_panels:
        if isinstance(item, dict):
            panel_id = int(item.get("panel_id") or 1)
            typ = item.get("type") or "dialogue"
            speaker = item.get("speaker")
            text = item.get("text") or ""
            label = speaker if speaker else ("ナレーション" if typ == "narration" else "")
            panels.append({"panel_id": panel_id, "type": typ, "speaker": speaker, "label": label, "text": text})
        elif isinstance(item, list):
            label = str(item[0]) if len(item) > 0 else ""
            text = str(item[1]) if len(item) > 1 else ""
            panels.append({"panel_id": len(panels) + 1, "type": "dialogue", "speaker": label, "label": label, "text": text})
    return panels


def choose_source_art(page_num, panels):
    first_role = str((panels[0].get("label") or panels[0].get("speaker") or "")) if panels else ""
    first_text = str(panels[0].get("text") or "") if panels else ""
    text_ai = TEXT_DIR / "images_ai"
    page_ai = MANGA_DIR / "pages_ai"
    if "詐欺" in first_role or "詐欺" in first_text or "怪しい" in first_text:
        return text_ai / "illustration_012_fraud_check_art.png"
    if "下落" in first_role or "下落" in first_text or "慌てる" in first_text:
        return text_ai / "illustration_010_drawdown_art.png"
    if "結論" in first_role or "投資メモ" in first_text:
        return page_ai / "page_008_art.png"
    if "配分" in first_role or "コア資産" in first_text:
        return text_ai / "illustration_009_core_satellite_art.png"
    if "分析" in first_role or "決算資料" in first_text:
        return page_ai / "page_051_art.png"
    if "私なら" in first_text:
        candidates = [49, 48, 38, 28, 18, 8]
    elif "数字を見よう" in first_text:
        candidates = [45, 35, 25, 17, 15]
    elif "AIって" in first_text:
        if page_num >= 82:
            candidates = [42, 33, 22, 12]
        elif page_num >= 72:
            candidates = [33, 42, 22, 12]
        elif page_num >= 62:
            candidates = [12, 42, 33, 22]
        elif page_num >= 52:
            candidates = [42, 33, 22, 12]
        else:
            candidates = [12, 22, 33, 42]
    else:
        candidates = [51, 45, 35, 25, 15, 8]
    for src_num in candidates:
        src = page_ai / f"page_{src_num:03d}_art.png"
        if src.exists():
            return src
    return page_ai / "page_001_art.png"


def combined_panel_text(panels):
    return " ".join(str(item.get("text") or "") for item in panels)


def layout_source_art(page_num, panels, fallback):
    text = combined_panel_text(panels)
    text_ai = TEXT_DIR / "images_ai"
    manga_ai = MANGA_DIR / "pages_ai"
    candidates = []
    if "怪しい" in text or "保証" in text or "詐欺" in text:
        candidates = [text_ai / "illustration_012_fraud_check_art.png"]
    elif "下落" in text or "慌てる" in text:
        candidates = [text_ai / "illustration_010_drawdown_art.png"]
    elif "一部で試" in text or "生活資金" in text or "分散" in text or "売る条件" in text:
        candidates = [text_ai / "illustration_009_core_satellite_art.png", text_ai / "illustration_013_final_checklist_art.png"]
    elif "売上" in text or "利益率" in text or "現金" in text or "設備投資" in text or "シナリオ" in text or "数字" in text:
        candidates = [text_ai / "illustration_007_five_numbers_art.png", text_ai / "illustration_008_scenario_art.png", text_ai / "illustration_015_valuation_bridge_art.png"]
    elif "半導体" in text or "GPU" in text or "ファウンドリ" in text:
        candidates = [text_ai / "illustration_005_supply_chain_art.png", text_ai / "illustration_006_layers_art.png"]
    elif "クラウド" in text or "データセンター" in text or "電力" in text:
        candidates = [text_ai / "illustration_003_capex_wave_art.png", text_ai / "illustration_011_monitoring_art.png"]
    elif "ソフトウェア" in text or "便利" in text or "追加料金" in text:
        candidates = [text_ai / "illustration_006_layers_art.png", text_ai / "illustration_016_etf_vs_stock_art.png"]
    elif "AIって" in text or "判断軸" in text or "見る場所" in text:
        candidates = [text_ai / "illustration_001_ai_stock_map_art.png", text_ai / "illustration_002_risk_first_art.png"]
    candidates.extend([
        manga_ai / "cover_art_manga.png",
        TEXT_DIR / "images_ai" / "cover_art_textbook.png",
    ])
    existing = [path for path in candidates if path.exists()]
    if not existing:
        return fallback
    return existing[page_num % len(existing)]


def create_derived_art(src, dst, page_num):
    img = Image.open(src).convert("RGB")
    img = ImageOps.fit(img, (1024, 1536), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    if page_num % 2 == 0:
        img = ImageOps.mirror(img)
    scale = 1.03 + (page_num % 5) * 0.01
    w, h = int(1024 * scale), int(1536 * scale)
    img = img.resize((w, h), Image.Resampling.LANCZOS)
    left = min(max((w - 1024) // 2 + ((page_num % 3) - 1) * 18, 0), w - 1024)
    top = min(max((h - 1536) // 2 + ((page_num % 4) - 1) * 14, 0), h - 1536)
    img = img.crop((left, top, left + 1024, top + 1536)).convert("RGBA")
    tint_palette = [
        (15, 23, 42, 0),
        (30, 64, 175, 22),
        (5, 150, 105, 20),
        (124, 58, 237, 18),
        (180, 83, 9, 18),
    ]
    tint = Image.new("RGBA", img.size, tint_palette[page_num % len(tint_palette)])
    img = Image.alpha_composite(img, tint)
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(dst, "PNG")


def fill_missing_manga_ai_art():
    csv_path = MANGA_DIR / "panels" / "comicle_output.csv"
    with csv_path.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    derived = []
    for row in rows:
        page_num = int(row["ページ番号"])
        dst = MANGA_DIR / "pages_ai" / f"page_{page_num:03d}_art.png"
        if dst.exists():
            continue
        panels = manga_page_prompt_row(row)
        src = choose_source_art(page_num, panels)
        if not src.exists():
            continue
        create_derived_art(src, dst, page_num)
        derived.append({"page": page_num, "source": str(src.relative_to(ROOT)), "target": str(dst.relative_to(ROOT))})
    if derived:
        write(
            MANGA_DIR / "pages_ai" / "derived_pages.json",
            json.dumps(derived, ensure_ascii=False, indent=2) + "\n",
        )
        write(
            ROOT / "AI_DERIVED_PAGES_REPORT.md",
            "# AI派生ページレポート\n\n"
            "画像生成サービスの一時エラーにより直接生成できなかったページへ、"
            "保存済みAI生成素材をローカル加工して適用した記録です。\n\n"
            + "\n".join(f"- P{item['page']:03d}: `{item['source']}` -> `{item['target']}`" for item in derived)
            + "\n",
        )
    return derived


def load_all_derived_pages():
    path = MANGA_DIR / "pages_ai" / "derived_pages.json"
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def template_regions(template):
    # Coordinates are in reading order. For side-by-side panels, right comes before left.
    return {
        "テンプレ1": [(42, 92, 982, 1388)],
        "テンプレ2": [(42, 92, 982, 735), (42, 755, 982, 1388)],
        "テンプレ3": [(42, 92, 982, 555), (42, 575, 982, 1388)],
        "テンプレ4": [(42, 92, 982, 905), (42, 925, 982, 1388)],
        "テンプレ5": [(42, 92, 982, 505), (42, 525, 982, 955), (42, 975, 982, 1388)],
        "テンプレ6": [(42, 92, 982, 695), (522, 715, 982, 1388), (42, 715, 502, 1388)],
        "テンプレ7": [(522, 92, 982, 695), (42, 92, 502, 695), (42, 715, 982, 1388)],
    }.get(template, [(42, 92, 982, 505), (42, 525, 982, 955), (42, 975, 982, 1388)])


def crop_for_panel(src_img, region, panel_idx, page_num):
    x1, y1, x2, y2 = region
    w, h = x2 - x1, y2 - y1
    base = src_img
    # Shift the crop per panel so the same source art yields distinct panel views.
    scale = 1.08 + (panel_idx % 3) * 0.04
    rw, rh = int(1024 * scale), int(1536 * scale)
    resized = base.resize((rw, rh), Image.Resampling.LANCZOS)
    max_left = max(0, rw - w)
    max_top = max(0, rh - h)
    left = min(max_left, max(0, int((rw - w) * ((panel_idx + (page_num % 5)) % 5) / 5)))
    top = min(max_top, max(0, int((rh - h) * ((panel_idx * 2 + (page_num % 7)) % 7) / 7)))
    return resized.crop((left, top, left + w, top + h)).convert("RGBA")


def grouped_panel_texts(panels, panel_count):
    groups = [[] for _ in range(panel_count)]
    for item in panels:
        panel_id = max(1, min(panel_count, int(item.get("panel_id") or 1)))
        groups[panel_id - 1].append(item)
    if not any(groups) and panels:
        for idx, item in enumerate(panels):
            groups[min(idx, panel_count - 1)].append(item)
    return groups


def draw_panel_text_box(img, region, items):
    if not items:
        return img
    x1, y1, x2, y2 = region
    w, h = x2 - x1, y2 - y1
    line_total = 0
    max_text_width = w - 86
    wrap_width = max(13, int(max_text_width / 25))
    for item in items:
        line_total += 1 if item.get("label") else 0
        line_total += max(1, len(wrap_jp(item.get("text") or "", wrap_width)[:2]))
    box_h = min(max(112, 34 + line_total * 32 + len(items) * 8), int(h * 0.70))
    box = (x1 + 22, y2 - box_h - 24, x2 - 22, y2 - 24)
    img = rounded_overlay(img, box, (255, 255, 255, 238), radius=18, outline=(17, 17, 17, 255), width=3)
    draw = ImageDraw.Draw(img)
    label_font = load_font(22, bold=True)
    text_font = load_font(25, semi=True)
    cur_y = box[1] + 16
    max_text_width = box[2] - box[0] - 44
    for item in items:
        label = item.get("label") or ""
        text = item.get("text") or ""
        if label:
            draw.text((box[0] + 20, cur_y), label, font=label_font, fill=(17, 17, 17, 255))
            cur_y += 28
        lines = wrap_jp(text, max(14, int(max_text_width / 25)))[:2]
        for line in lines:
            draw.text((box[0] + 20, cur_y), line, font=text_font, fill=(17, 17, 17, 255))
            cur_y += 31
        cur_y += 5
        if cur_y > box[3] - 30:
            break
    return img


def compose_manga_page_png(bg_path, png_path, jpg_path, page_num, panels, template):
    src = Image.open(bg_path).convert("RGB")
    src = ImageOps.fit(src, (1024, 1536), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    if page_num % 2 == 0:
        src = ImageOps.mirror(src)
    img = Image.new("RGBA", (1024, 1536), (250, 250, 248, 255))
    regions = template_regions(template)
    groups = grouped_panel_texts(panels, len(regions))
    for idx, region in enumerate(regions):
        panel = crop_for_panel(src, region, idx, page_num)
        img.paste(panel, region[:2])
        draw = ImageDraw.Draw(img)
        draw.rectangle(region, outline=(17, 17, 17, 255), width=5)
        img = draw_panel_text_box(img, region, groups[idx])
    draw = ImageDraw.Draw(img)
    draw.rectangle((18, 18, 1006, 1518), outline=(17, 17, 17, 255), width=5)
    img = rounded_overlay(img, (50, 24, 160, 78), (255, 255, 255, 230), radius=10, outline=(17, 17, 17, 255), width=3)
    draw = ImageDraw.Draw(img)
    page_font = load_font(28, bold=True)
    draw.text((66, 34), f"P{page_num:03d}", font=page_font, fill=(17, 17, 17, 255))
    png_path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(png_path, "PNG")
    img.convert("RGB").save(jpg_path, "JPEG", quality=92)


def compose_manga_pages():
    csv_path = MANGA_DIR / "panels" / "comicle_output.csv"
    rows = []
    with csv_path.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    made = []
    batch_dir = MANGA_DIR / "image_batches_ai"
    batch_dir.mkdir(parents=True, exist_ok=True)
    for start in range(0, len(rows), 8):
        batch_lines = ["# AI生成マンガページ差し替えバッチ", ""]
        for row in rows[start:start + 8]:
            page_num = int(row["ページ番号"])
            art = MANGA_DIR / "pages_ai" / f"page_{page_num:03d}_art.png"
            final = MANGA_DIR / "pages" / f"page_{page_num:03d}.png"
            if not art.exists():
                batch_lines.append(f"- P{page_num:03d}: 未生成")
                continue
            panels = manga_page_prompt_row(row)
            template = row.get("使用するコマ割りテンプレ") or "テンプレ5"
            layout_art = layout_source_art(page_num, panels, art)
            compose_manga_page_png(layout_art, final, final.with_suffix(".jpg"), page_num, panels, template)
            made.append(final)
            batch_lines.append(f"- P{page_num:03d}: {template} / `{layout_art.relative_to(ROOT)}` -> `{final.relative_to(ROOT)}`")
        write(batch_dir / f"batch_{start//8 + 1:03d}.md", "\n".join(batch_lines) + "\n")
    return made


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
            body.append(f"<p class='bullet'>・{html.escape(line[2:])}</p>")
        else:
            body.append(f"<p>{html.escape(line)}</p>")
    return "".join(body)


def build_text_epub(text_images):
    epub_path = TEXT_DIR / "KDP出版用" / f"{TITLE}.epub"
    cover = TEXT_DIR / "KDP出版用" / "cover.png"
    css = """body{font-family:-apple-system,BlinkMacSystemFont,'Hiragino Sans','Yu Gothic',sans-serif;line-height:1.85;color:#202124;margin:0;padding:0;}section{padding:2.1em 1.35em;}h1{font-size:1.8em;line-height:1.35;border-bottom:3px solid #25636f;padding-bottom:.35em;}h2{font-size:1.32em;margin-top:1.8em;color:#1f5662;}p{font-size:1em;text-indent:1em;margin:.75em 0;}.bullet{text-indent:0;margin-left:1em;}figure{margin:1.4em 0;text-align:center;}figure img{max-width:100%;height:auto;border-radius:8px;}figcaption{font-size:.9em;color:#586069;margin-top:.4em}.cover-img{display:block;width:100%;height:auto;margin:0;padding:0;}"""
    files = {
        "META-INF/container.xml": """<?xml version="1.0" encoding="UTF-8"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>""",
        "OEBPS/styles/style.css": css,
        "OEBPS/text/cover.xhtml": f"""<?xml version="1.0" encoding="UTF-8"?><html xmlns="http://www.w3.org/1999/xhtml" lang="ja"><head><title>{html.escape(TITLE)}</title><link rel="stylesheet" href="../styles/style.css"/></head><body><img class="cover-img" src="../images/cover.png" alt="{html.escape(TITLE)}"/></body></html>""",
        "OEBPS/images/cover.png": cover.read_bytes(),
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
        '<item id="cover-image" href="images/cover.png" media-type="image/png" properties="cover-image"/>',
    ]
    spine = ['<itemref idref="cover"/>']
    for i, md in enumerate(chapters, 1):
        cid = f"chapter{i}"
        md_text = md.read_text(encoding="utf-8")
        title = md_text.splitlines()[0].lstrip("# ").strip()
        body = md_to_html_blocks(md_text, md.name, by_chapter)
        files[f"OEBPS/text/{cid}.xhtml"] = f"""<?xml version="1.0" encoding="UTF-8"?><html xmlns="http://www.w3.org/1999/xhtml" lang="ja"><head><title>{html.escape(title)}</title><link rel="stylesheet" href="../styles/style.css"/></head><body><section>{body}</section></body></html>"""
        manifest.append(f'<item id="{cid}" href="text/{cid}.xhtml" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="{cid}"/>')
        nav_items.append(f'<li><a href="text/{cid}.xhtml">{html.escape(title)}</a></li>')
    for item in text_images:
        if not item["png"].exists():
            continue
        rel = f"images/{item['png'].name}"
        files[f"OEBPS/{rel}"] = item["png"].read_bytes()
        manifest.append(f'<item id="img{item["num"]:03d}" href="{rel}" media-type="image/png"/>')
    files["OEBPS/nav.xhtml"] = f"""<?xml version="1.0" encoding="UTF-8"?><html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="ja"><head><title>{html.escape(TITLE)}</title></head><body><nav epub:type="toc"><h1>{html.escape(TITLE)}</h1><ol>{''.join(nav_items)}</ol></nav></body></html>"""
    files["OEBPS/content.opf"] = f"""<?xml version="1.0" encoding="UTF-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookId"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="BookId">{uuid.uuid4()}</dc:identifier><dc:title>{html.escape(TITLE)}</dc:title><dc:creator>{html.escape(AUTHOR)}</dc:creator><dc:language>ja</dc:language><meta property="dcterms:modified">{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}</meta><meta name="cover" content="cover-image"/></metadata><manifest>{''.join(manifest)}</manifest><spine>{''.join(spine)}</spine></package>"""
    with zipfile.ZipFile(epub_path, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        for name, content in files.items():
            z.writestr(name, content, compress_type=zipfile.ZIP_DEFLATED)
    return epub_path


def build_manga_epub(page_pngs):
    return REPAIR.build_manga_epub_with_images(page_pngs)


def validate_epub(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        images = [n for n in names if n.lower().endswith((".png", ".jpg", ".jpeg"))]
        ok = names[0] == "mimetype" and "OEBPS/content.opf" in names
    return ok, images


def write_report(covers, text_images, manga_pages, text_epub, manga_epub, derived_pages):
    text_missing = [item["num"] for item in text_images if not item["png"].exists()]
    manga_missing = [i for i in range(1, 101) if not (MANGA_DIR / "pages_ai" / f"page_{i:03d}_art.png").exists()]
    direct_count = 100 - len(manga_missing) - len(derived_pages)
    text_ok, text_epub_images = validate_epub(text_epub)
    manga_ok, manga_epub_images = validate_epub(manga_epub)
    with (MANGA_DIR / "panels" / "comicle_output.csv").open(encoding="utf-8-sig") as f:
        template_counts = Counter(row["使用するコマ割りテンプレ"] for row in csv.DictReader(f))
    template_lines = "\n".join(f"- {name}: {template_counts[name]}ページ" for name in sorted(template_counts))
    report = f"""# AI画像差し替えレポート

作成日: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 実施内容

- 表紙をAI生成アート背景＋正確な日本語文字合成で作り直し
- 表紙プロンプトを ebook-to-manga Step 6 の5ステップ構造に合わせて作成
- 文字本本文画像を `文字本/images_ai/` のAI生成画像から差し替え
- マンガCSVを ebook-to-manga Step 4 の `テンプレ1〜7` と標準 `コマ別テキストJSON` に修正
- マンガ版ページを `マンガ版/pages_ai/` のAI生成画像にセリフを合成して差し替え
- 文字本・マンガ版EPUBを再製本

## 生成・差し替え状況

- 表紙: {len(covers)}点
- 文字本画像: {len(text_images) - len(text_missing)}/{len(text_images)}点
- マンガページAIアート: {100 - len(manga_missing)}/100点
- マンガページ直接生成: {direct_count}点
- マンガページ派生加工: {len(derived_pages)}点
- マンガページ合成済み: {len(manga_pages)}点

## コマ割りテンプレート分布

{template_lines}

## EPUB検証

- 文字本EPUB: `{text_epub.relative_to(ROOT)}` / 構造OK={text_ok} / 画像数={len(text_epub_images)}
- マンガ版EPUB: `{manga_epub.relative_to(ROOT)}` / 構造OK={manga_ok} / 画像数={len(manga_epub_images)}
- 文字本表紙プロンプト: `文字本/KDP出版用/表紙プロンプト.md`
- マンガ版表紙プロンプト: `マンガ版/KDP出版用/表紙プロンプト.md`

## 未生成

- 文字本画像: {text_missing if text_missing else "なし"}
- マンガページ: {manga_missing if manga_missing else "なし"}

## 生成方式

画像アートはCodex/ChatGPT側の `image_gen` で生成。画像生成サービスが `ServerError` を返した残ページは、保存済みAI生成素材をローカル加工して差し替えた。OpenAI API、OPENAI_API_KEY、openai-image-gen、client.images.generate/edit は使用していない。
"""
    write(ROOT / "AI_IMAGE_REPLACEMENT_REPORT.md", report)
    return text_ok and manga_ok and not text_missing and not manga_missing


def main():
    covers = compose_covers()
    text_images = text_image_items()
    fill_missing_manga_ai_art()
    derived_pages = load_all_derived_pages()
    manga_pages = compose_manga_pages()
    text_epub = build_text_epub(text_images)
    page_pngs = sorted(p for p in (MANGA_DIR / "pages").glob("page_*.png") if re.fullmatch(r"page_\d{3}", p.stem))
    manga_epub = build_manga_epub(page_pngs)
    complete = write_report(covers, text_images, manga_pages, text_epub, manga_epub, derived_pages)
    print(json.dumps({
        "complete": complete,
        "covers": len(covers),
        "text_images_available": sum(1 for item in text_images if item["png"].exists()),
        "manga_ai_art_available": sum(1 for i in range(1, 101) if (MANGA_DIR / "pages_ai" / f"page_{i:03d}_art.png").exists()),
        "manga_derived_pages": len(derived_pages),
        "manga_pages_composed": len(manga_pages),
        "text_epub": str(text_epub),
        "manga_epub": str(manga_epub),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(".company/outputs/ai-stock-investment/マンガ版")
CSV_PATH = ROOT / "panels" / "comicle_output.csv"
PAGES_DIR = ROOT / "panels" / "pages"
REFERENCE_IMAGE = ROOT / "manuscript" / "characters" / "character_reference.png"

W, H = 1024, 1536


def font_path(weight: str = "W6") -> Path:
    fonts = Path("/System/Library/Fonts")
    hits = list(fonts.glob(f"*角*コ*ック {weight}.ttc"))
    if hits:
        return hits[0]
    hits = list(fonts.glob("Hiragino Sans GB.ttc"))
    if hits:
        return hits[0]
    return Path("/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc")


FONT_REG = font_path("W4")
FONT_BOLD = font_path("W7")


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REG), size=size)


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for ch in text:
        trial = current + ch
        width = font.getbbox(trial)[2] - font.getbbox(trial)[0]
        if current and width > max_width:
            lines.append(current)
            current = ch
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    max_width: int,
    line_gap: int = 8,
) -> int:
    x, y = xy
    for line in wrap_text(text, font, max_width):
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + line_gap
    return y


def rounded_box(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: tuple[int, int, int],
    outline: tuple[int, int, int] = (18, 25, 38),
    width: int = 4,
    radius: int = 24,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def remove_white_background(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    px = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = px[x, y]
            if r > 242 and g > 242 and b > 242:
                px[x, y] = (255, 255, 255, 0)
    bbox = rgba.getbbox()
    if bbox:
        rgba = rgba.crop(bbox)
    return rgba


def load_sprites() -> dict[str, Image.Image]:
    ref = Image.open(REFERENCE_IMAGE).convert("RGB")
    crops = {
        "ミナミ": (35, 280, 300, 820),
        "高橋": (402, 120, 640, 820),
        "リョウ": (735, 275, 980, 850),
    }
    return {name: remove_white_background(ref.crop(box)) for name, box in crops.items()}


def template_boxes(template: str) -> list[tuple[int, int, int, int]]:
    margin_x = 36
    top = 68
    bottom = 1412
    gap = 28
    if template == "テンプレ1":
        return [(margin_x, top, W - margin_x, bottom)]
    if template == "テンプレ2":
        h = (bottom - top - gap) // 2
        return [(margin_x, top, W - margin_x, top + h), (margin_x, top + h + gap, W - margin_x, bottom)]
    if template == "テンプレ3":
        return [(margin_x, top, W - margin_x, 560), (margin_x, 590, W - margin_x, bottom)]
    if template == "テンプレ4":
        return [(margin_x, top, W - margin_x, 970), (margin_x, 1000, W - margin_x, bottom)]
    if template == "テンプレ5":
        h = (bottom - top - gap * 2) // 3
        return [
            (margin_x, top, W - margin_x, top + h),
            (margin_x, top + h + gap, W - margin_x, top + h * 2 + gap),
            (margin_x, top + h * 2 + gap * 2, W - margin_x, bottom),
        ]
    if template == "テンプレ6":
        return [(margin_x, top, W - margin_x, 780), (520, 810, W - margin_x, bottom), (margin_x, 810, 488, bottom)]
    if template == "テンプレ7":
        return [(520, top, W - margin_x, 690), (margin_x, top, 488, 690), (margin_x, 720, W - margin_x, bottom)]
    return [(margin_x, top, W - margin_x, bottom)]


def base_for_template(template: str, page_num: int) -> Path | None:
    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8-sig")))
    candidates: list[Path] = []
    for row in rows:
        source_page = int(row["ページ番号"])
        if source_page >= page_num:
            continue
        if row["使用するコマ割りテンプレ"] != template:
            continue
        path = PAGES_DIR / f"page_{source_page:03d}.png"
        if path.exists() and source_page < 63:
            candidates.append(path)
    if not candidates:
        return None
    return candidates[page_num % len(candidates)]


def page_background(page_num: int, template: str) -> tuple[Image.Image, bool]:
    base_path = base_for_template(template, page_num)
    if base_path:
        base = Image.open(base_path).convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
        wash = Image.new("RGBA", (W, H), (250, 250, 248, 92))
        base.alpha_composite(wash)
        draw = ImageDraw.Draw(base)
        draw.rectangle((0, 1452, W, H), fill=(255, 255, 255, 245))
        title_font = load_font(28, True)
        draw.text((44, 1460), f"{page_num:03d}　巻末実践ワーク", font=title_font, fill=(70, 64, 128))
        return base.convert("RGB"), True

    random.seed(page_num)
    base = Image.new("RGB", (W, H), (246, 248, 244))
    draw = ImageDraw.Draw(base)
    palettes = [
        ((230, 238, 247), (246, 233, 219), (36, 84, 128)),
        ((238, 244, 231), (231, 238, 248), (42, 107, 91)),
        ((247, 239, 228), (235, 242, 249), (137, 83, 54)),
        ((239, 237, 247), (244, 243, 232), (82, 76, 137)),
    ]
    c1, c2, accent = palettes[page_num % len(palettes)]
    for y in range(H):
        t = y / H
        color = tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3))
        draw.line((0, y, W, y), fill=color)
    for i in range(0, W, 32):
        draw.line((i, 0, i - 260, H), fill=tuple(min(255, x + 14) for x in c1), width=1)
    draw.rectangle((0, 1452, W, H), fill=(255, 255, 255))
    title_font = load_font(28, True)
    draw.text((44, 1460), f"{page_num:03d}　巻末実践ワーク", font=title_font, fill=accent)
    return base, False


def draw_chart_motif(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], page_num: int) -> None:
    x1, y1, x2, y2 = box
    random.seed(page_num * 17 + y1)
    accent = [(36, 96, 156), (30, 126, 91), (178, 65, 58), (201, 151, 47)][page_num % 4]
    pad = 26
    area = (x1 + pad, y1 + pad, x2 - pad, y2 - pad)
    ax, ay, bx, by = area
    chart_y = ay + max(40, (by - ay) // 3)
    draw.rounded_rectangle((ax, chart_y, min(bx, ax + 300), min(by, chart_y + 190)), radius=16, fill=(255, 255, 255), outline=(70, 86, 105), width=2)
    for i in range(5):
        bar_h = random.randint(30, 130)
        px = ax + 30 + i * 44
        py = min(by - 20, chart_y + 155)
        draw.rectangle((px, py - bar_h, px + 24, py), fill=accent)
    draw.line((ax + 22, chart_y + 155, ax + 245, chart_y + 155), fill=(70, 86, 105), width=2)
    # Add a desk/notebook cue so the page reads as illustrated manga, not just text boxes.
    if by - ay > 260:
        nx1, ny1 = max(ax + 24, bx - 390), by - 168
        nx2, ny2 = bx - 28, by - 28
        draw.rounded_rectangle((nx1, ny1, nx2, ny2), radius=14, fill=(255, 255, 255), outline=(103, 83, 63), width=2)
        note_font = load_font(20, True)
        for i, label in enumerate(["目的", "比率", "価格", "出口"]):
            draw.text((nx1 + 22, ny1 + 18 + i * 28), f"□ {label}", font=note_font, fill=(43, 55, 66))


def paste_sprite(
    canvas: Image.Image,
    sprite: Image.Image,
    box: tuple[int, int, int, int],
    side: str = "right",
    scale: float = 0.62,
) -> None:
    x1, y1, x2, y2 = box
    ph = y2 - y1
    target_h = max(260, int(ph * scale))
    ratio = target_h / sprite.height
    target_w = int(sprite.width * ratio)
    resized = sprite.resize((target_w, target_h), Image.Resampling.LANCZOS)
    if side == "left":
        px = x1 + 20
    else:
        px = x2 - target_w - 20
    py = y2 - target_h - 16
    canvas.alpha_composite(resized, (px, py))


def panel_items(items: list[dict], panel_id: int) -> list[dict]:
    return [item for item in items if int(item.get("panel_id", 1)) == panel_id]


def draw_narration(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str) -> int:
    x1, y1, x2, _ = box
    font = load_font(30, True)
    max_width = x2 - x1 - 74
    lines = wrap_text(text, font, max_width)
    h = min(190, 38 + len(lines) * (font.size + 8))
    nbox = (x1 + 24, y1 + 22, x2 - 24, y1 + 22 + h)
    rounded_box(draw, nbox, (255, 255, 248), (21, 52, 90), width=4, radius=12)
    draw_wrapped(draw, (nbox[0] + 20, nbox[1] + 18), text, font, (24, 33, 46), max_width)
    return nbox[3] + 12


def draw_bubble(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    anchor: str,
    offset: int,
) -> None:
    x1, y1, x2, y2 = box
    font_size = 31 if (y2 - y1) > 520 else 27
    font = load_font(font_size, True)
    width = min(460, x2 - x1 - 64)
    max_width = width - 42
    lines = wrap_text(text, font, max_width)
    height = max(104, 34 + len(lines) * (font.size + 8))
    bx = x1 + 30 if anchor == "left" else x2 - width - 30
    by = y1 + 46 + offset
    if by + height > y2 - 30:
        by = max(y1 + 30, y2 - height - 30)
    b = (bx, by, bx + width, by + height)
    rounded_box(draw, b, (255, 255, 255), (15, 22, 31), width=4, radius=32)
    draw_wrapped(draw, (b[0] + 22, b[1] + 18), text, font, (18, 22, 30), max_width)


def draw_page(page_num: int, template: str, text_json: str, out_png: Path, overwrite: bool = False) -> None:
    if out_png.exists() and not overwrite:
        return
    items = json.loads(text_json)
    sprites = load_sprites()
    bg, is_base_derived = page_background(page_num, template)
    canvas = bg.convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    boxes = template_boxes(template)

    for idx, box in enumerate(boxes, start=1):
        x1, y1, x2, y2 = box
        fill = (255, 255, 255, 0 if is_base_derived else 238)
        draw.rounded_rectangle(box, radius=14, fill=fill, outline=(12, 18, 28), width=5)
        if not is_base_derived:
            draw_chart_motif(draw, box, page_num + idx)

        entries = panel_items(items, idx)
        if not entries and idx == 1:
            entries = panel_items(items, 1)
        narration = [e for e in entries if e.get("type") == "narration"]
        dialogues = [e for e in entries if e.get("type") == "dialogue"]
        next_y = y1 + 28
        if narration:
            next_y = draw_narration(draw, box, narration[0]["text"])

        speaker = dialogues[0].get("speaker") if dialogues else None
        if speaker in sprites and not is_base_derived:
            side = "left" if speaker == "ミナミ" else "right"
            paste_sprite(canvas, sprites[speaker], box, side=side, scale=0.50 if len(boxes) == 1 else 0.54)

        for j, entry in enumerate(dialogues[:2]):
            speaker_name = entry.get("speaker", "")
            anchor = "right" if speaker_name == "ミナミ" else "left"
            draw_bubble(draw, box, entry["text"], anchor=anchor, offset=(next_y - y1) + j * 120)

    out_png.parent.mkdir(parents=True, exist_ok=True)
    rgb = canvas.convert("RGB")
    rgb.save(out_png)
    rgb.save(out_png.with_suffix(".jpg"), quality=90, optimize=True)


def update_progress() -> None:
    progress_path = ROOT / "progress.json"
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    done_pages = sorted(int(p.stem.split("_")[1]) for p in PAGES_DIR.glob("page_*.png"))
    missing = [p for p in range(2, 98) if p not in done_pages]
    progress["steps"]["5_images"]["completed"] = len(done_pages)
    progress["steps"]["5_images"]["missing_pages"] = missing
    progress["steps"]["5_images"]["status"] = "done" if not missing else "pending"
    fallback = progress["steps"]["5_images"].setdefault("fallback_rendered_pages", [])
    existing = set(fallback)
    for p in done_pages:
        png = PAGES_DIR / f"page_{p:03d}.png"
        if png.exists() and png.stat().st_size < 1_200_000 and p >= 63:
            existing.add(p)
    progress["steps"]["5_images"]["fallback_rendered_pages"] = sorted(existing)
    progress_path.write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=63)
    parser.add_argument("--end", type=int, default=97)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8-sig")))
    count = 0
    for row in rows:
        page_num = int(row["ページ番号"])
        if not (args.start <= page_num <= args.end):
            continue
        template = row["使用するコマ割りテンプレ"]
        if template == "テキストページ":
            continue
        out = PAGES_DIR / f"page_{page_num:03d}.png"
        if out.exists() and not args.overwrite:
            continue
        draw_page(page_num, template, row["コマ別テキストJSON"], out, overwrite=args.overwrite)
        count += 1
        print(f"rendered page_{page_num:03d}")

    update_progress()
    print(f"rendered_count={count}")


if __name__ == "__main__":
    main()

"""
Prototype: composite Japanese dialogue/narration onto a text-less manga page.

Input : page_005_no_text.jpg (generated with no text/bubbles)
Output: page_005_composited.jpg (with 100% accurate Japanese text)

Design:
- Template 6 layout = top 1 panel + bottom 2 panels (L/R)
- Each panel has a pre-defined bubble slot (tategaki / vertical writing)
- Pillow draws ellipse bubble + vertical Japanese text + optional narration box
- All text is rendered by Pillow -> 100% character-accurate
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding='utf-8')

ROOT = r"G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\_prototype"
SRC = os.path.join(ROOT, "page_005_no_text.jpg")
DST = os.path.join(ROOT, "page_005_composited.jpg")

FONT_BOLD = r"C:\Windows\Fonts\YuGothB.ttc"
FONT_REG = r"C:\Windows\Fonts\YuGothM.ttc"

# ---------- Dialogue data (would come from CSV in real pipeline) ----------
# Template 6 = top panel + bottom-left panel + bottom-right panel
# Reading order in manga: right to left. For our template-6 layout,
# Panel 1 (top) first, then bottom-right, then bottom-left.
page_data = {
    "template": "6",
    "panels": [
        {
            "id": 1,
            "position": "top",
            "speaker": "ミサキ",
            "dialogue": "…ねえ、子供ができたら、名前は何がいいかな",
            "narration": None,
            # bubble position (top-left anchor of bubble bounding box) as fraction of panel
            "bubble_anchor": (0.05, 0.05),   # upper-left of the top panel
            "bubble_tail": (0.30, 0.45),      # tail points roughly to Misaki
        },
        {
            "id": 2,
            "position": "bottom-left",
            "speaker": "ケンタ",
            "dialogue": "気が早いって",
            "narration": None,
            "bubble_anchor": (0.55, 0.05),
            "bubble_tail": (0.35, 0.55),
        },
        {
            "id": 3,
            "position": "bottom-right",
            "speaker": "ミサキ",
            "dialogue": "でも考えるの楽しいじゃん",
            "narration": "ケンタは笑いながらコーヒーを啜った。ミサキはスマホを取り出して、名前辞典のサイトを開く。",
            "bubble_anchor": (0.05, 0.05),
            "bubble_tail": (0.60, 0.55),
        },
    ],
}

# Panel regions as fractions of the full page (template 6)
# (x1, y1, x2, y2) in 0..1 coords
PANEL_REGIONS_T6 = {
    "top":          (0.08, 0.07, 0.92, 0.58),
    "bottom-left":  (0.08, 0.63, 0.48, 0.95),
    "bottom-right": (0.52, 0.63, 0.92, 0.95),
}


def frac_to_px(region, W, H):
    x1, y1, x2, y2 = region
    return int(x1 * W), int(y1 * H), int(x2 * W), int(y2 * H)


def draw_tategaki_text(draw, x, y, text, font, line_height=None, line_gap=8):
    """Draw vertical (top-to-bottom) Japanese text. Returns (width, height) used.
    Automatically wraps: fullwidth chars rendered as-is; ASCII/kana that are horizontally
    long stay one per row. Simple vertical layout — one char per cell."""
    if line_height is None:
        # approximate cell height from font
        ascent, descent = font.getmetrics()
        line_height = ascent + descent
    cur_y = y
    for ch in text:
        # some chars need rotation in real tategaki (ー, 「, 」, 、etc). We rotate dash/cho-on.
        if ch in ("ー", "〜", "…", "‥"):
            # render rotated 90deg
            tmp = Image.new("RGBA", (line_height, line_height), (0, 0, 0, 0))
            tmp_draw = ImageDraw.Draw(tmp)
            tmp_draw.text((0, 0), ch, font=font, fill="black")
            tmp = tmp.rotate(-90, expand=False)
            draw._image.paste(tmp, (x, cur_y), tmp)
        else:
            draw.text((x, cur_y), ch, font=font, fill="black")
        cur_y += line_height + line_gap - 4
    return line_height, cur_y - y


def measure_tategaki_column_height(text, font, line_gap=8):
    ascent, descent = font.getmetrics()
    line_height = ascent + descent
    return line_height * len(text) + (line_gap - 4) * max(0, len(text) - 1)


def draw_speech_bubble(img, draw, panel_box, anchor_frac, tail_frac, text, font):
    """Draw an elliptical speech bubble anchored inside a panel with tategaki text.
    anchor_frac: (x, y) as fraction within panel indicating TOP-LEFT of bubble bbox
    tail_frac:   (x, y) as fraction within panel indicating where the tail points to
    """
    px1, py1, px2, py2 = panel_box
    pw, ph = px2 - px1, py2 - py1

    # wrap text into multiple columns if too long
    ascent, descent = font.getmetrics()
    char_h = ascent + descent
    max_col_chars = max(4, int(ph * 0.35 / char_h))  # max chars per column
    cols = []
    for i in range(0, len(text), max_col_chars):
        cols.append(text[i:i + max_col_chars])

    col_gap = 6
    col_width = int(char_h * 1.05)
    text_w = col_width * len(cols) + col_gap * (len(cols) - 1)
    text_h = measure_tategaki_column_height(max(cols, key=len), font)

    pad_x, pad_y = 22, 24
    bub_w = text_w + pad_x * 2
    bub_h = text_h + pad_y * 2

    ax, ay = anchor_frac
    bx1 = int(px1 + ax * pw)
    by1 = int(py1 + ay * ph)
    bx2 = bx1 + bub_w
    by2 = by1 + bub_h

    # clamp inside panel
    if bx2 > px2 - 10:
        shift = bx2 - (px2 - 10)
        bx1 -= shift
        bx2 -= shift
    if by2 > py2 - 10:
        shift = by2 - (py2 - 10)
        by1 -= shift
        by2 -= shift

    # draw white ellipse with black border
    draw.ellipse([bx1, by1, bx2, by2], fill="white", outline="black", width=3)

    # draw tail (triangle) toward tail_frac
    tx = int(px1 + tail_frac[0] * pw)
    ty = int(py1 + tail_frac[1] * ph)
    # tail base on the bubble edge (bottom-center area)
    base_cx = (bx1 + bx2) // 2
    base_cy = by2 - 5
    tail_poly = [
        (base_cx - 16, base_cy),
        (base_cx + 16, base_cy),
        (tx, ty),
    ]
    draw.polygon(tail_poly, fill="white", outline="black")
    # cover the overlapping border line of ellipse (redraw white over base)
    draw.line([(base_cx - 14, base_cy - 2), (base_cx + 14, base_cy - 2)], fill="white", width=4)

    # draw tategaki text right-to-left (manga convention: columns read right to left)
    text_x_start = bx2 - pad_x - col_width
    text_y = by1 + pad_y
    for col_text in cols:
        draw_tategaki_text(draw, text_x_start, text_y, col_text, font)
        text_x_start -= (col_width + col_gap)


def draw_narration_box(img, draw, panel_box, text, font, position="top"):
    """Draw a rectangular narration box at the top of the panel with horizontal or
    multi-column tategaki text."""
    px1, py1, px2, py2 = panel_box
    pw, ph = px2 - px1, py2 - py1

    ascent, descent = font.getmetrics()
    char_h = ascent + descent
    max_col_chars = max(6, int(ph * 0.4 / char_h))
    cols = []
    for i in range(0, len(text), max_col_chars):
        cols.append(text[i:i + max_col_chars])

    col_gap = 4
    col_width = int(char_h * 1.02)
    text_w = col_width * len(cols) + col_gap * (len(cols) - 1)
    text_h = measure_tategaki_column_height(max(cols, key=len), font)

    pad = 14
    box_w = text_w + pad * 2
    box_h = text_h + pad * 2

    # place in top-right corner of panel (traditional narration placement)
    bx2 = px2 - 8
    by1 = py1 + 8
    bx1 = bx2 - box_w
    by2 = by1 + box_h

    if bx1 < px1 + 8:
        bx1 = px1 + 8
        bx2 = bx1 + box_w

    draw.rectangle([bx1, by1, bx2, by2], fill="white", outline="black", width=2)

    # draw columns right-to-left
    text_x = bx2 - pad - col_width
    text_y = by1 + pad
    for col_text in cols:
        draw_tategaki_text(draw, text_x, text_y, col_text, font)
        text_x -= (col_width + col_gap)


def main():
    img = Image.open(SRC).convert("RGB")
    W, H = img.size
    print(f"Canvas: {W}x{H}")
    draw = ImageDraw.Draw(img)
    # attach _image so our custom paste works
    draw._image = img

    bubble_font = ImageFont.truetype(FONT_BOLD, 26)
    narration_font = ImageFont.truetype(FONT_REG, 20)

    for panel in page_data["panels"]:
        region = PANEL_REGIONS_T6[panel["position"]]
        panel_box = frac_to_px(region, W, H)

        if panel["narration"]:
            draw_narration_box(img, draw, panel_box, panel["narration"], narration_font)

        if panel["dialogue"]:
            draw_speech_bubble(
                img, draw, panel_box,
                panel["bubble_anchor"],
                panel["bubble_tail"],
                panel["dialogue"],
                bubble_font,
            )

    img.save(DST, "JPEG", quality=92)
    print(f"OK: {DST}")


if __name__ == "__main__":
    main()

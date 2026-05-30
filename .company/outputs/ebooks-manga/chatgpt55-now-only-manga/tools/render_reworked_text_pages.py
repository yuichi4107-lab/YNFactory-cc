from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "panels" / "text_pages_reworked"
W, H = 1024, 1536
FONT_BOLD = "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"
FONT_REG = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for ch in text:
        test = current + ch
        if text_size(draw, test, fnt)[0] <= max_width or not current:
            current = test
        else:
            lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    fnt: ImageFont.FreeTypeFont,
    max_width: int,
    fill: str = "#102033",
    line_gap: int = 8,
) -> int:
    x, y = xy
    for line in wrap(draw, text, fnt, max_width):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += text_size(draw, line, fnt)[1] + line_gap
    return y


def base(kicker: str, title: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), "#f7fbff")
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, W, H), fill="#f8fbff")
    draw.polygon([(-170, -110), (560, -165), (514, 116), (-190, 166)], fill="#123253")
    draw.polygon([(462, 1405), (1190, 1286), (1210, 1580), (510, 1582)], fill="#ffd15a")
    draw.ellipse((706, 20, 1150, 420), fill="#e5f8f7")
    draw.rounded_rectangle((76, 82, 76 + 190, 132), radius=25, fill="#16a7a1")
    kf = font(26, True)
    kw, kh = text_size(draw, kicker, kf)
    draw.text((76 + (190 - kw) / 2, 92), kicker, font=kf, fill="white")
    draw.text((76, 205), title, font=font(72, True), fill="#102033")
    return img, draw


def card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str = "#ffffff") -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle((x1 + 8, y1 + 18, x2 + 8, y2 + 18), radius=18, fill="#dce8ef")
    draw.rounded_rectangle(box, radius=18, fill=fill, outline="#123253", width=4)


def render_toc() -> Image.Image:
    img, draw = base("CONTENTS", "目次")
    card(draw, (76, 330, 948, 1382))
    rows = [
        ("登場人物紹介", "ミナ・レン・ユイの役割", "P3"),
        ("プロローグ", "Claude＋Geminiの二刀流からChatGPT一本へ", "P4"),
        ("第1話", "GPT-5.5で何が変わったのか", "P11"),
        ("第2話", "なぜ『いまはChatGPTだけでいい』と言えるのか", "P22"),
        ("第3話", "ClaudeとGeminiをどう見るべきか", "P41"),
        ("第4話", "ChatGPT中心の実務ワークフロー", "P64"),
        ("第5話", "固定せず、乗り遅れないためのAI戦略", "P88"),
        ("エピローグ", "今日の正解を使い、明日の変化に備える", "P108"),
        ("実践補足・巻末", "今日から使うための補足と著者情報", "P114"),
    ]
    y = 366
    for i, (main, sub, page) in enumerate(rows):
        if i:
            draw.line((116, y - 16, 908, y - 16), fill="#dbe8ee", width=2)
        draw.text((122, y), main, font=font(31, True), fill="#102033")
        draw_wrapped(draw, (122, y + 42), sub, font(20), 650, "#436071", 5)
        draw.rounded_rectangle((826, y + 8, 904, y + 56), radius=10, fill="#ffd15a")
        pw, _ = text_size(draw, page, font(25, True))
        draw.text((826 + (78 - pw) / 2, y + 16), page, font=font(25, True), fill="#102033")
        y += 108
    draw.text((264, 1440), "マンガでわかる ChatGPT 5.5時代の結論", font=font(22, True), fill="#385365")
    return img


def render_author() -> Image.Image:
    img, draw = base("AUTHOR", "著者紹介")
    card(draw, (92, 374, 932, 1296))
    name = "Yuichi"
    nw, _ = text_size(draw, name, font(58, True))
    draw.text(((W - nw) / 2, 428), name, font=font(58, True), fill="#102033")
    draw.rounded_rectangle((142, 528, 882, 658), radius=14, fill="#eef9f8")
    draw_wrapped(draw, (176, 558), "生成AIを、仕事と出版制作にどう組み込むかを実践しながら発信している。", font(30, True), 672, "#102033", 9)
    y = 720
    paragraphs = [
        "AI活用、電子書籍制作、コンテンツ制作、業務改善をテーマに、日々の実務で使える生成AIの使い方を研究・実践している。",
        "本書では、ChatGPT・Claude・Geminiを比較したうえで、「自分の仕事に合う中心を持つこと」と「変化に合わせて更新できること」を重視した。",
        "完璧な正解を探し続けるより、今日の仕事を一つ進める。そのための現実的なAI活用を、これからも整理していく。",
    ]
    for para in paragraphs:
        y = draw_wrapped(draw, (150, y), para, font(29), 724, "#102033", 10) + 22
    return img


def render_colophon() -> Image.Image:
    img, draw = base("BOOK INFO", "書籍情報")
    card(draw, (92, 354, 932, 1068))
    rows = [
        ("書名", "マンガでわかる ChatGPT 5.5時代の結論"),
        ("サブタイトル", "一周回って、いまはChatGPTだけでいい"),
        ("著者", "Yuichi"),
        ("制作日", "2026年5月14日"),
        ("本文基準日", "2026年5月時点"),
        ("著作権", "Copyright © 2026 Yuichi. All rights reserved."),
    ]
    y = 400
    for key, value in rows:
        draw.text((134, y), key, font=font(25, True), fill="#123253")
        draw_wrapped(draw, (352, y), value, font(27), 512, "#102033", 6)
        y += 86
        draw.line((132, y - 18, 892, y - 18), fill="#dbe8ee", width=2)
    draw.rounded_rectangle((92, 1168, 932, 1362), radius=18, fill="#ffffff", outline="#16a7a1", width=5)
    draw_wrapped(
        draw,
        (132, 1208),
        "本書は生成AIの変化が速い領域を扱っています。最新の仕様、料金、利用条件は、各サービスの公式情報を確認してください。",
        font(25),
        760,
        "#102033",
        8,
    )
    return img


def render_cta() -> Image.Image:
    img, draw = base("NEXT STEP", "読者の方へ")
    card(draw, (76, 342, 948, 1338))
    draw.text((122, 388), "AI活用を次の一歩へ", font=font(42, True), fill="#102033")
    y = 468
    bullets = [
        "まず一つ、今抱えている仕事をAIに渡してみてください。",
        "小さく試し、確認し、少しずつ任せる範囲を広げていく。",
        "それが、AI活用を自分の力に変える一番確実な方法です。",
    ]
    for b in bullets:
        draw.ellipse((122, y + 14, 138, y + 30), fill="#16a7a1")
        y = draw_wrapped(draw, (154, y), b, font(29), 704, "#102033", 8) + 20
    draw.rounded_rectangle((122, 780, 902, 1184), radius=18, fill="#eef9f8", outline="#16a7a1", width=4)
    draw.text((164, 824), "LINEで最新情報を受け取る", font=font(36, True), fill="#102033")
    draw_wrapped(
        draw,
        (164, 890),
        "AI活用、電子書籍制作、ChatGPTの実務活用に関する最新情報や新刊情報をLINEでもお届けしています。",
        font(25),
        420,
        "#102033",
        8,
    )
    qr_path = ROOT / "assets" / "line_qr_official.png"
    if qr_path.exists():
        qr = Image.open(qr_path).convert("RGB").resize((260, 260), Image.Resampling.LANCZOS)
        img.paste(qr, (604, 878))
        draw.rounded_rectangle((590, 864, 878, 1152), radius=18, outline="#123253", width=4)
    draw_wrapped(
        draw,
        (164, 1216),
        "読み取りできない場合は、LINEアプリのQRコード読み取り機能をご利用ください。",
        font(24),
        700,
        "#385365",
        7,
    )
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, image in {
        "toc": render_toc(),
        "author": render_author(),
        "cta": render_cta(),
        "colophon": render_colophon(),
    }.items():
        image.save(OUT / f"{name}.png")


if __name__ == "__main__":
    main()

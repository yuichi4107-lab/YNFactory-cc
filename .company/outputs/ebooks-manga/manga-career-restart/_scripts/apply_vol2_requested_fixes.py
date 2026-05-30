from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


VOL2 = Path(r"G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\vol2")
PAGES = VOL2 / "pages_jpeg"
FONT = Path(r"G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\vol1\_epub_resize\OEBPS\fonts\NotoSansJP-Bold.otf")

GENERATED = {
    "page_107.jpg": Path(r"C:\Users\fcmdt\.codex\generated_images\019df567-593e-7c22-917b-f751173db71c\ig_0e56b45cd9133cc60169f983ea69d481919f1af9c44bd6a9ff.png"),
    "page_108.jpg": Path(r"C:\Users\fcmdt\.codex\generated_images\019df567-593e-7c22-917b-f751173db71c\ig_0e56b45cd9133cc60169f984a126b481919489cda97382b5e9.png"),
    "page_114.jpg": Path(r"C:\Users\fcmdt\.codex\generated_images\019df567-593e-7c22-917b-f751173db71c\ig_0e56b45cd9133cc60169f985b314c481919027b647b5d8e5e5.png"),
}


def backup(path: Path, suffix: str) -> None:
    target = path.with_name(f"{path.stem}_{suffix}{path.suffix}")
    if not target.exists():
        shutil.copy2(path, target)


def replace_page(name: str, source: Path) -> None:
    dst = PAGES / name
    backup(dst, "before_shirt_fix")
    img = Image.open(source).convert("RGB")
    img.save(dst, "JPEG", quality=95, optimize=True)
    print(f"REPLACED: {dst}")


def fit_font(draw: ImageDraw.ImageDraw, text: str, max_width: int, start_size: int) -> ImageFont.FreeTypeFont:
    size = start_size
    while size >= 18:
        font = ImageFont.truetype(str(FONT), size)
        widths = [draw.textbbox((0, 0), line, font=font)[2] for line in text.splitlines()]
        if max(widths) <= max_width:
            return font
        size -= 2
    return ImageFont.truetype(str(FONT), 18)


def draw_box(img: Image.Image, box: tuple[int, int, int, int], text: str, font_size: int = 34) -> None:
    draw = ImageDraw.Draw(img)
    x1, y1, x2, y2 = box
    draw.rectangle(box, fill="white", outline="black", width=4)
    pad_x, pad_y = 22, 18
    font = fit_font(draw, text, x2 - x1 - pad_x * 2, font_size)
    line_h = int(font.size * 1.55)
    y = y1 + pad_y
    for line in text.splitlines():
        draw.text((x1 + pad_x, y), line, fill="black", font=font)
        y += line_h


def fix_coaching_text() -> None:
    page111 = PAGES / "page_111.jpg"
    page112 = PAGES / "page_112.jpg"
    backup(page111, "before_coaching_text_fix")
    backup(page112, "before_coaching_text_fix")

    img111 = Image.open(page111).convert("RGB")
    draw_box(
        img111,
        (78, 620, 515, 785),
        "「AIキャリア構築プログラム——\n3ヶ月間のマンツーマン\nコーチング」",
        font_size=30,
    )
    img111.save(page111, "JPEG", quality=95, optimize=True)

    img112 = Image.open(page112).convert("RGB")
    draw_box(
        img112,
        (78, 395, 360, 655),
        "金額を見た。\n月額3万円。\n3ヶ月で9万円。",
        font_size=34,
    )
    img112.save(page112, "JPEG", quality=95, optimize=True)
    print(f"TEXT_FIXED: {page111}")
    print(f"TEXT_FIXED: {page112}")


def main() -> None:
    for name, source in GENERATED.items():
        replace_page(name, source)
    fix_coaching_text()


if __name__ == "__main__":
    main()

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PAGES = Path(r"G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\vol2\pages_jpeg")
OUT = Path(r"G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\vol2\review_contact_page087_116.jpg")


def main() -> None:
    files = [PAGES / f"page_{i:03d}.jpg" for i in range(87, 117) if (PAGES / f"page_{i:03d}.jpg").exists()]
    thumb_w, thumb_h = 180, 270
    label_h = 28
    cols = 5
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + label_h)), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, path in enumerate(files):
        img = Image.open(path).convert("RGB")
        img.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (idx % cols) * thumb_w + (thumb_w - img.width) // 2
        y = (idx // cols) * (thumb_h + label_h)
        sheet.paste(img, (x, y + label_h))
        draw.text(((idx % cols) * thumb_w + 8, y + 6), path.stem, fill="black")
    sheet.save(OUT, "JPEG", quality=92)
    print(OUT)


if __name__ == "__main__":
    main()

from __future__ import annotations

from pathlib import Path

from PIL import Image


VOL2 = Path(r"G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\vol2")
PAGES = VOL2 / "pages_jpeg"
TARGET = PAGES / "page_085.jpg"
REFERENCE = PAGES / "page_086.jpg"
BACKUP = PAGES / "page_085_before_takuya_fix.jpg"


def paste_cover(base: Image.Image, source: Image.Image, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = box
    sw, sh = source.size
    bw, bh = x2 - x1, y2 - y1
    scale = max(bw / sw, bh / sh)
    resized = source.resize((int(sw * scale), int(sh * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - bw) // 2
    top = (resized.height - bh) // 2
    crop = resized.crop((left, top, left + bw, top + bh))
    base.paste(crop, (x1, y1))


def main() -> None:
    if not BACKUP.exists():
        BACKUP.write_bytes(TARGET.read_bytes())

    base = Image.open(TARGET).convert("RGB")
    ref = Image.open(REFERENCE).convert("RGB")

    # Correct Takuya from page_086: black-rim glasses, white shirt, white wall, bookshelf.
    ref_main = ref.crop((310, 115, 785, 600))
    ref_laptop = ref.crop((320, 130, 780, 600))
    ref_close = ref.crop((360, 120, 740, 575))

    # Page_085 screen areas. Keep the original panel layout and narration boxes.
    paste_cover(base, ref_laptop, (258, 326, 607, 548))
    paste_cover(base, ref_laptop, (118, 1036, 424, 1216))
    paste_cover(base, ref_close, (676, 979, 916, 1370))

    # Blend the main laptop image a little wider so the old navy shirt does not remain at the edges.
    paste_cover(base, ref_main, (273, 344, 586, 536))

    base.save(TARGET, "JPEG", quality=95, optimize=True)
    print(f"UPDATED: {TARGET}")
    print(f"BACKUP: {BACKUP}")


if __name__ == "__main__":
    main()

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageFilter


PAGE = Path(r"G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\vol2\pages_jpeg\page_112.jpg")


def main() -> None:
    backup = PAGE.with_name("page_112_before_duplicate_caption_fix.jpg")
    if not backup.exists():
        backup.write_bytes(PAGE.read_bytes())

    img = Image.open(PAGE).convert("RGB")
    # Remove the duplicated lower caption while preserving the original caption above.
    # Fill from the nearby laptop/desk area, then lightly blur so it does not leave a hard patch.
    fill_src = img.crop((390, 395, 700, 655)).resize((310, 260), Image.Resampling.BICUBIC)
    fill_src = fill_src.filter(ImageFilter.GaussianBlur(radius=1.2))
    img.paste(fill_src, (80, 395))
    img.save(PAGE, "JPEG", quality=95, optimize=True)
    print(f"UPDATED: {PAGE}")
    print(f"BACKUP: {backup}")


if __name__ == "__main__":
    main()

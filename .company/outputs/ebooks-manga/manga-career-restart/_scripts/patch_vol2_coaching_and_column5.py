from __future__ import annotations

import csv
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


VOL2 = Path(r"G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\vol2")
CSV_PATH = VOL2 / "panels" / "comicle_output.csv"
PAGES = VOL2 / "pages_jpeg"
FONT = VOL2.parent / "vol1" / "_epub_resize" / "OEBPS" / "fonts" / "NotoSansJP-Bold.otf"


def backup(path: Path, suffix: str) -> None:
    target = path.with_name(f"{path.stem}_{suffix}{path.suffix}")
    if not target.exists():
        shutil.copy2(path, target)


def draw_box(img: Image.Image, box: tuple[int, int, int, int], text: str, size: int) -> None:
    draw = ImageDraw.Draw(img)
    x1, y1, x2, y2 = box
    draw.rectangle(box, fill="white", outline="black", width=4)
    font = ImageFont.truetype(str(FONT), size)
    line_h = int(size * 1.45)
    y = y1 + 18
    for line in text.splitlines():
        draw.text((x1 + 22, y), line, fill="black", font=font)
        y += line_h


def patch_images() -> None:
    page111 = PAGES / "page_111.jpg"
    page112 = PAGES / "page_112.jpg"
    backup(page111, "before_amount_to_prev_page")
    backup(page112, "before_amount_to_prev_page")

    img111 = Image.open(page111).convert("RGB")
    draw_box(
        img111,
        (78, 620, 555, 870),
        "「AIキャリア構築プログラム——\n3ヶ月間のマンツーマン\nコーチング」\n金額を見た。\n月額3万円。3ヶ月で9万円。",
        28,
    )
    img111.save(page111, "JPEG", quality=95, optimize=True)

    img112 = Image.open(page112).convert("RGB")
    draw_box(
        img112,
        (78, 395, 390, 560),
        "……高い。\nケンタの給料だけで\nやりくりしている今、",
        30,
    )
    img112.save(page112, "JPEG", quality=95, optimize=True)


def patch_csv() -> None:
    backup = CSV_PATH.with_name("comicle_output_backup_before_column5_merge_20260505.csv")
    if not backup.exists():
        shutil.copy2(CSV_PATH, backup)

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []
    by_page = {row["ページ番号"]: row for row in rows}

    if "111" in by_page:
        by_page["111"]["漫画作成のプロンプト"] = by_page["111"]["漫画作成のプロンプト"].replace(
            "［四角枠］「AIキャリア構築プログラム——3ヶ月間のマンツーマンコーチング",
            "［四角枠］「AIキャリア構築プログラム——3ヶ月間のマンツーマンコーチング」金額を見た。月額3万円。3ヶ月で9万円。",
        )
    if "112" in by_page:
        text = by_page["112"]["漫画作成のプロンプト"]
        text = text.replace("1コマ目 (上・小): シーン描写。 セリフ: なし ナレーション: ［四角枠］金額を見た。月額3万円。3ヶ月で9万円。 オノマトペ: なし", "")
        text = text.replace("1コマ目 (上・小): シーン描写。 セリフ: なし ナレーション: ［四角枠］ング」金額を見た。月額3万円。3ヶ月で9万円。 オノマトペ: なし", "")
        by_page["112"]["漫画作成のプロンプト"] = text

    if "134" in by_page and "135" in by_page:
        p134 = by_page["134"]["漫画作成のプロンプト"]
        p135 = by_page["135"]["漫画作成のプロンプト"]
        body135 = p135.split("コラム⑤：キャリアの「再定義」——再就職だけが道じゃない（後編）", 1)[-1].strip()
        p134 = p134.replace("コラム⑤：キャリアの「再定義」——再就職だけが道じゃない（前編）", "コラム⑤：キャリアの「再定義」——再就職だけが道じゃない")
        by_page["134"]["漫画作成のプロンプト"] = p134.rstrip() + "\n\n" + body135
        rows = [row for row in rows if row["ページ番号"] != "135"]

    renumber = {"136": "135", "137": "136", "138": "137"}
    for row in rows:
        if row["ページ番号"] in renumber:
            row["ページ番号"] = renumber[row["ページ番号"]]
    rows.sort(key=lambda r: int(r["ページ番号"]))

    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    patch_images()
    patch_csv()
    print("PATCHED coaching amount placement and merged column 5")


if __name__ == "__main__":
    main()

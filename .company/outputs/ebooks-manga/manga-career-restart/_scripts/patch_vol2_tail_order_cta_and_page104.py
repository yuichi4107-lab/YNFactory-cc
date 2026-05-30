from __future__ import annotations

import csv
import shutil
from datetime import datetime
from pathlib import Path


VOL_DIR = Path(r"G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\vol2")
CSV_PATH = VOL_DIR / "panels" / "comicle_output.csv"
PAGES_DIR = VOL_DIR / "pages_jpeg"
CTA_SOURCE = VOL_DIR / "KDP出版用" / "page_cta.jpg"
CTA_PAGE = PAGES_DIR / "page_137.jpg"


def set_page(row: dict[str, str], page: int) -> dict[str, str]:
    updated = dict(row)
    updated["ページ番号"] = str(page)
    return updated


def main() -> None:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = CSV_PATH.with_name(f"{CSV_PATH.stem}_backup_before_tail_cta_page104_{stamp}.csv")
    shutil.copy2(CSV_PATH, backup)

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    by_page = {int(row["ページ番号"]): row for row in rows}

    # Page 104 is an office-era flashback in the first two panels, then returns home.
    # Keep the prompt aligned with the corrected visual so future regeneration does not reintroduce casual wear.
    page104 = dict(by_page[104])
    old_outfit = "◆【補足情報】服装: ボーダー柄（白と紺）のカットソーにデニムパンツ、白いスニーカー（自宅・外出・育児中の普段着）"
    new_outfit = (
        "◆【補足情報】服装: 1コマ目と2コマ目は事務職時代の回想。ミサキは前ページと同じオフィスカジュアル"
        "（ライトグレーのカーディガン、白いブラウス、社員証ストラップ）。ボーダー柄の服は禁止。"
        "3コマ目のみ現在の自宅シーンで、ボーダー柄（白と紺）のカットソーにデニムパンツ。"
    )
    page104["漫画作成のプロンプト"] = page104["漫画作成のプロンプト"].replace(old_outfit, new_outfit)

    old_next_and_cta = by_page[136]["漫画作成のプロンプト"]
    next_body = old_next_and_cta.split("読者の方へ", 1)[0].rstrip()
    next_page = dict(by_page[136])
    next_page["ページ番号"] = "135"
    next_page["漫画作成のプロンプト"] = next_body

    author_page = set_page(by_page[135], 136)

    cta_image_page = dict(by_page[136])
    cta_image_page["ページ番号"] = "137"
    cta_image_page["使用するコマ割りテンプレ"] = "テンプレ1"
    cta_image_page["漫画作成のプロンプト"] = (
        "◆【画像ページ】第1巻と同じLINE登録用CTA画像を使用する。"
        "EPUB製本時は pages_jpeg/page_137.jpg をそのまま配置する。"
    )
    cta_image_page["コマ別テキストJSON"] = "[]"

    colophon_page = set_page(by_page[137], 138)

    patched_rows: list[dict[str, str]] = []
    for row in rows:
        page = int(row["ページ番号"])
        if page == 104:
            patched_rows.append(page104)
        elif page in {135, 136, 137}:
            continue
        else:
            patched_rows.append(row)
    patched_rows.extend([next_page, author_page, cta_image_page, colophon_page])
    patched_rows.sort(key=lambda r: int(r["ページ番号"]))

    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(patched_rows)

    if not CTA_SOURCE.exists():
        raise FileNotFoundError(CTA_SOURCE)
    CTA_PAGE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(CTA_SOURCE, CTA_PAGE)

    print(f"CSV_BACKUP: {backup}")
    print(f"CTA_PAGE: {CTA_PAGE}")


if __name__ == "__main__":
    main()

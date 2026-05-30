from __future__ import annotations

import csv
import shutil
from datetime import datetime
from pathlib import Path


CSV_PATH = Path(r"G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\vol2\panels\comicle_output.csv")


def main() -> None:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = CSV_PATH.with_name(f"{CSV_PATH.stem}_backup_before_colophon_date_may_{stamp}.csv")
    shutil.copy2(CSV_PATH, backup)

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    changed = 0
    for row in rows:
        if row.get("ページ番号") == "138":
            before = row["漫画作成のプロンプト"]
            after = before.replace("2026年4月　初版", "2026年5月　初版")
            row["漫画作成のプロンプト"] = after
            changed += before != after

    if changed != 1:
        raise RuntimeError(f"Expected one colophon date change, got {changed}")

    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV_BACKUP: {backup}")
    print("UPDATED: 2026年5月　初版")


if __name__ == "__main__":
    main()

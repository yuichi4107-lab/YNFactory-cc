from __future__ import annotations

import csv
import shutil
from pathlib import Path


CSV_PATH = Path(r"G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\vol2\panels\comicle_output.csv")


INSERT = """

無料で学べることには、大きな価値があります。入口を知る、雰囲気をつかむ、怪しいものを見分ける。そこまでは無料でも十分にできます。

でも、無料だけでは越えにくい壁もあります。自分の場合は何から始めるべきか。どこでつまずいているのか。続けるために何を削り、何を残すのか。

そこには、個別に見てもらう時間や、伴走してもらう環境が必要になることがあります。

もちろん、だからといって高額な商品を無条件に信じていいわけではありません。

その金額が妥当かどうかは、誰かが決めることではありません。SNSの評判でも、販売者の言葉でもなく、最後は自分が決めることです。

ミサキにとって9万円は、決して小さな金額ではありませんでした。だからこそ彼女は、怖さをごまかさずに見つめました。
"""


def main() -> None:
    backup = CSV_PATH.with_name("comicle_output_backup_before_column5_free_limit_20260505.csv")
    if not backup.exists():
        shutil.copy2(CSV_PATH, backup)

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    for row in rows:
        if row.get("ページ番号") == "134":
            prompt = row["漫画作成のプロンプト"]
            if "無料で学べることには、大きな価値があります。" not in prompt:
                marker = "9万円の意味"
                prompt = prompt.replace(marker, INSERT.strip() + "\n\n" + marker)
            row["漫画作成のプロンプト"] = prompt

    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"PATCHED: {CSV_PATH}")
    print(f"BACKUP: {backup}")


if __name__ == "__main__":
    main()

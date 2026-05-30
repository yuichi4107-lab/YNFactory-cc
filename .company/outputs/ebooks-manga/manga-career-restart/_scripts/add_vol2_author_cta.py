from __future__ import annotations

import csv
import shutil
from pathlib import Path


CSV_PATH = Path(r"G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\vol2\panels\comicle_output.csv")


AUTHOR_PROMPT = """◆【テキストページ】このページは画像生成不要。EPUB製本時にテキストとして直接レンダリングする。
◆【著者紹介】
著者紹介　Yuichi

キャリアコンサルタント／AI活用アドバイザー

企業人事として20年以上の経験を持ち、採用・育成・評価・労務管理に従事。

国家資格キャリアコンサルタントとして、これまでに100名以上のキャリア支援を行う。

現在は、転職・副業・AI活用をテーマに情報発信を行うほか、中小企業の経営者に対してAI導入・業務効率化の支援も行っている。

非エンジニア視点でのAI活用と、現場で使える形への落とし込みを強みとし、再現性の高い実践ノウハウを提供している。

※最新情報・無料相談はプロフィールよりご確認ください。"""


CTA_PROMPT = """◆【テキストページ】このページは画像生成不要。EPUB製本時にテキストとして直接レンダリングする。
◆【CTA】
次巻へ続く

第3巻では、ミサキがいよいよAIに触れ、自分の言葉で仕事を作る第一歩を踏み出します。

「事務しかできない」と思っていた自分が、AIを使って何を生み出せるのか。

不安と期待の間で揺れながらも、ミサキの再出発はここから本格的に動き始めます。

読者の方へ

本書が少しでも心に残りましたら、Amazonでレビューをいただけると励みになります。

続巻や関連情報は、著者プロフィールからご確認ください。"""


def make_text_row(fieldnames: list[str], page: str, prompt: str) -> dict[str, str]:
    row = {name: "" for name in fieldnames}
    row["ページ番号"] = page
    row["使用するコマ割りテンプレ"] = "テキストページ"
    row["漫画作成のプロンプト"] = prompt
    if "コマ別テキストJSON" in row:
        row["コマ別テキストJSON"] = "[]"
    return row


def main() -> None:
    backup = CSV_PATH.with_name("comicle_output_backup_before_author_cta_20260505.csv")
    if not backup.exists():
        shutil.copy2(CSV_PATH, backup)

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []
    if not fieldnames:
        raise RuntimeError("CSV header not found")

    colophon = None
    for row in rows:
        if "◆【奥付】" in row.get("漫画作成のプロンプト", ""):
            colophon = dict(row)
            break
    if not colophon:
        raise RuntimeError("Colophon row not found")
    rows = [
        row for row in rows
        if row.get("ページ番号") not in {"136", "137", "138"}
        and "◆【奥付】" not in row.get("漫画作成のプロンプト", "")
    ]

    colophon["ページ番号"] = "138"
    rows.append(make_text_row(fieldnames, "136", AUTHOR_PROMPT))
    rows.append(make_text_row(fieldnames, "137", CTA_PROMPT))
    rows.append(colophon)
    rows.sort(key=lambda r: int(r["ページ番号"]))

    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"UPDATED: {CSV_PATH}")
    print(f"BACKUP: {backup}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import csv
import shutil
from pathlib import Path


CSV_PATH = Path(r"G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\vol2\panels\comicle_output.csv")


def main() -> None:
    backup = CSV_PATH.with_name("comicle_output_backup_before_20260505_visual_fixes.csv")
    if not backup.exists():
        shutil.copy2(CSV_PATH, backup)

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames
    if not fieldnames:
        raise RuntimeError("CSV header not found")

    for row in rows:
        page = row.get("ページ番号", "")
        prompt = row.get("漫画作成のプロンプト", "")
        if "タクヤ" in prompt or row.get("outfit_id") == "takuya_zoom_mentor":
            prompt = prompt.replace(
                "白い無地のTシャツ、自室の白い壁を背景",
                "白い襟付きシャツ（白いボタンダウンシャツ）。Tシャツは禁止。自室の白い壁を背景",
            )
        if page == "111":
            prompt = prompt.replace(
                "「AIキャリア構築プログラム——3ヶ月間のマンツーマンコーチ",
                "「AIキャリア構築プログラム——3ヶ月間のマンツーマンコーチング",
            )
        if page == "112":
            prompt = prompt.replace("［四角枠］ング」金額を見た。月額3万円。3ヶ月で9万円。", "［四角枠］金額を見た。月額3万円。3ヶ月で9万円。")
            prompt = prompt.replace("ング」金額を見た。月額3万円。3ヶ月で9万円。", "金額を見た。月額3万円。3ヶ月で9万円。")
        if page == "114" and "タクヤ" not in prompt:
            prompt = prompt.replace(
                "◆【絶対最優先】キャラクター外見: ミサキは添付のミサキ.pngと100%同一の外見で描画（32歳女性、ショートボブの黒髪、丸顔）",
                "◆【絶対最優先】キャラクター外見: ミサキは添付のミサキ.pngと100%同一の外見で描画（32歳女性、ショートボブの黒髪、丸顔）\n◆【絶対最優先】キャラクター外見: タクヤは添付のタクヤ.pngと100%同一の外見で描画（42歳男性、短髪の黒髪、黒縁メガネ、白い襟付きシャツ。Tシャツは禁止）",
            )
        row["漫画作成のプロンプト"] = prompt

    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"PATCHED: {CSV_PATH}")
    print(f"BACKUP: {backup}")


if __name__ == "__main__":
    main()

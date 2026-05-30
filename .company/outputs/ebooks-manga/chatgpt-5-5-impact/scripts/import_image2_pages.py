from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[3]
REGEN_JOB = "chatgpt-5-5-impact_pages109-128_image2_20260506"
ORIGINAL_JOB = "chatgpt-5-5-impact_manga_vol1_20260505_051500"
REGEN_DONE = WORKSPACE / ".company" / "codex" / "done" / REGEN_JOB / "pages"
ORIGINAL_DONE = WORKSPACE / ".company" / "codex" / "done" / ORIGINAL_JOB / "pages"
FINAL_PAGES = ROOT / "panels" / "pages"
KDP = ROOT / "KDP出版用"


def jst_now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def find_image2_page(page_num: int) -> Path | None:
    stem = f"page_{page_num:03}"
    for ext in (".jpg", ".jpeg", ".png"):
        candidate = REGEN_DONE / f"{stem}{ext}"
        if candidate.exists():
            return candidate
    return None


def save_png_master(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        if im.mode != "RGB":
            im = im.convert("RGB")
        im.save(dst, "PNG")


def main() -> None:
    missing = [f"page_{i:03}.jpg/.png" for i in range(109, 129) if find_image2_page(i) is None]
    if missing:
        raise SystemExit("image2 pages are not complete: " + ", ".join(missing))

    backup = FINAL_PAGES / "_pre_image2_backup_20260506"
    backup.mkdir(parents=True, exist_ok=True)
    replaced = []
    for i in range(109, 129):
        name = f"page_{i:03}.png"
        dst = FINAL_PAGES / name
        if dst.exists():
            shutil.copy2(dst, backup / name)
        src = find_image2_page(i)
        assert src is not None
        ORIGINAL_DONE.mkdir(parents=True, exist_ok=True)
        save_png_master(src, ORIGINAL_DONE / name)
        replaced.append(name)

    subprocess.run(["python", str(ROOT / "scripts" / "finalize_manga.py")], cwd=WORKSPACE, check=True)

    progress_path = ROOT / "progress.json"
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    progress["completed_at"] = jst_now()
    progress["generation_mode"] = "chatgpt_builtin_image_generation_image2_for_pages_109_128"
    progress["pages"]["image2_replaced"] = len(replaced)
    progress["pages"]["needs_manual_review"] = 0
    progress["needs_manual_review_pages"] = []
    progress["needs_manual_review_reasons"] = {}
    progress_path.write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")

    report = f"""# image 2.0 差し替え完了レポート

- 完了時刻: {progress['completed_at']}
- 差し替え対象: page_109〜page_128
- 差し替え件数: {len(replaced)}
- EPUB: `マンガでわかる ChatGPT5.5の衝撃.epub`

page_109〜page_128 は Codex / ChatGPT 内蔵画像生成（image 2.0）版に差し替え済み。
"""
    (KDP / "image2_replacement_report.md").write_text(report, encoding="utf-8")
    print(json.dumps({"replaced": len(replaced), "backup": str(backup)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

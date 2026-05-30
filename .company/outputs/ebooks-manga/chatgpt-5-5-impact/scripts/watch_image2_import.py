from __future__ import annotations

import subprocess
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[3]
JOB_ID = "chatgpt-5-5-impact_pages109-128_image2_20260506"
DONE_PAGES = WORKSPACE / ".company" / "codex" / "done" / JOB_ID / "pages"
LOG = ROOT / "KDP出版用" / "image2_watch.log"
IMPORT_SCRIPT = ROOT / "scripts" / "import_image2_pages.py"


def jst() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def log(message: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{jst()}] {message}\n")


def page_exists(page_num: int) -> bool:
    stem = f"page_{page_num:03}"
    return any((DONE_PAGES / f"{stem}{ext}").exists() for ext in (".jpg", ".jpeg", ".png"))


def main() -> None:
    log("watch started")
    while True:
        count = sum(1 for i in range(109, 129) if page_exists(i))
        log(f"detected {count}/20 image2 pages")
        if count == 20:
            log("all pages detected; importing")
            subprocess.run(["python", str(IMPORT_SCRIPT)], cwd=WORKSPACE, check=True)
            log("import completed")
            break
        time.sleep(300)


if __name__ == "__main__":
    main()

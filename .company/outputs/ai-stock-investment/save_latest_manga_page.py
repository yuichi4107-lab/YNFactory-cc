# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from PIL import Image


ROOT = Path(".company/outputs/ai-stock-investment/マンガ版")
GENERATED_ROOT = Path("/Users/yuichi/.codex/generated_images")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("page", type=int)
    args = parser.parse_args()

    generated = sorted(GENERATED_ROOT.glob("*/*.png"), key=lambda p: p.stat().st_mtime)
    if not generated:
        raise RuntimeError("No generated images found")
    src = generated[-1]
    out = ROOT / "panels" / "pages" / f"page_{args.page:03d}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, out)
    im = Image.open(out).convert("RGB")
    im.save(out.with_suffix(".jpg"), quality=90, optimize=True)

    progress_path = ROOT / "progress.json"
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    done_pages = sorted(int(p.stem.split("_")[1]) for p in (ROOT / "panels" / "pages").glob("page_*.png"))
    progress["steps"]["5_images"]["completed"] = len(done_pages)
    missing = [p for p in range(2, 98) if p not in done_pages]
    progress["steps"]["5_images"]["missing_pages"] = missing
    progress["steps"]["5_images"]["status"] = "done" if not missing else "pending"
    progress_path.write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")

    print(out)
    print(out.with_suffix(".jpg"))
    print(f"completed={len(done_pages)} missing={len(missing)}")


if __name__ == "__main__":
    main()

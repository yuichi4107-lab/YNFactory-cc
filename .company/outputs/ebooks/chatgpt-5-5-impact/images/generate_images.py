from __future__ import annotations

import base64
import os
import re
import sys
import time
from pathlib import Path

from openai import OpenAI


ROOT = Path(__file__).resolve().parent
PLAN = ROOT / "image_plan.md"
MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1.5")
SIZE = os.environ.get("OPENAI_IMAGE_SIZE", "1536x1024")
QUALITY = os.environ.get("OPENAI_IMAGE_QUALITY", "medium")


def load_prompts() -> list[tuple[str, str]]:
    text = PLAN.read_text(encoding="utf-8")
    sections = re.split(r"^###\s+", text, flags=re.MULTILINE)[1:]
    prompts: list[tuple[str, str]] = []
    for section in sections:
        first, *rest = section.splitlines()
        filename = first.strip()
        body = "\n".join(rest)
        match = re.search(r"^- プロンプト:\s*(.+)$", body, flags=re.MULTILINE)
        if not match:
            continue
        prompts.append((filename, match.group(1).strip()))
    return prompts


def main() -> int:
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY is not set.")
        return 1

    client = OpenAI()
    prompts = load_prompts()
    if not prompts:
        print("ERROR: No prompts found.")
        return 1

    for index, (filename, prompt) in enumerate(prompts, start=1):
        out = ROOT / filename
        if out.exists() and out.stat().st_size > 0:
            print(f"SKIP [{index}/{len(prompts)}] {filename}")
            continue

        print(f"GENERATE [{index}/{len(prompts)}] {filename}", flush=True)
        try:
            result = client.images.generate(
                model=MODEL,
                prompt=prompt,
                size=SIZE,
                quality=QUALITY,
                n=1,
            )
        except Exception as exc:
            print(f"ERROR: API call failed for {filename}: {exc}")
            return 1

        item = (result.data or [None])[0]
        b64 = getattr(item, "b64_json", None)
        if not b64:
            print(f"ERROR: No image data returned for {filename}")
            return 1

        out.write_bytes(base64.b64decode(b64))
        print(f"OK {out} ({out.stat().st_size} bytes)", flush=True)
        time.sleep(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())

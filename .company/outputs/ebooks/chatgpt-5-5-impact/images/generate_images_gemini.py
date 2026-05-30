from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types


ROOT = Path(__file__).resolve().parent
PLAN = ROOT / "image_plan.md"
MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image-preview")
ASPECT_RATIO = os.environ.get("GEMINI_IMAGE_ASPECT_RATIO", "3:2")


def load_prompts() -> list[tuple[str, str]]:
    text = PLAN.read_text(encoding="utf-8")
    sections = re.split(r"^###\s+", text, flags=re.MULTILINE)[1:]
    prompts: list[tuple[str, str]] = []
    for section in sections:
        first, *rest = section.splitlines()
        filename = first.strip()
        body = "\n".join(rest)
        match = re.search(r"^- プロンプト:\s*(.+)$", body, flags=re.MULTILINE)
        if match:
            prompts.append((filename, match.group(1).strip()))
    return prompts


def main() -> int:
    api_key = os.environ.get("GOOGLE_AI_STUDIO_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_AI_STUDIO_API_KEY is not set.")
        return 1

    client = genai.Client(api_key=api_key)
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
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio=ASPECT_RATIO),
                ),
            )
        except Exception as exc:
            print(f"ERROR: API call failed for {filename}: {exc}")
            return 1

        image_saved = False
        text_parts: list[str] = []
        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts or []:
                if getattr(part, "inline_data", None) is not None:
                    image = part.as_image()
                    image.save(out)
                    image_saved = True
                    print(f"OK {out} ({out.stat().st_size} bytes)", flush=True)
                    break
                if getattr(part, "text", None):
                    text_parts.append(part.text)

        if not image_saved:
            print(f"ERROR: No image returned for {filename}")
            if text_parts:
                print("TEXT:", "".join(text_parts)[:500])
            return 1

        time.sleep(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Batch2 (2026-04-15) — Instagram Stories 30 images via NanoBanana2 (gemini-3.1-flash-image-preview).

Reads prompts.md, extracts the 30 "画像生成プロンプト:" blocks (one per Post N),
generates each image at 9:16 aspect ratio, saves to this directory as
post_{NN}_{timestamp}.png.

Runs sequentially with a small delay between calls to stay within rate limits.
Retries up to 3 times per image on transient errors.
"""
import os
import re
import sys
import time
import datetime

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "biz_idea_generator", ".env"
))

from google import genai
from google.genai import types

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPTS_PATH = os.path.join(BASE_DIR, "prompts.md")

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_AI_STUDIO_API_KEY")
if not API_KEY:
    print("ERROR: GEMINI_API_KEY / GOOGLE_AI_STUDIO_API_KEY not set")
    sys.exit(1)

MODEL = "gemini-3.1-flash-image-preview"
ASPECT = "9:16"
DELAY_BETWEEN = 4.0  # seconds between successful calls
MAX_RETRIES = 3


def parse_prompts(md_text: str) -> list[tuple[int, str]]:
    """Return [(post_no, english_prompt_text), ...] sorted by post_no."""
    result = []
    # Each post is "### Post N —" followed by "**画像生成プロンプト:**" then prompt until blank line before "**日本語原稿:**"
    post_pattern = re.compile(r"^### Post (\d+)\s*[—-]", re.MULTILINE)
    matches = list(post_pattern.finditer(md_text))
    for i, m in enumerate(matches):
        post_no = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md_text)
        section = md_text[start:end]
        # Find prompt block
        mp = re.search(
            r"\*\*画像生成プロンプト:\*\*\s*\n(.*?)(?=\n\s*\*\*日本語原稿:|\n\s*---\s*\n|\Z)",
            section,
            re.DOTALL,
        )
        if mp:
            prompt_text = mp.group(1).strip()
            result.append((post_no, prompt_text))
    result.sort(key=lambda x: x[0])
    return result


def generate_image(client, prompt: str) -> bytes | None:
    cfg = types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
        image_config=types.ImageConfig(aspect_ratio=ASPECT),
    )
    resp = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=cfg,
    )
    if not resp.candidates or not resp.candidates[0].content:
        return None
    for part in resp.candidates[0].content.parts or []:
        if getattr(part, "inline_data", None):
            return part.inline_data.data
    return None


def save_image(data: bytes, post_no: int) -> str:
    ts = int(time.time() * 1000)
    filename = f"post_{post_no:02d}_{ts}.png"
    path = os.path.join(BASE_DIR, filename)
    with open(path, "wb") as f:
        f.write(data)
    return path


def main():
    with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
        md = f.read()

    prompts = parse_prompts(md)
    print(f"Parsed {len(prompts)} prompts from prompts.md")
    if len(prompts) != 30:
        print(f"WARNING: expected 30 posts, got {len(prompts)}")

    # Skip if already generated
    existing = {int(m.group(1)) for m in (re.match(r"post_(\d+)_", fn) for fn in os.listdir(BASE_DIR)) if m}
    if existing:
        print(f"Found existing posts: {sorted(existing)} — skipping those")

    client = genai.Client(api_key=API_KEY)
    success = []
    failed = []

    for post_no, prompt in prompts:
        if post_no in existing:
            continue
        print(f"[Post {post_no:02d}] Generating...")
        last_err = None
        data = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                data = generate_image(client, prompt)
                if data:
                    break
                last_err = "no image in response"
            except Exception as e:
                last_err = str(e)
                print(f"  attempt {attempt} failed: {last_err[:200]}")
                time.sleep(5 * attempt)
        if data:
            path = save_image(data, post_no)
            print(f"  OK → {os.path.basename(path)}")
            success.append(post_no)
            time.sleep(DELAY_BETWEEN)
        else:
            print(f"  FAILED: {last_err}")
            failed.append((post_no, last_err))

    print("\n=== SUMMARY ===")
    print(f"Success: {len(success)}/{len(prompts) - len(existing)}")
    if failed:
        print("Failed:")
        for p, err in failed:
            print(f"  Post {p:02d}: {err}")
    print("=== DONE ===")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())

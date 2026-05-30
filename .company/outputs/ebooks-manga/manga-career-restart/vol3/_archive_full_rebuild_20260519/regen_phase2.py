# -*- coding: utf-8 -*-
"""Vol3 Phase 2 batch regeneration script.
Fixes instruction-marker leaks and dialogue inaccuracies for 10 pages.
Uses character reference images via Gemini multimodal input.
"""
import os, sys, io, csv, datetime, re, time
from google import genai
from google.genai import types
from PIL import Image

ROOT = r"g:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart"
VOL = os.path.join(ROOT, "vol3")
CSV_PATH = os.path.join(VOL, "panels", "comicle_output.csv")
CHARS_DIR = os.path.join(ROOT, "manuscript", "characters")
OUT_DIR = os.path.join(VOL, "pages", "_regen_test")
os.makedirs(OUT_DIR, exist_ok=True)

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("ERROR: GEMINI_API_KEY missing"); sys.exit(1)

# Load character reference images
REFS = {
    "ミサキ": Image.open(os.path.join(CHARS_DIR, "ミサキ.png")),
    "ケンタ": Image.open(os.path.join(CHARS_DIR, "ケンタ.png")),
    "タクヤ": Image.open(os.path.join(CHARS_DIR, "タクヤ.png")),
    "ひなた_2歳期": Image.open(os.path.join(CHARS_DIR, "ひなた_2歳期.png")),
}

# Reinforcement prefix to prepend to each prompt
REINFORCE_PREFIX = """【本画像生成の最重要ルール・絶対遵守】
1. 画像内に描画してよいテキストは「セリフ本文」「ナレーション本文」「オノマトペ」「時計表示」「画面内テキスト」のみです。
2. **下記の指示記号類は絶対に画像内に文字として描画しないこと**:
   - 「［四角枠］」「［ナレーション］」「［ミサキ］」「［ケンタ］」「［タクヤ］」等の話者マーカー
   - 「ナレーション:」「セリフ:」「吹き出しに」などのラベル文字
   - 【】で囲まれた指示（【タイトル】【感情】等）
3. 日本語ナレーションとセリフは、指定された原文を**一字一句正確に**、文字化けさせずに描画すること。
4. 同じナレーション・セリフを画像内で重複描画しないこと（1箇所のみ）。
5. キャラクターは添付の参照画像どおりの顔立ち・髪型・体格を厳守すること（参照画像の雰囲気・スタイルを忠実に再現）。
6. 屋内シーン（リビング・ダイニング・寝室等）ではスニーカー・パンプス等の靴を履かせないこと（白い靴下または素足）。

以下、具体的なページプロンプト:

"""

# Target pages and character refs needed
TARGETS = {
    28: ["ミサキ", "タクヤ"],
    32: ["ミサキ"],
    37: ["ミサキ"],
    57: ["ミサキ"],
    66: ["ミサキ"],
    89: ["ミサキ"],
    96: ["ミサキ", "タクヤ"],
    102: ["ミサキ"],
    104: ["ミサキ", "ケンタ"],
    110: ["ミサキ", "ケンタ", "ひなた_2歳期"],
}


def load_csv_prompts():
    """Parse the CSV and return {page_num: prompt_text}."""
    prompts = {}
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i == 0:
                continue
            if len(row) < 3:
                continue
            try:
                page = int(row[0])
            except ValueError:
                continue
            prompts[page] = row[2]
    return prompts


def clean_prompt(prompt: str) -> str:
    """Remove instruction-marker patterns that are getting literally drawn.
    Keep the story content intact but strip explicit marker notation.
    """
    # Replace ［四角枠］ markers in narration lines with just "ナレーション枠:"
    prompt = prompt.replace("［四角枠］", "")
    # Remove ［キャラ名］の吹き出しに patterns - keep just the dialogue
    prompt = re.sub(r"［[^］]+］の吹き出しに", "", prompt)
    prompt = re.sub(r"［[^］]+］", "", prompt)
    return prompt


def regenerate_page(client, page: int, prompt: str, refs: list):
    """Generate one page and save to _regen_test/."""
    full_prompt = REINFORCE_PREFIX + clean_prompt(prompt)
    contents = [full_prompt] + refs
    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                image_config=types.ImageConfig(aspect_ratio="9:16"),
            ),
        )
    except Exception as e:
        print(f"[P{page}] API ERROR: {e}")
        return False

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    saved = False
    for part in response.candidates[0].content.parts:
        if getattr(part, "inline_data", None) is not None:
            path = os.path.join(OUT_DIR, f"page_{page:03d}_p2_{ts}.jpg")
            img = Image.open(io.BytesIO(part.inline_data.data))
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.save(path, "JPEG", quality=92)
            print(f"[P{page}] OK: {path}")
            saved = True
        elif getattr(part, "text", None):
            print(f"[P{page}] TEXT: {part.text[:150]}")
    if not saved:
        print(f"[P{page}] WARN: no image in response")
    return saved


def main():
    prompts = load_csv_prompts()
    print(f"Loaded {len(prompts)} prompts from CSV")
    client = genai.Client(api_key=API_KEY)

    results = {}
    for page, char_keys in TARGETS.items():
        if page not in prompts:
            print(f"[P{page}] SKIP: not in CSV")
            continue
        refs = [REFS[k] for k in char_keys if k in REFS]
        print(f"\n=== Page {page} (refs: {char_keys}) ===")
        ok = regenerate_page(client, page, prompts[page], refs)
        results[page] = ok
        time.sleep(2)

    print("\n=== Summary ===")
    for p, ok in results.items():
        print(f"  P{p}: {'OK' if ok else 'FAIL'}")


if __name__ == "__main__":
    main()

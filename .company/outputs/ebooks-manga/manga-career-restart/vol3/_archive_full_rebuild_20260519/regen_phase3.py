# -*- coding: utf-8 -*-
"""Vol3 Phase 3 batch regeneration: indoor-shoes fix for 28 pages.
Strategy: reuse the original CSV prompt but rewrite the 服装 line to replace
「白いスニーカー」 with 「白い靴下」 for indoor scenes. Also attach character
reference images so the regenerated character stays visually consistent.
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

REFS = {
    "ミサキ": Image.open(os.path.join(CHARS_DIR, "ミサキ.png")),
    "ケンタ": Image.open(os.path.join(CHARS_DIR, "ケンタ.png")),
    "タクヤ": Image.open(os.path.join(CHARS_DIR, "タクヤ.png")),
    "ひなた_2歳期": Image.open(os.path.join(CHARS_DIR, "ひなた_2歳期.png")),
}

REINFORCE = """【本画像生成の最重要ルール・絶対遵守】
1. 画像内に描画してよいテキストは「セリフ本文」「ナレーション本文」「オノマトペ」「時計表示」「画面内テキスト」のみ。
2. 以下は絶対に画像内に文字として描画しないこと:
   - 指示記号「［四角枠］」「［ナレーション］」「［ミサキ］」「［ケンタ］」「［タクヤ］」
   - ラベル「ナレーション:」「セリフ:」「吹き出しに」
   - 【】で囲まれた指示
3. 日本語ナレーションとセリフは原文を一字一句正確に、文字化けなしで描画。
4. 同じナレーション・セリフを画像内で重複描画しないこと（1箇所のみ）。
5. キャラクターは添付参照画像どおりの顔立ち・髪型・体格を厳守。
6. **重要: 屋内シーン（自宅リビング・ダイニング・寝室）では登場人物全員を白い靴下または素足で描画。スニーカー・パンプス・革靴の描写を絶対禁止。**

以下、具体的なページプロンプト:

"""

# Target pages for indoor shoes fix (retry of failed pages from first run)
TARGETS = [6, 8, 9, 10, 11, 22, 24, 25, 30]


def load_prompts():
    prompts = {}
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i == 0 or len(row) < 3:
                continue
            try:
                page = int(row[0])
            except ValueError:
                continue
            prompts[page] = row[2]
    return prompts


def detect_chars(prompt: str) -> list:
    """Detect which character refs are needed based on prompt text."""
    chars = []
    if "ミサキ" in prompt:
        chars.append("ミサキ")
    if "ケンタ" in prompt:
        chars.append("ケンタ")
    if "タクヤ" in prompt:
        chars.append("タクヤ")
    if "ひなた" in prompt:
        chars.append("ひなた_2歳期")
    return chars


def clean_prompt(prompt: str) -> str:
    """Remove instruction markers and replace sneaker specs for indoor fix."""
    prompt = prompt.replace("［四角枠］", "")
    prompt = re.sub(r"［[^］]+］の吹き出しに", "", prompt)
    prompt = re.sub(r"［[^］]+］", "", prompt)
    # Replace indoor-shoe spec
    prompt = prompt.replace("白いスニーカー", "白い靴下")
    return prompt


def regen(client, page, prompt, refs, max_retry=3):
    full = REINFORCE + clean_prompt(prompt)
    contents = [full] + refs
    resp = None
    for attempt in range(max_retry):
        try:
            resp = client.models.generate_content(
                model="gemini-3.1-flash-image-preview",
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio="9:16"),
                ),
            )
            break
        except Exception as e:
            print(f"[P{page}] attempt {attempt+1} ERROR: {e}")
            if attempt < max_retry - 1:
                time.sleep(10 * (attempt + 1))
    if resp is None:
        return False

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    saved = False
    for part in resp.candidates[0].content.parts:
        if getattr(part, "inline_data", None) is not None:
            path = os.path.join(OUT_DIR, f"page_{page:03d}_p3_{ts}.jpg")
            img = Image.open(io.BytesIO(part.inline_data.data))
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.save(path, "JPEG", quality=92)
            print(f"[P{page}] OK: {path}")
            saved = True
    return saved


def main():
    prompts = load_prompts()
    print(f"Loaded {len(prompts)} prompts")
    client = genai.Client(api_key=API_KEY)
    ok, fail = 0, 0
    for page in TARGETS:
        if page not in prompts:
            print(f"[P{page}] SKIP: not in CSV")
            fail += 1
            continue
        chars = detect_chars(prompts[page])
        refs = [REFS[c] for c in chars if c in REFS]
        print(f"\n=== P{page} (refs: {chars}) ===")
        if regen(client, page, prompts[page], refs):
            ok += 1
        else:
            fail += 1
        time.sleep(2)
    print(f"\nDone: {ok} OK, {fail} FAIL")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""ChatGPTを部下にする働き方 — 挿絵・表紙を温かいアニメ調イラストで再生成(v2)
career-restartシリーズの雰囲気（半リアル系アニメ/ライトノベル風・暖色シネマティック）に合わせる。
"""
import os, sys, time
from google import genai
from google.genai import types

API_KEY = os.environ["GOOGLE_AI_STUDIO_API_KEY"]
OUTDIR = r"g:/マイドライブ/YNFactory-cc/.company/outputs/ebooks-text/chatgpt-bukadesuru/images"
os.makedirs(OUTDIR, exist_ok=True)
client = genai.Client(api_key=API_KEY)

# 共通アートディレクション（career-restartの温かいアニメ調に合わせる）
STYLE = (
    "Warm, soft, semi-realistic Japanese anime / light-novel illustration style. "
    "Gentle cinematic lighting with cozy golden warmth, soft rim light and subtle bokeh; "
    "detailed, inviting interior or office backgrounds (plants, books, lamp, window light); "
    "expressive natural face, clean crisp line art, soft cel shading and gentle ambient glow. "
    "Wholesome, emotional, hopeful, heartwarming mood. High-quality modern Japanese web-manga illustration. "
)
# 一貫した主人公
HERO = (
    "The recurring main character is the SAME relatable Japanese woman office worker in her late 30s: "
    "shoulder-length dark brown hair, gentle kind face, soft natural smile, smart-casual blouse and cardigan. "
)
# AI表現
AI_NOTE = ("AI is represented subtly by a softly glowing laptop or smartphone screen (NOT a cartoon robot mascot). "
           "All laptops and devices are plain and unbranded — NO logo on the lid, no apple, no trademark of any kind. ")

NOTEXT = "Do NOT render any text, letters, logos, captions or UI words in the image. No watermark. "

JOBS = [
    # (filename, aspect, scene, with_text)
    ("ch0_header","3:2",
     "Scene: evening, the woman sits at a tidy home desk lit by a warm lamp, looking at her glowing laptop with a slightly worried but softening, reassured expression. Cozy room, plant and family photo in soft focus. Quiet, intimate, hopeful mood.", False),
    ("ch1_header","3:2",
     "Scene: the woman pauses thoughtfully at her office desk by a large window with a warm city view; some documents on the desk, a calm contemplative look as if weighing a choice. Soft daylight, gentle warmth.", False),
    ("ch2_header","3:2",
     "Scene: the woman works confidently at her laptop in a cozy warm office, a soft glowing chat interface light on the screen reflecting on her face; she has a calm, in-control, slightly confident smile, as if directing a capable assistant.", False),
    ("ch3_header","3:2",
     "Scene: bright morning, the woman studies happily at a cafe-like desk with an open laptop and a notebook, a cup of coffee and a small plant; warm sunlight through the window, an eager, learning-something-new expression.", False),
    ("ch4_header","3:2",
     "Scene: in a warm modern office, the woman presents something on her laptop while two colleagues and an older manager look on with appreciative, approving smiles; collaborative, trusted, supported atmosphere, warm light.", False),
    ("ch5_header","3:2",
     "Scene: evening at a cozy home desk, the woman does relaxed side-work on her laptop, a warm mug beside her, soft lamp and string lights, content and calm; a faint hint of a small growth/income chart glowing softly on screen.", False),
    ("ch6_header","3:2",
     "Scene: the woman stands by a window at sunrise looking out toward a bright, gently glowing city skyline, a hopeful, peaceful, forward-looking expression; warm golden morning light bathes the room.", False),
    ("ch7_header","3:2",
     "Scene: fresh bright morning, the woman steps forward out of a doorway into warm sunlight on a quiet street, smiling with gentle confidence and a fresh-start feeling; soft lens flare, hopeful uplifting mood.", False),
    ("ch1_inline","3:2",
     "Split composition. LEFT half: a glowing laptop on a desk efficiently processing documents and charts by itself (representing routine work AI handles), cool soft glow. RIGHT half: the woman warmly talking and gently shaking hands with a client across a table (human trust and connection), warm light. Balanced, storytelling contrast.", False),
    ("ch2_inline","3:2",
     "Close, cozy scene: over-the-shoulder view of the woman calmly typing a clear instruction into a softly glowing AI chat on her laptop, thoughtful confident expression, warm desk lamp, plant nearby. Feeling of giving direction to a capable helper.", False),
    ("ch3_inline","3:2",
     "Heartwarming progression feeling: the woman studying with growing confidence at her desk; a wall calendar and a small potted plant that looks like it is thriving, soft upward beam of warm light suggesting growth over time.", False),
    ("ch5_inline","3:2",
     "Cozy evening scene: the woman at a warm home desk, gently surrounded by a few soft glowing vignettes floating like warm thought-bubbles representing side activities — writing/a book, a smartphone with a heart, a small video play icon — all in soft warm light. Inviting, hopeful.", False),
    ("cover","2:3",
     "Vertical book cover. A confident, gently smiling Japanese woman office worker in her late 30s sits at a tidy desk with a warmly glowing plain unbranded silver laptop (NO logo on the lid, no apple, no trademark), looking hopefully toward the viewer; cozy evening room with soft warm lamp light, plant and bookshelf softly blurred behind. Cinematic, emotional, premium bestselling-book look. "
     'Leave clear space at top and bottom for title text. TITLE (top, large, bold, dark navy on a soft light band): the Japanese text reads "ChatGPTを部下にする働き方". SUBTITLE band (below title, smaller, on a navy ribbon): the Japanese text reads "AI時代のキャリア防衛＆副業入門". A small rounded gold badge in a top corner: the text reads "2026年最新版". AUTHOR at the very bottom (smaller, centered): the Japanese text reads "暮らしの貯蓄研究所". Render ONLY these exact words, large and perfectly legible, no garbled characters, no other text.', True),
]

def gen(fn, aspect, scene, with_text):
    if with_text:
        prompt = STYLE + scene
    else:
        prompt = STYLE + HERO + AI_NOTE + "SCENE: " + scene + " " + NOTEXT
    prompt += f" Composition aspect {aspect}."
    path = os.path.join(OUTDIR, fn + ".png")
    for attempt in range(3):
        try:
            r = client.models.generate_content(
                model="gemini-3.1-flash-image-preview", contents=prompt,
                config=types.GenerateContentConfig(response_modalities=["TEXT","IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio=aspect)))
            for p in r.candidates[0].content.parts:
                if getattr(p,"inline_data",None):
                    p.as_image().save(path); print("OK", fn); return True
            print("NOIMG", fn, attempt)
        except Exception as e:
            print("ERR", fn, repr(e)[:140])
        time.sleep(4)
    return False

if __name__ == "__main__":
    only = sys.argv[1:] if len(sys.argv)>1 else None
    ok=0
    for fn,aspect,scene,wt in JOBS:
        if only and fn not in only: continue
        if gen(fn,aspect,scene,wt): ok+=1
        time.sleep(2)
    print(f"--- DONE {ok} images ---")

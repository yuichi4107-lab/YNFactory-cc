# -*- coding: utf-8 -*-
"""ChatGPTを部下にする働き方 — 本文挿絵12点をNanoBanana2で生成"""
import os, sys, time
from google import genai
from google.genai import types

API_KEY = os.environ["GOOGLE_AI_STUDIO_API_KEY"]
OUTDIR = r"g:/マイドライブ/YNFactory-cc/.company/outputs/ebooks-text/chatgpt-bukadesuru/images"
os.makedirs(OUTDIR, exist_ok=True)
client = genai.Client(api_key=API_KEY)

STYLE = (
    "Clean modern flat design illustration for a Japanese business self-help ebook. "
    "Color palette: deep navy #1B3A5C, warm gold #E8A33D, teal #4A90A4, on a clean white background. "
    "Rounded shapes, simple friendly icons, professional yet approachable and trustworthy aesthetic. "
    "IMPORTANT TEXT RULE: render ONLY the exact Japanese words specified below, large and clean and correct. "
    "Do NOT add any extra badge, subtitle, watermark, caption or decorative label. No garbled or fake characters. "
    "No real company logos or trademarks."
)

JOBS = [
    # (filename, aspect, scene)
    ("ch0_header","3:2",
     'Chapter header banner. Show the large Japanese title text "はじめに". '
     'Scene: a friendly Japanese office worker sitting at a desk together with a cute simple robot/AI character beside them; '
     'the AI is organizing documents while the person looks relaxed and reassured. Warm, collaborative, hopeful mood.'),
    ("ch1_header","3:2",
     'Chapter header banner. Show the large Japanese title text "AI時代の仕事". '
     'Scene: a Japanese office worker standing at a forked road, calmly choosing a direction; one branch has data and calculator icons, the other has speech-bubble and lightbulb icons.'),
    ("ch2_header","3:2",
     'Chapter header banner. Show the large Japanese title text "AIを部下に". '
     'Scene: a Japanese office worker calmly giving instructions like a manager, while a cute simple robot/AI character takes notes attentively. The human is clearly in charge.'),
    ("ch3_header","3:2",
     'Chapter header banner. Show the large Japanese title text "リスキリング". '
     'Scene: a Japanese office worker climbing a bright three-step staircase, each step marked with a simple app/AI icon, optimistic upward motion.'),
    ("ch4_header","3:2",
     'Chapter header banner. Show the large Japanese title text "キャリア防衛". '
     'Scene: in an office, one Japanese worker with a laptop is relied upon by colleagues; a boss nods approvingly; a subtle shield motif in the background suggests protection.'),
    ("ch5_header","3:2",
     'Chapter header banner. Show the large Japanese title text "AIで副業". '
     'Scene: a person relaxing at a home desk with a laptop, a small AI helper on the screen, beside a small upward income graph and a few coins.'),
    ("ch6_header","3:2",
     'Chapter header banner. Show the large Japanese title text "AIと共存". '
     'Scene: a person and a cute simple robot/AI character walking side by side seen from behind, heading toward a bright future cityscape. Hopeful, calm.'),
    ("ch7_header","3:2",
     'Chapter header banner. Show the large Japanese title text "おわりに". '
     'Scene: at a sunrise start line, a Japanese office worker steps forward positively while a cute simple robot/AI character gently pushes their back. Encouraging, fresh-start mood.'),
    ("ch1_inline","3:2",
     'A simple two-card comparison infographic. Left card title text "AIが得意" with three short bullet items text "定型処理", "大量反復", "データ分析" (with small icons). '
     'Right card title text "人が得意" with three short bullet items text "対話と信頼", "判断と責任", "新しい発想" (with small icons). Balanced, clean.'),
    ("ch2_inline","3:2",
     'A simple vertical list infographic titled text "良い指示の4要素". Four rows, each a rounded card with one large kanji and a tiny label: '
     'row1 big "役", row2 big "的", row3 big "件", row4 big "型". Small friendly icons beside each. Keep it minimal.'),
    ("ch3_inline","3:2",
     'A simple ascending three-step staircase infographic. Three steps labeled text "1ヶ月目", "2ヶ月目", "3ヶ月目" from low to high, each with a small icon, an upward arrow. Optimistic.'),
    ("ch5_inline","3:2",
     'A simple hub-and-spoke infographic. Center circle text "AI副業". Around it, seven small rounded labels with icons: '
     'text "Kindle出版", "ブログ", "SNS運用", "オンライン講座", "翻訳要約", "資料作成", "動画編集". Keep labels short and readable.'),
]

def gen(fn, aspect, scene):
    prompt = STYLE + "\n\nSCENE: " + scene + f"\nComposition: {'horizontal banner' if aspect=='3:2' else 'balanced'}."
    path = os.path.join(OUTDIR, fn + ".png")
    for attempt in range(2):
        try:
            r = client.models.generate_content(
                model="gemini-3.1-flash-image-preview", contents=prompt,
                config=types.GenerateContentConfig(response_modalities=["TEXT","IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio=aspect)))
            for p in r.candidates[0].content.parts:
                if getattr(p,"inline_data",None):
                    p.as_image().save(path); print("OK", fn); return True
            print("NOIMG", fn, "(retry)" if attempt==0 else "(fail)")
        except Exception as e:
            print("ERR", fn, repr(e)[:160], "(retry)" if attempt==0 else "(fail)")
        time.sleep(3)
    return False

if __name__ == "__main__":
    only = sys.argv[1:] if len(sys.argv)>1 else None
    ok=0
    for fn,aspect,scene in JOBS:
        if only and fn not in only: continue
        if gen(fn,aspect,scene): ok+=1
        time.sleep(2)
    print(f"--- DONE {ok} images ---")

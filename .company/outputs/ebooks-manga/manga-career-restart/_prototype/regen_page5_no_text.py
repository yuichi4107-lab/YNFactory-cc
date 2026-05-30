"""
Prototype: regenerate page 5 WITHOUT any text/dialogue baked into the image.
Purpose: prove that keeping the generator focused on visuals only, and overlaying
Japanese text in post via Pillow, produces 100% accurate dialogue.
"""
import os
import sys
import datetime

sys.stdout.reconfigure(encoding='utf-8')

try:
    from google import genai
    from google.genai import types
    from PIL import Image
except ImportError as e:
    print(f"ERROR: missing package: {e}")
    sys.exit(1)

API_KEY = os.environ.get("GOOGLE_AI_STUDIO_API_KEY")
if not API_KEY:
    print("ERROR: GOOGLE_AI_STUDIO_API_KEY not set")
    sys.exit(1)

ROOT = r"G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart"
CHAR_DIR = os.path.join(ROOT, "manuscript", "characters")
OUT_DIR = os.path.join(ROOT, "_prototype")
os.makedirs(OUT_DIR, exist_ok=True)

PROMPT = """◆【絶対最優先】必ず日本のアニメ・マンガ調のイラストで描いてください。実写風・フォトリアル風は禁止です。
◆【絶対最優先】必ずフルカラーにしてください
◆【絶対最優先】キャラクター外見: ミサキは添付のミサキ.pngと100%同一の外見で描画
◆【絶対最優先】キャラクター外見: ケンタは添付のケンタ.pngと100%同一の外見で描画

◆【最重要・テキスト除去】このページには一切のテキスト・文字・セリフ・吹き出し・ナレーションボックス・オノマトペを描かないでください。
- No text, no dialogue, no speech bubbles, no onomatopoeia, no narration boxes
- 吹き出しの枠も描かないでください(後処理で合成します)
- 擬音・効果音の文字も描かないでください
- コマ内はキャラクター・背景・小物のみで構成してください

◆【出力サイズ】9:16
◆【補足情報】上下左右に50ピクセルの余白を設けてください
◆【補足情報】服装: ミサキ: ボーダー柄(白と紺)のカットソーにデニムパンツ、白いスニーカー
◆【補足情報】服装: ケンタ: グレーのTシャツにネイビーのスウェットパンツ

◆【コマ構成】テンプレ6: 上1コマ+下左右2コマ
上段に大きい横長1コマ、下段を左右2分割して小さい2コマ。コマ同士の間には白い溝(ガター)を入れてください。

◆【作画】ジャンル: 副業に最適化した統一スタイル / 作画スタイル: 親しみやすく実践的,現代的なライフスタイル表現 / 色調: 明るく前向きな色調,オレンジ・青・黄色基調,活力ある配色 / 線画: 親しみやすい柔らかな線,カジュアルで読みやすい表現 / 演出: 必要に応じて集中線,効果線などのマンガらしい演出(ただし文字は一切入れない)

◆【ストーリー・構図のみ】
1コマ目(上・横長): ミサキとケンタが並んで立ち、ミサキがケンタに顔を向けて期待に満ちた笑顔で話しかけている。背景は暖色系のフラッシュエフェクト。吹き出しは描かない。
2コマ目(下左): ケンタのバストアップ。コーヒーカップを片手に持ちながら穏やかに笑っている。吹き出しは描かない。
3コマ目(下右): ミサキのバストアップ。スマホを取り出して画面を見せるようにかざし、楽しそうな表情。スマホ画面は空白でよい(アプリUIは描かない)。吹き出しは描かない。
"""

def load_ref(name):
    path = os.path.join(CHAR_DIR, name)
    with open(path, "rb") as f:
        return types.Part.from_bytes(data=f.read(), mime_type="image/png")

client = genai.Client(api_key=API_KEY)

contents = [
    PROMPT,
    load_ref("ミサキ.png"),
    load_ref("ケンタ.png"),
]

print("Generating page 5 (no text)...")
response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=contents,
    config=types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
        image_config=types.ImageConfig(aspect_ratio="9:16"),
    ),
)

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
saved = False
import io
if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data is not None:
            out_path = os.path.join(OUT_DIR, f"page_005_no_text_{timestamp}.jpg")
            raw = part.inline_data.data
            pil_img = Image.open(io.BytesIO(raw)).convert("RGB")
            pil_img.save(out_path, "JPEG", quality=92)
            stable_path = os.path.join(OUT_DIR, "page_005_no_text.jpg")
            pil_img.save(stable_path, "JPEG", quality=92)
            print(f"OK: {out_path}")
            print(f"OK: {stable_path}")
            saved = True

if not saved:
    print("ERROR: no image in response")
    if response.candidates:
        for part in response.candidates[0].content.parts or []:
            if hasattr(part, "text") and part.text:
                print("TEXT:", part.text[:500])

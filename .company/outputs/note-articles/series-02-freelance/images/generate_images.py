import sys
import os
import time

from dotenv import load_dotenv
load_dotenv(dotenv_path="/Users/yuichi/Library/CloudStorage/GoogleDrive-yuichi4107@gmail.com/マイドライブ/YNFactory-cc/biz_idea_generator/.env")

from google import genai
from google.genai import types

OUTPUT_DIR = "/Users/yuichi/Library/CloudStorage/GoogleDrive-yuichi4107@gmail.com/マイドライブ/YNFactory-cc/.company/outputs/note-articles/series-02-freelance/images/"

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

IMAGES = [
    {
        "filename": "2026-04-20_eyecatch.png",
        "aspect_ratio": "16:9",
        "prompt": "Digital manga style illustration, 16:9 aspect ratio, vibrant colors, clean lines. A young Japanese businessman in a modern meeting room pressing the record button on a smartphone placed on the conference table. Laptops and a whiteboard in the background. Sound wave visualization floating above the smartphone. No handwritten notes anywhere. Bright office lighting, cheerful atmosphere. No text.",
    },
    {
        "filename": "2026-04-20_img01.png",
        "aspect_ratio": "16:9",
        "prompt": "Digital manga style illustration, 16:9 aspect ratio, clean lines, muted tired color palette. A tired Japanese office worker sitting at a desk late at night, surrounded by scattered handwritten memo papers and sticky notes. A clock on the wall showing midnight. The worker looks exhausted staring at a laptop screen. Messy desk with coffee cups. No text.",
    },
    {
        "filename": "2026-04-20_img02.png",
        "aspect_ratio": "16:9",
        "prompt": "Digital manga style illustration, 16:9 aspect ratio, vibrant colors, clean lines. Split-screen Before/After comparison. Left side: a stressed Japanese worker buried in papers, clock showing 55 minutes, dark tones. Right side: the same worker smiling and relaxed drinking coffee, clock showing 8 minutes, bright warm tones. A large arrow in the center pointing from left to right. No text.",
    },
    {
        "filename": "2026-04-21_eyecatch.png",
        "aspect_ratio": "16:9",
        "prompt": "Digital manga style illustration, 16:9 aspect ratio, vibrant colors, clean lines. A Japanese person's hands typing on a laptop keyboard. The laptop screen shows a digital bookstore interface with book covers displayed. Several colorful e-book covers floating beside the screen in a dynamic composition. Warm, bright, achievement-oriented atmosphere. Home office desk with a coffee mug. No text on book covers, no text anywhere.",
    },
    {
        "filename": "2026-04-21_img01.png",
        "aspect_ratio": "16:9",
        "prompt": "Digital manga style illustration, 16:9 aspect ratio, clean lines, vibrant colors. A conceptual diagram showing a document file icon on the left transforming into an e-book file icon on the right via a large arrow. Warning signs, exclamation marks, and small obstacle icons floating around the arrow path. A Japanese person looking puzzled at the conversion process. Light background with tech elements. No text.",
    },
    {
        "filename": "2026-04-21_img02.png",
        "aspect_ratio": "16:9",
        "prompt": "Digital manga style illustration, 16:9 aspect ratio, vibrant colors, clean lines. A friendly cute AI robot character in the center. Four icons floating around it in a circular arrangement: a pen icon for proofreading, a paintbrush icon for cover art, a speech bubble icon for copywriting, and a comic panel icon for manga conversion. Bright cheerful background with sparkles. No text.",
    },
    {
        "filename": "2026-04-22_eyecatch.png",
        "aspect_ratio": "16:9",
        "prompt": "Digital manga style illustration, 16:9 aspect ratio, vibrant colors, clean lines. A bookshelf displaying four e-books with a unified cover design in a series, each with a different accent color but same layout. A rising graph arrow overlaid on the first book showing growth. A young Japanese author standing beside the shelf looking satisfied and proud. Warm lighting, success atmosphere. No text on books, no text anywhere.",
    },
    {
        "filename": "2026-04-22_img01.png",
        "aspect_ratio": "16:9",
        "prompt": "Digital manga style illustration, 16:9 aspect ratio, clean lines, vibrant colors. Split comparison. Left side: a single lonely book on an empty shelf, dull colors, one small arrow pointing to one reader silhouette. Right side: four books in a series on a shelf with bright colors, multiple arrows connecting between books and multiple reader silhouettes, showing cross-selling effect. No text.",
    },
    {
        "filename": "2026-04-22_img02.png",
        "aspect_ratio": "16:9",
        "prompt": "Digital manga style illustration, 16:9 aspect ratio, clean lines, vibrant colors. Four book covers displayed side by side, all sharing the same font style, layout structure, and a common logo band at the top. Each cover has a different background color: red, blue, green, and purple. Visual emphasis on design consistency with dotted lines connecting the shared elements. Clean white background. No text on covers.",
    },
    {
        "filename": "2026-04-23_eyecatch.png",
        "aspect_ratio": "16:9",
        "prompt": "Digital manga style illustration, 16:9 aspect ratio, vibrant colors, clean lines. A young Japanese freelancer doing a fist pump of joy while holding a smartphone. The smartphone screen shows a skill marketplace with star ratings and sold badges glowing. Laptop on a desk in the background showing sales notifications. Bright, energetic, success atmosphere. No text.",
    },
    {
        "filename": "2026-04-23_img01.png",
        "aspect_ratio": "16:9",
        "prompt": "Digital manga style illustration, 16:9 aspect ratio, clean lines, vibrant colors. Three key success elements displayed vertically with icons. Top: a detailed profile card with a photo and portfolio images. Middle: a service description document with checkmarks and bullet points. Bottom: a price tag with a coin and a beginner-friendly badge. Each element connected by arrows flowing downward. Clean bright background. No text.",
    },
    {
        "filename": "2026-04-23_img02.png",
        "aspect_ratio": "16:9",
        "prompt": "Digital manga style illustration, 16:9 aspect ratio, clean lines, vibrant colors. Before/After split screen. Left (Before): a blank profile page, a vague service card, an expensive price tag, a sad Japanese freelancer with zero notifications, gray tones. Right (After): a rich profile with portfolio, a detailed service description, a reasonable price tag, the same freelancer smiling with notification bells ringing, warm bright tones. Arrow from left to right. No text.",
    },
    {
        "filename": "2026-04-24_eyecatch.png",
        "aspect_ratio": "16:9",
        "prompt": "Digital manga style illustration, 16:9 aspect ratio, vibrant colors, clean lines. Before/After split scene. Left: a stressed Japanese office worker clutching their head in front of a mountain of receipts, invoices, and a calculator, dark stressed atmosphere. Right: the same worker calmly using accounting software on a laptop with an organized desk, smiling confidently, bright warm atmosphere. No text.",
    },
    {
        "filename": "2026-04-24_img01.png",
        "aspect_ratio": "16:9",
        "prompt": "Digital manga style illustration, 16:9 aspect ratio, clean lines, vibrant colors. Three solution steps displayed horizontally. Step 1: a laptop icon with an accounting software interface and sync arrows connecting to a bank icon. Step 2: a calendar page with the last day highlighted and a small clock showing 30 minutes. Step 3: a dedicated credit card and bank passbook separated from personal items by a dividing line. Connected by forward arrows. Clean white background. No text except the numbers 1, 2, 3.",
    },
    {
        "filename": "2026-04-24_img02.png",
        "aspect_ratio": "4:3",
        "prompt": "Digital manga style illustration, 4:3 aspect ratio, clean lines, vibrant colors. A visual bar chart comparison. Left: a tall red bar representing 15 hours with a tired character icon on top, labeled Year 1 visually. Right: a short blue bar representing 3 hours with a happy character icon on top, labeled Year 3 visually. A dramatic downward arrow between them showing the reduction. Simple clean background. No text labels, convey meaning through visual size contrast only.",
    },
    {
        "filename": "2026-04-25_eyecatch.png",
        "aspect_ratio": "16:9",
        "prompt": "Digital manga style illustration, 16:9 aspect ratio, vibrant colors, clean lines. A smartphone held by a Japanese person's hand on the left and a laptop on the right, facing each other. A glowing 4-digit number code floating between them as a bridge. Text snippets and URL link icons flying bidirectionally between the two devices along the bridge. Modern tech atmosphere with blue and purple glow effects. No readable text.",
    },
    {
        "filename": "2026-04-25_img01.png",
        "aspect_ratio": "16:9",
        "prompt": "Digital manga style illustration, 16:9 aspect ratio, clean lines, vibrant colors. A three-step flow diagram. Step 1: a laptop screen displaying a QR code and a 4-digit room code. Step 2: a smartphone camera scanning the QR code. Step 3: both devices showing the same content with sync arrows between them. Connected by numbered arrows (1, 2, 3). Simple clean background with soft blue tones. No text except the numbers 1, 2, 3.",
    },
    {
        "filename": "2026-04-25_img02.png",
        "aspect_ratio": "16:9",
        "prompt": "Digital manga style illustration, 16:9 aspect ratio, vibrant colors, clean lines. Two-panel manga layout. Panel 1: a young Japanese person on a train looking at a smartphone with an interested expression, discovering an article. Panel 2: the same person at home, sitting at a desk, the laptop screen already showing the same article page. A small clipboard share icon connecting the two panels. Warm everyday life atmosphere. No text.",
    },
    {
        "filename": "2026-04-27_eyecatch.png",
        "aspect_ratio": "16:9",
        "prompt": "Digital manga style illustration, 16:9 aspect ratio, vibrant colors, clean lines. A Japanese creator sitting at a desk looking amazed and delighted. On the laptop screen, a prompt input field is visible. From the screen, various styled images are magically flying out: a photo-realistic image, a cartoon illustration, a watercolor painting, a minimalist graphic. Sparkle and magic particle effects around the images. Creative energetic atmosphere. No text.",
    },
    {
        "filename": "2026-04-27_img01.png",
        "aspect_ratio": "16:9",
        "prompt": "Digital manga style illustration, 16:9 aspect ratio, clean lines, slightly muted colors. Multiple browser windows overlapping, each showing a different blog or website, but all using the exact same stock photo as their header image. A Japanese blogger looking at these with a disappointed, unimpressed expression. Repetitive and boring visual atmosphere. No text.",
    },
    {
        "filename": "2026-04-27_img02.png",
        "aspect_ratio": "16:9",
        "prompt": "Digital manga style illustration, 16:9 aspect ratio, vibrant colors, clean lines. Before/After split screen. Left: a frustrated Japanese person with multiple browser tabs open showing stock photo sites, searching endlessly, a clock showing 40 minutes, tired expression, gray-ish tones. Right: the same person typing a single prompt into an AI tool, a beautiful generated image appearing instantly, a clock showing 30 seconds, happy expression, bright warm tones. Dramatic contrast. No text.",
    },
    {
        "filename": "2026-04-27_img03.png",
        "aspect_ratio": "4:3",
        "prompt": "Digital manga style illustration, 4:3 aspect ratio, clean lines, vibrant colors. Three prompt technique tips visualized as cards. Card 1 (Be specific): a detailed cityscape icon with multiple descriptive arrows pointing to elements. Card 2 (Style selection): three small sample images in different styles - photorealistic, illustration, watercolor. Card 3 (Exclude unwanted): icons of text and logos with red X marks over them. Clean organized layout with a bright background. No readable text.",
    },
]

def generate_image(img_info, retry=3):
    filepath = os.path.join(OUTPUT_DIR, img_info["filename"])
    aspect_ratio = img_info["aspect_ratio"]
    prompt = img_info["prompt"]

    for attempt in range(retry):
        try:
            print(f"  Generating: {img_info['filename']} (attempt {attempt+1})", flush=True)
            response = client.models.generate_content(
                model="gemini-3.1-flash-image-preview",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
                ),
            )
            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    with open(filepath, "wb") as f:
                        f.write(part.inline_data.data)
                    print(f"  -> Saved: {filepath}", flush=True)
                    return True
            print(f"  -> No image data in response (attempt {attempt+1})", flush=True)
        except Exception as e:
            print(f"  -> Error (attempt {attempt+1}): {e}", flush=True)
            if attempt < retry - 1:
                time.sleep(5)
    return False

success_count = 0
fail_count = 0
failed_files = []

for i, img_info in enumerate(IMAGES):
    print(f"\n[{i+1}/{len(IMAGES)}] {img_info['filename']}", flush=True)
    result = generate_image(img_info)
    if result:
        success_count += 1
    else:
        fail_count += 1
        failed_files.append(img_info["filename"])

    if i < len(IMAGES) - 1:
        time.sleep(4)

print(f"\n===== 完了 =====")
print(f"成功: {success_count} 枚")
print(f"失敗: {fail_count} 枚")
if failed_files:
    print("失敗ファイル:")
    for f in failed_files:
        print(f"  - {f}")

print("\n===== 生成済みファイル =====")
for fname in sorted(os.listdir(OUTPUT_DIR)):
    if fname.endswith(".png"):
        fpath = os.path.join(OUTPUT_DIR, fname)
        size_kb = os.path.getsize(fpath) // 1024
        print(f"  {fname} ({size_kb} KB)")

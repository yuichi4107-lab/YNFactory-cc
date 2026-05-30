"""Generate p045 with vertical narration instruction for gpt-image-2."""
import os, json, base64, datetime, re
from openai import OpenAI

PAGE = os.environ.get("PAGE", "45")
PROJECT_ROOT = r"G:/マイドライブ/YNFactory-cc"
CHAR_DIR = os.path.join(PROJECT_ROOT, ".company", "outputs", "ebooks-manga",
                        "manga-career-restart", "manuscript", "characters")
PROMPTS_JSON = os.path.join(PROJECT_ROOT, ".company", "outputs",
                            "openai-image-gen", "vol1-sample", "prompts.json")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, ".company", "outputs",
                          "openai-image-gen", "vol1-sample", "v2")

with open(PROMPTS_JSON, encoding="utf-8") as f:
    all_prompts = json.load(f)
entry = all_prompts[PAGE]
base_prompt = entry["prompt"]

# 縦書き指示を最優先ブロックに追加
VERTICAL_RULE = (
    "◆【絶対最優先・テキスト方向】セリフ吹き出し・ナレーション四角枠内の日本語テキストは"
    "すべて日本のマンガ伝統の縦書き（top-to-bottom, right-to-left）で描画してください。"
    "横書き（left-to-right）は禁止です。1行が長い場合は複数列に分けて縦書きで組んでください。\n"
)
# 先頭の「◆【注意】」の直後に挿入
new_prompt = base_prompt.replace(
    "◆【注意】",
    VERTICAL_RULE + "◆【注意】"
)

refs = list(dict.fromkeys(re.findall(r"添付の([^\s、,]+?\.png)", new_prompt)))
ref_paths = [os.path.join(CHAR_DIR, n) for n in refs if os.path.exists(os.path.join(CHAR_DIR, n))]
print(f"Page {PAGE} with VERTICAL rule: {len(ref_paths)} refs")

os.makedirs(OUTPUT_DIR, exist_ok=True)
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
files = [open(p, "rb") for p in ref_paths]
try:
    result = client.images.edit(
        model="gpt-image-2",
        image=files[0] if len(files) == 1 else files,
        prompt=new_prompt,
        size="1024x1536",
        quality="high",
        n=1,
    )
finally:
    for f in files: f.close()

ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
out = os.path.join(OUTPUT_DIR, f"p{int(PAGE):03d}_vertical_{ts}.png")
with open(out, "wb") as f:
    f.write(base64.b64decode(result.data[0].b64_json))
print(f"OK: {out}")

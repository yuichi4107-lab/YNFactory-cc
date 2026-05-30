"""Generate p045 with narration-overlay instruction to avoid text occupying half panel."""
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

# セリフのみ縦書き + ナレーション枠は横書きOK + オーバーレイ配置ルール
EXTRA_RULES = (
    "◆【絶対最優先・セリフ方向】セリフ吹き出し内の日本語テキストは日本のマンガ伝統の"
    "縦書き（top-to-bottom, right-to-left）で描画してください。横書きは禁止です。\n"
    "◆【ナレーション方向】ナレーション四角枠内のテキストは横書き（left-to-right）で描画してください。"
    "長文の場合は複数行で自然に折り返してください。\n"
    "◆【絶対最優先・ナレーション枠配置】ナレーション四角枠は画像の上にオーバーレイして配置し、"
    "コマ領域を画像部分とテキスト部分に分割しないでください。画像（キャラや背景）はコマ全体に"
    "広がるように描画し、ナレーション枠はその上に白背景の小さな長方形として重ね、"
    "コマ幅の最大40%・コマ高の最大50%以内に収めてください。ナレーション枠のために画像領域を"
    "狭めることは禁止です。\n"
)
new_prompt = base_prompt.replace("◆【注意】", EXTRA_RULES + "◆【注意】")

refs = list(dict.fromkeys(re.findall(r"添付の([^\s、,]+?\.png)", new_prompt)))
ref_paths = [os.path.join(CHAR_DIR, n) for n in refs if os.path.exists(os.path.join(CHAR_DIR, n))]
print(f"Page {PAGE} with VERTICAL+OVERLAY rules: {len(ref_paths)} refs")

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
out = os.path.join(OUTPUT_DIR, f"p{int(PAGE):03d}_overlay_{ts}.png")
with open(out, "wb") as f:
    f.write(base64.b64decode(result.data[0].b64_json))
print(f"OK: {out}")

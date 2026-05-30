"""Generate one manga panel via openai-image-gen for vol1-sample test."""
import os
import sys
import json
import base64
import datetime
import re
from openai import OpenAI

PAGE = os.environ["PAGE"]
QUALITY = os.environ.get("QUALITY", "medium")
PROJECT_ROOT = r"G:/マイドライブ/YNFactory-cc"
CHAR_DIR = os.path.join(
    PROJECT_ROOT,
    ".company", "outputs", "ebooks-manga", "manga-career-restart",
    "manuscript", "characters",
)
PROMPTS_JSON = os.path.join(
    PROJECT_ROOT,
    ".company", "outputs", "openai-image-gen", "vol1-sample", "prompts.json",
)
OUTPUT_DIR = os.path.join(
    PROJECT_ROOT,
    ".company", "outputs", "openai-image-gen", "vol1-sample",
)

with open(PROMPTS_JSON, encoding="utf-8") as f:
    all_prompts = json.load(f)
entry = all_prompts[PAGE]
PROMPT = entry["prompt"]

# Find referenced character PNGs by scanning "添付のXXX.png" pattern
refs = re.findall(r"添付の([^\s、,]+?\.png)", PROMPT)
refs = list(dict.fromkeys(refs))  # dedupe preserving order
ref_paths = []
for name in refs:
    p = os.path.join(CHAR_DIR, name)
    if os.path.exists(p):
        ref_paths.append(p)
    else:
        print(f"WARN: reference not found, skipping: {name}")

print(f"Page {PAGE} ({entry['template']}): {len(ref_paths)} refs → {[os.path.basename(r) for r in ref_paths]}")

os.makedirs(OUTPUT_DIR, exist_ok=True)
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

image_files = [open(p, "rb") for p in ref_paths]
try:
    result = client.images.edit(
        model="chatgpt-image-latest",
        image=image_files[0] if len(image_files) == 1 else image_files,
        prompt=PROMPT,
        size="1024x1536",
        quality=QUALITY,
        n=1,
    )
finally:
    for f in image_files:
        f.close()

ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
item = result.data[0]
b64 = item.b64_json
out_path = os.path.join(OUTPUT_DIR, f"p{int(PAGE):03d}_{ts}.png")
with open(out_path, "wb") as f:
    f.write(base64.b64decode(b64))
print(f"OK: {out_path}")

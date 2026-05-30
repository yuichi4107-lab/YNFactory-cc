import os, sys, base64, datetime
from openai import OpenAI

# args: prompt_file, out_dir, filename_prefix, size, quality
prompt_file = sys.argv[1]
out_dir = sys.argv[2]
prefix = sys.argv[3]
size = sys.argv[4]
quality = sys.argv[5]

with open(prompt_file, "r", encoding="utf-8") as f:
    prompt = f.read()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
try:
    r = client.images.generate(model="gpt-image-2", prompt=prompt, size=size, quality=quality, n=1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
os.makedirs(out_dir, exist_ok=True)
for item in r.data or []:
    b64 = getattr(item, "b64_json", None)
    if not b64:
        continue
    fp = os.path.join(out_dir, f"{prefix}_{ts}.png")
    with open(fp, "wb") as f:
        f.write(base64.b64decode(b64))
    print(f"OK: {fp}")

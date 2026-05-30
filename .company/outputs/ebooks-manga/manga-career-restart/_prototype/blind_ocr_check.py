"""Blind OCR: ask Gemini to read text WITHOUT showing expected text (no priming)."""
import os, sys, json, argparse
sys.stdout.reconfigure(encoding='utf-8')
from google import genai
from google.genai import types

API_KEY = os.environ.get("GOOGLE_AI_STUDIO_API_KEY") or os.environ.get("GEMINI_API_KEY")

BLIND_PROMPT = """添付のマンガ画像を見て、下記の要素を画像に描かれている通り正確に読み取ってください。
推測や補完は一切せず、画像に実際に見える文字列だけを返してください。読めない崩し字は "[読めない]" と書いてください。

対象:
- 吹き出し(楕円・雲形)内の文字
- ナレーションボックス(四角枠)内の文字

対象外(無視):
- オノマトペ・擬音
- 背景の看板・ポスター
- 小物のUI(スマホ画面・PC画面・本の表紙等)
- 服のロゴ

出力形式: JSONのみ。説明文禁止。
{
  "bubbles": [
    {"panel_id": int, "type": "dialogue"|"narration", "detected_text": str}
  ]
}"""


def blind_read(client, image_path, model="gemini-2.5-flash"):
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    response = client.models.generate_content(
        model=model,
        contents=[BLIND_PROMPT, types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")],
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.0),
    )
    return json.loads(response.text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    args = ap.parse_args()
    client = genai.Client(api_key=API_KEY)
    result = blind_read(client, args.image)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

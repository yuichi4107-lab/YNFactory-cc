"""
Prototype: Gemini Vision as judge for dialogue accuracy check.

Input : manga page image + expected dialogue list (from CSV)
Output: structured verdict per-bubble (PASS/FAIL + specific mismatches)

This is the core of the improved QC loop. Verdict is used to:
- Accept page if all bubbles PASS
- Regenerate with targeted feedback if any FAIL
"""
import os
import sys
import json
import argparse

sys.stdout.reconfigure(encoding='utf-8')

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("ERROR: google-genai not installed")
    sys.exit(1)

API_KEY = os.environ.get("GOOGLE_AI_STUDIO_API_KEY") or os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("ERROR: set GOOGLE_AI_STUDIO_API_KEY or GEMINI_API_KEY")
    sys.exit(1)


JUDGE_PROMPT_TEMPLATE = """あなたはマンガのセリフ校正を行う専門エディタです。
添付のマンガ画像に含まれる「セリフ(吹き出し内の文字)」と「ナレーション(四角枠内の文字)」を読み取り、
下記の期待されるテキストと **一字一句一致しているか** を判定してください。

【判定対象】
- 吹き出し(楕円・雲形)の中のセリフ
- ナレーションボックス(四角枠)の中の文章

【判定対象外(無視する)】
- オノマトペ・擬音(「ドンッ」「キラキラ」等)
- 背景の看板・ポスター・標識に描かれた文字
- 小物のUI・ラベル(スマホ画面、本の表紙、ノートPC画面、商品パッケージ等)
- キャラクターの服の文字・ロゴ
- これらは extra_text_found に入れない

【判定ルール】
- 句読点(、。…)の有無も含めて厳密に比較する
- 吹き出しの字形の違い(崩し・フォント差)は無視し、文字としての正誤のみ判定
- 画像の文字が崩れて読めない場合は "unreadable" として指摘
- **吹き出し/ナレーションボックス内**に期待リストに無いテキストがあれば extra_text_found に列挙

【期待されるセリフ・ナレーション】
{expected_json}

【出力フォーマット】
必ず下記JSONのみを出力してください。説明文・マークダウンは一切禁止。

{{
  "overall_verdict": "PASS" | "FAIL",
  "bubbles": [
    {{
      "panel_id": <int>,
      "expected": "<期待テキスト>",
      "detected": "<画像から読み取ったテキスト or 'missing' or 'unreadable'>",
      "match": true | false,
      "issue": "<不一致の内容。一致なら空文字>"
    }}
  ],
  "extra_text_found": ["<期待リストに無いが画像に描かれていたテキスト>", ...],
  "summary": "<全体所見を1-2文で>"
}}
"""


def build_judge_prompt(expected_items):
    """expected_items: list of {panel_id, type: 'dialogue'|'narration', speaker, text}"""
    expected_json = json.dumps(expected_items, ensure_ascii=False, indent=2)
    return JUDGE_PROMPT_TEMPLATE.format(expected_json=expected_json)


def judge_page(image_path, expected_items, model="gemini-2.5-flash"):
    client = genai.Client(api_key=API_KEY)
    with open(image_path, "rb") as f:
        img_bytes = f.read()

    prompt = build_judge_prompt(expected_items)
    response = client.models.generate_content(
        model=model,
        contents=[
            prompt,
            types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.0,
        ),
    )
    raw = response.text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # sometimes wrapped in markdown fence
        cleaned = raw.strip("`").lstrip("json").strip()
        return json.loads(cleaned)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--expected", required=True, help="JSON file with expected items")
    ap.add_argument("--model", default="gemini-2.5-flash")
    args = ap.parse_args()

    with open(args.expected, encoding="utf-8") as f:
        expected_items = json.load(f)

    print(f"Judging: {args.image}")
    print(f"Expected items: {len(expected_items)}")
    verdict = judge_page(args.image, expected_items, model=args.model)
    print(json.dumps(verdict, ensure_ascii=False, indent=2))

    if verdict.get("overall_verdict") == "PASS":
        print("\n==> PASS (all bubbles match)")
        sys.exit(0)
    else:
        print("\n==> FAIL")
        for b in verdict.get("bubbles", []):
            if not b.get("match"):
                print(f"  Panel {b.get('panel_id')}: expected='{b.get('expected')}' "
                      f"detected='{b.get('detected')}' issue={b.get('issue')}")
        for extra in verdict.get("extra_text_found", []) or []:
            print(f"  EXTRA: {extra}")
        sys.exit(1)


if __name__ == "__main__":
    main()

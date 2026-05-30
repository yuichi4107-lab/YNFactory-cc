"""
E2E prototype: generate -> VLM judge -> inject feedback -> regenerate (loop).

Demonstrates that the QC+regen loop actually CONVERGES by feeding specific
mismatch info from the judge back into the next generation prompt.

Usage:
    python e2e_loop.py --page 5 --max-iter 3
"""
import os
import sys
import json
import io
import time
import datetime
import argparse

sys.stdout.reconfigure(encoding='utf-8')

from google import genai
from google.genai import types
from PIL import Image

API_KEY = os.environ.get("GOOGLE_AI_STUDIO_API_KEY") or os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("ERROR: API key not set")
    sys.exit(1)

ROOT = r"G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart"
CHAR_DIR = os.path.join(ROOT, "manuscript", "characters")
OUT_DIR = os.path.join(ROOT, "_prototype", "e2e_run")
os.makedirs(OUT_DIR, exist_ok=True)

# ==== Fixed inputs for page 5 (template 6) ====
BASE_PROMPT = """◆【注意】【】で囲まれた単語は感情や状況の指示であり、画像内に文字として描画しないでください
◆【絶対最優先】必ずフルカラーにしてください
◆【絶対最優先】必ず日本のアニメ・マンガ調のイラストで描いてください。実写風・フォトリアル風は禁止です。
◆【絶対最優先】キャラクター外見: ミサキは添付のミサキ.pngと100%同一の外見で描画
◆【絶対最優先】キャラクター外見: ケンタは添付のケンタ.pngと100%同一の外見で描画
◆【出力サイズ】9:16
◆【補足情報】上下左右に50ピクセルの余白を設けてください
◆【補足情報】服装: ミサキ: ボーダー柄(白と紺)のカットソーにデニムパンツ、白いスニーカー
◆【補足情報】服装: ケンタ: グレーのTシャツにネイビーのスウェットパンツ
◆【コマ構成】テンプレ6: 上1コマ+下左右2コマ
◆【作画】ジャンル: 副業に最適化した統一スタイル / 作画スタイル: 親しみやすく実践的,現代的なライフスタイル表現 / 色調: 明るく前向きな色調,オレンジ・青・黄色基調,活力ある配色 / 線画: 親しみやすい柔らかな線,カジュアルで読みやすい表現 / 演出: 必要に応じて集中線,効果線,擬音などのマンガらしい演出
◆【ストーリー】
1コマ目 (上): ミサキがケンタに話しかける。期待に満ちた笑顔。 セリフ: ［ミサキ］の吹き出しに「…ねえ、子供ができたら、名前は何がいいかな」 ナレーション: なし オノマトペ: なし
2コマ目 (下左): ケンタがコーヒーカップを持ちながら笑う。 セリフ: ［ケンタ］の吹き出しに「気が早いって」 ナレーション: なし オノマトペ: なし
3コマ目 (下右): ミサキがスマホを取り出して名前辞典のサイトを開いている。楽しそうな表情。 セリフ: ［ミサキ］の吹き出しに「でも考えるの楽しいじゃん」 ナレーション: ［四角枠］ケンタは笑いながらコーヒーを啜った。ミサキはスマホを取り出して、名前辞典のサイトを開く。 オノマトペ: なし"""

EXPECTED = [
    {"panel_id": 1, "type": "dialogue", "speaker": "ミサキ",
     "text": "…ねえ、子供ができたら、名前は何がいいかな"},
    {"panel_id": 2, "type": "dialogue", "speaker": "ケンタ",
     "text": "気が早いって"},
    {"panel_id": 3, "type": "dialogue", "speaker": "ミサキ",
     "text": "でも考えるの楽しいじゃん"},
    {"panel_id": 3, "type": "narration", "speaker": None,
     "text": "ケンタは笑いながらコーヒーを啜った。ミサキはスマホを取り出して、名前辞典のサイトを開く。"},
]

JUDGE_PROMPT = """あなたはマンガのセリフ校正を行う専門エディタです。
添付画像の「吹き出し内のセリフ」「ナレーションボックス内の文章」を読み取り、
下記の期待テキストと一字一句一致しているか判定してください。

【判定対象外(無視)】
- オノマトペ・擬音
- 背景の看板・ポスター・標識
- 小物のUI・ラベル(スマホ画面・ノートPC画面・本の表紙・商品パッケージ等)
- キャラクターの服のロゴ

【期待テキスト】
{expected_json}

【出力】下記JSONのみ。説明文は禁止。
{{
  "overall_verdict": "PASS" | "FAIL",
  "bubbles": [
    {{"panel_id": int, "expected": str, "detected": str, "match": bool, "issue": str}}
  ],
  "extra_text_found": [str],
  "summary": str
}}"""


def load_char_ref(name):
    with open(os.path.join(CHAR_DIR, name), "rb") as f:
        return types.Part.from_bytes(data=f.read(), mime_type="image/png")


def generate_image(client, prompt_text, char_refs, out_path):
    contents = [prompt_text] + char_refs
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="9:16"),
        ),
    )
    if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data is not None:
                img = Image.open(io.BytesIO(part.inline_data.data)).convert("RGB")
                img.save(out_path, "JPEG", quality=92)
                return True
    return False


def judge_image(client, image_path, expected):
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    prompt = JUDGE_PROMPT.format(expected_json=json.dumps(expected, ensure_ascii=False, indent=2))
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")],
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.0),
    )
    return json.loads(response.text)


def build_feedback_prompt(base_prompt, verdict):
    """Inject specific mismatch info into the next-iteration prompt."""
    failed = [b for b in verdict.get("bubbles", []) if not b.get("match")]
    if not failed:
        return base_prompt
    lines = ["", "◆【前回の失敗・絶対に修正すること】前回生成では以下のセリフが誤って描画されました。今回は下記のとおり一字一句正確に描くこと:"]
    for b in failed:
        lines.append(
            f"- パネル{b.get('panel_id')}: 正しいテキスト「{b.get('expected')}」。"
            f"前回は「{b.get('detected')}」と誤描画。絶対に同じ誤りを繰り返さないこと。"
        )
    return base_prompt + "\n" + "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-iter", type=int, default=3)
    args = ap.parse_args()

    client = genai.Client(api_key=API_KEY)
    char_refs = [load_char_ref("ミサキ.png"), load_char_ref("ケンタ.png")]

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log = {"run_id": ts, "iterations": []}
    current_prompt = BASE_PROMPT

    for i in range(1, args.max_iter + 1):
        print(f"\n===== Iteration {i} =====")
        img_path = os.path.join(OUT_DIR, f"iter_{i}_{ts}.jpg")

        print(f"[gen] generating image...")
        t0 = time.time()
        ok = generate_image(client, current_prompt, char_refs, img_path)
        t_gen = time.time() - t0
        if not ok:
            print("[gen] FAILED to produce image")
            log["iterations"].append({"iter": i, "error": "no image"})
            break
        print(f"[gen] saved: {img_path} ({t_gen:.1f}s)")

        print(f"[judge] evaluating...")
        t0 = time.time()
        verdict = judge_image(client, img_path, EXPECTED)
        t_judge = time.time() - t0
        print(f"[judge] verdict={verdict.get('overall_verdict')} ({t_judge:.1f}s)")

        # log per-bubble
        for b in verdict.get("bubbles", []):
            mark = "OK" if b.get("match") else "NG"
            print(f"  [{mark}] panel{b.get('panel_id')}: expected={b.get('expected')[:30]}... "
                  f"detected={(b.get('detected') or '')[:30]}...")

        log["iterations"].append({
            "iter": i,
            "image": img_path,
            "gen_time": t_gen,
            "judge_time": t_judge,
            "verdict": verdict,
        })

        if verdict.get("overall_verdict") == "PASS":
            print(f"\n*** CONVERGED at iteration {i} ***")
            log["converged_at"] = i
            break
        else:
            print(f"\n[feedback] injecting failure info into next prompt...")
            current_prompt = build_feedback_prompt(BASE_PROMPT, verdict)
    else:
        print(f"\n*** FAILED to converge after {args.max_iter} iterations ***")
        log["converged_at"] = None

    log_path = os.path.join(OUT_DIR, f"run_{ts}.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    print(f"\nLog saved: {log_path}")


if __name__ == "__main__":
    main()

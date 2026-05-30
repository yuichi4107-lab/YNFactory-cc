"""E2E loop test on page 39 (high-density text, known-hard)."""
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
ROOT = r"G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart"
CHAR_DIR = os.path.join(ROOT, "manuscript", "characters")
OUT_DIR = os.path.join(ROOT, "_prototype", "e2e_run")
os.makedirs(OUT_DIR, exist_ok=True)

BASE_PROMPT = """◆【注意】【】で囲まれた単語は感情や状況の指示であり、画像内に文字として描画しないでください
◆【絶対最優先】必ずフルカラーにしてください
◆【絶対最優先】必ず日本のアニメ・マンガ調のイラストで描いてください。実写風・フォトリアル風は禁止です。
◆【絶対最優先】キャラクター外見: ミサキは添付のミサキ.pngと100%同一の外見で描画
◆【絶対最優先】キャラクター外見: 山田課長は添付の山田課長.pngと100%同一の外見で描画
◆【出力サイズ】9:16
◆【補足情報】上下左右に50ピクセルの余白を設けてください
◆【補足情報】服装: ミサキ: ボーダー柄(白と紺)のカットソーにデニムパンツ、白いスニーカー
◆【補足情報】服装: 山田課長: 紺のスーツに白シャツ
◆【コマ構成】テンプレ5: 上中下3段
◆【作画】ジャンル: 副業に最適化した統一スタイル / 作画スタイル: 親しみやすく実践的,現代的なライフスタイル表現 / 色調: 明るく前向きな色調,オレンジ・青・黄色基調,活力ある配色 / 線画: 親しみやすい柔らかな線,カジュアルで読みやすい表現 / 演出: 必要に応じて集中線,効果線,擬音などのマンガらしい演出
◆【ストーリー】
1コマ目 (上段): 翌日。ミサキが自宅でスマホを耳に当てて電話している。緊張した表情。 セリフ: ［ミサキ］の吹き出しに「あの、保育園が決まらなくて…。在宅勤務の制度はありますか？」 ナレーション: ［四角枠］翌日、ミサキは会社に電話をかけた。電話口の沈黙が、長く感じた。 オノマトペ: なし
2コマ目 (中段): 電話の向こう側（イメージ）。山田課長がオフィスで電話している。申し訳なさそうな表情。 セリフ: ［山田課長（電話越し）］の吹き出しに「佐藤さん、うちはまだリモートワーク対応していなくてね。コロナのときは一時的にやったんだけど、今は原則出社に戻ってるんだよ」 ナレーション: ［四角枠］山田課長の声は穏やかだったが、答えは明確だった。 オノマトペ: なし
3コマ目 (下段): ミサキが電話を切った後、スマホを握りしめたまま動けない。 セリフ: ［山田課長（電話越し・回想）］の吹き出しに「制度としてはないんだ。申し訳ないけど」 ナレーション: ［四角枠］電話を切った後、しばらくスマホを握りしめたまま動けなかった。 オノマトペ: なし"""

EXPECTED = [
    {"panel_id": 1, "type": "dialogue", "speaker": "ミサキ",
     "text": "あの、保育園が決まらなくて…。在宅勤務の制度はありますか？"},
    {"panel_id": 1, "type": "narration", "speaker": None,
     "text": "翌日、ミサキは会社に電話をかけた。電話口の沈黙が、長く感じた。"},
    {"panel_id": 2, "type": "dialogue", "speaker": "山田課長",
     "text": "佐藤さん、うちはまだリモートワーク対応していなくてね。コロナのときは一時的にやったんだけど、今は原則出社に戻ってるんだよ"},
    {"panel_id": 2, "type": "narration", "speaker": None,
     "text": "山田課長の声は穏やかだったが、答えは明確だった。"},
    {"panel_id": 3, "type": "dialogue", "speaker": "山田課長",
     "text": "制度としてはないんだ。申し訳ないけど"},
    {"panel_id": 3, "type": "narration", "speaker": None,
     "text": "電話を切った後、しばらくスマホを握りしめたまま動けなかった。"},
]

JUDGE_PROMPT = """あなたはマンガのセリフ校正を行う専門エディタです。
添付画像の「吹き出し内のセリフ」「ナレーションボックス内の文章」を読み取り、
下記の期待テキストと一字一句一致しているか判定してください。

【判定対象外(無視)】
- オノマトペ・擬音
- 背景の看板・ポスター・標識・ロゴ
- 小物のUI・ラベル(スマホ画面・PC画面・本の表紙等)

【判定ルール】
- 句読点(、。…「」？)の有無も厳密に比較
- 字形の違い(フォント差・崩し)は無視し、文字としての正誤のみ判定
- 期待テキストの語が1つでも欠けたり別の語に置き換わっていたら match=false

【期待テキスト】
{expected_json}

【出力】下記JSONのみ。説明文・マークダウンは禁止。
{{
  "overall_verdict": "PASS" | "FAIL",
  "bubbles": [
    {{"panel_id": int, "type": "dialogue"|"narration", "expected": str, "detected": str, "match": bool, "issue": str}}
  ],
  "extra_text_found": [str],
  "summary": str
}}"""


def load_char_ref(name):
    with open(os.path.join(CHAR_DIR, name), "rb") as f:
        return types.Part.from_bytes(data=f.read(), mime_type="image/png")


def generate_image(client, prompt_text, char_refs, out_path):
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[prompt_text] + char_refs,
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
    failed = [b for b in verdict.get("bubbles", []) if not b.get("match")]
    if not failed:
        return base_prompt
    lines = ["", "◆【前回失敗・最重要】前回生成では以下の誤りが発生しました。今回は一字一句正確に描くこと:"]
    for b in failed:
        kind = "セリフ" if b.get("type") == "dialogue" else "ナレーション"
        lines.append(
            f"- パネル{b.get('panel_id')}の{kind}: "
            f"正「{b.get('expected')}」 ⇔ 前回誤「{b.get('detected')}」。"
            f"同じ誤りを絶対に繰り返さないこと。"
        )
    return base_prompt + "\n" + "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-iter", type=int, default=3)
    args = ap.parse_args()

    client = genai.Client(api_key=API_KEY)
    char_refs = [load_char_ref("ミサキ.png"), load_char_ref("山田課長.png")]

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log = {"run_id": ts, "page": 39, "iterations": []}
    current_prompt = BASE_PROMPT

    converged = False
    for i in range(1, args.max_iter + 1):
        print(f"\n===== Iteration {i} =====")
        img_path = os.path.join(OUT_DIR, f"p39_iter_{i}_{ts}.jpg")

        t0 = time.time()
        ok = generate_image(client, current_prompt, char_refs, img_path)
        t_gen = time.time() - t0
        if not ok:
            print("[gen] FAILED")
            break
        print(f"[gen] {img_path} ({t_gen:.1f}s)")

        t0 = time.time()
        verdict = judge_image(client, img_path, EXPECTED)
        t_judge = time.time() - t0
        print(f"[judge] verdict={verdict.get('overall_verdict')} ({t_judge:.1f}s)")
        for b in verdict.get("bubbles", []):
            mark = "OK" if b.get("match") else "NG"
            print(f"  [{mark}] p{b.get('panel_id')}/{b.get('type','?')}: "
                  f"exp={b.get('expected','')[:40]}")
            if not b.get("match"):
                print(f"         det={(b.get('detected') or '')[:60]}")
                print(f"         issue={(b.get('issue') or '')[:80]}")

        log["iterations"].append({
            "iter": i, "image": img_path, "gen_time": t_gen, "judge_time": t_judge,
            "verdict": verdict,
        })

        if verdict.get("overall_verdict") == "PASS":
            print(f"\n*** CONVERGED at iteration {i} ***")
            log["converged_at"] = i
            converged = True
            break
        else:
            print(f"\n[feedback] injecting failure info into next prompt")
            current_prompt = build_feedback_prompt(BASE_PROMPT, verdict)

    if not converged:
        print(f"\n*** Did not converge in {args.max_iter} iterations ***")
        log["converged_at"] = None

    log_path = os.path.join(OUT_DIR, f"p39_run_{ts}.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    print(f"\nLog: {log_path}")


if __name__ == "__main__":
    main()

"""
Hybrid A+B prototype:
  A) Blind-OCR judge + programmatic comparison (no confirmation bias)
  B) After N failed regen attempts, fall back to Pillow text compositing
     which guarantees 100% accurate Japanese text.

Pipeline per page:
  iter 1..N:
    generate image (with dialogue embedded in prompt)
    blind-OCR image (expected text NOT shown to the model)
    compare detected vs expected programmatically
    if PASS -> done (use this image)
    if FAIL -> build feedback, retry
  if not converged after N:
    regenerate clean (no text / no bubbles) image
    Pillow-composite bubbles and narration with exact expected text
    -> guaranteed PASS
"""
import os
import sys
import json
import io
import time
import datetime
import argparse
import re
import unicodedata

sys.stdout.reconfigure(encoding='utf-8')

from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont

API_KEY = os.environ.get("GOOGLE_AI_STUDIO_API_KEY") or os.environ.get("GEMINI_API_KEY")
ROOT = r"G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart"
CHAR_DIR = os.path.join(ROOT, "manuscript", "characters")
OUT_DIR = os.path.join(ROOT, "_prototype", "hybrid_run")
os.makedirs(OUT_DIR, exist_ok=True)

FONT_BOLD = r"C:\Windows\Fonts\YuGothB.ttc"
FONT_REG = r"C:\Windows\Fonts\YuGothM.ttc"

# ==== Test target: page 39 (template 5, hard case) ====
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

CLEAN_PROMPT = """◆【絶対最優先】必ず日本のアニメ・マンガ調のイラストで描いてください。実写風・フォトリアル風は禁止です。
◆【絶対最優先】必ずフルカラーにしてください
◆【絶対最優先】キャラクター外見: ミサキは添付のミサキ.pngと100%同一の外見で描画
◆【絶対最優先】キャラクター外見: 山田課長は添付の山田課長.pngと100%同一の外見で描画

◆【最重要・テキスト除去】このページには一切のテキスト・文字・セリフ・吹き出し・ナレーションボックス・オノマトペを描かないでください。
- No text, no dialogue, no speech bubbles, no onomatopoeia, no narration boxes
- 吹き出しの枠も描かないでください(後処理で合成します)
- 擬音・効果音の文字も描かないでください
- コマ内はキャラクター・背景・小物のみで構成してください

◆【出力サイズ】9:16
◆【補足情報】服装: ミサキ: ボーダー柄(白と紺)のカットソーにデニムパンツ、白いスニーカー
◆【補足情報】服装: 山田課長: 紺のスーツに白シャツ

◆【コマ構成】テンプレ5: 縦に3段均等分割。上段・中段・下段それぞれ横長1コマ。コマ間は白い溝(ガター)。

◆【作画】ジャンル: 副業に最適化した統一スタイル / 色調: 明るく前向きな色調,オレンジ・青・黄色基調

◆【ストーリー・構図のみ】
1コマ目(上段・横長): 自宅。ミサキがスマホを耳に当てて緊張した表情で電話している。吹き出しは描かない。
2コマ目(中段・横長): オフィス。山田課長(40代男性・スーツ)が電話しながら申し訳なさそうな表情。吹き出しは描かない。
3コマ目(下段・横長): ミサキが電話を切った後、スマホを握りしめたまま動けず沈んだ表情。吹き出しは描かない。
"""

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

# Template 5 panel regions (3 equal horizontal rows)
PANEL_REGIONS_T5 = {
    1: (0.06, 0.04, 0.94, 0.33),
    2: (0.06, 0.36, 0.94, 0.65),
    3: (0.06, 0.68, 0.94, 0.96),
}

BLIND_OCR_PROMPT = """添付のマンガ画像を見て、下記の要素を画像に描かれている通り正確に読み取ってください。
推測や補完は一切せず、画像に実際に見える文字列だけを返してください。
読めない崩し字や意味不明な文字列も、見える通りに書いてください(勝手に正しい日本語に補正しない)。

対象:
- 吹き出し(楕円・雲形)内の文字 -> type="dialogue"
- ナレーションボックス(四角枠・角丸枠)内の文字 -> type="narration"

対象外(読み取らない):
- オノマトペ・擬音
- 背景の看板・ポスター・標識
- 小物のUI・ラベル(スマホ画面・PC画面・本の表紙・商品パッケージ等)
- 服のロゴ・ブランド表記

出力形式: JSONのみ。説明文・マークダウン禁止。読み取れたテキストは改行なしで1行に連結。
{
  "bubbles": [
    {"panel_id": int, "type": "dialogue"|"narration", "detected_text": str}
  ]
}"""


# ========== Helpers ==========

def load_char_ref(name):
    with open(os.path.join(CHAR_DIR, name), "rb") as f:
        return types.Part.from_bytes(data=f.read(), mime_type="image/png")


def normalize_text(s: str) -> str:
    """Normalize for comparison: strip, NFKC, remove whitespace/newlines."""
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"\s+", "", s)
    return s


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


def blind_ocr(client, image_path, retries=2):
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    last_err = None
    for attempt in range(retries + 1):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[BLIND_OCR_PROMPT, types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0,
                    max_output_tokens=4096,
                ),
            )
            raw = response.text or ""
            try:
                return json.loads(raw)
            except json.JSONDecodeError as je:
                # attempt minor repair: trim at last complete bubble entry
                m = re.search(r'(\{.*"bubbles"\s*:\s*\[.*?\])', raw, flags=re.DOTALL)
                if m:
                    try:
                        return json.loads(m.group(1) + "}")
                    except Exception:
                        pass
                last_err = je
        except Exception as e:
            last_err = e
        time.sleep(1)
    # graceful fallback: return empty bubbles so comparison will FAIL
    print(f"[ocr] WARN: OCR failed after retries: {last_err}")
    return {"bubbles": []}


def compare_texts(expected_items, ocr_bubbles):
    """Programmatic comparison. Returns verdict dict.
    Match strategy: find the OCR bubble with same panel_id and type,
    then compare normalized text exact.
    """
    results = []
    ocr_by_key = {}
    # allow multiple bubbles per (panel, type) — keep list
    for b in ocr_bubbles:
        key = (b.get("panel_id"), b.get("type"))
        ocr_by_key.setdefault(key, []).append(b.get("detected_text", ""))

    used = set()
    all_match = True
    for exp in expected_items:
        key = (exp["panel_id"], exp["type"])
        candidates = ocr_by_key.get(key, [])
        # find first unused match
        detected = ""
        match = False
        exp_norm = normalize_text(exp["text"])
        for idx, cand in enumerate(candidates):
            tag = (key, idx)
            if tag in used:
                continue
            detected = cand
            if normalize_text(cand) == exp_norm:
                match = True
                used.add(tag)
                break
        if not match and candidates:
            # take first candidate as best-effort detected
            detected = candidates[0]
        if not match:
            all_match = False
        results.append({
            "panel_id": exp["panel_id"],
            "type": exp["type"],
            "expected": exp["text"],
            "detected": detected,
            "match": match,
        })
    return {
        "overall_verdict": "PASS" if all_match else "FAIL",
        "bubbles": results,
    }


def build_feedback_prompt(base_prompt, verdict):
    failed = [b for b in verdict["bubbles"] if not b["match"]]
    if not failed:
        return base_prompt
    lines = ["", "◆【前回失敗・最重要】前回生成では以下が正しく描画されませんでした。今回は一字一句正確に描くこと:"]
    for b in failed:
        kind = "セリフ" if b["type"] == "dialogue" else "ナレーション"
        lines.append(
            f"- パネル{b['panel_id']}の{kind}: 正「{b['expected']}」 ⇔ 前回誤「{b['detected'][:40]}」"
        )
    return base_prompt + "\n" + "\n".join(lines)


# ========== Pillow composite (fallback) ==========

def draw_tategaki_text(draw, img, x, y, text, font, line_gap=6):
    ascent, descent = font.getmetrics()
    line_height = ascent + descent
    cur_y = y
    for ch in text:
        if ch in ("ー", "〜", "…", "‥"):
            tmp = Image.new("RGBA", (line_height, line_height), (0, 0, 0, 0))
            tmp_d = ImageDraw.Draw(tmp)
            tmp_d.text((0, 0), ch, font=font, fill="black")
            tmp = tmp.rotate(-90, expand=False)
            img.paste(tmp, (x, cur_y), tmp)
        else:
            draw.text((x, cur_y), ch, font=font, fill="black")
        cur_y += line_height + line_gap - 4


def measure_column_height(text_len, font, line_gap=6):
    ascent, descent = font.getmetrics()
    return (ascent + descent) * text_len + (line_gap - 4) * max(0, text_len - 1)


def composite_bubble(img, draw, panel_box, anchor_frac, tail_frac, text, font):
    px1, py1, px2, py2 = panel_box
    pw, ph = px2 - px1, py2 - py1
    ascent, descent = font.getmetrics()
    char_h = ascent + descent
    max_col_chars = max(3, int(ph * 0.7 / char_h))
    cols = [text[i:i + max_col_chars] for i in range(0, len(text), max_col_chars)]
    col_gap = 5
    col_width = int(char_h * 1.05)
    text_w = col_width * len(cols) + col_gap * (len(cols) - 1)
    text_h = measure_column_height(max((len(c) for c in cols), default=0), font)
    pad_x, pad_y = 18, 18
    bub_w = text_w + pad_x * 2
    bub_h = text_h + pad_y * 2
    ax, ay = anchor_frac
    bx1 = int(px1 + ax * pw)
    by1 = int(py1 + ay * ph)
    bx2 = bx1 + bub_w
    by2 = by1 + bub_h
    if bx2 > px2 - 6:
        shift = bx2 - (px2 - 6)
        bx1 -= shift; bx2 -= shift
    if by2 > py2 - 6:
        shift = by2 - (py2 - 6)
        by1 -= shift; by2 -= shift
    draw.ellipse([bx1, by1, bx2, by2], fill="white", outline="black", width=3)
    # tail
    tx = int(px1 + tail_frac[0] * pw)
    ty = int(py1 + tail_frac[1] * ph)
    base_cx = (bx1 + bx2) // 2
    base_cy = by2 - 4
    draw.polygon([(base_cx - 14, base_cy), (base_cx + 14, base_cy), (tx, ty)],
                 fill="white", outline="black")
    draw.line([(base_cx - 12, base_cy - 2), (base_cx + 12, base_cy - 2)], fill="white", width=4)
    # tategaki right-to-left
    text_x = bx2 - pad_x - col_width
    text_y = by1 + pad_y
    for col in cols:
        draw_tategaki_text(draw, img, text_x, text_y, col, font)
        text_x -= (col_width + col_gap)


def composite_narration(img, draw, panel_box, text, font):
    px1, py1, px2, py2 = panel_box
    pw, ph = px2 - px1, py2 - py1
    ascent, descent = font.getmetrics()
    char_h = ascent + descent
    max_col_chars = max(4, int(ph * 0.7 / char_h))
    cols = [text[i:i + max_col_chars] for i in range(0, len(text), max_col_chars)]
    col_gap = 3
    col_width = int(char_h * 1.0)
    text_w = col_width * len(cols) + col_gap * (len(cols) - 1)
    text_h = measure_column_height(max((len(c) for c in cols), default=0), font)
    pad = 10
    box_w = text_w + pad * 2
    box_h = text_h + pad * 2
    # top-right corner inside panel
    bx2 = px2 - 4
    by1 = py1 + 4
    bx1 = bx2 - box_w
    by2 = by1 + box_h
    if bx1 < px1 + 4:
        bx1 = px1 + 4
        bx2 = bx1 + box_w
    draw.rectangle([bx1, by1, bx2, by2], fill="white", outline="black", width=2)
    text_x = bx2 - pad - col_width
    text_y = by1 + pad
    for col in cols:
        draw_tategaki_text(draw, img, text_x, text_y, col, font)
        text_x -= (col_width + col_gap)


def pillow_fallback(clean_image_path, expected_items, panel_regions, out_path):
    img = Image.open(clean_image_path).convert("RGB")
    W, H = img.size
    draw = ImageDraw.Draw(img)
    bubble_font = ImageFont.truetype(FONT_BOLD, 22)
    narration_font = ImageFont.truetype(FONT_REG, 18)

    # group by panel
    by_panel = {}
    for item in expected_items:
        by_panel.setdefault(item["panel_id"], []).append(item)

    for pid, items in by_panel.items():
        region = panel_regions[pid]
        box = (int(region[0]*W), int(region[1]*H), int(region[2]*W), int(region[3]*H))
        # draw narration first (top-right), then bubble (left center-ish)
        for it in items:
            if it["type"] == "narration":
                composite_narration(img, draw, box, it["text"], narration_font)
        for it in items:
            if it["type"] == "dialogue":
                composite_bubble(img, draw, box, (0.04, 0.25), (0.4, 0.6),
                                 it["text"], bubble_font)

    img.save(out_path, "JPEG", quality=92)


# ========== Main loop ==========

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-iter", type=int, default=3, help="max regen attempts before fallback")
    args = ap.parse_args()

    client = genai.Client(api_key=API_KEY)
    char_refs = [load_char_ref("ミサキ.png"), load_char_ref("山田課長.png")]

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log = {"run_id": ts, "page": 39, "iterations": [], "fallback_used": False}
    current_prompt = BASE_PROMPT
    converged_image = None

    for i in range(1, args.max_iter + 1):
        print(f"\n===== Iteration {i} (text-embedded regen) =====")
        img_path = os.path.join(OUT_DIR, f"p39_iter_{i}_{ts}.jpg")
        t0 = time.time()
        ok = generate_image(client, current_prompt, char_refs, img_path)
        t_gen = time.time() - t0
        if not ok:
            print("[gen] FAILED to produce image")
            break
        print(f"[gen] saved ({t_gen:.1f}s)")

        t0 = time.time()
        ocr = blind_ocr(client, img_path)
        t_ocr = time.time() - t0
        print(f"[ocr] {len(ocr.get('bubbles', []))} bubbles read ({t_ocr:.1f}s)")

        verdict = compare_texts(EXPECTED, ocr.get("bubbles", []))
        for b in verdict["bubbles"]:
            mark = "OK" if b["match"] else "NG"
            print(f"  [{mark}] p{b['panel_id']}/{b['type']}: exp={b['expected'][:30]}")
            if not b["match"]:
                print(f"         det={b['detected'][:60]}")

        log["iterations"].append({
            "iter": i, "image": img_path, "gen_time": t_gen, "ocr_time": t_ocr,
            "ocr": ocr, "verdict": verdict,
        })

        if verdict["overall_verdict"] == "PASS":
            print(f"\n*** CONVERGED at iter {i} (no fallback needed) ***")
            log["converged_at"] = i
            converged_image = img_path
            break
        else:
            print(f"\n[feedback] injecting specific mismatch info for next iter")
            current_prompt = build_feedback_prompt(BASE_PROMPT, verdict)

    # Fallback path
    if not converged_image:
        print(f"\n===== Fallback: generate clean image + Pillow composite =====")
        clean_path = os.path.join(OUT_DIR, f"p39_clean_{ts}.jpg")
        t0 = time.time()
        ok = generate_image(client, CLEAN_PROMPT, char_refs, clean_path)
        t_clean = time.time() - t0
        if not ok:
            print("[clean-gen] FAILED")
            sys.exit(1)
        print(f"[clean-gen] {clean_path} ({t_clean:.1f}s)")

        final_path = os.path.join(OUT_DIR, f"p39_final_{ts}.jpg")
        pillow_fallback(clean_path, EXPECTED, PANEL_REGIONS_T5, final_path)
        print(f"[composite] saved: {final_path}")

        log["fallback_used"] = True
        log["clean_image"] = clean_path
        log["final_image"] = final_path
        log["converged_at"] = None
        converged_image = final_path

    log["final_image"] = converged_image
    log_path = os.path.join(OUT_DIR, f"p39_run_{ts}.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    print(f"\nFinal: {converged_image}")
    print(f"Log: {log_path}")


if __name__ == "__main__":
    main()

"""
generate_pages.py
manga-career-restart 全巻 Step5 ハイブリッドQCループ 画像生成スクリプト

使い方:
  bash -c 'source ~/.bash_profile && python generate_pages.py --vol vol1 --pages 1-10'
  bash -c 'source ~/.bash_profile && python generate_pages.py --vol vol1 --pages 1-10 --dry-run'
  bash -c 'source ~/.bash_profile && python generate_pages.py --vol vol1'  # 全ページ

引数:
  --vol       対象巻 (vol1/vol2/vol3/vol4)
  --pages     ページ範囲 例: 1-10  未指定なら全ページ
  --max-iter  QCループ上限 (デフォルト: 3)
  --dry-run   API 呼び出しなしでプロンプト構築だけ確認

ebook-to-manga skill.md Step5 疑似コード準拠
"""

import argparse
import base64
import csv
import json
import logging
import os
import re
import shutil
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path

# ───────────────────────────────────────────
# 定数・パス設定
# ───────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
MANGA_DIR = SCRIPT_DIR.parent   # manga-career-restart/
MANUSCRIPT_DIR = MANGA_DIR / "manuscript"
CHAR_DEFS_PATH = MANUSCRIPT_DIR / "character_defs.json"
CHAR_IMG_DIR = MANUSCRIPT_DIR / "characters"

# コスト単価 (2026-04 時点の gpt-image-2 high 1024x1536)
COST_IMAGE_EDIT = 0.21      # gpt-image-2 /枚
COST_OCR_CALL = 0.01        # gpt-4o / OCR コール
COST_VISION_CALL = 0.008    # gpt-4o / vision コール (画像込み)
COST_LIMIT_PER_PAGE = 1.0   # 1ページ超えたら中断
COST_LIMIT_PILOT = 10.0     # パイロット全体上限

# リトライ設定
MAX_API_RETRY = 2
API_RETRY_SLEEP = 1.0
API_CALL_INTERVAL = 2.0     # ページ間インターバル

# ───────────────────────────────────────────
# API キー取得
# ───────────────────────────────────────────
def load_api_key():
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        # .bashrc / .bash_profile から直接パース（export OPENAI_API_KEY="..." 行を検索）
        for rc_path in [
            "C:/Users/fcmdt/.bashrc",
            "C:/Users/fcmdt/.bash_profile",
            os.path.expanduser("~/.bashrc"),
            os.path.expanduser("~/.bash_profile"),
        ]:
            if os.path.exists(rc_path):
                try:
                    with open(rc_path, encoding="utf-8", errors="replace") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("export OPENAI_API_KEY="):
                                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                                if val:
                                    key = val
                                    os.environ["OPENAI_API_KEY"] = key
                                    break
                except Exception:
                    pass
            if key:
                break

    if not key:
        try:
            from dotenv import load_dotenv
            for env_path in [
                str(MANGA_DIR.parent.parent.parent.parent / ".env"),
                "G:/マイドライブ/YNFactory-cc/.env",
                "C:/Users/fcmdt/.env",
            ]:
                if os.path.exists(env_path):
                    load_dotenv(env_path)
                    key = os.environ.get("OPENAI_API_KEY", "")
                    if key:
                        break
        except ImportError:
            pass
    return key


# ───────────────────────────────────────────
# キャラ名正規化（全角括弧 → アンダースコア）
# プロンプト内 "ひなた（赤ちゃん期）" → "ひなた_赤ちゃん期"
# ───────────────────────────────────────────
def normalize_char_name(name: str) -> str:
    """全角括弧付きキャラ名をファイル名形式に変換"""
    # 「ひなた（赤ちゃん期）」→「ひなた_赤ちゃん期」
    name = re.sub(r'（(.+?)）', r'_\1', name)
    # 半角括弧も念のため
    name = re.sub(r'\((.+?)\)', r'_\1', name)
    return name.strip()


# ───────────────────────────────────────────
# キャラ参照画像パスを解決
# ───────────────────────────────────────────
def resolve_char_image(char_name: str) -> str | None:
    """キャラ名から参照画像パスを解決。複数パターンを試みる。"""
    candidates = [
        CHAR_IMG_DIR / f"{char_name}.png",
        CHAR_IMG_DIR / f"{normalize_char_name(char_name)}.png",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return None


# ───────────────────────────────────────────
# プロンプトからキャラ名を抽出
# ───────────────────────────────────────────
def extract_char_names_from_prompt(prompt: str) -> list[str]:
    """
    プロンプトの「添付の〇〇.png」から キャラ名リストを抽出（重複なし・順序保持）
    """
    found = re.findall(r'添付の([^\s、,]+?)\.png', prompt)
    # 重複除去（順序保持）
    seen = set()
    result = []
    for name in found:
        name = name.strip()
        if name not in seen:
            seen.add(name)
            result.append(name)
    return result


# ───────────────────────────────────────────
# extract_page_chars (skill.md 準拠)
# ───────────────────────────────────────────
def extract_page_chars(prompt: str, char_defs: dict) -> list[dict]:
    """
    プロンプトからキャラ名を抽出し、character_defs.json の外見情報と結合して返す。
    Returns: [{"name": "ミサキ", "appearance": "32歳女性..."}, ...]
    """
    char_names = extract_char_names_from_prompt(prompt)
    result = []
    for name in char_names:
        # character_defs.json のキーと直接マッチ試行
        appearance = char_defs.get(name)
        if not appearance:
            # 全角括弧→アンダースコア変換で再試行
            # （例: "ひなた_赤ちゃん期" → "ひなた（赤ちゃん期）"）
            for def_name in char_defs:
                if normalize_char_name(def_name) == name:
                    appearance = char_defs[def_name]
                    break
        result.append({
            "name": name,
            "appearance": appearance or "（外見情報なし）",
        })
    return result


# ───────────────────────────────────────────
# フィードバックセクション注入
# ───────────────────────────────────────────
def inject_feedback(prompt: str, missing_chars: list[str], ocr_fail_texts: list[str]) -> str:
    """
    iter 2以降: 「◆【前回失敗・最重要】」セクションをプロンプト先頭に注入
    """
    lines = ["◆【前回失敗・最重要】以下の問題が前回の生成で発生しました。今回は必ず修正してください:"]
    if missing_chars:
        chars_str = "、".join(missing_chars)
        lines.append(f"  - キャラクター {chars_str} のイラストが画像に存在しません。必ず全員を描画してください。")
    if ocr_fail_texts:
        for t in ocr_fail_texts[:3]:  # 最大3件
            lines.append(f"  - セリフ「{t}」が正確に描画されていません。テキスト通りに吹き出しに書いてください。")
    feedback_block = "\n".join(lines)
    return feedback_block + "\n" + prompt


# ───────────────────────────────────────────
# Blind-OCR (skill.md Step 5-QC 準拠)
# ───────────────────────────────────────────
OCR_SYSTEM_PROMPT = """添付のマンガ画像を見て、下記の要素を画像に描かれている通り正確に読み取ってください。
推測や補完は一切せず、画像に実際に見える文字列だけを返してください。
読めない崩し字や意味不明な文字列も、見える通りに書いてください（勝手に正しい日本語に補正しない）。

対象:
- 吹き出し（楕円・雲形）内の文字 -> type="dialogue"
- ナレーションボックス（四角枠・角丸枠）内の文字 -> type="narration"

対象外（読み取らない）:
- オノマトペ・擬音
- 背景の看板・ポスター・標識
- 小物のUI・ラベル（スマホ画面・PC画面・本の表紙・商品パッケージ等）
- 服のロゴ・ブランド表記

出力形式: JSONのみ。説明文・マークダウン禁止。読み取れたテキストは改行なしで1行に連結。
{
  "bubbles": [
    {"panel_id": int, "type": "dialogue"|"narration", "detected_text": str}
  ]
}"""


def blind_ocr(client, image_path: str, logger: logging.Logger) -> dict:
    with open(image_path, "rb") as f:
        b64img = base64.b64encode(f.read()).decode()

    last_error = None
    for attempt in range(MAX_API_RETRY + 1):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                temperature=0.0,
                max_tokens=4096,
                response_format={"type": "json_object"},
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64img}"}},
                        {"type": "text", "text": OCR_SYSTEM_PROMPT},
                    ],
                }],
            )
            raw = response.choices[0].message.content
            result = json.loads(raw)
            return result
        except json.JSONDecodeError:
            try:
                match = re.search(r'"bubbles"\s*:\s*\[.*?\]', raw, re.DOTALL)
                if match:
                    return json.loads("{" + match.group(0) + "}")
            except Exception:
                pass
            return {"bubbles": []}
        except Exception as e:
            last_error = e
            if attempt < MAX_API_RETRY:
                time.sleep(API_RETRY_SLEEP)
            logger.warning(f"[ocr] attempt {attempt+1} failed: {e}")

    logger.warning(f"[ocr] failed after retries: {last_error}")
    return {"bubbles": []}


# ───────────────────────────────────────────
# OCR 判定
# ───────────────────────────────────────────
def normalize_text(s: str) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"\s+", "", s)
    return s


def ocr_pass_check(bubbles: list, expected_items: list) -> tuple[bool, list[str]]:
    """
    OCR 結果と期待テキストを突き合わせて PASS/FAIL を判定。
    Returns: (is_pass, fail_texts)
    """
    if not expected_items:
        return True, []

    ocr_map: dict[tuple, list] = {}
    for b in bubbles:
        key = (b.get("panel_id"), b.get("type"))
        ocr_map.setdefault(key, []).append(b.get("detected_text", ""))

    fail_texts = []
    used: dict[tuple, set] = {}

    for item in expected_items:
        if item.get("type") not in ("dialogue", "narration"):
            continue
        key = (item.get("panel_id"), item.get("type"))
        expected = item.get("text", "")
        candidates = ocr_map.get(key, [])
        used_indices = used.get(key, set())

        matched = False
        for i, detected in enumerate(candidates):
            if i in used_indices:
                continue
            if normalize_text(detected) == normalize_text(expected):
                used_indices.add(i)
                used[key] = used_indices
                matched = True
                break

        if not matched:
            fail_texts.append(expected[:50])

    return (len(fail_texts) == 0), fail_texts


# ───────────────────────────────────────────
# Vision-check (skill.md Step 5-QC 準拠、validate_vision_check.py 方式)
# ───────────────────────────────────────────
def vision_check(client, image_path: str, page_chars: list[dict], logger: logging.Logger) -> dict:
    """
    1キャラずつ YES/NO 判定。
    Returns: {"vision_checks": [{"char_name": str, "result": "YES"|"NO", "reason": str}]}
    """
    if not page_chars:
        return {"vision_checks": []}

    with open(image_path, "rb") as f:
        b64img = base64.b64encode(f.read()).decode("utf-8")

    n = len(page_chars)
    name_list = "、".join(c["name"] for c in page_chars)
    char_questions = "\n".join(
        f"- {c['name']}（{c['appearance'][:80]}）" for c in page_chars
    )

    system_msg = (
        "あなたは画像品質チェッカーです。与えられたマンガ画像を分析し、"
        "指定されたキャラクターが全身イラストとして描かれているかを1人ずつ YES または NO で判定してください。"
        "テキスト枠・名前ラベルのみでキャラクターのイラスト本体が存在しない場合は NO としてください。"
        "イラストが実際に画像内に描かれているかを画像の内容から判断してください。必ず JSON で返してください。"
    )
    user_msg = (
        f"以下のマンガ画像に、キャラクター{n}人 [{name_list}] がそれぞれ"
        f"全身イラストとして描かれているか、1人ずつ YES/NO で答えてください。"
        "テキスト枠のみ（名前タグのみでイラストなし）は NO とします。\n\n"
        f"確認対象:\n{char_questions}\n\n"
        '出力形式（JSONのみ。説明文禁止）:\n'
        '{"vision_checks": [{"char_name": "ミサキ", "result": "YES", "reason": "..."}]}'
    )

    last_error = None
    for attempt in range(MAX_API_RETRY + 1):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                temperature=0.0,
                max_tokens=1024,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_msg},
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64img}"}},
                            {"type": "text", "text": user_msg},
                        ],
                    },
                ],
            )
            raw = response.choices[0].message.content
            result = json.loads(raw)
            return result
        except Exception as e:
            last_error = e
            if attempt < MAX_API_RETRY:
                time.sleep(API_RETRY_SLEEP)
            logger.warning(f"[vision] attempt {attempt+1} failed: {e}")

    logger.warning(f"[vision] failed after retries: {last_error}")
    return {"vision_checks": []}


def vision_pass_check(vision_result: dict) -> tuple[bool, list[str]]:
    checks = vision_result.get("vision_checks", [])
    missing = [c["char_name"] for c in checks if c.get("result") != "YES"]
    return (len(missing) == 0), missing


# ───────────────────────────────────────────
# Step 5.5 Pillow フォールバック (OCR FAIL 起因のみ)
# ───────────────────────────────────────────
def pillow_fallback(image_path: str, expected_items: list[dict], output_path: str, logger: logging.Logger) -> bool:
    """
    Pillow でテキストを直接描画してOCR FAILを補正する。
    OCR FAIL 起因のみ有効。
    Returns: True = 成功、False = 失敗（Pillow 未インストール等）
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        logger.warning("[fallback] Pillow が未インストールのため、フォールバック不可")
        return False

    try:
        img = Image.open(image_path).convert("RGBA")
        draw = ImageDraw.Draw(img)
        width, height = img.size

        # フォントを探す（日本語対応）
        font_candidates = [
            "C:/Windows/Fonts/meiryo.ttc",
            "C:/Windows/Fonts/msgothic.ttc",
            "C:/Windows/Fonts/YuGothM.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        ]
        font = None
        font_size = max(16, height // 40)
        for fc in font_candidates:
            if os.path.exists(fc):
                try:
                    font = ImageFont.truetype(fc, font_size)
                    break
                except Exception:
                    continue

        if font is None:
            font = ImageFont.load_default()

        # 吹き出しとテキストを下部に追記（シンプルな重ね描き）
        y_offset = height - (len(expected_items) + 1) * (font_size + 8)
        y_offset = max(y_offset, height // 2)

        for item in expected_items:
            if item.get("type") not in ("dialogue", "narration"):
                continue
            text = item.get("text", "")
            speaker = item.get("speaker", "")
            label = f"[{speaker}] {text}" if speaker else f"[ナレ] {text}"

            # 背景矩形
            bbox = draw.textbbox((10, y_offset), label, font=font)
            draw.rectangle([bbox[0]-4, bbox[1]-2, bbox[2]+4, bbox[3]+2], fill=(255, 255, 220, 200))
            draw.text((10, y_offset), label, font=font, fill=(20, 20, 20, 255))
            y_offset += font_size + 10

        # PNG として保存
        img_rgb = img.convert("RGB")
        img_rgb.save(output_path, "PNG")
        logger.info(f"[fallback] Pillow フォールバック完了: {output_path}")
        return True

    except Exception as e:
        logger.error(f"[fallback] Pillow 処理エラー: {e}")
        return False


# ───────────────────────────────────────────
# 画像生成 (gpt-image-2)
# ───────────────────────────────────────────
def generate_image(
    client,
    prompt: str,
    ref_image_paths: list[str],
    output_path: str,
    logger: logging.Logger,
    dry_run: bool = False,
) -> bool:
    """
    gpt-image-2 で画像生成。
    Returns: True = 成功
    """
    if dry_run:
        logger.info(f"[dry-run] prompt length: {len(prompt)}, refs: {[os.path.basename(p) for p in ref_image_paths]}")
        # ダミー PNG を作成（Pillow があれば）
        try:
            from PIL import Image
            img = Image.new("RGB", (100, 150), color=(200, 220, 255))
            img.save(output_path, "PNG")
            logger.info(f"[dry-run] dummy image saved: {output_path}")
        except ImportError:
            # Pillow なしでも最低限のダミーファイルを作成
            Path(output_path).touch()
        return True

    image_files = []
    try:
        for p in ref_image_paths:
            if os.path.exists(p):
                image_files.append(open(p, "rb"))
            else:
                logger.warning(f"[gen] 参照画像が見つかりません: {p}")

        if not image_files:
            logger.warning("[gen] 参照画像なし、テキストプロンプトのみで生成")
            result = client.images.generate(
                model="gpt-image-2",
                prompt=prompt,
                size="1024x1536",
                quality="high",
                n=1,
            )
        else:
            result = client.images.edit(
                model="gpt-image-2",
                image=image_files,
                prompt=prompt,
                size="1024x1536",
                quality="high",
                n=1,
            )

        item = result.data[0]
        b64 = item.b64_json
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(b64))
        logger.info(f"[gen] 生成完了: {output_path}")
        return True

    except Exception as e:
        logger.error(f"[gen] 画像生成エラー: {e}")
        return False
    finally:
        for f in image_files:
            f.close()


# ───────────────────────────────────────────
# 進捗管理
# ───────────────────────────────────────────
def load_progress(progress_path: Path) -> dict:
    if progress_path.exists():
        with open(progress_path, encoding="utf-8") as f:
            return json.load(f)
    return {
        "completed": [],
        "failed": [],
        "fallback": [],
        "skipped": [],
        "stats": {
            "total_pages": 0,
            "ocr_pass_count": 0,
            "vision_pass_count": 0,
            "fallback_count": 0,
            "estimated_cost_usd": 0.0,
            "image_gen_count": 0,
            "ocr_call_count": 0,
            "vision_call_count": 0,
        },
    }


def save_progress(progress: dict, progress_path: Path):
    with open(progress_path, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


# ───────────────────────────────────────────
# コスト計算
# ───────────────────────────────────────────
def calc_cost(image_gen_count: int, ocr_count: int, vision_count: int) -> float:
    return (
        image_gen_count * COST_IMAGE_EDIT
        + ocr_count * COST_OCR_CALL
        + vision_count * COST_VISION_CALL
    )


# ───────────────────────────────────────────
# メイン処理
# ───────────────────────────────────────────
def process_vol(
    vol: str,
    page_range: tuple[int, int] | None,
    max_iter: int,
    dry_run: bool,
):
    vol_dir = MANGA_DIR / vol
    csv_path = vol_dir / "panels" / "comicle_output.csv"
    pages_dir = vol_dir / "pages"
    progress_path = vol_dir / "progress.json"
    log_path = vol_dir / "generation.log"
    cost_path = vol_dir / "cost_pilot.md"

    # ─ ディレクトリ作成
    pages_dir.mkdir(parents=True, exist_ok=True)

    # ─ ロギング設定
    logger = logging.getLogger(f"gen_{vol}")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fh = logging.FileHandler(str(log_path), encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s %(message)s", datefmt="%H:%M:%S"))
        # Windows cp932 対策: stdout に書けない文字は replace して継続
        import io
        safe_stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace") if hasattr(sys.stdout, 'buffer') else sys.stdout
        ch = logging.StreamHandler(safe_stdout)
        ch.setFormatter(logging.Formatter("%(asctime)s %(message)s", datefmt="%H:%M:%S"))
        logger.addHandler(fh)
        logger.addHandler(ch)

    logger.info(f"=== {vol} 画像生成開始 {'[DRY-RUN]' if dry_run else ''} ===")
    logger.info(f"CSV: {csv_path}")
    logger.info(f"pages dir: {pages_dir}")

    # ─ CSV 読み込み
    if not csv_path.exists():
        logger.error(f"CSV が見つかりません: {csv_path}")
        return

    pages_data = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pages_data.append(row)

    # ─ ページ範囲フィルタ
    if page_range:
        start, end = page_range
        pages_data = [r for r in pages_data if start <= int(r["ページ番号"]) <= end]
        logger.info(f"ページ範囲: {start}〜{end} ({len(pages_data)}ページ)")
    else:
        logger.info(f"全ページ: {len(pages_data)}ページ")

    # ─ character_defs.json 読み込み
    if not CHAR_DEFS_PATH.exists():
        logger.error(f"character_defs.json が見つかりません: {CHAR_DEFS_PATH}")
        return

    with open(CHAR_DEFS_PATH, encoding="utf-8") as f:
        char_defs = json.load(f)
    logger.info(f"character_defs.json ロード: {list(char_defs.keys())}")

    # ─ 進捗管理（リセット：新規スキルでの再生成）
    # 注意: 工程2の要件定義書に従い、旧モデルの progress.json をリセットする
    progress = {
        "completed": [],
        "failed": [],
        "fallback": [],
        "skipped": [],
        "stats": {
            "total_pages": len(pages_data),
            "ocr_pass_count": 0,
            "vision_pass_count": 0,
            "fallback_count": 0,
            "estimated_cost_usd": 0.0,
            "image_gen_count": 0,
            "ocr_call_count": 0,
            "vision_call_count": 0,
        },
    }
    logger.info("progress.json をリセット（新規スキル再生成モード）")

    # ─ OpenAI クライアント
    if not dry_run:
        api_key = load_api_key()
        if not api_key:
            logger.error("OPENAI_API_KEY が設定されていません。bash_profile をソースしてから実行してください。")
            sys.exit(1)
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    else:
        client = None

    # ─ コスト追跡
    total_image_gen = 0
    total_ocr_calls = 0
    total_vision_calls = 0
    total_cost = 0.0
    start_time = datetime.now()

    # ─ 統計
    pages_processed = 0
    pages_passed = 0
    pages_failed = 0
    pages_skipped = 0
    pages_fallback = 0
    ocr_pass_count = 0
    ocr_checked_count = 0
    vision_pass_count = 0
    vision_checked_count = 0

    # ─────────────────────────────────────────
    # ページループ
    # ─────────────────────────────────────────
    for row in pages_data:
        page_num = int(row["ページ番号"])
        template = row.get("使用するコマ割りテンプレ", "")
        prompt = row.get("漫画作成のプロンプト", "")
        text_json_str = row.get("コマ別テキストJSON", "[]")

        try:
            text_items = json.loads(text_json_str)
        except json.JSONDecodeError:
            text_items = []

        page_label = f"page_{page_num:03d}"
        final_page_path = pages_dir / f"{page_label}.png"

        logger.info(f"--- {page_label} (テンプレ: {template}) ---")

        # ─ テキストページはスキップ
        if template == "テキストページ":
            logger.info(f"[skip] {page_label}: テキストページ")
            progress["skipped"].append(page_num)
            pages_skipped += 1
            save_progress(progress, progress_path)
            continue

        # ─ キャラ情報抽出
        page_chars = extract_page_chars(prompt, char_defs)
        logger.info(f"  キャラ: {[c['name'] for c in page_chars]}")

        # ─ 参照画像パス解決
        ref_image_paths = []
        for c in page_chars:
            img_path = resolve_char_image(c["name"])
            if img_path:
                ref_image_paths.append(img_path)
                logger.info(f"  参照画像: {os.path.basename(img_path)}")
            else:
                logger.warning(f"  参照画像なし: {c['name']}")

        # ─ セリフありページの判定
        has_text = any(item.get("type") in ("dialogue", "narration") for item in text_items)

        # ─ dry-run: プロンプト情報だけ表示
        if dry_run:
            logger.info(f"  [dry-run] prompt length: {len(prompt)}, refs: {[os.path.basename(p) for p in ref_image_paths]}, has_text: {has_text}")
            logger.info(f"  [dry-run] text_items ({len(text_items)}): {text_items[:2]}")
            progress["completed"].append(page_num)
            pages_processed += 1
            pages_passed += 1
            save_progress(progress, progress_path)
            continue

        # ─────────────────────────────────────
        # iter ループ (最大 max_iter 回)
        # ─────────────────────────────────────
        page_passed = False
        page_fallback = False
        last_iter_path = None
        current_prompt = prompt
        missing_chars_feedback = []
        ocr_fail_texts_feedback = []

        for iter_num in range(1, max_iter + 1):
            # コスト上限チェック
            current_cost = calc_cost(total_image_gen, total_ocr_calls, total_vision_calls)
            if current_cost > COST_LIMIT_PILOT:
                logger.error(f"[COST LIMIT] パイロット上限 ${COST_LIMIT_PILOT} を超過。中断します。")
                # コスト記録して終了
                _write_cost_report(cost_path, total_image_gen, total_ocr_calls, total_vision_calls, total_cost, pages_processed, start_time, dry_run)
                save_progress(progress, progress_path)
                return

            iter_path = str(pages_dir / f"{page_label}_iter_{iter_num}.png")
            logger.info(f"  [iter {iter_num}] 画像生成中...")

            # iter 2以降: フィードバック注入
            if iter_num > 1:
                current_prompt = inject_feedback(prompt, missing_chars_feedback, ocr_fail_texts_feedback)
                logger.info(f"  [iter {iter_num}] フィードバック注入済み (missing: {missing_chars_feedback}, ocr_fail: {ocr_fail_texts_feedback[:1]})")

            gen_ok = generate_image(client, current_prompt, ref_image_paths, iter_path, logger)
            if not gen_ok:
                logger.error(f"  [iter {iter_num}] 画像生成失敗")
                continue
            total_image_gen += 1
            last_iter_path = iter_path

            iter_ocr_pass = True
            iter_vision_pass = True
            ocr_fail_texts_current = []
            missing_chars_current = []

            # ─ Blind-OCR（セリフありページのみ）
            if has_text:
                logger.info(f"  [iter {iter_num}] Blind-OCR 実行...")
                time.sleep(API_CALL_INTERVAL)
                ocr_result = blind_ocr(client, iter_path, logger)
                total_ocr_calls += 1
                ocr_checked_count += 1
                bubbles = ocr_result.get("bubbles", [])
                iter_ocr_pass, ocr_fail_texts_current = ocr_pass_check(bubbles, text_items)
                logger.info(f"  [iter {iter_num}] OCR: {'PASS' if iter_ocr_pass else 'FAIL'} (bubbles={len(bubbles)}, fail_texts={ocr_fail_texts_current[:2]})")
            else:
                logger.info(f"  [iter {iter_num}] OCR: スキップ（セリフなしページ）")

            # ─ Vision-check（常時実行）
            if page_chars:
                logger.info(f"  [iter {iter_num}] Vision-check 実行...")
                time.sleep(API_CALL_INTERVAL)
                vision_result = vision_check(client, iter_path, page_chars, logger)
                total_vision_calls += 1
                vision_checked_count += 1
                iter_vision_pass, missing_chars_current = vision_pass_check(vision_result)
                for vc in vision_result.get("vision_checks", []):
                    logger.info(f"    {vc.get('char_name')}: {vc.get('result')} — {vc.get('reason','')[:60]}")
                logger.info(f"  [iter {iter_num}] Vision: {'PASS' if iter_vision_pass else 'FAIL'} (missing={missing_chars_current})")
            else:
                logger.info(f"  [iter {iter_num}] Vision-check: スキップ（キャラなしページ）")

            log_line = f"[iter {iter_num}] {page_label}: ocr={'PASS' if iter_ocr_pass else 'FAIL'} vision={'PASS' if iter_vision_pass else 'FAIL'} verdict={'PASS' if (iter_ocr_pass and iter_vision_pass) else 'FAIL'}"
            logger.info(f"  {log_line}")

            # ─ 統合判定
            if iter_ocr_pass and iter_vision_pass:
                shutil.copy2(iter_path, str(final_page_path))
                logger.info(f"  [PASS] {page_label} 確定: {final_page_path}")
                page_passed = True
                if has_text:
                    ocr_pass_count += 1
                if page_chars:
                    vision_pass_count += 1
                break

            # フィードバック更新（次 iter へ）
            missing_chars_feedback = missing_chars_current
            ocr_fail_texts_feedback = ocr_fail_texts_current

        # ─────────────────────────────────────
        # iter 終了後の処理
        # ─────────────────────────────────────
        if not page_passed:
            logger.info(f"  {max_iter} iter 全て FAIL")

            # Step 5.5 Pillow フォールバック（OCR FAIL 起因のみ）
            ocr_was_failing = has_text and not iter_ocr_pass
            vision_was_failing = page_chars and not iter_vision_pass

            if ocr_was_failing and last_iter_path:
                logger.info(f"  [fallback] OCR FAIL 起因 → Pillow フォールバック実行")
                fallback_ok = pillow_fallback(last_iter_path, text_items, str(final_page_path), logger)
                if fallback_ok:
                    page_passed = True
                    page_fallback = True
                    pages_fallback += 1
                    progress["fallback"].append({
                        "page": page_num,
                        "reason": "ocr_fail",
                        "iter_count": max_iter,
                    })
                    logger.info(f"  [fallback] 完了: {final_page_path}")
                else:
                    logger.error(f"  [fallback] 失敗")

            if not page_passed:
                # Vision FAIL 起因 or フォールバックも失敗 → failed 記録 + 最後の iter を採用
                reason = "vision_fail" if vision_was_failing else "ocr_fail"
                if last_iter_path and os.path.exists(last_iter_path):
                    shutil.copy2(last_iter_path, str(final_page_path))
                    logger.warning(f"  [FAIL] {page_label}: {reason} — iter_{max_iter} を暫定採用: {final_page_path}")
                progress["failed"].append({"page": page_num, "reason": reason})
                pages_failed += 1

        # 完了記録
        if page_passed or final_page_path.exists():
            if page_num not in progress["completed"]:
                progress["completed"].append(page_num)

        pages_processed += 1
        save_progress(progress, progress_path)

        # ページ間インターバル
        time.sleep(API_CALL_INTERVAL)

    # ─────────────────────────────────────
    # 最終集計
    # ─────────────────────────────────────
    elapsed = (datetime.now() - start_time).total_seconds()
    total_cost = calc_cost(total_image_gen, total_ocr_calls, total_vision_calls)
    progress["stats"]["estimated_cost_usd"] = round(total_cost, 4)
    progress["stats"]["image_gen_count"] = total_image_gen
    progress["stats"]["ocr_call_count"] = total_ocr_calls
    progress["stats"]["vision_call_count"] = total_vision_calls
    progress["stats"]["ocr_pass_count"] = ocr_pass_count
    progress["stats"]["vision_pass_count"] = vision_pass_count
    progress["stats"]["fallback_count"] = pages_fallback
    save_progress(progress, progress_path)

    # コストレポート
    _write_cost_report(cost_path, total_image_gen, total_ocr_calls, total_vision_calls, total_cost, pages_processed, start_time, dry_run)

    # ─ 最終ログ
    img_processed = pages_processed - pages_skipped
    ocr_pass_rate = ocr_pass_count / max(ocr_checked_count, 1) * 100
    vision_pass_rate = vision_pass_count / max(vision_checked_count, 1) * 100
    avg_time = elapsed / max(img_processed, 1)

    logger.info("=" * 60)
    logger.info(f"=== {vol} 生成完了 {'[DRY-RUN]' if dry_run else ''} ===")
    logger.info(f"処理ページ: {pages_processed} (画像生成: {img_processed}, スキップ: {pages_skipped})")
    logger.info(f"PASS: {pages_passed - pages_fallback}, FAIL: {pages_failed}, フォールバック: {pages_fallback}")
    logger.info(f"OCR PASS率: {ocr_pass_rate:.1f}% ({ocr_pass_count}/{ocr_checked_count})")
    logger.info(f"Vision PASS率: {vision_pass_rate:.1f}% ({vision_pass_count}/{vision_checked_count})")
    logger.info(f"推定コスト: ${total_cost:.3f}")
    logger.info(f"所要時間: {elapsed:.0f}秒 ({elapsed/60:.1f}分)")
    logger.info(f"1ページ平均: {avg_time:.1f}秒")
    logger.info("=" * 60)


def _write_cost_report(cost_path, image_gen, ocr_calls, vision_calls, total_cost, pages, start_time, dry_run):
    elapsed = (datetime.now() - start_time).total_seconds()
    img_cost = image_gen * COST_IMAGE_EDIT
    ocr_cost = ocr_calls * COST_OCR_CALL
    vision_cost = vision_calls * COST_VISION_CALL

    lines = [
        f"# コスト集計レポート {'(DRY-RUN)' if dry_run else ''}",
        f"",
        f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"",
        f"## API 呼び出し回数",
        f"| 項目 | 回数 | 単価 | 計 |",
        f"|------|------|------|-----|",
        f"| gpt-image-2 生成 | {image_gen} | ${COST_IMAGE_EDIT} | ${img_cost:.3f} |",
        f"| Blind-OCR (gpt-4o) | {ocr_calls} | ${COST_OCR_CALL} | ${ocr_cost:.3f} |",
        f"| Vision-check (gpt-4o) | {vision_calls} | ${COST_VISION_CALL} | ${vision_cost:.3f} |",
        f"| **合計** | | | **${total_cost:.3f}** |",
        f"",
        f"## サマリー",
        f"- 処理ページ数: {pages}",
        f"- 所要時間: {elapsed:.0f}秒 ({elapsed/60:.1f}分)",
        f"- パイロット予算上限: ${COST_LIMIT_PILOT}",
        f"- 残余予算: ${COST_LIMIT_PILOT - total_cost:.3f}",
        f"",
        f"## 全巻スケールアップ見積もり (342ページ)",
        f"",
    ]

    if pages > 0:
        per_page_cost = total_cost / max(pages, 1)
        estimated_total = per_page_cost * 342
        lines += [
            f"- 1ページあたりコスト: ${per_page_cost:.3f}",
            f"- 342ページ推定合計: ${estimated_total:.2f}",
            f"- 予算上限 $150 に対して: {'OK' if estimated_total <= 150 else 'OVER'}",
        ]

    with open(cost_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ───────────────────────────────────────────
# エントリポイント
# ───────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="manga-career-restart 画像生成")
    parser.add_argument("--vol", default="vol1", help="対象巻 (vol1/vol2/vol3/vol4)")
    parser.add_argument("--pages", default=None, help="ページ範囲 例: 1-10")
    parser.add_argument("--max-iter", type=int, default=3, help="QCループ上限 (デフォルト: 3)")
    parser.add_argument("--dry-run", action="store_true", help="API呼び出しなしでプロンプト構築確認")
    args = parser.parse_args()

    # ページ範囲パース
    page_range = None
    if args.pages:
        if "-" in args.pages:
            parts = args.pages.split("-", 1)
            page_range = (int(parts[0]), int(parts[1]))
        else:
            n = int(args.pages)
            page_range = (n, n)

    process_vol(
        vol=args.vol,
        page_range=page_range,
        max_iter=args.max_iter,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()

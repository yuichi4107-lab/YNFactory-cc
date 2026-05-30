"""
generate_simple.py
manga-career-restart  iter_1 シンプルモード 画像生成スクリプト

方針:
  - gpt-image-2 で iter_1 のみ 1回生成 → そのまま page_{NNN}.png として保存
  - OCR / Vision-check / Pillow合成は一切なし
  - 参照画像抽出と全角括弧→アンダースコア変換は維持

使い方:
  python generate_simple.py --vol vol1
  python generate_simple.py --vol vol1 --pages 11-50
  python generate_simple.py --vol vol1 --pages all --skip-existing
  python generate_simple.py --vol vol1 --dry-run

引数:
  --vol           対象巻 (vol1/vol2/vol3/vol4)
  --pages         ページ範囲 例: 11-50, all  未指定=all
  --skip-existing  既存 page_{NNN}.png があればスキップ
  --dry-run       API呼び出しなしでプロンプト構築だけ確認
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
from datetime import datetime
from pathlib import Path

# ───────────────────────────────────────────
# パス定数
# ───────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
MANGA_DIR = SCRIPT_DIR.parent          # manga-career-restart/
MANUSCRIPT_DIR = MANGA_DIR / "manuscript"
CHAR_DEFS_PATH = MANUSCRIPT_DIR / "character_defs.json"
CHAR_IMG_DIR = MANUSCRIPT_DIR / "characters"

# コスト単価 (2026-04 時点の gpt-image-2 high 1024x1536)
COST_PER_IMAGE = 0.21
COST_LIMIT_TOTAL = 20.0   # vol1 上限 $20

# リトライ設定
MAX_API_RETRY = 2
API_RETRY_SLEEP = 30      # レートリミット対応
API_CALL_INTERVAL = 5     # ページ間インターバル（秒）

# 旧 .png 退避しきい値（2026-04-23 16:00 のタイムスタンプ）
NEW_PNG_THRESHOLD = datetime(2026, 4, 23, 16, 0, 0).timestamp()


# ───────────────────────────────────────────
# ロギング設定
# ───────────────────────────────────────────
def setup_logging(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("generate_simple")
    logger.setLevel(logging.DEBUG)

    # ファイルハンドラ（追記）
    fh = logging.FileHandler(str(log_path), encoding="utf-8", mode="a")
    fh.setLevel(logging.DEBUG)

    # コンソールハンドラ
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")
    fh.setFormatter(fmt)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


# ───────────────────────────────────────────
# API キー取得
# ───────────────────────────────────────────
def load_api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY", "")
    if key:
        return key

    # .bashrc / .bash_profile から直接パース
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
                                return key
            except Exception:
                pass

    # .env ファイルからも試みる
    for env_path in [
        "G:/マイドライブ/YNFactory-cc/.env",
        "C:/Users/fcmdt/.env",
    ]:
        if os.path.exists(env_path):
            try:
                with open(env_path, encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("OPENAI_API_KEY="):
                            val = line.split("=", 1)[1].strip().strip('"').strip("'")
                            if val:
                                key = val
                                os.environ["OPENAI_API_KEY"] = key
                                return key
            except Exception:
                pass

    return ""


# ───────────────────────────────────────────
# キャラ名正規化（全角括弧 → アンダースコア）
# 例: ひなた（赤ちゃん期） → ひなた_赤ちゃん期
# ───────────────────────────────────────────
def normalize_char_name(name: str) -> str:
    name = re.sub(r'（(.+?)）', r'_\1', name)
    name = re.sub(r'\((.+?)\)', r'_\1', name)
    return name.strip()


# ───────────────────────────────────────────
# プロンプトからキャラ名を抽出
# 「添付の〇〇.png」パターンを検索
# ───────────────────────────────────────────
def extract_char_names_from_prompt(prompt: str) -> list:
    found = re.findall(r'添付の([^\s、,]+?)\.png', prompt)
    seen = set()
    result = []
    for name in found:
        name = name.strip()
        if name not in seen:
            seen.add(name)
            result.append(name)
    return result


# ───────────────────────────────────────────
# キャラ参照画像パスを解決
# ───────────────────────────────────────────
def resolve_char_image(char_name: str) -> str | None:
    candidates = [
        CHAR_IMG_DIR / f"{char_name}.png",
        CHAR_IMG_DIR / f"{normalize_char_name(char_name)}.png",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return None


# ───────────────────────────────────────────
# CSV 読み込み
# ───────────────────────────────────────────
def load_csv(vol_dir: Path) -> list:
    csv_path = vol_dir / "panels" / "comicle_output.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


# ───────────────────────────────────────────
# 旧 .png を _legacy_png/ に退避
# 対象: page_{NNN}.png かつ mtime < NEW_PNG_THRESHOLD かつ iter_なし
# ───────────────────────────────────────────
def retire_old_pngs(pages_dir: Path, logger: logging.Logger) -> int:
    legacy_dir = pages_dir / "_legacy_png"
    legacy_dir.mkdir(exist_ok=True)

    count = 0
    for f in sorted(pages_dir.glob("page_*.png")):
        # iter_付きファイルは触らない
        if "iter" in f.name:
            continue
        mtime = f.stat().st_mtime
        if mtime < NEW_PNG_THRESHOLD:
            dest = legacy_dir / f.name
            shutil.move(str(f), str(dest))
            logger.info(f"[retire] {f.name} → _legacy_png/")
            count += 1

    return count


# ───────────────────────────────────────────
# 画像生成（gpt-image-2、シンプル1回生成）
# ───────────────────────────────────────────
def generate_image(client, prompt: str, ref_paths: list, logger: logging.Logger,
                   page_num: int, dry_run: bool = False) -> bytes | None:
    """
    gpt-image-2 で1回生成。base64 デコードして返す。
    エラー時は MAX_API_RETRY 回リトライ。
    """
    if dry_run:
        logger.info(f"[dry-run] page_{page_num:03d}: prompt_len={len(prompt)}, refs={ref_paths}")
        return b"(dry-run placeholder)"

    for attempt in range(MAX_API_RETRY + 1):
        try:
            if ref_paths:
                # 参照画像あり → images.edit
                images = []
                for rp in ref_paths:
                    with open(rp, "rb") as img_f:
                        images.append(("image[]", (Path(rp).name, img_f.read(), "image/png")))

                # openai SDK の images.edit
                import io
                image_files = []
                for rp in ref_paths:
                    with open(rp, "rb") as img_f:
                        img_bytes = img_f.read()
                    image_files.append(
                        (Path(rp).name, io.BytesIO(img_bytes), "image/png")
                    )

                # SDK v1.x: images.edit(model, image=[...], prompt=..., size=..., n=1)
                response = client.images.edit(
                    model="gpt-image-2",
                    image=[
                        (name, buf, mime)
                        for name, buf, mime in image_files
                    ],
                    prompt=prompt,
                    size="1024x1536",
                    n=1,
                )
            else:
                # 参照画像なし → images.generate
                response = client.images.generate(
                    model="gpt-image-2",
                    prompt=prompt,
                    size="1024x1536",
                    quality="high",
                    n=1,
                )

            # base64 デコード
            b64_data = response.data[0].b64_json
            if b64_data:
                return base64.b64decode(b64_data)

            # URL形式の場合
            url = response.data[0].url
            if url:
                import urllib.request
                with urllib.request.urlopen(url) as resp:
                    return resp.read()

            logger.error(f"page_{page_num:03d}: No image data in response")
            return None

        except Exception as e:
            err_str = str(e)
            if attempt < MAX_API_RETRY:
                logger.warning(f"page_{page_num:03d}: API error (attempt {attempt+1}/{MAX_API_RETRY+1}): {err_str[:200]}")
                logger.info(f"page_{page_num:03d}: Retrying in {API_RETRY_SLEEP}s...")
                time.sleep(API_RETRY_SLEEP)
            else:
                logger.error(f"page_{page_num:03d}: API error (all retries exhausted): {err_str[:400]}")
                return None

    return None


# ───────────────────────────────────────────
# メイン処理
# ───────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="manga-career-restart iter_1 シンプル生成")
    parser.add_argument("--vol", default="vol1", help="対象巻 (vol1/vol2/vol3/vol4)")
    parser.add_argument("--pages", default="all", help="ページ範囲 例: 11-50, all")
    parser.add_argument("--skip-existing", action="store_true",
                        help="既存 page_{NNN}.png があればスキップ")
    parser.add_argument("--dry-run", action="store_true",
                        help="API呼び出しなし（プロンプト確認のみ）")
    parser.add_argument("--no-retire", action="store_true",
                        help="旧 .png の退避をスキップ")
    args = parser.parse_args()

    # ─── パス設定 ─────────────────────────────
    vol_dir = MANGA_DIR / args.vol
    pages_dir = vol_dir / "pages"
    log_path = vol_dir / "generation_simple.log"
    progress_path = vol_dir / "progress.json"
    cost_path = vol_dir / "cost_simple.md"

    pages_dir.mkdir(parents=True, exist_ok=True)

    logger = setup_logging(log_path)
    logger.info("=" * 60)
    logger.info(f"generate_simple.py 開始: vol={args.vol}, pages={args.pages}, "
                f"skip-existing={args.skip_existing}, dry-run={args.dry_run}")
    logger.info("=" * 60)

    # ─── API キー確認 ─────────────────────────
    if not args.dry_run:
        api_key = load_api_key()
        if not api_key:
            logger.error("OPENAI_API_KEY が未設定です。処理を中断します。")
            sys.exit(1)
        logger.info("OPENAI_API_KEY: 取得済み")

        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    else:
        client = None

    # ─── character_defs.json 読み込み ──────────
    char_defs = {}
    if CHAR_DEFS_PATH.exists():
        with open(CHAR_DEFS_PATH, encoding="utf-8") as f:
            char_defs = json.load(f)
        logger.info(f"character_defs: {list(char_defs.keys())}")
    else:
        logger.warning(f"character_defs.json が見つかりません: {CHAR_DEFS_PATH}")

    # ─── CSV 読み込み ─────────────────────────
    rows = load_csv(vol_dir)
    logger.info(f"CSV: {len(rows)} ページ読み込み")

    # ─── ページ範囲フィルタ ───────────────────
    if args.pages == "all":
        page_range = None  # 全ページ
    else:
        # "11-50" 形式
        parts = args.pages.split("-")
        if len(parts) == 2:
            page_range = (int(parts[0]), int(parts[1]))
        elif len(parts) == 1:
            n = int(parts[0])
            page_range = (n, n)
        else:
            logger.error(f"--pages 引数が不正です: {args.pages}")
            sys.exit(1)

    # ─── ステップA/B: 旧 .png 退避 ───────────
    retired_png_count = 0
    if not args.no_retire and not args.dry_run:
        logger.info("[ステップB/C] 旧 .png を _legacy_png/ に退避中...")
        retired_png_count = retire_old_pngs(pages_dir, logger)
        logger.info(f"[ステップB/C] 退避完了: {retired_png_count} 件")
    else:
        logger.info("[ステップB/C] 退避スキップ")

    # ─── 統計カウンタ ─────────────────────────
    stats = {
        "completed": [],
        "skipped_text": [],
        "skipped_existing": [],
        "failed": [],
        "total_cost_usd": 0.0,
    }

    start_time = time.time()
    consecutive_errors = 0

    # ─── ページ処理ループ ─────────────────────
    for row_idx, row in enumerate(rows):
        page_num = int(row["ページ番号"])
        template = row["使用するコマ割りテンプレ"]
        prompt_text = row["漫画作成のプロンプト"]

        # ページ範囲フィルタ
        if page_range and not (page_range[0] <= page_num <= page_range[1]):
            continue

        # ─── テキストページ判定（スキップ）
        if template == "テキストページ":
            logger.info(f"[skip/text] page_{page_num:03d}: テキストページのためスキップ")
            stats["skipped_text"].append(page_num)
            continue

        # ─── 既存 .png スキップ判定
        out_path = pages_dir / f"page_{page_num:03d}.png"
        if args.skip_existing and out_path.exists():
            logger.info(f"[skip/exist] page_{page_num:03d}: 既存 .png があるためスキップ")
            stats["skipped_existing"].append(page_num)
            continue

        # ─── プロンプトからキャラ名抽出・参照画像解決
        char_names = extract_char_names_from_prompt(prompt_text)
        ref_paths = []
        for cname in char_names:
            img_path = resolve_char_image(cname)
            if img_path:
                ref_paths.append(img_path)
                logger.debug(f"  [ref] {cname} → {img_path}")
            else:
                logger.warning(f"  [warn] page_{page_num:03d}: 参照画像が見つかりません: {cname}")

        logger.info(f"[gen] page_{page_num:03d}: 生成開始 (refs={[Path(p).name for p in ref_paths]})")

        # ─── 画像生成
        t0 = time.time()
        img_bytes = generate_image(
            client=client,
            prompt=prompt_text,
            ref_paths=ref_paths,
            logger=logger,
            page_num=page_num,
            dry_run=args.dry_run,
        )
        elapsed = time.time() - t0

        if img_bytes is None:
            logger.error(f"[fail] page_{page_num:03d}: 生成失敗")
            stats["failed"].append({"page": page_num, "reason": "api_error"})
            consecutive_errors += 1
            if consecutive_errors >= 3:
                logger.error("API エラーが3連続で発生しました。処理を中断します。")
                break
            continue

        consecutive_errors = 0

        # ─── 保存
        if not args.dry_run:
            with open(out_path, "wb") as f:
                f.write(img_bytes)
            size_kb = len(img_bytes) / 1024
            logger.info(f"[gen] page_{page_num:03d}: done ({size_kb:.0f}KB, {elapsed:.1f}s)")
        else:
            logger.info(f"[dry-run] page_{page_num:03d}: 処理完了 ({elapsed:.1f}s)")

        stats["completed"].append(page_num)
        stats["total_cost_usd"] += COST_PER_IMAGE

        # コスト上限チェック
        if stats["total_cost_usd"] >= COST_LIMIT_TOTAL:
            logger.error(f"コスト上限 ${COST_LIMIT_TOTAL} に達しました。処理を中断します。"
                         f"(現在: ${stats['total_cost_usd']:.2f})")
            break

        # ─── API インターバル（最後のページ以外）
        if row_idx < len(rows) - 1 and not args.dry_run:
            time.sleep(API_CALL_INTERVAL)

    # ─── 処理完了 ─────────────────────────────
    total_elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info(f"処理完了: elapsed={total_elapsed:.0f}s")
    logger.info(f"  生成成功: {len(stats['completed'])} ページ")
    logger.info(f"  スキップ(テキスト): {len(stats['skipped_text'])} ページ {stats['skipped_text']}")
    logger.info(f"  スキップ(既存): {len(stats['skipped_existing'])} ページ")
    logger.info(f"  失敗: {len(stats['failed'])} ページ {[f['page'] for f in stats['failed']]}")
    logger.info(f"  推定コスト: ${stats['total_cost_usd']:.2f}")
    logger.info(f"  退避済み旧 .png: {retired_png_count} 件")
    logger.info("=" * 60)

    # ─── progress.json 更新 ──────────────────
    if not args.dry_run:
        try:
            if progress_path.exists():
                with open(progress_path, encoding="utf-8") as f:
                    progress_data = json.load(f)
            else:
                progress_data = {}

            progress_data["5_images_simple"] = {
                "completed": stats["completed"],
                "total_image_pages": len(stats["completed"]) + len(stats["failed"]),
                "skipped_text_pages": stats["skipped_text"],
                "skipped_existing": stats["skipped_existing"],
                "failed": stats["failed"],
                "estimated_cost_usd": round(stats["total_cost_usd"], 2),
                "elapsed_seconds": round(total_elapsed),
                "updated_at": datetime.now().isoformat(),
            }

            with open(progress_path, "w", encoding="utf-8") as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
            logger.info(f"progress.json 更新: {progress_path}")
        except Exception as e:
            logger.warning(f"progress.json 更新失敗: {e}")

    # ─── cost_simple.md 記録 ────────────────
    if not args.dry_run:
        try:
            cost_lines = [
                f"# cost_simple.md - generate_simple.py コスト記録",
                f"",
                f"更新日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"",
                f"## 単価",
                f"- gpt-image-2 high 1024x1536: ${COST_PER_IMAGE}/枚",
                f"",
                f"## 実績",
                f"- 生成成功枚数: {len(stats['completed'])} 枚",
                f"- 推定合計コスト: ${stats['total_cost_usd']:.2f}",
                f"- 所要時間: {total_elapsed:.0f}s",
                f"",
                f"## 生成済みページ一覧",
                f"- {sorted(stats['completed'])}",
            ]
            with open(cost_path, "w", encoding="utf-8") as f:
                f.write("\n".join(cost_lines) + "\n")
            logger.info(f"cost_simple.md 記録: {cost_path}")
        except Exception as e:
            logger.warning(f"cost_simple.md 記録失敗: {e}")

    # ─── 終了コード ──────────────────────────
    if stats["failed"]:
        sys.exit(2)  # 一部失敗
    sys.exit(0)


if __name__ == "__main__":
    main()

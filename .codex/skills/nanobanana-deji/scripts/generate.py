#!/usr/bin/env python3
"""
nanobanana2 — Gemini API直接呼び出しによる画像生成
モデル: gemini-3.1-flash-image-preview (固定)
透かしなし・APIキー認証・高品質

Usage:
    python scripts/generate.py --prompt "..." --output out.png
    python scripts/generate.py --prompt "..." --output out.png --size 1920x1080
    python scripts/generate.py --prompt "..." --output out.png --aspect landscape

Environment:
    GEMINI_API_KEY  — .env または環境変数
    GEMINI_IMAGE_MODEL — (任意) デフォルト: gemini-3.1-flash-image-preview
"""

import argparse
import os
import sys
from pathlib import Path

# .env 読み込み
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

# 必須モデル名（絶対に変更しない）
REQUIRED_MODEL = "gemini-3.1-flash-image-preview"


def parse_args():
    parser = argparse.ArgumentParser(description="nanobanana2 — Gemini API image generation")
    parser.add_argument("--prompt", required=True, help="画像生成プロンプト（英語推奨）")
    parser.add_argument("--output", default="output/generated.png", help="出力ファイルパス")
    parser.add_argument(
        "--aspect",
        choices=["square", "landscape", "portrait", "wide"],
        default="landscape",
        help="アスペクト比 (square=1:1, landscape=16:9, portrait=9:16, wide=21:9)",
    )
    parser.add_argument("--negative", default="", help="ネガティブプロンプト（避けたい要素）")
    parser.add_argument("--style", default="", help="スタイル指定（例: flat design, 3D, infographic）")
    parser.add_argument("--debug", action="store_true", help="デバッグ出力を有効化")
    return parser.parse_args()


def build_prompt(prompt: str, style: str, negative: str, aspect: str) -> str:
    """プロンプトにスタイル・品質指定を追加"""
    parts = [prompt.strip()]

    if style:
        parts.append(style.strip())

    # アスペクト比に応じたヒント
    aspect_hints = {
        "landscape": "horizontal composition, 16:9 ratio",
        "portrait": "vertical composition, 9:16 ratio",
        "wide": "ultra-wide cinematic composition, 21:9 ratio",
        "square": "square composition, 1:1 ratio",
    }
    if aspect in aspect_hints:
        parts.append(aspect_hints[aspect])

    # 品質強化
    parts.append("high quality, crisp, professional")

    if negative:
        parts.append(f"avoid: {negative}")

    return ", ".join(p for p in parts if p)


def generate_image(prompt: str, output_path: str, debug: bool = False) -> bool:
    """Gemini APIで画像生成"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY が設定されていません。.env ファイルを確認してください。", file=sys.stderr)
        return False

    model = os.getenv("GEMINI_IMAGE_MODEL", REQUIRED_MODEL)
    if model != REQUIRED_MODEL:
        print(f"[WARNING] .envのGEMINI_IMAGE_MODELが '{model}' ですが、'{REQUIRED_MODEL}' に上書きします。")
        model = REQUIRED_MODEL

    if debug:
        print(f"[DEBUG] Model: {model}")
        print(f"[DEBUG] Prompt: {prompt[:100]}...")
        print(f"[DEBUG] Output: {output_path}")

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("[ERROR] google-genai が未インストールです。`pip install google-genai` を実行してください。", file=sys.stderr)
        return False

    client = genai.Client(api_key=api_key)

    print(f"[nanobanana2] 画像生成中... (model: {model})")
    print(f"[nanobanana2] プロンプト: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )
    except Exception as e:
        print(f"[ERROR] API呼び出し失敗: {e}", file=sys.stderr)
        if "404" in str(e):
            print(f"[ERROR] モデル '{model}' が見つかりません。APIキーの権限または地域制限を確認してください。", file=sys.stderr)
        return False

    # 画像データを取得
    image_data = None
    for candidate in response.candidates:
        for part in candidate.content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                image_data = part.inline_data.data
                break
        if image_data:
            break

    if not image_data:
        print("[ERROR] 画像データが返されませんでした。プロンプトを見直してください。", file=sys.stderr)
        # テキスト応答があれば表示
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if part.text:
                    print(f"[INFO] Geminiの応答: {part.text}", file=sys.stderr)
        return False

    # 保存
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    with open(out, "wb") as f:
        f.write(image_data)

    size_kb = out.stat().st_size // 1024
    print(f"[nanobanana2] 保存完了: {out} ({size_kb} KB)")
    return True


def main():
    args = parse_args()

    prompt = build_prompt(args.prompt, args.style, args.negative, args.aspect)
    success = generate_image(prompt, args.output, args.debug)

    if not success:
        sys.exit(1)

    print(f"[nanobanana2] 完了: {args.output}")


if __name__ == "__main__":
    main()

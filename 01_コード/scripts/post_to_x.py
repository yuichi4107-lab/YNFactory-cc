import sys
import os
import argparse
import json
import re
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args, **_kwargs):
        return False

ENV_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    ".company",
    "engineering",
    "sns-credentials",
    ".env",
)
load_dotenv(ENV_PATH)


def get_client():
    import tweepy

    return tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_KEY_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET"),
    )


def get_api_v1():
    import tweepy

    auth = tweepy.OAuth1UserHandler(
        os.getenv("X_API_KEY"),
        os.getenv("X_API_KEY_SECRET"),
        os.getenv("X_ACCESS_TOKEN"),
        os.getenv("X_ACCESS_TOKEN_SECRET"),
    )
    return tweepy.API(auth)


def upload_video(video_path: str, timeout_sec: int = 300):
    """動画をチャンクアップロードし、処理完了を待って media_id を返す。"""
    import time

    api_v1 = get_api_v1()
    media = api_v1.media_upload(
        filename=video_path,
        chunked=True,
        media_category="tweet_video",
    )
    # 非同期処理の完了待ち（tweepyが待ち切らないケースに備えて明示ポーリング）
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        info = getattr(media, "processing_info", None)
        if not info or info.get("state") == "succeeded":
            return media.media_id
        if info.get("state") == "failed":
            raise RuntimeError(f"X動画処理失敗: {info.get('error')}")
        time.sleep(info.get("check_after_secs", 5))
        media = api_v1.get_media_upload_status(media.media_id)
    raise TimeoutError("X動画処理がタイムアウトしました")


def post(text: str, image_path: str = None, video_path: str = None) -> str:
    client = get_client()
    media_ids = None

    if video_path:
        media_ids = [upload_video(video_path)]
    elif image_path:
        api_v1 = get_api_v1()
        media = api_v1.media_upload(filename=image_path)
        media_ids = [media.media_id]

    response = client.create_tweet(text=text, media_ids=media_ids)
    tweet_id = response.data["id"]
    return f"https://x.com/i/status/{tweet_id}"


def dry_run(text: str, image_path: str = None, video_path: str = None) -> dict:
    blockers = []
    warnings = ["dry-runのため実投稿しません"]

    if not text.strip():
        blockers.append("投稿本文が空です")
    if len(text) > 280:
        blockers.append(f"文字数上限を超えています ({len(text)}/280)")

    placeholders = sorted(set(re.findall(r"\{[A-Z0-9_]+\}", text)))
    if placeholders:
        blockers.append(f"未解決プレースホルダーがあります: {', '.join(placeholders)}")

    resolved_image = None
    if image_path:
        resolved_image = Path(image_path).expanduser()
        if not resolved_image.exists():
            blockers.append(f"画像ファイルが見つかりません: {resolved_image}")

    resolved_video = None
    if video_path:
        resolved_video = Path(video_path).expanduser()
        if not resolved_video.exists():
            blockers.append(f"動画ファイルが見つかりません: {resolved_video}")
        elif resolved_video.suffix.lower() != ".mp4":
            blockers.append("動画はmp4のみ対応です")
        elif resolved_video.stat().st_size > 512 * 1024 * 1024:
            blockers.append("動画サイズが512MBを超えています")
        if image_path:
            warnings.append("--image と --video の同時指定は動画を優先します")

    return {
        "platform": "x",
        "mode": "dry-run",
        "status": "blocked" if blockers else "ready_for_review",
        "would_post": False,
        "tokens_read": False,
        "api_called": False,
        "text_length": len(text),
        "text_limit": 280,
        "has_image": bool(image_path),
        "image_path": str(resolved_image) if resolved_image else None,
        "has_video": bool(video_path),
        "video_path": str(resolved_video) if resolved_video else None,
        "blockers": blockers,
        "warnings": warnings,
        "preview": text,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post to X (Twitter)")
    parser.add_argument("text", help="Tweet text")
    parser.add_argument("--image", help="Path to image file", default=None)
    parser.add_argument("--video", help="Path to mp4 video file", default=None)
    parser.add_argument("--dry-run", action="store_true", help="Validate without posting")
    args = parser.parse_args()

    if args.dry_run:
        print(json.dumps(dry_run(args.text, args.image, args.video), ensure_ascii=False, indent=2))
    else:
        url = post(args.text, args.image, args.video)
        print(f"Posted: {url}")

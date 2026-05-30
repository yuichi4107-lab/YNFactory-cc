import sys
import os
import argparse
import tweepy
from dotenv import load_dotenv

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
    return tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_KEY_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET"),
    )


def get_api_v1():
    auth = tweepy.OAuth1UserHandler(
        os.getenv("X_API_KEY"),
        os.getenv("X_API_KEY_SECRET"),
        os.getenv("X_ACCESS_TOKEN"),
        os.getenv("X_ACCESS_TOKEN_SECRET"),
    )
    return tweepy.API(auth)


def post(text: str, image_path: str = None) -> str:
    client = get_client()
    media_ids = None

    if image_path:
        api_v1 = get_api_v1()
        media = api_v1.media_upload(filename=image_path)
        media_ids = [media.media_id]

    response = client.create_tweet(text=text, media_ids=media_ids)
    tweet_id = response.data["id"]
    return f"https://x.com/i/status/{tweet_id}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post to X (Twitter)")
    parser.add_argument("text", help="Tweet text")
    parser.add_argument("--image", help="Path to image file", default=None)
    args = parser.parse_args()

    url = post(args.text, args.image)
    print(f"Posted: {url}")

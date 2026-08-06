"""楽天ウェブサービス(公式API)を使った補充候補の選定。

従来のランキングページ・スクレイピング(上位から順に採用)と違い、
公式ランキングAPIからレビュー・価格・料率付きでデータを取り、
「順位 + 急上昇 + レビュー + 価格帯 + 期待報酬」でスコアリングして
売れる見込みの高い順に候補を返す。

急上昇検出のため、実行ごとのランキングを root_dir/data/ranking_snapshots.json に
保存し、前回スナップショットとの順位差を見る(毎日実行すると精度が上がる)。

認証情報は環境変数(~/rakuten-room-auto/.env に置ける):
  RAKUTEN_APP_ID          楽天ウェブサービスのアプリID
  RAKUTEN_ACCESS_KEY      アクセスキー (pk_...)
  RAKUTEN_ALLOWED_DOMAIN  「許可されたWebサイト」に登録したドメイン (既定 example.com)
未設定の場合は selection を使わず、従来のブラウザ方式にフォールバックする。
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

RANKING_API_URL = "https://openapi.rakuten.co.jp/ichibaranking/api/IchibaItem/Ranking/20220601"
GENRE_ID_PATTERN = re.compile(r"/daily/(\d+)")
REQUEST_INTERVAL_SEC = 1.0
PAGES_PER_GENRE = 2  # 30件/ページ
SNAPSHOT_KEEP_DAYS = 14

_last_request_at = 0.0


class SelectionError(RuntimeError):
    pass


def api_credentials_available() -> bool:
    return bool(os.environ.get("RAKUTEN_APP_ID") and os.environ.get("RAKUTEN_ACCESS_KEY"))


def genre_ids_from_urls(ranking_urls) -> list[str]:
    """config の ranking_urls (https://ranking.rakuten.co.jp/daily/<genreId>/) からジャンルIDを取り出す。"""
    ids = []
    for url in ranking_urls:
        match = GENRE_ID_PATTERN.search(url)
        if match and match.group(1) not in ids:
            ids.append(match.group(1))
    return ids


def plain_item_url(item_url: str) -> str:
    """アフィリエイトパラメータ等を除いた素の商品URLにする(ROOM投稿はROOM側で成果紐付けされる)。"""
    parsed = urllib.parse.urlsplit(item_url)
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def fetch_ranking_page(genre_id: str, page: int) -> list[dict]:
    global _last_request_at
    wait = REQUEST_INTERVAL_SEC - (time.time() - _last_request_at)
    if wait > 0:
        time.sleep(wait)
    domain = os.environ.get("RAKUTEN_ALLOWED_DOMAIN", "example.com")
    query = urllib.parse.urlencode(
        {
            "applicationId": os.environ["RAKUTEN_APP_ID"],
            "accessKey": os.environ["RAKUTEN_ACCESS_KEY"],
            "format": "json",
            "genreId": genre_id,
            "page": page,
        }
    )
    request = urllib.request.Request(
        f"{RANKING_API_URL}?{query}",
        headers={
            "Referer": f"https://{domain}/",
            "Origin": f"https://{domain}",
            "User-Agent": "rakuten-room-auto/1.0",
        },
    )
    _last_request_at = time.time()
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # HTTPError含む。呼び出し側でフォールバック判断する
        raise SelectionError(f"ランキングAPIの取得に失敗しました: {exc}") from exc
    return [row.get("Item", row) for row in data.get("Items", [])]


def load_snapshots(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_snapshot(path: Path, snapshots: dict, today: str, ranks: dict) -> None:
    snapshots[today] = ranks
    for old_date in sorted(snapshots)[:-SNAPSHOT_KEEP_DAYS]:
        del snapshots[old_date]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshots, ensure_ascii=False), encoding="utf-8")


def previous_ranks(snapshots: dict, today: str) -> dict:
    past_dates = [d for d in sorted(snapshots) if d < today]
    return snapshots[past_dates[-1]] if past_dates else {}


def _price_fit(price: int) -> float:
    """ROOMの投稿実績で反応が良い価格帯(1000〜9999円)を優遇する。"""
    if 1000 <= price < 10000:
        return 1.0
    if price < 1000:
        return 0.6
    if price < 20000:
        return 0.7
    return 0.4


def score_item(item: dict, prev: dict, item_key: str, has_history: bool) -> tuple[float, bool]:
    """スコアと急上昇フラグを返す。"""
    rank = int(item.get("rank") or 90)
    price = int(item.get("itemPrice") or 0)
    review_count = int(item.get("reviewCount") or 0)
    review_average = float(item.get("reviewAverage") or 0)
    affiliate_rate = float(item.get("affiliateRate") or 0)

    rank_score = max(0.0, (91 - rank) / 90)
    review_score = min(review_count, 1000) / 1000 * (review_average / 5 if review_average else 0.5)
    if 0 < review_average < 4.0:  # 低評価商品の紹介はフォロワーの信頼を損なう
        review_score *= 0.3
    reward_score = min(price * affiliate_rate / 100, 500) / 500

    prev_rank = prev.get(item_key)
    is_surge = False
    if prev_rank is None:
        surge_score = 0.6 if has_history else 0.0  # 履歴があるのに前回圏外→新規ランクイン
    elif prev_rank - rank >= 10:
        surge_score, is_surge = 1.0, True
    elif prev_rank > rank:
        surge_score = 0.3
    else:
        surge_score = 0.0

    total = (
        0.30 * rank_score
        + 0.25 * review_score
        + 0.15 * _price_fit(price)
        + 0.15 * reward_score
        + 0.15 * surge_score
    )
    return total, is_surge


def fetch_scored_candidates(genre_ids, data_dir: Path, today: str | None = None) -> list[dict]:
    """全対象ジャンルのランキングを取得し、スコア降順の候補リストを返す。

    返り値の各要素: {"url", "title", "review_count", "review_average", "surge", "score"}
    """
    today = today or date.today().isoformat()
    snapshot_path = Path(data_dir) / "ranking_snapshots.json"
    snapshots = load_snapshots(snapshot_path)
    prev = previous_ranks(snapshots, today)

    items: list[tuple[str, dict]] = []
    for genre_id in genre_ids:
        for page in range(1, PAGES_PER_GENRE + 1):
            for item in fetch_ranking_page(genre_id, page):
                key = f"{genre_id}:{item.get('itemCode') or plain_item_url(item.get('itemUrl') or '')}"
                items.append((key, item))

    if not items:
        raise SelectionError("ランキングAPIから商品を1件も取得できませんでした。")

    save_snapshot(snapshot_path, snapshots, today, {key: int(it.get("rank") or 0) for key, it in items})

    seen_urls: set[str] = set()
    candidates = []
    for key, item in items:
        url = plain_item_url(item.get("itemUrl") or "")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        score, is_surge = score_item(item, prev, key, has_history=bool(prev))
        candidates.append(
            {
                "url": url,
                "title": item.get("itemName") or "",
                "review_count": int(item.get("reviewCount") or 0),
                "review_average": float(item.get("reviewAverage") or 0),
                "surge": is_surge,
                "score": score,
            }
        )
    candidates.sort(key=lambda c: -c["score"])
    return candidates

from __future__ import annotations

from rakuten_room_auto import selection
from rakuten_room_auto.selection import (
    fetch_scored_candidates,
    genre_ids_from_urls,
    load_snapshots,
    plain_item_url,
    previous_ranks,
    save_snapshot,
    score_item,
)


def test_genre_ids_from_urls_extracts_and_dedupes():
    urls = [
        "https://ranking.rakuten.co.jp/daily/100804/",
        "https://ranking.rakuten.co.jp/daily/215783/",
        "https://ranking.rakuten.co.jp/daily/100804/",
        "https://example.com/not-a-ranking-url",
    ]
    assert genre_ids_from_urls(urls) == ["100804", "215783"]


def test_plain_item_url_strips_query_and_fragment():
    url = "https://item.rakuten.co.jp/shop/item01/?rafcid=abc&scid=xyz#review"
    assert plain_item_url(url) == "https://item.rakuten.co.jp/shop/item01/"


def make_item(rank=1, price=3000, review_count=500, review_average=4.5, affiliate_rate=3.0):
    return {
        "rank": rank,
        "itemPrice": price,
        "reviewCount": review_count,
        "reviewAverage": review_average,
        "affiliateRate": affiliate_rate,
    }


def test_score_item_detects_surge():
    item = make_item(rank=5)
    prev = {"g:item": 30}
    score, is_surge = score_item(item, prev, "g:item", has_history=True)
    assert is_surge
    assert score > 0


def test_score_item_prefers_better_reviews():
    prev: dict = {}
    good, _ = score_item(make_item(review_count=1000, review_average=4.8), prev, "a", has_history=False)
    poor, _ = score_item(make_item(review_count=1000, review_average=3.0), prev, "b", has_history=False)
    assert good > poor


def test_snapshot_roundtrip_and_pruning(tmp_path):
    path = tmp_path / "ranking_snapshots.json"
    snapshots = load_snapshots(path)
    assert snapshots == {}
    for day in range(1, 20):
        save_snapshot(path, snapshots, f"2026-07-{day:02d}", {"g:item": day})
    stored = load_snapshots(path)
    assert len(stored) == selection.SNAPSHOT_KEEP_DAYS
    assert "2026-07-01" not in stored
    prev = previous_ranks(stored, "2026-07-19")
    assert prev == {"g:item": 18}


def test_fetch_scored_candidates_sorts_and_dedupes(tmp_path, monkeypatch):
    pages = {
        ("100", 1): [
            {
                "rank": 1,
                "itemCode": "shop:a",
                "itemUrl": "https://item.rakuten.co.jp/shop/a/?scid=x",
                "itemName": "商品A",
                "itemPrice": 3000,
                "reviewCount": 900,
                "reviewAverage": 4.6,
                "affiliateRate": 3.0,
            },
            {
                "rank": 2,
                "itemCode": "shop:b",
                "itemUrl": "https://item.rakuten.co.jp/shop/b/",
                "itemName": "商品B",
                "itemPrice": 50,
                "reviewCount": 0,
                "reviewAverage": 0,
                "affiliateRate": 2.0,
            },
        ],
        ("100", 2): [
            {
                # 別ジャンルページに同一商品が再登場しても1件にまとまる
                "rank": 40,
                "itemCode": "shop:a",
                "itemUrl": "https://item.rakuten.co.jp/shop/a/",
                "itemName": "商品A",
                "itemPrice": 3000,
                "reviewCount": 900,
                "reviewAverage": 4.6,
                "affiliateRate": 3.0,
            }
        ],
    }
    monkeypatch.setattr(selection, "fetch_ranking_page", lambda genre_id, page: pages.get((genre_id, page), []))
    candidates = fetch_scored_candidates(["100"], tmp_path, today="2026-08-06")
    urls = [c["url"] for c in candidates]
    assert urls == ["https://item.rakuten.co.jp/shop/a/", "https://item.rakuten.co.jp/shop/b/"]
    assert candidates[0]["score"] > candidates[1]["score"]
    # スナップショットが保存されている
    assert (tmp_path / "ranking_snapshots.json").exists()

"""GMOコイン公開APIから BTC_JPY の日足を取得し、スナップショットとして保存する。

MVP-0 S0 用。依存は標準ライブラリのみ。
取得したデータは data/ohlcv_btc_jpy.json に保存し、以後の検証はこのファイルだけを読む
（提供元が変更・削除しても過去の検証を再現できるようにするため）。
"""
import json
import os
import ssl
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone

BASE = "https://api.coin.z.com/public/v1/klines"
SYMBOL = "BTC_JPY"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "ohlcv_btc_jpy.json")
JST = timezone(timedelta(hours=9))


def fetch_year(year):
    url = f"{BASE}?symbol={SYMBOL}&priceType=ASK&interval=1day&date={year}"
    req = urllib.request.Request(url, headers={"User-Agent": "mmat-mvp0/0.1"})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
        body = json.loads(r.read().decode())
    if body.get("status") != 0:
        raise RuntimeError(f"{year}: status={body.get('status')} messages={body.get('messages')}")
    return body.get("data") or []


def to_bar(raw):
    """openTime(ms) を JST の日付ラベルに変換する。

    GMOの日足は 06:00 JST 始まり。そのバーが始まった日を日付ラベルとする。
    """
    ts = int(raw["openTime"]) / 1000
    d = datetime.fromtimestamp(ts, JST)
    return {
        "date": d.strftime("%Y-%m-%d"),
        "open": float(raw["open"]),
        "high": float(raw["high"]),
        "low": float(raw["low"]),
        "close": float(raw["close"]),
        "volume": float(raw["volume"]),
    }


def main():
    start_year = 2018
    end_year = datetime.now(JST).year
    bars = []
    for year in range(start_year, end_year + 1):
        try:
            raw = fetch_year(year)
        except Exception as e:
            print(f"  {year}: 取得失敗 {e}", file=sys.stderr)
            continue
        got = [to_bar(x) for x in raw]
        bars.extend(got)
        print(f"  {year}: {len(got)}本")
        time.sleep(0.3)

    # 日付で一意化して昇順に
    seen = {}
    for b in bars:
        seen[b["date"]] = b
    bars = [seen[k] for k in sorted(seen)]

    snapshot = {
        "source": "GMO Coin public API /public/v1/klines",
        "symbol": SYMBOL,
        "interval": "1day",
        "price_type": "ASK",
        "fetched_at": datetime.now(JST).isoformat(),
        "bar_boundary": "06:00 JST",
        "count": len(bars),
        "first": bars[0]["date"] if bars else None,
        "last": bars[-1]["date"] if bars else None,
        "bars": bars,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(snapshot, f, ensure_ascii=False, separators=(",", ":"))
    print(f"保存: {len(bars)}本 / {snapshot['first']} 〜 {snapshot['last']}")


if __name__ == "__main__":
    main()

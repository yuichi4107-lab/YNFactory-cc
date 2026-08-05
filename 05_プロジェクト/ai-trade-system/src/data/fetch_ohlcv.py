"""
ステップ1-1: ビットコインのローソク足データを取得して保存する
"""
import ccxt
import pandas as pd
import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "../../data/ohlcv")


def fetch_ohlcv(
    symbol="BTC/USDT",
    timeframe="4h",
    limit=1000,
    exchange_id="binance",
):
    """
    取引所からOHLCVデータを取得してCSV/JSONで保存する。

    Args:
        symbol: 通貨ペア
        timeframe: 時間足 (1m, 5m, 15m, 1h, 4h, 1d)
        limit: 取得するローソク足の本数
        exchange_id: 取引所ID
    Returns:
        pandas DataFrame
    """
    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class({"enableRateLimit": True})

    print(f"Fetching {symbol} {timeframe} x {limit} from {exchange_id}...")
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df[["datetime", "timestamp", "open", "high", "low", "close", "volume"]]

    # 保存
    os.makedirs(DATA_DIR, exist_ok=True)
    safe_symbol = symbol.replace("/", "-")
    filename = f"{safe_symbol}_{timeframe}_{len(df)}"

    csv_path = os.path.join(DATA_DIR, f"{filename}.csv")
    df.to_csv(csv_path, index=False)
    print(f"Saved CSV: {csv_path}")

    json_path = os.path.join(DATA_DIR, f"{filename}.json")
    records = df.copy()
    records["datetime"] = records["datetime"].astype(str)
    records.to_json(json_path, orient="records", indent=2)
    print(f"Saved JSON: {json_path}")

    print(f"Done: {len(df)} candles from {df['datetime'].iloc[0]} to {df['datetime'].iloc[-1]}")
    return df


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch OHLCV data")
    parser.add_argument("--symbol", default="BTC/USDT", help="Trading pair")
    parser.add_argument("--timeframe", default="4h", help="Timeframe (1m,5m,15m,1h,4h,1d)")
    parser.add_argument("--limit", type=int, default=1000, help="Number of candles")
    parser.add_argument("--exchange", default="binance", help="Exchange ID")
    args = parser.parse_args()

    fetch_ohlcv(args.symbol, args.timeframe, args.limit, args.exchange)

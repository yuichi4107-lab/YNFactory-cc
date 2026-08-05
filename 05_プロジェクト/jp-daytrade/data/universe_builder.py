"""
ユニバース候補リスト生成

銘柄マスター DB から翌日のデイトレ対象ユニバース（候補銘柄リスト）を生成する。

フィルター条件:
    1. 値嵩除外: 株価 > 3,000円 または 単元代金 > 300,000円 → 除外
    2. 市場フィルター: デフォルトは東証グロース市場
    3. 直近ボラティリティ: 直近5日日中値幅率 ≥ 5%（オプション）

Example:
    >>> from jp_daytrade.data.universe_builder import build_universe
    >>> candidates = build_universe(market="growth", exclude_value_stock=True)
    >>> print(len(candidates))
"""

import logging
import os
import sqlite3
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# デフォルトパス
DEFAULT_MASTER_DB = os.path.join(os.path.dirname(__file__), "stocks_master.db")
DEFAULT_PRICES_DB = os.path.join(os.path.dirname(__file__), "daily_prices.db")

# 値嵩株フィルター定数
VALUE_STOCK_PRICE_THRESHOLD = 3000      # 株価閾値（円）
VALUE_STOCK_UNIT_VALUE_THRESHOLD = 300000  # 単元代金閾値（円）

# ボラティリティフィルター定数
DEFAULT_VOLATILITY_DAYS = 5
DEFAULT_VOLATILITY_MIN_PCT = 5.0  # 最低日中値幅率 (%)

# 市場コードマッピング
MARKET_MAP = {
    "growth": "グロース",
    "prime":  "プライム",
    "standard": "スタンダード",
    "all": None,  # 全市場
}


def is_value_stock(price: float, unit_shares: int) -> bool:
    """
    値嵩株判定。

    条件: 株価 > 3,000円 OR 単元代金（株価 × 単元株数）> 300,000円

    Args:
        price:       株価（円）
        unit_shares: 単元株数（例: 100）

    Returns:
        True = 値嵩株（除外対象）、False = 対象銘柄

    Example:
        >>> is_value_stock(2999, 100)
        False
        >>> is_value_stock(3001, 100)
        True
        >>> is_value_stock(1500, 200)  # 単元代金 300,000円
        False
        >>> is_value_stock(1500, 201)  # 単元代金 301,500円 > 300,000円
        True
    """
    unit_value = price * unit_shares
    return price > VALUE_STOCK_PRICE_THRESHOLD or unit_value > VALUE_STOCK_UNIT_VALUE_THRESHOLD


def calculate_volatility(
    db_path: str,
    code: str,
    days: int = DEFAULT_VOLATILITY_DAYS,
    as_of: Optional[str] = None,
) -> Optional[float]:
    """
    指定銘柄の直近 N 日間の平均日中値幅率を算出する。

    日中値幅率 = (high - low) / close * 100

    Args:
        db_path: daily_prices.db パス
        code:    銘柄コード
        days:    集計日数（デフォルト 5 日）
        as_of:   基準日 (YYYY-MM-DD, 省略時は今日)

    Returns:
        平均日中値幅率 (%) または None（データ不足の場合）

    Example:
        >>> vol = calculate_volatility("daily_prices.db", "7203", days=5)
        >>> print(f"{vol:.1f}%") if vol else print("N/A")
    """
    as_of = as_of or date.today().isoformat()

    if not os.path.exists(db_path):
        logger.warning("daily_prices.db が存在しません: %s", db_path)
        return None

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """SELECT high, low, close
               FROM daily_prices
               WHERE code = ? AND date <= ?
               ORDER BY date DESC
               LIMIT ?""",
            (code, as_of, days),
        ).fetchall()

    if len(rows) < days:
        logger.debug("Insufficient data for %s: %d < %d rows", code, len(rows), days)
        return None

    volatilities = []
    for high, low, close in rows:
        if close and close > 0 and high and low:
            volatilities.append((high - low) / close * 100)

    if not volatilities:
        return None

    return sum(volatilities) / len(volatilities)


def build_universe(
    market: str = "growth",
    exclude_value_stock: bool = True,
    min_volatility_pct: Optional[float] = None,
    master_db: str = DEFAULT_MASTER_DB,
    prices_db: str = DEFAULT_PRICES_DB,
    as_of: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    翌日のデイトレ対象ユニバース候補リストを生成する。

    Args:
        market:              市場フィルター ("growth", "prime", "standard", "all")
        exclude_value_stock: True のとき値嵩株を除外
        min_volatility_pct:  最低日中値幅率 (%). None の場合はチェックなし
        master_db:           stocks_master.db パス
        prices_db:           daily_prices.db パス（ボラ計算に使用）
        as_of:               基準日 (YYYY-MM-DD)

    Returns:
        候補銘柄リスト。各要素は以下の dict::

            {
                "code": "7203",
                "name": "トヨタ自動車",
                "market": "グロース",
                "market_cap": 42_000_000_000_000,
                "last_price": 2500.0,
                "unit_shares": 100,
                "is_value_stock": False,
                "volatility_5d_pct": 5.2,  # min_volatility_pct 指定時のみ
            }

    Raises:
        FileNotFoundError: master_db が存在しない場合

    Example:
        >>> candidates = build_universe(market="growth", exclude_value_stock=True)
        >>> assert all(not c["is_value_stock"] for c in candidates)
    """
    if not os.path.exists(master_db):
        raise FileNotFoundError(
            f"銘柄マスター DB が存在しません: {master_db}\n"
            "setup_db.sh を実行して DB を初期化してください。"
        )

    market_name = MARKET_MAP.get(market)

    # ベースクエリ
    query = "SELECT code, name, market, market_cap, last_price, unit_shares FROM stocks_master"
    params: List[Any] = []

    conditions = []
    if market_name:
        conditions.append("market LIKE ?")
        params.append(f"%{market_name}%")

    if exclude_value_stock:
        # 計算列 is_value_stock = 0 のみ（SQLite STORED GENERATED COLUMN 使用）
        conditions.append("is_value_stock = 0")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    with sqlite3.connect(master_db) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()

    candidates: List[Dict[str, Any]] = []

    for row in rows:
        price = row["last_price"] or 0.0
        unit_shares = row["unit_shares"] or 100

        # 値嵩チェック（DB の計算列を信頼するが念のためアプリ側でも確認）
        value_flag = is_value_stock(price, unit_shares) if price > 0 else False

        record: Dict[str, Any] = {
            "code":           row["code"],
            "name":           row["name"],
            "market":         row["market"],
            "market_cap":     row["market_cap"],
            "last_price":     price,
            "unit_shares":    unit_shares,
            "is_value_stock": value_flag,
        }

        # ボラティリティフィルター（オプション）
        if min_volatility_pct is not None:
            vol = calculate_volatility(prices_db, row["code"], as_of=as_of)
            record["volatility_5d_pct"] = vol
            if vol is None or vol < min_volatility_pct:
                continue

        candidates.append(record)

    logger.info(
        "Universe built: market=%s, exclude_value=%s, min_vol=%s → %d candidates",
        market, exclude_value_stock, min_volatility_pct, len(candidates),
    )
    return candidates


# ---------------------------------------------------------------------------
# CLI エントリポイント
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="ユニバース候補リスト生成")
    parser.add_argument("--market", default="growth", choices=list(MARKET_MAP.keys()))
    parser.add_argument("--no-exclude-value", action="store_true", help="値嵩除外をスキップ")
    parser.add_argument("--min-vol", type=float, help="最低日中値幅率 (%)")
    parser.add_argument("--as-of", help="基準日 YYYY-MM-DD")
    args = parser.parse_args()

    candidates = build_universe(
        market=args.market,
        exclude_value_stock=not args.no_exclude_value,
        min_volatility_pct=args.min_vol,
        as_of=args.as_of,
    )

    print(f"\n=== Universe: {len(candidates)} candidates ===")
    for c in candidates[:10]:
        print(
            f"  {c['code']} {c['name'][:15]:<15} "
            f"¥{c['last_price']:,.0f}  "
            f"{'[値嵩]' if c['is_value_stock'] else ''}"
        )
    if len(candidates) > 10:
        print(f"  ... (remaining {len(candidates) - 10} stocks)")

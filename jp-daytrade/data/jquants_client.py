"""
J-Quants API V2 クライアント

2026/04 時点で J-Quants API V1 は廃止予定となり、V2 への移行が公式アナウンスされている。
V2 の認証はダッシュボード発行の API Key を `x-api-key` ヘッダーに設定する方式で、
V1 の refresh_token → id_token フローは不要になった。

V1 → V2 主な差分:
    - Base URL:  /v1/ → /v2/
    - 認証:       Bearer id_token → x-api-key ヘッダー
    - 銘柄コード: 4桁 (例: "7203") → 5桁 (例: "72030")
    - エンドポイント:
        /listed/info            → /equities/master
        /prices/daily_quotes    → /equities/bars/daily
        /markets/trading_calendar → /markets/calendar
        /fins/statements        → /fins/summary (Freeプラン範囲)
    - パラメータ:
        dateFrom / dateTo       → from / to
    - レスポンス:
        `info` / `daily_quotes` キー → `data` キーに統一
        日足フィールド Open/High/Low/Close/Volume/TurnoverValue
                       → O/H/L/C/Vo/Va + Adj*
        マスターに MarketCapitalization / DailyClose / TradingUnit は含まれない

Freeプランのデータ期間（2026-04 時点）:
    2024-01-24 ~ 2026-01-24（直近3ヶ月は遅延）

Example:
    >>> from dotenv import load_dotenv
    >>> load_dotenv()
    >>> client = JQuantsClient()
    >>> records = client.get_listed_info()
    >>> print(records[0])
    {'Code': '13010', 'CoName': '極洋', 'MktNm': 'プライム', ...}
"""

import json
import logging
import os
import sqlite3
import time
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../config/.env"))

logger = logging.getLogger(__name__)

# J-Quants API V2 ベースURL
JQUANTS_BASE_URL = "https://api.jquants.com/v2"

# デフォルト DB パス
# 重要: SQLite DB を Google Drive 配下に置くと Drive 同期が書込中に干渉して
# "database disk image is malformed" で破損する。
# JP_DAYTRADE_DATA_DIR 環境変数でローカルディスク（例: C:/dev/jp-daytrade-data）を指定する運用を推奨。
DEFAULT_DB_DIR = os.environ.get("JP_DAYTRADE_DATA_DIR") or os.path.join(os.path.dirname(__file__))
DEFAULT_PRICES_DB = os.path.join(DEFAULT_DB_DIR, "daily_prices.db")
DEFAULT_MASTER_DB = os.path.join(DEFAULT_DB_DIR, "stocks_master.db")

# スキーマファイルパス
SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "schemas")

# Freeプランのデータ取得可能範囲（2026-04 時点、参考値）
FREE_PLAN_DATA_START = "2024-01-24"
FREE_PLAN_DATA_END = "2026-01-24"


# ---------------------------------------------------------------------------
# カスタム例外
# ---------------------------------------------------------------------------

class JPDaytradeError(Exception):
    """JP-DAYTRADE 基底例外クラス"""
    pass


class JQuantsConfigError(JPDaytradeError):
    """設定・環境変数エラー"""
    pass


class JQuantsAuthError(JPDaytradeError):
    """J-Quants 認証エラー (API Key 無効 / プラン未契約など)"""
    pass


class JQuantsAPIError(JPDaytradeError):
    """J-Quants API リクエストエラー"""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


# ---------------------------------------------------------------------------
# DB ユーティリティ
# ---------------------------------------------------------------------------

def init_db(db_path: str, schema_sql: str) -> None:
    """SQLite DB を初期化する（スキーマ適用）"""
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_sql)
        conn.commit()
    logger.info("DB initialized: %s", db_path)


def load_schema(schema_filename: str) -> str:
    """schemas/ ディレクトリからスキーマSQLを読み込む"""
    path = os.path.join(SCHEMA_DIR, schema_filename)
    with open(path, encoding="utf-8") as f:
        return f.read()


def normalize_code(code: str) -> str:
    """
    銘柄コードを V2 仕様の 5 桁に正規化する。

    - 4 桁の場合は末尾に "0" を追加（例: "7203" → "72030"）
    - 5 桁の場合はそのまま返す
    - それ以外はそのまま返す（呼び出し側で検証）

    Args:
        code: 銘柄コード

    Returns:
        5 桁の銘柄コード
    """
    if code and len(code) == 4 and code.isdigit():
        return code + "0"
    return code


# ---------------------------------------------------------------------------
# J-Quants V2 クライアント
# ---------------------------------------------------------------------------

class JQuantsClient:
    """
    J-Quants API V2 クライアント

    Args:
        api_key:       API Key（省略時は環境変数 JQUANTS_API_KEY から取得）
        prices_db:     日足DB パス
        master_db:     銘柄マスターDB パス
        max_retries:   リトライ最大回数
        retry_wait:    リトライ間隔（秒）

    Raises:
        JQuantsConfigError: JQUANTS_API_KEY が未設定の場合

    Example:
        >>> client = JQuantsClient()
        >>> info = client.get_listed_info()
        >>> prices = client.get_daily_prices("7203", "2024-02-01", "2024-02-29")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        prices_db: str = DEFAULT_PRICES_DB,
        master_db: str = DEFAULT_MASTER_DB,
        max_retries: int = 6,
        retry_wait: float = 5.0,
    ) -> None:
        self._api_key = api_key or os.environ.get("JQUANTS_API_KEY")
        if not self._api_key:
            raise JQuantsConfigError(
                "J-Quants API Key が未設定です。"
                ".env で JQUANTS_API_KEY=xxx を設定してください。"
                "取得方法: https://jpx-jquants.com/ にログイン → ダッシュボード → API Keys。"
                "Free プラン（無料）の契約が必須です。"
            )

        self.prices_db = prices_db
        self.master_db = master_db
        self.max_retries = max_retries
        self.retry_wait = retry_wait

        self._session = requests.Session()
        logger.info("JQuantsClient (V2) initialized (prices_db=%s, master_db=%s)", prices_db, master_db)

    # ------------------------------------------------------------------
    # 汎用リクエスト
    # ------------------------------------------------------------------

    def _headers(self) -> Dict[str, str]:
        return {"x-api-key": self._api_key}

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        J-Quants V2 API GET リクエスト（リトライ・レート制限・ページング非対応版）

        単純な一発 GET。ページネーションは _get_paginated() を使う。
        """
        url = f"{JQUANTS_BASE_URL}{path}"
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self._session.get(url, headers=self._headers(), params=params, timeout=30)

                if resp.status_code == 401 or resp.status_code == 403:
                    raise JQuantsAuthError(
                        f"J-Quants 認証エラー (status={resp.status_code}): {resp.text[:200]}. "
                        f"API Key が有効か、プラン契約が済んでいるか確認してください。"
                    )

                if resp.status_code == 429:
                    # 指数バックオフ（5s, 10s, 20s, 40s, 80s, 120s…最大60s下限→最大120s上限）
                    wait = min(120.0, max(self.retry_wait, self.retry_wait * (2 ** (attempt - 1))))
                    logger.warning("Rate limit hit, waiting %.1fs (attempt %d/%d)", wait, attempt, self.max_retries)
                    time.sleep(wait)
                    continue

                resp.raise_for_status()
                return resp.json()

            except JQuantsAuthError:
                raise
            except requests.HTTPError as e:
                last_error = e
                logger.warning("HTTP error on %s (attempt %d/%d): %s", path, attempt, self.max_retries, e)
                time.sleep(self.retry_wait)
            except requests.RequestException as e:
                last_error = e
                logger.warning("Request error on %s (attempt %d/%d): %s", path, attempt, self.max_retries, e)
                time.sleep(self.retry_wait)

        raise JQuantsAPIError(
            f"J-Quants APIリクエスト失敗 ({path}): {last_error}",
        )

    def _get_paginated(self, path: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        pagination_key を使って data を全ページ集約する。

        Returns:
            data 配列の全件
        """
        merged: List[Dict[str, Any]] = []
        q = dict(params or {})
        while True:
            body = self._get(path, params=q)
            page = body.get("data", [])
            merged.extend(page)
            pagination_key = body.get("pagination_key")
            if not pagination_key:
                break
            q["pagination_key"] = pagination_key
        return merged

    # ------------------------------------------------------------------
    # 銘柄マスター
    # ------------------------------------------------------------------

    def get_listed_info(self) -> List[Dict[str, Any]]:
        """
        上場銘柄一覧を取得する（V2: GET /equities/master）

        Returns:
            銘柄情報のリスト（各要素は V2 スキーマの dict）

        Example:
            >>> records = client.get_listed_info()
            >>> print(records[0].keys())
            dict_keys(['Date', 'Code', 'CoName', 'CoNameEn', 'S17', 'S17Nm',
                       'S33', 'S33Nm', 'ScaleCat', 'Mkt', 'MktNm', 'Mrgn', 'MrgnNm'])
        """
        return self._get_paginated("/equities/master")

    def save_listed_info_to_db(self, records: Optional[List[Dict[str, Any]]] = None) -> int:
        """
        銘柄マスターを SQLite に保存する。

        V2 の master レスポンスには MarketCapitalization / DailyClose / TradingUnit が含まれない。
        last_price と unit_shares は save_daily_prices 後に別途更新する想定。
        """
        if records is None:
            records = self.get_listed_info()

        schema_sql = load_schema("stocks_master.sql")
        init_db(self.master_db, schema_sql)

        now_str = datetime.now().isoformat()
        rows = []
        for r in records:
            code = r.get("Code", "")
            if not code:
                continue
            rows.append((
                code,
                r.get("CoName", ""),
                r.get("MktNm", ""),
                None,              # market_cap: V2 master には含まれない
                None,              # last_price: 日足取得後に UPDATE する前提
                100,               # unit_shares: 東証は原則 100。個別例外は別途対応
                now_str,
            ))

        with sqlite3.connect(self.master_db) as conn:
            conn.executemany(
                """INSERT OR REPLACE INTO stocks_master
                   (code, name, market, market_cap, last_price, unit_shares, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                rows,
            )
            conn.commit()

        logger.info("stocks_master: %d records saved to %s", len(rows), self.master_db)
        return len(rows)

    # ------------------------------------------------------------------
    # 日足データ
    # ------------------------------------------------------------------

    def get_daily_prices(
        self,
        code: str,
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """
        指定銘柄の日足データを取得する（V2: GET /equities/bars/daily）

        Args:
            code:       銘柄コード（4桁 or 5桁。4桁の場合は自動で5桁に正規化）
            start_date: 開始日 YYYY-MM-DD
            end_date:   終了日 YYYY-MM-DD

        Returns:
            日足データリスト。各レコードは V2 スキーマ:
            {Date, Code, O, H, L, C, UL, LL, Vo, Va, AdjFactor, AdjO, AdjH, AdjL, AdjC, AdjVo}
        """
        params = {
            "code": normalize_code(code),
            "from": start_date,
            "to": end_date,
        }
        return self._get_paginated("/equities/bars/daily", params=params)

    def save_daily_prices_to_db(self, prices: List[Dict[str, Any]]) -> int:
        """
        日足データを SQLite に書き込む。

        V2 フィールド (O/H/L/C/Vo/Va + AdjFactor) を DB カラム
        (open/high/low/close/volume/turnover/adjustment_factor) にマップする。
        """
        if not prices:
            return 0

        schema_sql = load_schema("daily_prices.sql")
        init_db(self.prices_db, schema_sql)

        rows = []
        for r in prices:
            rows.append((
                r.get("Code", ""),
                r.get("Date", ""),
                r.get("O"),
                r.get("H"),
                r.get("L"),
                r.get("C"),
                r.get("Vo"),
                r.get("Va"),
                r.get("AdjFactor", 1.0),
            ))

        with sqlite3.connect(self.prices_db) as conn:
            conn.executemany(
                """INSERT OR IGNORE INTO daily_prices
                   (code, date, open, high, low, close, volume, turnover, adjustment_factor)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                rows,
            )
            conn.commit()

        logger.info("daily_prices: %d rows saved for %d codes", len(rows), len({r[0] for r in rows}))
        return len(rows)

    # ------------------------------------------------------------------
    # マスター last_price バックフィル
    # ------------------------------------------------------------------

    def update_master_from_daily_prices(self) -> int:
        """
        stocks_master.last_price を daily_prices の最新終値で埋める。
        is_value_stock (STORED GENERATED COLUMN) の自動再計算のために実行する。
        """
        with sqlite3.connect(self.master_db) as conn:
            conn.execute(f"ATTACH DATABASE '{self.prices_db}' AS prices_db")
            cur = conn.execute(
                """
                UPDATE stocks_master
                SET last_price = (
                    SELECT close FROM prices_db.daily_prices p
                    WHERE p.code = stocks_master.code
                    ORDER BY p.date DESC LIMIT 1
                )
                WHERE EXISTS (
                    SELECT 1 FROM prices_db.daily_prices p WHERE p.code = stocks_master.code
                )
                """
            )
            updated = cur.rowcount
            conn.commit()
        logger.info("stocks_master.last_price updated for %d codes", updated)
        return updated

    # ------------------------------------------------------------------
    # バルク取得（グロース全銘柄2年分）
    # ------------------------------------------------------------------

    def _already_fetched_codes(self) -> set:
        """daily_prices DB に既にデータがある銘柄コードの集合を返す（リジューム用）"""
        if not os.path.exists(self.prices_db):
            return set()
        try:
            with sqlite3.connect(self.prices_db) as conn:
                rows = conn.execute("SELECT DISTINCT code FROM daily_prices").fetchall()
            return {r[0] for r in rows}
        except sqlite3.OperationalError:
            # テーブル未作成
            return set()

    def fetch_all_growth_market_stocks(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        request_interval: float = 6.0,
        resume: bool = True,
    ) -> Dict[str, int]:
        """
        東証グロース市場全銘柄の日足データを指定期間分取得し DB に保存する。

        Args:
            start_date:       開始日 YYYY-MM-DD。省略時は Freeプラン最古日
            end_date:         終了日 YYYY-MM-DD。省略時は Freeプラン最新日
            request_interval: リクエスト間隔（秒）。J-Quants Freeプランは実測 ~15req/min 程度まで
            resume:           True の場合、既に daily_prices DB にデータがあるコードをスキップ

        Returns:
            {"total_codes": N, "fetched": K, "skipped": S, "failed": F, "total_rows": M}
        """
        if start_date is None:
            start_date = FREE_PLAN_DATA_START
        if end_date is None:
            end_date = FREE_PLAN_DATA_END

        logger.info("Fetching growth market stocks from %s to %s (resume=%s)", start_date, end_date, resume)

        # 銘柄マスター取得 → グロース銘柄抽出
        records = self.get_listed_info()
        growth_codes = [
            r["Code"] for r in records
            if "グロース" in (r.get("MktNm") or "")
        ]
        logger.info("Growth market codes: %d", len(growth_codes))

        if not growth_codes:
            logger.warning("No growth market codes found. Check MktNm field.")
            return {"total_codes": 0, "fetched": 0, "skipped": 0, "failed": 0, "total_rows": 0}

        # マスター保存
        self.save_listed_info_to_db(records)

        already = self._already_fetched_codes() if resume else set()
        if already:
            logger.info("Resume: %d codes already in DB will be skipped", len(already))

        total_rows = 0
        fetched = 0
        skipped = 0
        failed = 0
        target = [c for c in growth_codes if c not in already]

        for i, code in enumerate(target, 1):
            try:
                prices = self.get_daily_prices(code, start_date, end_date)
                n = self.save_daily_prices_to_db(prices)
                total_rows += n
                fetched += 1
                logger.info("[%d/%d] %s: %d rows (total rows=%d)", i, len(target), code, n, total_rows)
            except JQuantsAPIError as e:
                failed += 1
                logger.error("Failed to fetch %s: %s", code, e)
            except JQuantsAuthError:
                raise  # 認証系は即停止

            if i < len(target):
                time.sleep(request_interval)

        skipped = len(growth_codes) - len(target)

        # last_price バックフィル
        self.update_master_from_daily_prices()

        return {
            "total_codes": len(growth_codes),
            "fetched": fetched,
            "skipped": skipped,
            "failed": failed,
            "total_rows": total_rows,
        }


# ---------------------------------------------------------------------------
# CLI エントリポイント
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="J-Quants V2 データ取得")
    parser.add_argument("command", choices=["listed_info", "daily_prices", "fetch_all_growth"],
                        help="実行コマンド")
    parser.add_argument("--code", help="銘柄コード（daily_prices時、4桁 or 5桁）")
    parser.add_argument("--start", help="開始日 YYYY-MM-DD")
    parser.add_argument("--end", help="終了日 YYYY-MM-DD")
    args = parser.parse_args()

    client = JQuantsClient()

    if args.command == "listed_info":
        n = client.save_listed_info_to_db()
        print(f"saved {n} records")
    elif args.command == "daily_prices":
        end = args.end or FREE_PLAN_DATA_END
        start = args.start or FREE_PLAN_DATA_START
        prices = client.get_daily_prices(args.code or "72030", start, end)
        n = client.save_daily_prices_to_db(prices)
        print(f"saved {n} rows")
    elif args.command == "fetch_all_growth":
        result = client.fetch_all_growth_market_stocks(args.start, args.end)
        print(result)

"""
kabu PUSH API 気配スナップショット保存スクリプト

8:00〜9:00 の間、1 分おきに kabu API から気配データを取得し SQLite に保存する。

動作モード:
    websocket  — kabu ステーション PUSH API (ws://localhost:18080/kabusapi/websocket)
                 本番 Surface 運用時に使用
    polling    — HTTP ポーリング (GET /kabusapi/board)
                 モック (localhost:18081) または開発環境で使用（テスト容易）

環境変数:
    KABU_API_PASSWORD   — kabu ステーション API パスワード
    KABU_API_BASE_URL   — API ベース URL (デフォルト: http://localhost:18080)
    KABU_MOCK_BASE_URL  — モック URL (デフォルト: http://localhost:18081)

使い方:
    # 本番（ポーリングモード）
    python kabu_push_recorder.py --mode polling --symbols 7203 9984

    # モック使用
    python kabu_push_recorder.py --mode polling --use-mock --symbols 7203

Example:
    >>> from jp_daytrade.data.kabu_push_recorder import KabuPushRecorder
    >>> recorder = KabuPushRecorder(use_mock=True)
    >>> recorder.record_snapshot("7203")
"""

import json
import logging
import os
import sqlite3
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../config/.env"))

logger = logging.getLogger(__name__)

# デフォルト設定
DEFAULT_PROD_BASE_URL = "http://localhost:18080"
DEFAULT_MOCK_BASE_URL = "http://localhost:18081"
DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "quotes_live.db")
SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "schemas")

# 気配取得時間帯（JST）
RECORD_START_HOUR = 8
RECORD_START_MINUTE = 0
RECORD_END_HOUR = 9
RECORD_END_MINUTE = 0


# ---------------------------------------------------------------------------
# カスタム例外
# ---------------------------------------------------------------------------

class JPDaytradeError(Exception):
    """JP-DAYTRADE 基底例外"""
    pass


class KabuAPIError(JPDaytradeError):
    """kabu API エラー"""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


# ---------------------------------------------------------------------------
# DB ユーティリティ
# ---------------------------------------------------------------------------

def init_quotes_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """
    気配スナップショット DB を初期化する。

    Args:
        db_path: SQLite ファイルパス
    """
    schema_path = os.path.join(SCHEMA_DIR, "quotes_live.sql")
    with open(schema_path, encoding="utf-8") as f:
        schema_sql = f.read()

    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_sql)
        conn.commit()
    logger.info("quotes_live DB initialized: %s", db_path)


def save_snapshot(db_path: str, snapshot: Dict[str, Any]) -> int:
    """
    気配スナップショットを DB に保存する。

    Args:
        db_path:  SQLite ファイルパス
        snapshot: get_board() レスポンス dict

    Returns:
        挿入した rowid

    Example:
        >>> rowid = save_snapshot(db_path, board_data)
        >>> assert rowid > 0
    """
    sell_levels = []
    buy_levels = []

    for i in range(1, 11):
        sell = snapshot.get(f"Sell{i}")
        if sell:
            sell_levels.append({
                "price": sell.get("Price"),
                "qty": sell.get("Qty"),
                "sign": sell.get("Sign"),
            })
        buy = snapshot.get(f"Buy{i}")
        if buy:
            buy_levels.append({
                "price": buy.get("Price"),
                "qty": buy.get("Qty"),
                "sign": buy.get("Sign"),
            })

    now_str = snapshot.get("_recorded_at") or datetime.now().isoformat()

    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            """INSERT INTO quotes_snapshot
               (symbol, timestamp, ask_sign, bid_sign,
                current_price, calc_price, over_sell, under_buy,
                sell_levels_json, buy_levels_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(snapshot.get("Symbol", "")),
                now_str,
                snapshot.get("AskSign"),
                snapshot.get("BidSign"),
                snapshot.get("CurrentPrice"),
                snapshot.get("CalcPrice"),
                snapshot.get("OverSell"),
                snapshot.get("UnderBuy"),
                json.dumps(sell_levels, ensure_ascii=False),
                json.dumps(buy_levels, ensure_ascii=False),
            ),
        )
        conn.commit()
        rowid = cursor.lastrowid

    logger.debug("Snapshot saved: symbol=%s ts=%s rowid=%s", snapshot.get("Symbol"), now_str, rowid)
    return rowid  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# kabu API HTTP クライアント
# ---------------------------------------------------------------------------

class KabuHTTPClient:
    """
    kabu ステーション API の HTTP クライアント（REST / ポーリング用）。

    Args:
        base_url:    API ベース URL
        api_password: API パスワード（省略時は環境変数 KABU_API_PASSWORD）

    Example:
        >>> client = KabuHTTPClient("http://localhost:18081", "mock_pw")
        >>> board = client.get_board("7203")
    """

    def __init__(
        self,
        base_url: str = DEFAULT_PROD_BASE_URL,
        api_password: Optional[str] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._api_password = api_password or os.environ.get("KABU_API_PASSWORD", "")
        self._token: Optional[str] = None
        self._session = requests.Session()

    def _get_token(self) -> str:
        """
        API トークンを取得する。

        Returns:
            トークン文字列

        Raises:
            KabuAPIError: トークン取得失敗
        """
        if self._token:
            return self._token

        url = f"{self.base_url}/kabusapi/token"
        try:
            resp = self._session.post(
                url,
                json={"APIPassword": self._api_password},
                timeout=10,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            raise KabuAPIError(f"kabu API トークン取得失敗 ({url}): {e}") from e

        data = resp.json()
        self._token = data.get("Token")
        if not self._token:
            raise KabuAPIError(f"Token がレスポンスに含まれていません: {data}")

        logger.info("kabu API token acquired from %s", self.base_url)
        return self._token

    def get_board(self, symbol: str, exchange: int = 1) -> Dict[str, Any]:
        """
        板情報・気配データを取得する。

        Args:
            symbol:   銘柄コード（例: "7203"）
            exchange: 取引所コード（1=東証）

        Returns:
            板情報 dict

        Raises:
            KabuAPIError: リクエスト失敗

        Example:
            >>> board = client.get_board("7203")
            >>> assert "AskSign" in board
        """
        token = self._get_token()
        url = f"{self.base_url}/kabusapi/board/{symbol}@{exchange}"
        try:
            resp = self._session.get(
                url,
                headers={"X-API-KEY": token},
                timeout=10,
            )
            resp.raise_for_status()
        except requests.HTTPError as e:
            raise KabuAPIError(
                f"board 取得失敗 (symbol={symbol}, status={resp.status_code}): {resp.text}",
                status_code=resp.status_code,
            ) from e
        except requests.RequestException as e:
            raise KabuAPIError(f"board リクエスト失敗 (symbol={symbol}): {e}") from e

        return resp.json()


# ---------------------------------------------------------------------------
# レコーダー
# ---------------------------------------------------------------------------

class KabuPushRecorder:
    """
    kabu 気配スナップショット保存クラス

    ポーリングモード（デフォルト）と WebSocket モードに対応する。
    テスト・開発時は use_mock=True でモックサーバーを使用する。

    Args:
        db_path:   SQLite 書き込み先
        use_mock:  True のとき localhost:18081 モックに接続
        base_url:  カスタム API URL（省略時は use_mock に従う）
        interval:  ポーリング間隔（秒）

    Example:
        >>> recorder = KabuPushRecorder(use_mock=True)
        >>> recorder.init_db()
        >>> rowid = recorder.record_snapshot("7203")
        >>> assert rowid > 0
    """

    def __init__(
        self,
        db_path: str = DEFAULT_DB_PATH,
        use_mock: bool = False,
        base_url: Optional[str] = None,
        interval: float = 60.0,
    ) -> None:
        self.db_path = db_path
        self.interval = interval

        if base_url:
            _base = base_url
        elif use_mock:
            _base = DEFAULT_MOCK_BASE_URL
        else:
            _base = os.environ.get("KABU_API_BASE_URL", DEFAULT_PROD_BASE_URL)

        self._client = KabuHTTPClient(_base)
        logger.info("KabuPushRecorder initialized (db=%s, base_url=%s)", db_path, _base)

    def init_db(self) -> None:
        """DB を初期化する（初回実行時に呼ぶ）。"""
        init_quotes_db(self.db_path)

    def record_snapshot(self, symbol: str, exchange: int = 1) -> int:
        """
        指定銘柄の気配スナップショットを 1 件取得して DB に保存する。

        Args:
            symbol:   銘柄コード
            exchange: 取引所コード（1=東証）

        Returns:
            保存した rowid

        Raises:
            KabuAPIError: API リクエスト失敗

        Example:
            >>> rowid = recorder.record_snapshot("7203")
            >>> assert rowid > 0
        """
        board = self._client.get_board(symbol, exchange)
        board["_recorded_at"] = datetime.now().isoformat()
        rowid = save_snapshot(self.db_path, board)
        logger.info("Snapshot recorded: symbol=%s rowid=%d", symbol, rowid)
        return rowid

    def run_polling(
        self,
        symbols: List[str],
        exchange: int = 1,
        check_time_window: bool = True,
    ) -> None:
        """
        指定銘柄を 1 分おきにポーリングして気配を保存する（8:00〜9:00）。

        Args:
            symbols:           監視銘柄コードリスト
            exchange:          取引所コード（1=東証）
            check_time_window: True のとき 8:00-9:00 以外は処理をスキップ

        Example:
            >>> recorder = KabuPushRecorder(use_mock=True, interval=1.0)
            >>> recorder.init_db()
            >>> # テストでは check_time_window=False で動作確認
            >>> recorder.run_polling(["7203"], check_time_window=False)
        """
        logger.info("Starting polling recorder (symbols=%s, interval=%.0fs)", symbols, self.interval)
        self.init_db()

        while True:
            now = datetime.now()

            if check_time_window:
                in_window = (
                    (now.hour == RECORD_START_HOUR and now.minute >= RECORD_START_MINUTE)
                    or (now.hour == RECORD_END_HOUR and now.minute < RECORD_END_MINUTE)
                ) and now.hour < RECORD_END_HOUR + 1

                if not in_window:
                    # 時間外は 30 秒待機してから再チェック
                    logger.debug("Outside time window (%02d:%02d), sleeping 30s", now.hour, now.minute)
                    time.sleep(30)
                    continue

            for symbol in symbols:
                try:
                    self.record_snapshot(symbol, exchange)
                except KabuAPIError as e:
                    logger.error("Failed to record %s: %s", symbol, e)

            time.sleep(self.interval)

    def run_websocket(self, symbols: List[str], exchange: int = 1) -> None:
        """
        WebSocket (PUSH API) で気配データをリアルタイム受信して保存する。

        本番 kabu ステーション接続用（工程3以降で実装完成）。
        現在はスケルトン実装。

        Args:
            symbols:  監視銘柄コードリスト
            exchange: 取引所コード

        Raises:
            NotImplementedError: スケルトン実装中
        """
        try:
            import websocket  # noqa: F401
        except ImportError:
            logger.error("websocket-client が未インストールです: pip install websocket-client")
            raise

        # TODO(工程3): WebSocket PUSH 接続実装
        # 手順:
        #   1. POST /kabusapi/token でトークン取得
        #   2. PUT /kabusapi/register で銘柄登録
        #   3. ws://localhost:18080/kabusapi/websocket に接続
        #   4. on_message コールバックで JSON パース → save_snapshot()
        raise NotImplementedError(
            "WebSocket PUSH モードは工程3で実装します。"
            "開発・テスト時は --mode polling --use-mock を使用してください。"
        )


# ---------------------------------------------------------------------------
# CLI エントリポイント
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    parser = argparse.ArgumentParser(description="kabu 気配スナップショット保存")
    parser.add_argument(
        "--mode", choices=["polling", "websocket"], default="polling",
        help="動作モード（デフォルト: polling）",
    )
    parser.add_argument("--use-mock", action="store_true", help="モックサーバー (localhost:18081) を使用")
    parser.add_argument("--symbols", nargs="+", default=["7203"], help="監視銘柄コード")
    parser.add_argument("--interval", type=float, default=60.0, help="ポーリング間隔（秒）")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="SQLite 書き込み先")
    parser.add_argument("--no-time-window", action="store_true", help="時間帯チェックをスキップ（デバッグ用）")
    args = parser.parse_args()

    recorder = KabuPushRecorder(
        db_path=args.db,
        use_mock=args.use_mock,
        interval=args.interval,
    )

    if args.mode == "polling":
        recorder.run_polling(
            args.symbols,
            check_time_window=not args.no_time_window,
        )
    else:
        recorder.run_websocket(args.symbols)
